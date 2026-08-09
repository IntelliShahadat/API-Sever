from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from auth import get_current_employee
import models
import schemas

router = APIRouter(prefix="/holidays", tags=["Holidays"])


@router.get("", response_model=List[schemas.HolidayOut])
def list_holidays(
    upcoming_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current=Depends(get_current_employee),  # still requires login
):
    q = db.query(models.Holiday)
    if upcoming_only:
        q = q.filter(models.Holiday.holiday_date >= date.today())
    return q.order_by(models.Holiday.holiday_date.asc()).all()
