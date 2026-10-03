import json
import os
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database configuration
POSTGRES_HOST = os.environ.get(
    "DB_HOST", "your-db-instance.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com"
)
POSTGRES_PORT = os.environ.get("DB_PORT", "5432")
POSTGRES_DB = os.environ.get("DB_NAME", "your_db_name")
POSTGRES_USER = os.environ.get("DB_USER", "your_db_user")
POSTGRES_PASSWORD = os.environ.get("DB_PASSWORD", "your_db_password")

# Create database URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create engine and session factory
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"connect_timeout": 10},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def lambda_handler(event, context):
    """
    Lambda function to handle Bedrock Agent requests
    """
    print(f"Received event: {json.dumps(event)}")

    # Parse the Bedrock Agent request
    action_group = event.get("actionGroup", "")
    api_path = event.get("apiPath", "")
    http_method = event.get("httpMethod", "")
    parameters = event.get("parameters", [])

    # Extract parameters
    params = {param["name"]: param["value"] for param in parameters}

    # Route to appropriate function
    try:
        if api_path == "/employees" and http_method == "GET":
            filters = {}
            if params.get("department"):
                filters["department"] = params["department"]
            if params.get("min_salary"):
                filters["min_salary"] = float(params["min_salary"])
            result = get_employees(filters if filters else None)
        elif api_path == "/employees/{id}" and http_method == "GET":
            employee_id = int(params.get("id", 0))
            result = get_employee_by_id(employee_id)
        elif api_path == "/employees" and http_method == "POST":
            body = (
                event.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
            )
            result = add_employee(
                name=body.get("name"),
                email=body.get("email"),
                department=body.get("department"),
                salary=float(body.get("salary")),
                hire_date=body.get("hire_date"),
            )
        elif api_path == "/projects":
            result = get_projects(params.get("status"))
        elif api_path == "/departments/summary":
            result = get_department_summary()
        elif api_path == "/executeQuery":
            query = params.get("query", "")
            result = execute_query(query)
        else:
            result = {"error": f"Unknown API path: {api_path}"}

    except Exception as e:
        print(f"Error processing request: {e!s}")
        result = {"error": str(e)}

    # Format response for Bedrock Agent
    response = {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "apiPath": api_path,
            "httpMethod": http_method,
            "httpStatusCode": 200,
            "responseBody": {"application/json": {"body": json.dumps(result)}},
        },
    }

    return response


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        print(f"Database connection error: {e!s}")
        db.close()
        raise


