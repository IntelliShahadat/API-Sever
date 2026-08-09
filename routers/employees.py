from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from auth import get_current_employee, require_hr, hash_password
import models
import schemas

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("/me", response_model=schemas.EmployeeOut)
def get_my_profile(current=Depends(get_current_employee)):
    return current


@router.get("", response_model=List[schemas.EmployeeOut])
def list_employees(
    db: Session = Depends(get_db),
    current=Depends(require_hr),  # only HR/admin can list everyone
):
    return db.query(models.Employee).all()


@router.get("/{employee_id}", response_model=schemas.EmployeeOut)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_employee),
):
    # An employee may view their own record; HR/admin may view anyone's.
    if current.employee_id != employee_id and current.role not in ("hr", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized")

    emp = db.query(models.Employee).filter(models.Employee.employee_id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.post("", response_model=schemas.EmployeeOut, status_code=201)
def create_employee(
    payload: schemas.EmployeeCreate,
    db: Session = Depends(get_db),
    current=Depends(require_hr),  # only HR/admin can onboard new employees
):
    existing = db.query(models.Employee).filter(models.Employee.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    emp = models.Employee(
        employee_code=payload.employee_code,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        department=payload.department,
        designation=payload.designation,
        date_of_joining=payload.date_of_joining,
        phone=payload.phone,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp
