from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List


# ---------- Auth ----------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    employee_id: int
    full_name: str


# ---------- Employee ----------
class EmployeeOut(BaseModel):
    employee_id: int
    employee_code: str
    full_name: str
    email: EmailStr
    role: str
    department: Optional[str] = None
    designation: Optional[str] = None
    date_of_joining: Optional[date] = None
    phone: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    employee_code: str
    full_name: str
    email: EmailStr
    password: str
    role: str = "employee"
    department: Optional[str] = None
    designation: Optional[str] = None
    date_of_joining: Optional[date] = None
    phone: Optional[str] = None


# ---------- Leave ----------
class LeaveBalanceOut(BaseModel):
    leave_type: str
    total_days: float
    used_days: float
    remaining_days: float

    class Config:
        from_attributes = True


class LeaveRequestCreate(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    reason: Optional[str] = None


class LeaveRequestOut(BaseModel):
    id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    days: float
    reason: Optional[str]
    status: str
    applied_at: datetime

    class Config:
        from_attributes = True


# ---------- Attendance ----------
class AttendanceOut(BaseModel):
    work_date: date
    check_in: Optional[datetime]
    check_out: Optional[datetime]
    status: str

    class Config:
        from_attributes = True


# ---------- Holidays ----------
class HolidayOut(BaseModel):
    holiday_date: date
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


# ---------- HR Documents (admin) ----------
class HRDocumentOut(BaseModel):
    id: int
    original_name: str
    uploaded_at: datetime
    chunk_count: int
    vector_ids: Optional[str] = None  # comma-separated chroma ids, used for deletion

    class Config:
        from_attributes = True
