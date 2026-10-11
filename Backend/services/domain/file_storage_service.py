from pathlib import Path
from utils.helper import generate_id

class FileStorageService:
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf", "docx", "xlsx", "csv", "txt"}
    MAX_FILE_SIZE_MB = 10

    def __init__(self, upload_dir="storage/attachments"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, filename: str, file_size_bytes: int, content_bytes: bytes = None) -> bool:
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension '.{ext}' is not allowed.")
        if file_size_bytes > self.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"File size exceeds maximum limit of {self.MAX_FILE_SIZE_MB}MB.")
        if content_bytes:
            head = content_bytes[:2048].lower()
            if b"<script" in head or b"<?php" in head or b"<% " in head:
                raise ValueError("File content contains invalid executable script signatures.")
        return True

    def save_file(self, filename: str, content_bytes: bytes, subfolder: str = "") -> str:
        self.validate_file(filename, len(content_bytes), content_bytes=content_bytes)
        file_id = generate_id("FILE")
        safe_name = f"{file_id}_{filename.replace(' ', '_')}"
        target_dir = self.upload_dir / subfolder if subfolder else self.upload_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        filepath = target_dir / safe_name

        with open(filepath, "wb") as f:
            f.write(content_bytes)

        return str(filepath)
