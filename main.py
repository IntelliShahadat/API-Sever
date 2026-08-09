from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import auth_routes, employees, leave, attendance, holidays, admin, logs

# Creates tables if they don't exist (safe to leave in; schema.sql is the
# canonical source of truth and already sets everything up).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HR Chatbot API Server",
    description="Handles auth, employee, leave, attendance and holiday data. "
                 "The MCP/AI server calls these endpoints on behalf of logged-in users.",
    version="1.0.0",
)

# In production, restrict allow_origins to your actual frontend domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(employees.router)
app.include_router(leave.router)
app.include_router(attendance.router)
app.include_router(holidays.router)
app.include_router(admin.router)
app.include_router(logs.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
