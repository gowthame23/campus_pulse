"""
ML-assisted complaint classification.

Predicts department_id and complaint_type from a complaint's free-text
description, trained on existing rows in the `complaints` table. Used as an
assistive signal on submission — it auto-fills complaint_type only when the
caller didn't supply one, and only ever *suggests* a department_id (via
logging) rather than overriding the caller-supplied one, since department_id
is a required, routing-critical field validated elsewhere.

The training set in this database is currently tiny (a handful of rows), so
predictions below CONFIDENCE_THRESHOLD are treated as "no suggestion" and
training itself is skipped for a target that doesn't have enough samples or
distinct classes to learn from. Nothing in this module ever raises out to
its caller — failures are logged and degrade to "no prediction".
"""

import sqlite3
import threading

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from utils.logger import get_logger

logger = get_logger(__name__)

MIN_SAMPLES_PER_TARGET = 4
MIN_CLASSES_PER_TARGET = 2
CONFIDENCE_THRESHOLD = 0.35


class ClassificationResult:
    def __init__(
        self,
        department_id=None,
        department_confidence=0.0,
        complaint_type=None,
        complaint_type_confidence=0.0,
        trained_on=0,
    ):
        self.department_id = department_id
        self.department_confidence = department_confidence
        self.complaint_type = complaint_type
        self.complaint_type_confidence = complaint_type_confidence
        self.trained_on = trained_on

    def to_dict(self):
        return {
            "department_id": self.department_id,
            "department_confidence": round(self.department_confidence, 4),
            "complaint_type": self.complaint_type,
            "complaint_type_confidence": round(self.complaint_type_confidence, 4),
            "trained_on": self.trained_on,
        }


def _build_pipeline():
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(min_df=1, ngram_range=(1, 2), stop_words="english")),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )


class ClassificationService:
    """Trains on Backend/storage/campus_pulse.db `complaints` rows and
    predicts department_id / complaint_type for a new complaint description."""

    def __init__(self, db_path="storage/campus_pulse.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._department_model = None
        self._complaint_type_model = None
        self._trained_on = 0
        self._trained = False

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def _fetch_training_rows(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT description, department_id, complaint_type
                FROM complaints
                WHERE description IS NOT NULL AND TRIM(description) != ''
                  AND department_id IS NOT NULL AND TRIM(department_id) != ''
                  AND complaint_type IS NOT NULL AND TRIM(complaint_type) != ''
                """
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def train(self, force=False):
        """(Re)trains the department_id and complaint_type classifiers from
        the current `complaints` table. No-ops if already trained unless
        force=True. Never raises: logs and leaves the service untrained if
        data is too sparse or scikit-learn isn't installed, in which case
        predict() simply returns empty predictions."""
        if self._trained and not force:
            return

        with self._lock:
            if self._trained and not force:
                return

            if not SKLEARN_AVAILABLE:
                logger.warning(
                    "classification_service: scikit-learn not installed — "
                    "complaint auto-classification disabled."
                )
                return

            try:
                rows = self._fetch_training_rows()
            except Exception:
                logger.exception("classification_service: failed to load training data")
                return

            descriptions = [r["description"] for r in rows]

            self._department_model = self._train_target(
                descriptions, [r["department_id"] for r in rows], "department_id"
            )
            self._complaint_type_model = self._train_target(
                descriptions, [r["complaint_type"] for r in rows], "complaint_type"
            )
            self._trained_on = len(rows)
            self._trained = True

            logger.info(
                f"classification_service: trained on {len(rows)} complaint(s) "
                f"(department model {'ready' if self._department_model else 'skipped'}, "
                f"complaint_type model {'ready' if self._complaint_type_model else 'skipped'})"
            )

    def _train_target(self, descriptions, labels, target_name):
        n_classes = len(set(labels))
        if len(descriptions) < MIN_SAMPLES_PER_TARGET or n_classes < MIN_CLASSES_PER_TARGET:
            logger.info(
                f"classification_service: skipping '{target_name}' model — "
                f"{len(descriptions)} sample(s) across {n_classes} class(es), need >= "
                f"{MIN_SAMPLES_PER_TARGET} samples and >= {MIN_CLASSES_PER_TARGET} classes."
            )
            return None
        try:
            pipeline = _build_pipeline()
            pipeline.fit(descriptions, labels)
            return pipeline
        except Exception:
            logger.exception(f"classification_service: training failed for '{target_name}'")
            return None

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------
    def predict(self, description):
        """Returns a ClassificationResult. department_id / complaint_type are
        None when the corresponding model isn't trained/available or the top
        prediction falls below CONFIDENCE_THRESHOLD — callers should treat
        that as 'no suggestion', not as an error."""
        if not description or not description.strip():
            return ClassificationResult(trained_on=self._trained_on)

        if not self._trained:
            self.train()

        department_id, department_conf = self._predict_one(self._department_model, description)
        complaint_type, complaint_conf = self._predict_one(self._complaint_type_model, description)

        return ClassificationResult(
            department_id=department_id,
            department_confidence=department_conf,
            complaint_type=complaint_type,
            complaint_type_confidence=complaint_conf,
            trained_on=self._trained_on,
        )

    @staticmethod
    def _predict_one(pipeline, description):
        if pipeline is None:
            return None, 0.0
        try:
            proba = pipeline.predict_proba([description])[0]
            classes = pipeline.classes_
            best_index = proba.argmax()
            confidence = float(proba[best_index])
            if confidence < CONFIDENCE_THRESHOLD:
                return None, confidence
            return str(classes[best_index]), confidence
        except Exception:
            logger.exception("classification_service: prediction failed")
            return None, 0.0
