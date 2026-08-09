from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from auth import get_current_employee
import models
import schemas

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("", response_model=List[schemas.AttendanceOut])
def get_attendance(
    employee_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current=Depends(get_current_employee),
):
    target_id = employee_id or current.employee_id
    if current.employee_id != target_id and current.role not in ("hr", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized")

    q = db.query(models.Attendance).filter(models.Attendance.employee_id == target_id)
    if start_date:
        q = q.filter(models.Attendance.work_date >= start_date)
    if end_date:
        q = q.filter(models.Attendance.work_date <= end_date)
    return q.order_by(models.Attendance.work_date.desc()).all()


@router.get("/summary")
def get_attendance_summary(
    employee_id: Optional[int] = Query(None),
    month: int = Query(default=date.today().month),
    year: int = Query(default=date.today().year),
    db: Session = Depends(get_db),
    current=Depends(get_current_employee),
):
    """Quick counts used directly by the AI chat tool for natural-language answers."""
    target_id = employee_id or current.employee_id
    if current.employee_id != target_id and current.role not in ("hr", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized")

    rows = (
        db.query(models.Attendance)
        .filter(
            models.Attendance.employee_id == target_id,
        )
        .all()
    )
    rows = [r for r in rows if r.work_date.month == month and r.work_date.year == year]

    summary = {"present": 0, "absent": 0, "half_day": 0, "on_leave": 0, "holiday": 0}
    for r in rows:
        summary[r.status] = summary.get(r.status, 0) + 1
    summary["total_days_recorded"] = len(rows)
    summary["month"] = month
    summary["year"] = year
    return summary
