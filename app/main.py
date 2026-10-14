from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db 
from app.models import Employee, Department, Role, Salary, Attendance
from app.schemas import EmployeeCreate, EmployeeUpdate, EmployeeRead, EmployeePage, DepartmentRead, RoleRead
from app.services import employee_service as service

app = FastAPI(title="Employee & Team APIs", version="1.0.0", description="Employee directory CRUD, team, department, pagination, filtering and search.")

@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        body = detail
    else:
        body = {"error": "http_error", "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/employees", response_model=EmployeeRead, status_code=201)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    return service.create_employee(db, payload)

@app.get("/employees", response_model=EmployeePage)
def list_employees(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), department: int | None = Query(None, ge=1), q: str | None = Query(None, max_length=120), db: Session = Depends(get_db)):
    return service.list_employees(db, page, size, department, q)

@app.get("/employees/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    return service.employee_dict(service.get_employee(db, employee_id))

@app.patch("/employees/{employee_id}", response_model=EmployeeRead)
def patch_employee(employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    return service.update_employee(db, employee_id, payload)

@app.delete("/employees/{employee_id}", status_code=200)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    return service.soft_delete_employee(db, employee_id)

@app.get("/departments", response_model=list[DepartmentRead])
def list_departments(db: Session = Depends(get_db)):
    return db.query(Department).order_by(Department.id).all()

@app.get("/departments/{department_id}/employees", response_model=list[EmployeeRead])
def list_department_employees(department_id: int, db: Session = Depends(get_db)):
    return service.department_employees(db, department_id)

@app.get("/employees/{employee_id}/team", response_model=list[EmployeeRead])
def list_direct_reports(employee_id: int, db: Session = Depends(get_db)):
    return service.direct_reports(db, employee_id)

@app.get("/roles", response_model=list[RoleRead])
def list_roles(db: Session = Depends(get_db)):
    return db.query(Role).order_by(Role.id).all()

@app.get("/salaries")
def list_salaries(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Salary).join(Employee)
    total = query.count()
    items = (
        query.order_by(Salary.id)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return {
        "items": [
            {
                "id": salary.id,
                "employee_id": salary.employee_id,
                "annual_salary": float(salary.annual_salary),
                "currency": salary.currency,
            }
            for salary in items
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@app.get("/attendance")
def list_attendance(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    employee_id: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    query = db.query(Attendance).join(Employee)

    if employee_id is not None:
        query = query.filter(Attendance.employee_id == employee_id)

    total = query.count()
    items = (
        query.order_by(Attendance.work_date.desc(), Attendance.id)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return {
        "items": [
            {
                "id": record.id,
                "employee_id": record.employee_id,
                "work_date": record.work_date.isoformat(),
                "status": record.status,
                "hours_worked": record.hours_worked,
            }
            for record in items
        ],
        "total": total,
        "page": page,
        "size": size,
    }