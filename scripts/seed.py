
"""Idempotently seed synthetic employees, salary and attendance; export CSVs."""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd
from faker import Faker
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
fake.seed_instance(SEED)


def source_categories():
    """Load and clean department and job-role pairs from the HR dataset."""
    if not RAW_DATA.exists():
        raise FileNotFoundError(f"Required dataset not found: {RAW_DATA}")

    frame = pd.read_csv(RAW_DATA)
    frame.columns = frame.columns.str.strip()

    required = {"Department", "JobRole"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Dataset must contain columns: {sorted(required)}")

    frame = frame[["Department", "JobRole"]].copy()

    for column in ["Department", "JobRole"]:
        frame[column] = frame[column].astype("string").str.strip()
        frame[column] = frame[column].replace("", pd.NA)

    frame = frame.dropna(subset=["Department", "JobRole"]).drop_duplicates()

    if frame.empty:
        raise ValueError("No valid department and job-role records found.")

    role_by_department = {
        department: sorted(group["JobRole"].unique().tolist())
        for department, group in frame.groupby("Department")
    }

    departments = sorted(role_by_department)
    roles = sorted(frame["JobRole"].unique().tolist())

    print(f"Loaded dataset: {RAW_DATA.name}")
    print(f"Valid department-role pairs: {len(frame)}")
    print(f"Departments: {len(departments)}, Job roles: {len(roles)}")

    return departments, roles, role_by_department


def get_or_create_lookup(db: Session, model, name: str):
    obj = db.query(model).filter(model.name == name).first()

    if obj is None:
        obj = model(name=name)
        db.add(obj)
        db.flush()

    return obj


def ensure_lookups(db: Session, departments, roles):
    for name in departments:
        get_or_create_lookup(db, Department, name)

    for name in roles:
        get_or_create_lookup(db, Role, name)

    db.flush()


def month_days(end: date, months_back: int = 3):
    """Yield weekdays in the previous three complete calendar months."""
    first_this_month = end.replace(day=1)
    start = first_this_month

    for _ in range(months_back):
        start = (start - timedelta(days=1)).replace(day=1)

    current = start

    while current < first_this_month:
        if current.weekday() < 5:
            yield current
        current += timedelta(days=1)


def seed(db: Session):
    departments, role_names, role_by_department = source_categories()
    ensure_lookups(db, departments, role_names)

    dept_map = {d.name: d for d in db.query(Department).all()}
    role_map = {r.name: r for r in db.query(Role).all()}
    dept_names = sorted(dept_map)

    employees = []

    for n in range(1, COUNT + 1):
        new_email = f"{EMAIL_PREFIX}{n:04d}@example.com"
        old_email = f"{EMAIL_PREFIX}{n:04d}@example.test"

        # Reuse old records and change their email instead of creating duplicates.
        employee = (
            db.query(Employee)
            .filter(Employee.email == new_email)
            .first()
        )

        if employee is None:
            employee = (
                db.query(Employee)
                .filter(Employee.email == old_email)
                .first()
            )

            if employee is not None:
                employee.email = new_email

        if employee is None:
            department = random.choice(dept_names)
            role_name = random.choice(role_by_department[department])

            employee = Employee(
                full_name=fake.name(),
                email=new_email,
                department_id=dept_map[department].id,
                joining_date=fake.date_between(
                    start_date="-8y",
                    end_date="today",
                ),
                is_deleted=False,
            )

            db.add(employee)
            db.flush()
            employee.roles = [role_map[role_name]]

        elif not employee.roles:
            department_name = next(
                (
                    name
                    for name, obj in dept_map.items()
                    if obj.id == employee.department_id
                ),
                dept_names[0],
            )
            available_roles = role_by_department.get(
                department_name,
                role_names,
            )
            employee.roles = [role_map[random.choice(available_roles)]]

        employees.append(employee)

    db.flush()

    # Assign managers without self-management.
    for index, employee in enumerate(employees):
        if index == 0:
            employee.manager_id = None
        elif employee.manager_id is None:
            employee.manager_id = employees[
                random.randrange(0, index)
            ].id

    workdays = list(month_days(date.today()))

    for employee in employees:
        salary = (
            db.query(Salary)
            .filter(Salary.employee_id == employee.id)
            .first()
        )

        if salary is None:
            amount = random.randrange(36000, 150001, 500)
            db.add(
                Salary(
                    employee_id=employee.id,
                    annual_salary=Decimal(amount),
                    currency="USD",
                )
            )

        for workday in workdays:
            attendance_exists = (
                db.query(Attendance.id)
                .filter(
                    Attendance.employee_id == employee.id,
                    Attendance.work_date == workday,
                )
                .first()
            )

            if attendance_exists:
                continue

            status = random.choices(
                ["Present", "Leave", "Absent"],
                weights=[94, 4, 2],
                k=1,
            )[0]

            hours = 8 if status == "Present" else 0

            db.add(
                Attendance(
                    employee_id=employee.id,
                    work_date=workday,
                    status=status,
                    hours_worked=hours,
                )
            )

    db.commit()

    print(
        f"Seed complete: {len(employees)} synthetic employees checked/created."
    )


def export_csv(db: Session):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    employee_rows = (
        db.query(Employee)
        .filter(Employee.email.like(f"{EMAIL_PREFIX}%"))
        .order_by(Employee.id)
        .all()
    )

    with (EXPORT_DIR / "employees.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "employee_id", "full_name", "email",
            "department_id", "manager_id", "joining_date",
        ])

        for employee in employee_rows:
            writer.writerow([
                employee.id,
                employee.full_name,
                employee.email,
                employee.department_id,
                employee.manager_id,
                employee.joining_date,
            ])

    employee_ids = [employee.id for employee in employee_rows]

    salary_rows = (
        db.query(Salary)
        .filter(Salary.employee_id.in_(employee_ids))
        .order_by(Salary.employee_id)
        .all()
        if employee_ids else []
    )

    with (EXPORT_DIR / "salaries.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["employee_id", "annual_salary", "currency"])

        for salary in salary_rows:
            writer.writerow([
                salary.employee_id,
                salary.annual_salary,
                salary.currency,
            ])

    attendance_rows = (
        db.query(Attendance)
        .filter(Attendance.employee_id.in_(employee_ids))
        .order_by(Attendance.employee_id, Attendance.work_date)
        .all()
        if employee_ids else []
    )

    with (EXPORT_DIR / "attendance.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "employee_id", "work_date", "status", "hours_worked",
        ])

        for attendance in attendance_rows:
            writer.writerow([
                attendance.employee_id,
                attendance.work_date,
                attendance.status,
                attendance.hours_worked,
            ])

    print(
        f"CSV exports written: employees={len(employee_rows)}, "
        f"salaries={len(salary_rows)}, attendance={len(attendance_rows)}"
    )


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