def execute_query(query: str) -> dict[str, Any]:
    """Execute a custom SQL query"""
    db = get_db()
    try:
        result = db.execute(text(query))

        # Check if query returns rows
        if result.returns_rows:  # SELECT query
            rows = result.fetchall()
            # Convert rows to dictionaries (SQLAlchemy 1.4 compatible)
            data = [dict(row) for row in rows]
        else:  # INSERT/UPDATE/DELETE
            db.commit()
            data = {"affected_rows": result.rowcount}

        return {"success": True, "data": data}
    except Exception as e:
        print(f"Query execution error: {e!s}")
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_employees(filters: dict[str, Any] | None = None) -> dict[str, Any]:
    """List employees, optionally filtered by department and/or minimum salary."""
    db = get_db()
    try:
        sql = "SELECT id, name, email, department, salary, hire_date FROM employees"
        conditions = []
        params: dict[str, Any] = {}

        if filters:
            if filters.get("department"):
                conditions.append("department = :department")
                params["department"] = filters["department"]
            if filters.get("min_salary") is not None:
                conditions.append("salary >= :min_salary")
                params["min_salary"] = filters["min_salary"]

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY id"

        results = db.execute(text(sql), params).fetchall()
        employees = [
            {
                "id": row.id,
                "name": row.name,
                "email": row.email,
                "department": row.department,
                "salary": float(row.salary) if row.salary is not None else None,
                "hire_date": str(row.hire_date) if row.hire_date else None,
            }
            for row in results
        ]
        return {
            "success": True,
            "data": {"employees": employees, "count": len(employees)},
        }

    except Exception as e:
        print(f"Error fetching employees: {e!s}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_employee_by_id(employee_id: int) -> dict[str, Any]:
    """Fetch a single employee from the database by ID."""
    db = get_db()
    try:
        query = text("""
        SELECT id, name, email, department, salary, hire_date
        FROM employees
        WHERE id = :employee_id
        """)

        result = db.execute(query, {"employee_id": employee_id}).fetchone()

        if result:
            return {
                "success": True,
                "data": {
                    "id": result.id,
                    "name": result.name,
                    "email": result.email,
                    "department": result.department,
                    "salary": (
                        float(result.salary) if result.salary is not None else None
                    ),
                    "hire_date": str(result.hire_date) if result.hire_date else None,
                },
            }
        else:
            return {"success": False, "error": "Employee not found"}

    except Exception as e:
        print(f"Error fetching employee: {e!s}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_projects(status: str | None = None) -> dict[str, Any]:
    """List projects, optionally filtered by status."""
    db = get_db()
    try:
        sql = "SELECT id, name, description, budget, start_date, end_date, status FROM projects"
        params: dict[str, Any] = {}

        if status:
            sql += " WHERE status = :status"
            params["status"] = status
        sql += " ORDER BY start_date DESC"

        results = db.execute(text(sql), params).fetchall()
        projects = [
            {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "budget": float(row.budget) if row.budget is not None else None,
                "start_date": str(row.start_date) if row.start_date else None,
                "end_date": str(row.end_date) if row.end_date else None,
                "status": row.status,
            }
            for row in results
        ]
        return {"success": True, "data": {"projects": projects, "count": len(projects)}}

    except Exception as e:
        print(f"Error fetching projects: {e!s}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_department_summary() -> dict[str, Any]:
    """Get summary statistics (employee count, avg/min/max salary) per department."""
    db = get_db()
    try:
        query = text("""
        SELECT
            department,
            COUNT(*) as employee_count,
            AVG(salary) as avg_salary,
            MIN(salary) as min_salary,
            MAX(salary) as max_salary
        FROM employees
        GROUP BY department
        ORDER BY department
        """)

        results = db.execute(query).fetchall()
        departments = [
            {
                "department": row.department,
                "employee_count": row.employee_count,
                "avg_salary": (
                    float(row.avg_salary) if row.avg_salary is not None else None
                ),
                "min_salary": (
                    float(row.min_salary) if row.min_salary is not None else None
                ),
                "max_salary": (
                    float(row.max_salary) if row.max_salary is not None else None
                ),
            }
            for row in results
        ]
        return {"success": True, "data": {"departments": departments}}

    except Exception as e:
        print(f"Error fetching department summary: {e!s}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def add_employee(
    name: str, email: str, department: str, salary: float, hire_date: str
) -> dict[str, Any]:
    """Insert a new employee and return the created record."""
    db = get_db()
    try:
        query = text("""
        INSERT INTO employees (name, email, department, salary, hire_date)
        VALUES (:name, :email, :department, :salary, :hire_date)
        RETURNING id, name, email, department, salary, hire_date
        """)

        result = db.execute(
            query,
            {
                "name": name,
                "email": email,
                "department": department,
                "salary": salary,
                "hire_date": hire_date,
            },
        ).fetchone()
        db.commit()

        return {
            "success": True,
            "data": {
                "new_employee": {
                    "id": result.id,
                    "name": result.name,
                    "email": result.email,
                    "department": result.department,
                    "salary": (
                        float(result.salary) if result.salary is not None else None
                    ),
                    "hire_date": str(result.hire_date) if result.hire_date else None,
                },
                "status": "created",
            },
        }

    except Exception as e:
        print(f"Error adding employee: {e!s}")
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()
