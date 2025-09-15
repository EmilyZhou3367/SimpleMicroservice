from __future__ import annotations

import os
import socket
from datetime import datetime

from typing import Dict, List
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi import Query, Path
from typing import Optional

from models.person import PersonCreate, PersonRead, PersonUpdate
from models.address import AddressCreate, AddressRead, AddressUpdate
from models.health import Health

from models.my_models import Course, Enrollment


port = int(os.environ.get("FASTAPIPORT", 8000))

# -----------------------------------------------------------------------------
# Fake in-memory "databases"
# -----------------------------------------------------------------------------
persons: Dict[UUID, PersonRead] = {}
addresses: Dict[UUID, AddressRead] = {}

app = FastAPI(
    title="Person/Address API",
    description="Demo FastAPI app using Pydantic v2 models for Person and Address",
    version="0.1.0",
)

# -----------------------------------------------------------------------------
# Fake in-memory "databases" for Course / Enrollment
# -----------------------------------------------------------------------------
courses: Dict[str, Course] = {}  # key = course.code
enrollments: Dict[str, Enrollment] = {}  # key = f"{uni}|{course_code}|{year}|{term}"

def _enroll_key(uni: str, course_code: str, year: int, term: str) -> str:
    return f"{uni}|{course_code}|{year}|{term}"

# -----------------------------------------------------------------------------
# Address endpoints
# -----------------------------------------------------------------------------

def make_health(echo: Optional[str], path_echo: Optional[str]=None) -> Health:
    return Health(
        status=200,
        status_message="OK",
        timestamp=datetime.utcnow().isoformat() + "Z",
        ip_address=socket.gethostbyname(socket.gethostname()),
        echo=echo,
        path_echo=path_echo
    )

@app.get("/health", response_model=Health)
def get_health_no_path(echo: str | None = Query(None, description="Optional echo string")):
    # Works because path_echo is optional in the model
    return make_health(echo=echo, path_echo=None)

@app.get("/health/{path_echo}", response_model=Health)
def get_health_with_path(
    path_echo: str = Path(..., description="Required echo in the URL path"),
    echo: str | None = Query(None, description="Optional echo string"),
):
    return make_health(echo=echo, path_echo=path_echo)

@app.post("/addresses", response_model=AddressRead, status_code=201)
def create_address(address: AddressCreate):
    if address.id in addresses:
        raise HTTPException(status_code=400, detail="Address with this ID already exists")
    addresses[address.id] = AddressRead(**address.model_dump())
    return addresses[address.id]

