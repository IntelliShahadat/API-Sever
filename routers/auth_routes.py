from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from database import get_db
from auth import verify_password, create_access_token
from log_utils import log_event
import models
import schemas

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=schemas.TokenResponse)


def login(
    payload: schemas.LoginRequest,
    db: Session = Depends(get_db),
    x_session_id: str = Header(None, alias="X-Session-Id"),
):
    log_event(x_session_id, "login", f"Login attempt for {payload.email}", script="auth_routes.py")
    employee = db.query(models.Employee).filter(models.Employee.email == payload.email).first()

    if not employee or not verify_password(payload.password, employee.password_hash):
        log_event(x_session_id, "login", f"Failed login for {payload.email}", level="WARN", script="auth_routes.py")
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not employee.is_active:
        log_event(x_session_id, "login", f"Inactive account login attempt: {payload.email}", level="WARN", script="auth_routes.py")
        raise HTTPException(status_code=403, detail="Account is deactivated")

    # 'sub' (subject) and 'role' are the two claims every downstream service
    # (including the MCP/AI server) relies on to authorize requests.
    token = create_access_token(
        data={"sub": str(employee.employee_id), "role": employee.role}
    )

    log_event(x_session_id, "login", f"Login successful for employee_id={employee.employee_id}", script="auth_routes.py")

    return schemas.TokenResponse(
        access_token=token,
        role=employee.role,
        employee_id=employee.employee_id,
        full_name=employee.full_name,
    )
