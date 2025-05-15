import os

from typing import Any, Optional

class PDFProcessor:
    """
    Utility class for processing PDF files
    """
    def __init__(self, file: Any):
        """
        Initialize PDF Processor
        
        :param file: Uploaded file object
        """
        self.file = file
        self.filename = self._sanitize_filename(file.filename)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent security risks
        
        :param filename: Original filename
        :return: Sanitized filename
        """
        # Remove potentially harmful characters
        safe_filename = "".join(
            c for c in filename 
            if c.isalnum() or c in ('-', '_', '.')
        ).rstrip()
        
        # Ensure unique filename
        import uuid
        return f"{uuid.uuid4()}_{safe_filename}"
    
    def save_file(self, upload_directory: str) -> str:
        """
        Save uploaded file to specified directory
        
        :param upload_directory: Directory to save file
        :return: Full path of saved file
        """
        # Ensure upload directory exists
        os.makedirs(upload_directory, exist_ok=True)
        
        # Construct full file path
        file_path = os.path.join(upload_directory, self.filename)
        
        # Save file
        try:
            with open(file_path, 'wb') as buffer:
                buffer.write(self.file.file.read())
            return file_path
        except IOError as e:
            raise IOError(f"Failed to save file: {e}")

