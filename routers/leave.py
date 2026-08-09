from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from auth import get_current_employee, require_hr
from log_utils import log_event
import models
import schemas

router = APIRouter(prefix="/leave", tags=["Leave"])


def _authorize_target(current, target_employee_id: int):
    """An employee can only see their own leave data unless they are HR/admin."""
    if current.employee_id != target_employee_id and current.role not in ("hr", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized")


@router.get("/balance", response_model=List[schemas.LeaveBalanceOut])
def get_leave_balance(
    employee_id: Optional[int] = Query(None, description="HR only: view another employee's balance"),
    year: int = Query(default=date.today().year),
    db: Session = Depends(get_db),
    current=Depends(get_current_employee),
    x_session_id: str = Header(None, alias="X-Session-Id"),
):
    target_id = employee_id or current.employee_id
    log_event(x_session_id, "get_leave_balance", f"Fetching leave balance for employee_id={target_id}, year={year}", script="leave.py")
    _authorize_target(current, target_id)

    rows = (
        db.query(models.LeaveBalance)
        .filter(models.LeaveBalance.employee_id == target_id, models.LeaveBalance.year == year)
        .all()
    )
    log_event(x_session_id, "get_leave_balance", f"Found {len(rows)} leave balance rows", script="leave.py")
    return [
        schemas.LeaveBalanceOut(
            leave_type=r.leave_type,
            total_days=float(r.total_days),
            used_days=float(r.used_days),
            remaining_days=float(r.total_days) - float(r.used_days),
        )
        for r in rows
    ]


@router.get("/requests", response_model=List[schemas.LeaveRequestOut])
def get_leave_requests(
    employee_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current=Depends(get_current_employee),
):
    target_id = employee_id or current.employee_id
    _authorize_target(current, target_id)

    q = db.query(models.LeaveRequest).filter(models.LeaveRequest.employee_id == target_id)
    if status_filter:
        q = q.filter(models.LeaveRequest.status == status_filter)
    return q.order_by(models.LeaveRequest.applied_at.desc()).all()


@router.post("/requests", response_model=schemas.LeaveRequestOut, status_code=201)
def apply_for_leave(
    payload: schemas.LeaveRequestCreate,
    db: Session = Depends(get_db),
    current=Depends(get_current_employee),
):
    days = (payload.end_date - payload.start_date).days + 1
    if days <= 0:
        raise HTTPException(status_code=400, detail="end_date must be on/after start_date")

    leave_req = models.LeaveRequest(
        employee_id=current.employee_id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        days=days,
        reason=payload.reason,
        status="pending",
    )
    db.add(leave_req)
    db.commit()
    db.refresh(leave_req)
    return leave_req


@router.patch("/requests/{request_id}/status", response_model=schemas.LeaveRequestOut)
def review_leave_request(
    request_id: int,
    new_status: str = Query(..., pattern="^(approved|rejected)$"),
    db: Session = Depends(get_db),
    current=Depends(require_hr),  # only HR/admin can approve/reject
):
    leave_req = db.query(models.LeaveRequest).filter(models.LeaveRequest.id == request_id).first()
    if not leave_req:
        raise HTTPException(status_code=404, detail="Leave request not found")

    leave_req.status = new_status
    leave_req.reviewed_by = current.employee_id

    if new_status == "approved":
        bal = (
            db.query(models.LeaveBalance)
            .filter(
                models.LeaveBalance.employee_id == leave_req.employee_id,
                models.LeaveBalance.leave_type == leave_req.leave_type,
                models.LeaveBalance.year == leave_req.start_date.year,
            )
            .first()
        )
        if bal:
            bal.used_days = float(bal.used_days) + float(leave_req.days)

    db.commit()
    db.refresh(leave_req)
    return leave_req
