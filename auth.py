import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status, Header
#from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from log_utils import log_event
import models

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "insecure-dev-secret-change-me")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# tokenUrl is just for the interactive /docs page's "Authorize" button
#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
oauth2_scheme = HTTPBearer()


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_employee(
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    x_session_id: str = Header(None, alias="X-Session-Id"),
) -> models.Employee: # Call Point -> 24 (Searching employee info in DB with appropriate credentials)
    """
    Decodes the JWT, loads the employee row. This is the single source of
    truth for 'who is calling this API' used across every protected route
    (and reused by the MCP server indirectly, since it forwards the same
    token when it calls these APIs on the user's behalf).
    """
    log_event(x_session_id, "get_current_employee", "Decoding JWT and loading employee")
    payload = decode_access_token(token.credentials)
    employee_id = payload.get("sub")

    if employee_id is None:
        log_event(x_session_id, "get_current_employee", "Token missing 'sub' claim", level="ERROR")
        raise HTTPException(status_code=401, detail="Invalid token payload")

    employee = ( 
        db.query(models.Employee)
        .filter(models.Employee.employee_id == int(employee_id))
        .first()
    )  # Call Point -> 25 (Matching employee_id in Database)

    if employee is None or not employee.is_active:
        log_event(x_session_id, "get_current_employee", f"Employee {employee_id} not found or inactive", level="ERROR")
        raise HTTPException(status_code=401, detail="Employee not found or inactive")

    log_event(x_session_id, "get_current_employee", f"Authenticated employee_id={employee_id}, role={employee.role}")
    
    return employee  # Call Point -> 26 (Returning employee info to agent.py for farther processing...)


def require_hr(employee: models.Employee = Depends(get_current_employee)) -> models.Employee:
    """Dependency for endpoints only HR/admin may call."""
    if employee.role not in ("hr", "admin"):
        raise HTTPException(status_code=403, detail="HR access required")
    return employee
