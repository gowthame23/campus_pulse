from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import get_feedback_service
from api.security import block_super_admin, get_current_user, require_roles
from models.administrator import Administrator
from models.app_manager import AppManager
from models.coordinator import Coordinator
from models.location_in_charge import LocationInCharge

router = APIRouter(
    prefix="/feedback", tags=["feedback"], dependencies=[Depends(block_super_admin)]
)


# ==========================================
# SCHEMAS
# ==========================================
class TemplateCreateRequest(BaseModel):
    feedback_type: str
    title: str


class QuestionCreateRequest(BaseModel):
    question: str
    question_type: str = "Rating"
    required: bool = True
    display_order: int = 0


class AnswerItem(BaseModel):
    question_id: str
    answer_value: Any


class FeedbackSubmitRequest(BaseModel):
    feedback_type: str = "Complaint"
    reference_id: Optional[str] = ""
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field("", max_length=200)
    comments: Optional[str] = Field("", max_length=2000)
    anonymous: bool = False
    answers: Optional[List[AnswerItem]] = None


class StaffResponseRequest(BaseModel):
    response: str


# ==========================================
# 1. TEMPLATES & QUESTIONS API
# ==========================================
@router.get("/templates")
def list_templates(
    feedback_type: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    feedback_service=Depends(get_feedback_service),
):
    return feedback_service.list_templates(feedback_type=feedback_type)


@router.post("/templates", status_code=status.HTTP_201_CREATED)
def create_template(
    payload: TemplateCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    feedback_service=Depends(get_feedback_service),
):
    return feedback_service.create_template(
        feedback_type=payload.feedback_type, title=payload.title
    )


@router.get("/templates/{template_id}/questions")
def get_template_questions(
    template_id: str,
    current_user=Depends(get_current_user),
    feedback_service=Depends(get_feedback_service),
):
    return feedback_service.get_template_questions(template_id)


@router.post("/templates/{template_id}/questions", status_code=status.HTTP_201_CREATED)
def add_question(
    template_id: str,
    payload: QuestionCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    feedback_service=Depends(get_feedback_service),
):
    return feedback_service.add_question(
        template_id=template_id,
        question=payload.question,
        question_type=payload.question_type,
        required=payload.required,
        display_order=payload.display_order,
    )


# ==========================================
# 2. FEEDBACK SUBMISSION & QUERIES API
# ==========================================
@router.post("", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackSubmitRequest,
    current_user=Depends(get_current_user),
    feedback_service=Depends(get_feedback_service),
):
    try:
        return feedback_service.submit_feedback(
            feedback_type=payload.feedback_type,
            reference_id=payload.reference_id,
            submitted_by=current_user.user_id,
            rating=payload.rating,
            title=payload.title,
            comments=payload.comments,
            anonymous=payload.anonymous,
            answers=[a.dict() for a in payload.answers] if payload.answers else None,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("")
def list_feedback(
    feedback_type: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    rating: Optional[int] = Query(None, ge=1, le=5),
    status_filter: Optional[str] = Query(None, alias="status"),
    my_feedback: bool = Query(False),
    q: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    feedback_service=Depends(get_feedback_service),
):
    sub_by = (
        current_user.user_id
        if (my_feedback or current_user.role == "student")
        else None
    )
    return feedback_service.list_feedback(
        feedback_type=feedback_type,
        assigned_to=assigned_to,
        rating=rating,
        status=status_filter,
        submitted_by=sub_by,
        q=q,
        user=current_user,
    )


@router.get("/pending")
def list_pending_services(
    current_user=Depends(get_current_user),
    feedback_service=Depends(get_feedback_service),
):
    return feedback_service.list_pending_services(user_id=current_user.user_id)


@router.get("/analytics")
def get_feedback_analytics(
    current_user=Depends(
        require_roles(
            Administrator.ROLE, AppManager.ROLE, Coordinator.ROLE, LocationInCharge.ROLE
        )
    ),
    feedback_service=Depends(get_feedback_service),
):
    return feedback_service.get_analytics()


@router.get("/reports")
def get_feedback_reports(
    current_user=Depends(
        require_roles(
            Administrator.ROLE, AppManager.ROLE, Coordinator.ROLE, LocationInCharge.ROLE
        )
    ),
    feedback_service=Depends(get_feedback_service),
):
    return feedback_service.get_analytics()


@router.get("/{feedback_id}")
def get_feedback(
    feedback_id: str,
    current_user=Depends(get_current_user),
    feedback_service=Depends(get_feedback_service),
):
    fb = feedback_service.get_feedback(feedback_id, user=current_user)
    if not fb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found."
        )
    return fb


# ==========================================
# 3. STAFF RESPONSES API
# ==========================================
@router.post("/{feedback_id}/response", status_code=status.HTTP_201_CREATED)
def add_staff_response(
    feedback_id: str,
    payload: StaffResponseRequest,
    current_user=Depends(
        require_roles(
            Administrator.ROLE, AppManager.ROLE, Coordinator.ROLE, LocationInCharge.ROLE
        )
    ),
    feedback_service=Depends(get_feedback_service),
):
    try:
        return feedback_service.add_staff_response(
            feedback_id=feedback_id,
            responded_by=current_user.user_id,
            response_text=payload.response,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/{feedback_id}/responses")
def get_staff_responses(
    feedback_id: str,
    current_user=Depends(get_current_user),
    feedback_service=Depends(get_feedback_service),
):
    fb = feedback_service.get_feedback(feedback_id)
    if not fb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found."
        )
    staff_roles = (
        Administrator.ROLE.lower(),
        AppManager.ROLE.lower(),
        Coordinator.ROLE.lower(),
        LocationInCharge.ROLE.lower(),
    )
    if current_user.role.lower() not in staff_roles and fb.get("submitted_by") != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view responses for this feedback.",
        )
    return fb.get("responses", [])
