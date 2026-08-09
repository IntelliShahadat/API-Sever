from sqlalchemy import (
    Column, Integer, String, Date, DateTime, DECIMAL, Boolean,
    ForeignKey, Enum, Text, TIMESTAMP, func
)
from sqlalchemy.orm import relationship
from database import Base


class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("employee", "hr", "admin"), default="employee", nullable=False)
    department = Column(String(80))
    designation = Column(String(80))
    manager_id = Column(Integer, ForeignKey("employees.employee_id"))
    date_of_joining = Column(Date)
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class LeaveBalance(Base):
    __tablename__ = "leave_balance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"))
    year = Column(Integer, nullable=False)
    leave_type = Column(Enum("casual", "sick", "earned", "unpaid"), nullable=False)
    total_days = Column(DECIMAL(4, 1), default=0)
    used_days = Column(DECIMAL(4, 1), default=0)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"))
    leave_type = Column(Enum("casual", "sick", "earned", "unpaid"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(DECIMAL(4, 1), nullable=False)
    reason = Column(String(255))
    status = Column(Enum("pending", "approved", "rejected"), default="pending")
    applied_at = Column(TIMESTAMP, server_default=func.now())
    reviewed_by = Column(Integer, ForeignKey("employees.employee_id"))


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"))
    work_date = Column(Date, nullable=False)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    status = Column(
        Enum("present", "absent", "half_day", "on_leave", "holiday"),
        default="present",
    )


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    holiday_date = Column(Date, unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    description = Column(String(255))


class HRDocument(Base):
    __tablename__ = "hr_documents"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("employees.employee_id"))
    uploaded_at = Column(TIMESTAMP, server_default=func.now())
    chunk_count = Column(Integer, default=0)
    vector_ids = Column(Text)  # JSON-encoded list of chroma vector ids
