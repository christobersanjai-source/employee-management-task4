"""Add salary and attendance tables.

Revision ID: 0002_salary_attendance
Revises: 0001_employee_tables
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_salary_attendance"
down_revision = "0001_employee_tables"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "salaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("annual_salary", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.UniqueConstraint("employee_id", name="uq_salaries_employee_id"),
    )
    op.create_index("ix_salaries_employee_id", "salaries", ["employee_id"])
    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("hours_worked", sa.Integer(), nullable=False, server_default="8"),
        sa.UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_date"),
    )
    op.create_index("ix_attendance_employee_id", "attendance", ["employee_id"])
    op.create_index("ix_attendance_work_date", "attendance", ["work_date"])

def downgrade() -> None:
    op.drop_index("ix_attendance_work_date", table_name="attendance")
    op.drop_index("ix_attendance_employee_id", table_name="attendance")
    op.drop_table("attendance")
    op.drop_index("ix_salaries_employee_id", table_name="salaries")
    op.drop_table("salaries")