@app.get("/addresses", response_model=List[AddressRead])
def list_addresses(
    street: Optional[str] = Query(None, description="Filter by street"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state/region"),
    postal_code: Optional[str] = Query(None, description="Filter by postal code"),
    country: Optional[str] = Query(None, description="Filter by country"),
):
    results = list(addresses.values())

    if street is not None:
        results = [a for a in results if a.street == street]
    if city is not None:
        results = [a for a in results if a.city == city]
    if state is not None:
        results = [a for a in results if a.state == state]
    if postal_code is not None:
        results = [a for a in results if a.postal_code == postal_code]
    if country is not None:
        results = [a for a in results if a.country == country]

    return results

@app.get("/addresses/{address_id}", response_model=AddressRead)
def get_address(address_id: UUID):
    if address_id not in addresses:
        raise HTTPException(status_code=404, detail="Address not found")
    return addresses[address_id]

@app.patch("/addresses/{address_id}", response_model=AddressRead)
def update_address(address_id: UUID, update: AddressUpdate):
    if address_id not in addresses:
        raise HTTPException(status_code=404, detail="Address not found")
    stored = addresses[address_id].model_dump()
    stored.update(update.model_dump(exclude_unset=True))
    addresses[address_id] = AddressRead(**stored)
    return addresses[address_id]

# -----------------------------------------------------------------------------
# Person endpoints
# -----------------------------------------------------------------------------
@app.post("/persons", response_model=PersonRead, status_code=201)
def create_person(person: PersonCreate):
    # Each person gets its own UUID; stored as PersonRead
    person_read = PersonRead(**person.model_dump())
    persons[person_read.id] = person_read
    return person_read

@app.get("/persons", response_model=List[PersonRead])
def list_persons(
    uni: Optional[str] = Query(None, description="Filter by Columbia UNI"),
    first_name: Optional[str] = Query(None, description="Filter by first name"),
    last_name: Optional[str] = Query(None, description="Filter by last name"),
    email: Optional[str] = Query(None, description="Filter by email"),
    phone: Optional[str] = Query(None, description="Filter by phone number"),
    birth_date: Optional[str] = Query(None, description="Filter by date of birth (YYYY-MM-DD)"),
    city: Optional[str] = Query(None, description="Filter by city of at least one address"),
    country: Optional[str] = Query(None, description="Filter by country of at least one address"),
):
    results = list(persons.values())

    if uni is not None:
        results = [p for p in results if p.uni == uni]
    if first_name is not None:
        results = [p for p in results if p.first_name == first_name]
    if last_name is not None:
        results = [p for p in results if p.last_name == last_name]
    if email is not None:
        results = [p for p in results if p.email == email]
    if phone is not None:
        results = [p for p in results if p.phone == phone]
    if birth_date is not None:
        results = [p for p in results if str(p.birth_date) == birth_date]

    # nested address filtering
    if city is not None:
        results = [p for p in results if any(addr.city == city for addr in p.addresses)]
    if country is not None:
        results = [p for p in results if any(addr.country == country for addr in p.addresses)]

    return results

@app.get("/persons/{person_id}", response_model=PersonRead)
def get_person(person_id: UUID):
    if person_id not in persons:
        raise HTTPException(status_code=404, detail="Person not found")
    return persons[person_id]

@app.patch("/persons/{person_id}", response_model=PersonRead)
def update_person(person_id: UUID, update: PersonUpdate):
    if person_id not in persons:
        raise HTTPException(status_code=404, detail="Person not found")
    stored = persons[person_id].model_dump()
    stored.update(update.model_dump(exclude_unset=True))
    persons[person_id] = PersonRead(**stored)
    return persons[person_id]

# -----------------------------------------------------------------------------
# Course endpoints
# -----------------------------------------------------------------------------
@app.post("/courses", response_model=Course, status_code=201)
def create_course(course: Course):
    if course.code in courses:
        raise HTTPException(status_code=400, detail="Course with this code already exists")
    courses[course.code] = course
    return course

@app.get("/courses", response_model=List[Course])
def list_courses(
    code: Optional[str] = Query(None, description="Filter by exact course code, e.g., 'COMS W4153'"),
    dept_id: Optional[str] = Query(None, description="Filter by department id, e.g., 'COMS'"),
    instructor: Optional[str] = Query(None, description="Filter by instructor name"),
    min_credits: Optional[int] = Query(None, ge=0, description="Minimum credits"),
    max_credits: Optional[int] = Query(None, ge=0, description="Maximum credits"),
):
    results = list(courses.values())
    if code is not None:
        results = [c for c in results if c.code == code]
    if dept_id is not None:
        results = [c for c in results if c.dept_id == dept_id]
    if instructor is not None:
        results = [c for c in results if c.instructor == instructor]
    if min_credits is not None:
        results = [c for c in results if c.credits >= min_credits]
    if max_credits is not None:
        results = [c for c in results if c.credits <= max_credits]
    return results

@app.get("/courses/{course_code}", response_model=Course)
def get_course(
    course_code: str = Path(..., description="Catalog code, e.g., 'COMS W4153'")
):
    if course_code not in courses:
        raise HTTPException(status_code=404, detail="Course not found")
    return courses[course_code]

# -----------------------------------------------------------------------------
# Enrollment endpoints
# -----------------------------------------------------------------------------
@app.post("/enrollments", response_model=Enrollment, status_code=201)
def create_enrollment(enrollment: Enrollment):
    key = _enroll_key(enrollment.uni, enrollment.course_code, enrollment.year, enrollment.term)
    if key in enrollments:
        raise HTTPException(status_code=400, detail="Enrollment already exists for this (uni, course, year, term)")
    enrollments[key] = enrollment
    return enrollment

@app.get("/enrollments", response_model=List[Enrollment])
def list_enrollments(
    uni: Optional[str] = Query(None, description="Filter by student UNI"),
    course_code: Optional[str] = Query(None, description="Filter by course catalog code"),
    year: Optional[int] = Query(None, description="Filter by academic year"),
    term: Optional[str] = Query(None, description="Filter by term: 'FALL','SPRING','SUMMER'"),
    status: Optional[str] = Query(None, description="Filter by status: 'enrolled','waitlisted','dropped'"),
):
    results = list(enrollments.values())
    if uni is not None:
        results = [e for e in results if e.uni == uni]
    if course_code is not None:
        results = [e for e in results if e.course_code == course_code]
    if year is not None:
        results = [e for e in results if e.year == year]
    if term is not None:
        results = [e for e in results if e.term == term]
    if status is not None:
        results = [e for e in results if e.status == status]
    return results

@app.get(
    "/enrollments/{uni}/{course_code}/{year}/{term}",
    response_model=Enrollment
)
def get_enrollment(
    uni: str = Path(..., description="Student UNI"),
    course_code: str = Path(..., description="Course catalog code"),
    year: int = Path(..., description="Academic year"),
    term: str = Path(..., description="Term: 'FALL','SPRING','SUMMER'"),
):
    key = _enroll_key(uni, course_code, year, term)
    if key not in enrollments:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return enrollments[key]

@app.patch(
    "/enrollments/{uni}/{course_code}/{year}/{term}",
    response_model=Enrollment
)
def update_enrollment_status(
    uni: str = Path(..., description="Student UNI"),
    course_code: str = Path(..., description="Course catalog code"),
    year: int = Path(..., description="Academic year"),
    term: str = Path(..., description="Term: 'FALL','SPRING','SUMMER'"),
    status: str = Query(..., description="New status: 'enrolled','waitlisted','dropped'"),
):
    key = _enroll_key(uni, course_code, year, term)
    if key not in enrollments:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    current = enrollments[key].model_dump()
    current["status"] = status
    enrollments[key] = Enrollment(**current)
    return enrollments[key]

# -----------------------------------------------------------------------------
# Root
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Welcome to the Person/Address API. See /docs for OpenAPI UI."}

# -----------------------------------------------------------------------------
# Entrypoint for `python main.py`
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)