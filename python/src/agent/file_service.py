"""File handling service for agent document processing."""

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")


class FileService:
    """Service for handling file uploads and generated outputs."""

    def __init__(self):
        UPLOAD_DIR.mkdir(exist_ok=True)
        OUTPUT_DIR.mkdir(exist_ok=True)

    async def save_upload(self, file_content: bytes, filename: str) -> Tuple[str, str, str]:
        """Save an uploaded file and return (file_id, file_path, file_type).

        Args:
            file_content: File bytes
            filename: Original filename

        Returns:
            (file_id, stored_path, file_type)
        """
        file_id = str(uuid.uuid4())
        ext = Path(filename).suffix.lower()
        stored_name = f"{file_id}{ext}"
        stored_path = UPLOAD_DIR / stored_name

        with open(stored_path, 'wb') as f:
            f.write(file_content)

        file_type = self._get_file_type(ext)
        return file_id, str(stored_path), file_type

    def _get_file_type(self, ext: str) -> str:
        """Determine file type from extension."""
        if ext in ['.xlsx', '.xls']:
            return 'excel'
        elif ext in ['.docx', '.doc']:
            return 'word'
        return 'unknown'

    async def get_file_path(self, file_id: str) -> Optional[str]:
        """Get the stored file path for a file_id."""
        for ext in ['.xlsx', '.xls', '.docx', '.doc']:
            path = UPLOAD_DIR / f"{file_id}{ext}"
            if path.exists():
                return str(path)
        return None

    async def cleanup_file(self, file_id: str) -> None:
        """Delete an uploaded file and all related generated files."""
        # Delete uploaded file
        for ext in ['.xlsx', '.xls', '.docx', '.doc']:
            path = UPLOAD_DIR / f"{file_id}{ext}"
            if path.exists():
                path.unlink()

        # Delete output file
        for ext in ['.xlsx', '.docx']:
            output_path = OUTPUT_DIR / f"{file_id}_output{ext}"
            if output_path.exists():
                output_path.unlink()

        # Delete chart image if exists
        chart_path = OUTPUT_DIR / f"{file_id}_chart.png"
        if chart_path.exists():
            chart_path.unlink()

    def get_output_path(self, file_id: str, file_type: str) -> str:
        """Get path for a generated output file."""
        if file_type == 'excel':
            return str(OUTPUT_DIR / f"{file_id}_output.xlsx")
        else:
            return str(OUTPUT_DIR / f"{file_id}_output.docx")


file_service = FileService()