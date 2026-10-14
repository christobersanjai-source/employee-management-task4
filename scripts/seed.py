"""Idempotently seed synthetic employees, salary and attendance; then export CSVs."""
from __future__ import annotations
import csv, random
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd
from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Department, Employee, Role
from app.models.salary import Salary
from app.models.attendance import Attendance

ROOT = Path(__file__).resolve().parents[1]
RAW_DATA = ROOT / "data" / "raw" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
EXPORT_DIR = ROOT / "data" / "exports"
COUNT = 300
SEED = 20261014
EMAIL_PREFIX = "seed.task4+"
Faker.seed(SEED)
random.seed(SEED)
fake = Faker("en_US")
FALLBACK = {
    "Sales": ["Sales Executive", "Sales Representative", "Manager"],
    "Research & Development": ["Research Scientist", "Laboratory Technician", "Research Director"],
    "Human Resources": ["Human Resources", "Manager", "Recruiter"],
}


def source_categories() -> tuple[list[str], list[str], dict[str, list[str]]]:
    if not RAW_DATA.exists():
        raise FileNotFoundError(
            f"Required Kaggle HR dataset not found: {RAW_DATA}"
        )

    # Load and clean the public HR dataset using Pandas.
    frame = pd.read_csv(RAW_DATA)

    frame.columns = frame.columns.str.strip()

    required = {"Department", "JobRole"}
    if not required.issubset(frame.columns):
        raise ValueError(
            f"Dataset must contain columns: {sorted(required)}"
        )

    frame = frame[["Department", "JobRole"]].copy()

    for column in ["Department", "JobRole"]:
        frame[column] = frame[column].astype("string").str.strip()
        frame[column] = frame[column].replace("", pd.NA)

    frame = frame.dropna(subset=["Department", "JobRole"])
    frame = frame.drop_duplicates()

    if frame.empty:
        raise ValueError("No valid Department and JobRole records found.")

    role_by_department = {
        department: sorted(group["JobRole"].unique().tolist())
        for department, group in frame.groupby("Department")
    }

    departments = sorted(role_by_department)
    roles = sorted(frame["JobRole"].unique().tolist())

    print(f"Loaded and cleaned Kaggle dataset: {RAW_DATA.name}")
    print(f"Valid department-role pairs: {len(frame)}")
    print(f"Departments: {len(departments)}, Job roles: {len(roles)}")

    return departments, roles, role_by_department

def get_or_create_lookup(db: Session, model, name: str):
    obj = db.query(model).filter(model.name == name).first()
    if obj is None:
        obj = model(name=name)
        db.add(obj); db.flush()
    return obj

def ensure_lookups(db: Session, departments: list[str], roles: list[str]):
    for name in departments:
        get_or_create_lookup(db, Department, name)
    for name in roles:
        get_or_create_lookup(db, Role, name)
    db.flush()

def month_days(end: date, months_back: int = 3):
    # Previous three complete calendar months, excluding weekends.
    first_this_month = end.replace(day=1)
    start = first_this_month
    for _ in range(months_back):
        start = (start - timedelta(days=1)).replace(day=1)
    cur = start
    while cur < first_this_month:
        if cur.weekday() < 5:
            yield cur
        cur += timedelta(days=1)

def seed(db: Session):
    departments, role_names, role_by_department = source_categories()
    ensure_lookups(db, departments, role_names)
    dept_map = {d.name: d for d in db.query(Department).all()}
    role_map = {r.name: r for r in db.query(Role).all()}
    dept_names = sorted(dept_map)
    role_names = sorted(role_map)

    # Build or reuse this script's employees by deterministic email.
    employees = []
    for n in range(1, COUNT + 1):
        email = f"{EMAIL_PREFIX}{n:04d}@example.test"
        employee = db.query(Employee).filter(Employee.email == email).first()
        if employee is None:
            department = random.choice(dept_names)
            role = random.choice(role_by_department[department])
            employee = Employee(
                full_name=fake.name(), email=email,
                department_id=dept_map[department].id,
                joining_date=fake.date_between(start_date="-8y", end_date="today"),
                is_deleted=False,
            )
            db.add(employee); db.flush()
            employee.roles = [role_map[role]]
        employees.append(employee)
    db.flush()

    # Deterministic manager links, without self-management.
    for idx, employee in enumerate(employees):
        if idx == 0:
            employee.manager_id = None
        elif employee.manager_id is None:
            employee.manager_id = employees[random.randrange(0, idx)].id

    for employee in employees:
        if db.query(Salary).filter(Salary.employee_id == employee.id).first() is None:
            amount = random.randrange(36000, 150001, 500)
            db.add(Salary(employee_id=employee.id, annual_salary=Decimal(amount), currency="USD"))
        for workday in month_days(date.today()):
            exists = db.query(Attendance.id).filter(Attendance.employee_id == employee.id, Attendance.work_date == workday).first()
            if exists:
                continue
            status = random.choices(["Present", "Leave", "Absent"], weights=[94, 4, 2], k=1)[0]
            hours = 8 if status == "Present" else (0 if status == "Absent" else 0)
            db.add(Attendance(employee_id=employee.id, work_date=workday, status=status, hours_worked=hours))
    db.commit()
    print(f"Seed complete: {len(employees)} deterministic synthetic employees checked/created.")

def export_csv(db: Session):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    employee_rows = db.query(Employee).filter(Employee.email.like(f"{EMAIL_PREFIX}%")).order_by(Employee.id).all()
    with (EXPORT_DIR / "employees.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f); writer.writerow(["employee_id", "full_name", "email", "department_id", "manager_id", "joining_date"])
        for e in employee_rows:
            writer.writerow([e.id, e.full_name, e.email, e.department_id, e.manager_id, e.joining_date])
    employee_ids = [e.id for e in employee_rows]
    salary_rows = db.query(Salary).filter(Salary.employee_id.in_(employee_ids)).order_by(Salary.employee_id).all() if employee_ids else []
    with (EXPORT_DIR / "salaries.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f); writer.writerow(["employee_id", "annual_salary", "currency"])
        for s in salary_rows: writer.writerow([s.employee_id, s.annual_salary, s.currency])
    attendance_rows = db.query(Attendance).filter(Attendance.employee_id.in_(employee_ids)).order_by(Attendance.employee_id, Attendance.work_date).all() if employee_ids else []
    with (EXPORT_DIR / "attendance.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f); writer.writerow(["employee_id", "work_date", "status", "hours_worked"])
        for a in attendance_rows: writer.writerow([a.employee_id, a.work_date, a.status, a.hours_worked])
    print(f"CSV exports written to {EXPORT_DIR}: employees={len(employee_rows)}, salaries={len(salary_rows)}, attendance={len(attendance_rows)}")

def main():
    with SessionLocal() as db:
        try:
            seed(db)
            export_csv(db)
        except Exception:
            db.rollback()
            raise

if __name__ == "__main__":
    main()
