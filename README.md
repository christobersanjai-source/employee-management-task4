\# Employee Management System — Task 4



A REST API application built with \*\*Python, FastAPI, SQLAlchemy, PostgreSQL, Alembic, and pytest\*\*. This project extends the employee management system with salary tracking, attendance tracking, reproducible synthetic HR data generation, and CSV exports.



\## Features



\### Employee and Team APIs

\- Create, retrieve, update, and soft-delete employees.

\- List employees with pagination, department filtering, and search.

\- Retrieve departments, department employees, roles, and direct reports.

\- Validate employee data and handle duplicate email addresses.

\- Return consistent JSON error responses.



\### Salary and Attendance

\- List salary records with pagination.

\- List attendance records with pagination.

\- Filter attendance records by employee ID.

\- Store annual salary, currency, work date, attendance status, and hours worked.

\- Link salary and attendance records to employee IDs.



\### Data Processing and Database

\- Use Pandas to load and process the HR analytics dataset.

\- Use Faker to generate synthetic employee information.

\- Generate salary and attendance records for synthetic employees.

\- Use a fixed random seed for reproducible data generation.

\- Support repeatable seeding without creating duplicate records.

\- Export employee, salary, and attendance data to CSV files.

\- Use PostgreSQL, SQLAlchemy, and Alembic migrations.



\## Technology Stack



\- Python

\- FastAPI

\- SQLAlchemy

\- PostgreSQL

\- Alembic

\- Pydantic

\- Pandas

\- Faker

\- Docker and Docker Compose

\- pytest



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

│   │   └── README.md

│   └── exports/

│       ├── employees.csv

│       ├── salaries.csv

│       └── attendance.csv

├── scripts/

│   └── seed.py

├── tests/

├── .env.example

├── .gitignore

├── docker-compose.yml

├── Dockerfile

├── requirements.txt

└── README.md

```



\## Run the Application



\### Prerequisites



\- Python

\- Git

\- Docker Desktop



\### 1. Configure environment variables



Open PowerShell in the project directory and run:



```powershell

Copy-Item .env.example .env

```



Configure the required database URL and secret key in `.env` according to the project configuration.



\### 2. Start the application



Make sure Docker Desktop is running.



```powershell

docker compose up --build -d

```



Check the containers and API logs:



```powershell

docker compose ps

docker compose logs --tail=50 api

```



The Task 4 stack uses host port \*\*5433\*\* for PostgreSQL and host port \*\*8001\*\* for the API.



\### 3. Open API documentation



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



List employees:



```text

GET /employees?page=1\&size=20

```



Filter employees by department and search term:



```text

GET /employees?page=1\&size=20\&department=1\&q=Sanjai

```



List salary records:



```text

GET /salaries?page=1\&size=20

```



List attendance records for an employee:



```text

GET /attendance?page=1\&size=20\&employee\_id=1

```



List responses provide pagination metadata where applicable.



\## Database Migrations



Apply database migrations:



```powershell

docker compose exec api alembic upgrade head

```



The migration history includes the employee tables and the additional salary and attendance tables.



\## HR Dataset Source, License, and Processing



\### Dataset Source



The project uses the IBM HR Analytics Employee Attrition \& Performance dataset available on Kaggle:



https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset



Expected raw filename:



`WA\_Fn-UseC\_-HR-Employee-Attrition.csv`



Place the dataset in `data/raw/`.



\*\*License and redistribution:\*\* Check the dataset page and its applicable license or usage terms before redistributing the original CSV. The raw dataset is excluded from Git tracking unless redistribution is confirmed to be permitted. The project repository contains instructions for obtaining the dataset rather than the raw CSV itself.



\### Data Cleaning and Mapping



The seed script uses Pandas to load and process the source CSV. The source dataset supplies HR-related attributes, such as department and job role, for data processing.



\- Load the source CSV using Pandas.

\- Inspect and process department and job-role values used by the seed workflow.

\- Use valid department/job-role combinations to support the database mapping.

\- Generate synthetic employee names, work email addresses, phone numbers, and joining dates with Faker.

\- Create synthetic employee records rather than copying real employee identities from the source dataset.

\- Generate linked salary and attendance records using the synthetic employee IDs.



The exact cleaning and validation rules are implemented in `scripts/seed.py`.



\## Synthetic Data Generation and Reproducibility



Run the seed script inside the API container:



```powershell

docker compose exec api python -m scripts.seed

```



The script uses a fixed random seed (`20261014`) to support reproducible synthetic data generation.



The current configuration targets \*\*300 synthetic employees\*\*, corresponding salary records, and attendance records for the previous three complete calendar months.



The seed workflow is designed to check existing records before creating them, so rerunning it should not increase the record counts or create duplicates. Database counts should be checked after rerunning the script to verify idempotency.



Expected successful output includes:



```text

Seed complete: 300 synthetic employees checked/created.

CSV exports written: employees=300, salaries=300, attendance=19800

```



Actual output may vary if the seed configuration or dataset changes.



\## CSV Exports



The seed script writes the following CSV files:



| File | Description |

|---|---|

| `data/exports/employees.csv` | Synthetic employee records |

| `data/exports/salaries.csv` | Salary records linked to employees |

| `data/exports/attendance.csv` | Attendance records linked to employees |



The exports support data analysis, reporting, and reuse in other HR-related applications.



\## Reusing the Data Workflow in Other Domains



The same data-generation and export approach can be adapted for other domains, including:



\- \*\*Retail:\*\* synthetic customers, products, orders, and sales reports.

\- \*\*Education:\*\* synthetic students, courses, attendance, and marks.

\- \*\*Healthcare administration:\*\* synthetic staff schedules and attendance, using appropriate privacy safeguards.

\- \*\*Inventory management:\*\* synthetic products, stock movements, and reorder reports.



For another domain, replace the HR-specific source fields and database mappings with the relevant entities and relationships. Continue using synthetic data where appropriate and check the source dataset's license before redistribution.



\## Run Tests



Run the automated test suite inside the API container:



```powershell

docker compose exec api python -m pytest -v

```



The test suite previously completed successfully with 11 passing tests. Run it again after changes to confirm the current result.



\## Stop the Application



```powershell

docker compose down

```



The named database volume is retained unless explicitly removed.



\## Author



\*\*Christober Sanjai S.\*\*



MSc Computer Science Graduate | Aspiring Python Developer



GitHub: https://github.com/christobersanjai-source



\## Project Purpose



This project demonstrates practical skills in Python, FastAPI, REST API development, SQLAlchemy, PostgreSQL, database migrations, automated testing, Pandas-based data processing, synthetic data generation, and CSV exports.



