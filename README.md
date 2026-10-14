

\# Employee Management System — Task 4



A REST API application built with \*\*Python, FastAPI, SQLAlchemy, PostgreSQL, Alembic, and pytest\*\*. This project extends the employee directory with salary and attendance tracking, synthetic HR data seeding, and CSV exports.



\## Features



\### Employee \& Team APIs

\- Create, retrieve, update, and soft-delete employees.

\- List employees with pagination, department filtering, and search.

\- Retrieve departments, department employees, roles, and direct reports.

\- Validate employee data and handle duplicate email addresses.

\- Return consistent JSON error responses.



\### Salary \& Attendance

\- List salary records with pagination.

\- List attendance records with pagination.

\- Filter attendance records by employee ID.

\- Store annual salary, currency, work date, attendance status, and hours worked.



\### Data \& Database

\- PostgreSQL database managed through Docker Compose.

\- SQLAlchemy models and Alembic database migrations.

\- Synthetic employee, salary, and attendance data.

\- CSV exports for employees, salaries, and attendance.

\- Automated tests using pytest.



\## Technology Stack



\- Python

\- FastAPI

\- SQLAlchemy

\- PostgreSQL

\- Alembic

\- Pydantic

\- Docker and Docker Compose

\- pytest

\- Pandas

\- Faker



\## Project Structure



```text

employee\_management\_task4\_full/

├── app/

│   ├── core/

│   ├── db/

│   ├── models/

│   ├── routes/

│   ├── services/

│   ├── main.py

│   └── schemas.py

├── alembic/

│   └── versions/

├── data/

│   ├── raw/

│   └── exports/

├── scripts/

│   └── seed.py

├── tests/

├── .env.example

├── docker-compose.yml

├── Dockerfile

├── requirements.txt

└── README.md

```



\## Run the Application



\### Prerequisites

\- Python

\- Docker Desktop

\- Git



\### 1. Configure environment variables



In PowerShell, from the project folder:



```powershell

Copy-Item .env.example .env

```



Configure the required database URL and secret key in `.env` according to the project configuration.



\### 2. Start the application



Make sure Docker Desktop is running, then execute:



```powershell

docker compose up --build -d

```



Check the containers and API logs:



```powershell

docker compose ps

docker compose logs --tail=50 api

```



The Task 4 stack uses host port \*\*5433\*\* for PostgreSQL and host port \*\*8001\*\* for the API to avoid conflicts with the Task 3 stack.



\### 3. Open the API documentation



Swagger UI:



http://localhost:8001/docs



Health check:



```powershell

Invoke-RestMethod http://localhost:8001/health

```



\## API Endpoints



| Method | Endpoint | Description |

|---|---|---|

| POST | `/employees` | Create an employee |

| GET | `/employees` | List employees with pagination and filters |

| GET | `/employees/{employee\_id}` | Retrieve an employee |

| PATCH | `/employees/{employee\_id}` | Update an employee |

| DELETE | `/employees/{employee\_id}` | Soft-delete an employee |

| GET | `/departments` | List departments |

| GET | `/departments/{department\_id}/employees` | List employees in a department |

| GET | `/employees/{employee\_id}/team` | List direct reports |

| GET | `/roles` | List roles |

| GET | `/salaries` | List salary records |

| GET | `/attendance` | List attendance records |



\### Example Requests



List employees with pagination, department filtering, and search:



```text

GET /employees?page=1\&size=20\&department=1\&q=Sanjai

```



List salary records:



```text

GET /salaries?page=1\&size=20

```



List attendance records for a particular employee:



```text

GET /attendance?page=1\&size=20\&employee\_id=1

```



List responses include pagination metadata such as `items`, `total`, `page`, and `size`, where applicable.



\## Database Migrations



Apply database migrations:



```powershell

docker compose exec api alembic upgrade head

```



The migration history includes the initial employee tables and the additional salary and attendance tables.



\## Synthetic Data and CSV Exports



The project includes a data seeding script for synthetic employee, salary, and attendance records.



Run the seed script inside the API container:



```powershell

docker compose exec api python scripts/seed.py

```



The script creates or checks synthetic employee records and generates CSV exports.



Expected export files:



\- `data/exports/employees.csv`

\- `data/exports/salaries.csv`

\- `data/exports/attendance.csv`



The current seed configuration targets 300 synthetic employees and attendance records covering the previous three complete calendar months.



The raw HR analytics dataset and its documentation are located under `data/raw/`.



\## Run Tests



Run the automated test suite inside the API container:



```powershell

docker compose exec api python -m pytest -v

```



The test suite has previously completed successfully with \*\*11 passing tests\*\*.



\## Stop the Application



```powershell

docker compose down

```



The named database volume is retained unless explicitly removed.



\## Author



\*\*Christober Sanjai S.\*\*



MSc Computer Science Graduate | Aspiring Python Developer



GitHub: \[christobersanjai-source](https://github.com/christobersanjai-source)



\## Project Purpose



This project demonstrates my practical learning and development skills in Python, FastAPI, SQLAlchemy, PostgreSQL, REST API development, database migrations, automated testing, and synthetic data processing.



