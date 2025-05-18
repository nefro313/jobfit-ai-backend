

from pydantic import BaseModel


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

class ResumeData(BaseModel):
    name: str
    about_me: str
    contact_info: ContactInfo
    education: list[Education]
    experience: list[Experience]
    skills: list[str]
    soft_skills: list[str]

