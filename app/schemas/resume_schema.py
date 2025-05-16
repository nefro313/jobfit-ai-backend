

from pydantic import BaseModel


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
    achievements: list[str]

# Main model matching the expected JSON schema
class ResumeData(BaseModel):
    name: str
    about_me: str
    contact_info: ContactInfo
    education: list[Education]
    experience: list[Experience]
    skills: list[str]
    soft_skills: list[str]

