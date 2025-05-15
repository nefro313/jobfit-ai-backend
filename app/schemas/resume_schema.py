from pydantic import BaseModel
from typing import List

# Define sub-models for nested structures
class ContactInfo(BaseModel):
    address: str
    phone: str
    email: str
    github: str
    linkedin: str

class Education(BaseModel):
    degree: str
    institution: str
    start_date: str
    end_date: str

class Experience(BaseModel):
    job_title: str
    company: str
    start_date: str
    end_date: str
    achievements: List[str]

# Main model matching the expected JSON schema
class ResumeData(BaseModel):
    name: str
    about_me: str
    contact_info: ContactInfo
    education: List[Education]
    experience: List[Experience]
    skills: List[str]
    soft_skills: List[str]

