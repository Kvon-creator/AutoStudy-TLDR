import pdfplumber
from pydantic import BaseModel
from typing import List, Optional

class CourseMilestone(BaseModel):
    title: str
    date_str: str
    weight: Optional[float] = 0.0

class TopicNode(BaseModel):
    name: str
    week: int
    prerequisites: List[str] = []

def extract_raw_text(file_path: str) -> str:
    """Reads raw text from either PDF or TXT files."""
    if file_path.endswith(".pdf"):
        full_text = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)
        return "\n".join(full_text)
    elif file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError("Unsupported format. Please provide a .pdf or .txt file.")