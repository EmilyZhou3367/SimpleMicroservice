from pydantic import BaseModel, Field, EmailStr
from typing import Optional
class Course(BaseModel):
    code: str = Field(..., description="Catalog code, e.g., 'COMS W4153'")
    title: str = Field(..., description="Course title")
    instructor: str = Field(..., description="Instructor name")
    credits: int = Field(..., ge=0, le=6, description="Number of credit hours")
    dept_id: str = Field(..., description="Department identifier, e.g., 'COMS'")

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "COMS W4153",
                "title": "Cloud Computing",
                "instructor": "Donald F. Ferguson",
                "credits": 3,
                "dept_id": "COMS"
            }
        }
    }

class Enrollment(BaseModel):
    uni: str = Field(..., min_length=2, description="Student UNI, e.g., 'abc1234'")
    course_code: str = Field(..., description="Course catalog code, e.g., 'COMS W4153'")
    year: int = Field(..., description="Academic year, e.g., 2025")
    term: str = Field(..., description="Term identifier: 'FALL', 'SPRING', 'SUMMER'")
    status: str = Field(..., description="Enrollment status: 'enrolled', 'waitlisted', 'dropped'")

    model_config = {
        "json_schema_extra": {
            "example": {
                "uni": "abc1234",
                "course_code": "COMS W4153",
                "year": 2025,
                "term": "FALL",
                "status": "enrolled"
            }
        }
    }