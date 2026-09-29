"""
Lambda function to act as a proxy between Bedrock Agent and local PostgreSQL database.

This function will be invoked by Bedrock Agent through API Gateway.
It translates natural language queries into SQL and executes them against the local DB.
"""

import json
import os
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    """Establish connection to PostgreSQL database."""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
        database=os.environ.get("DB_NAME", "bedrockdb"),
        user=os.environ.get("DB_USER", "dbuser"),
        password=os.environ.get("DB_PASSWORD", "dbpassword123"),
    )


def execute_query(sql_query: str, params: tuple | None = None) -> list[dict[str, Any]]:
    """Execute SQL query and return results."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql_query, params)

            # Check if query returns results
            if cursor.description:
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                conn.commit()
                return [{"status": "success", "rows_affected": cursor.rowcount}]
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def get_employees(filters: dict[str, Any] | None = None) -> dict[str, Any]:
    """Get employees with optional filters."""
    query = "SELECT * FROM employees"
    conditions = []
    params = []

    if filters:
        if filters.get("department"):
            conditions.append("department = %s")
            params.append(filters["department"])
        if filters.get("min_salary"):
            conditions.append("salary >= %s")
            params.append(filters["min_salary"])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id"

    results = execute_query(query, tuple(params) if params else None)
    return {"employees": results, "count": len(results)}


def get_projects(status: str | None = None) -> dict[str, Any]:
    """Get projects with optional status filter."""
    query = "SELECT * FROM projects"
    params = None

    if status:
        query += " WHERE status = %s"
        params = (status,)

    query += " ORDER BY start_date DESC"

    results = execute_query(query, params)
    return {"projects": results, "count": len(results)}


def get_employee_by_id(employee_id: int) -> dict[str, Any]:
    """Get employee by ID."""
    query = "SELECT * FROM employees WHERE id = %s"
    results = execute_query(query, (employee_id,))

    if results:
        return {"employee": results[0]}
    else:
        return {"error": "Employee not found", "employee_id": employee_id}


def get_department_summary() -> dict[str, Any]:
    """Get summary statistics by department."""
    query = """
        SELECT 
            department,
            COUNT(*) as employee_count,
            AVG(salary) as avg_salary,
            MIN(salary) as min_salary,
            MAX(salary) as max_salary
        FROM employees
        GROUP BY department
        ORDER BY department
    """
    results = execute_query(query)
    return {"departments": results}


def add_employee(
    name: str, email: str, department: str, salary: float, hire_date: str
) -> dict[str, Any]:
    """Add a new employee."""
    query = """
        INSERT INTO employees (name, email, department, salary, hire_date)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, name, email, department, salary, hire_date
    """
    results = execute_query(query, (name, email, department, salary, hire_date))
    return {"new_employee": results[0], "status": "created"}


def lambda_handler(event, context):
    """
    Main Lambda handler for Bedrock Agent requests.

    Event structure from Bedrock Agent:
    {
        "messageVersion": "1.0",
        "agent": {...},
        "inputText": "user query",
        "sessionId": "...",
        "actionGroup": "...",
        "apiPath": "/path",
        "httpMethod": "GET/POST",
        "parameters": [...],
        "requestBody": {...}
    }
    """

    print(f"Received event: {json.dumps(event)}")

    try:
        # Extract action information from Bedrock Agent
        action_group = event.get("actionGroup", "")
        api_path = event.get("apiPath", "")
        http_method = event.get("httpMethod", "GET")
        parameters = event.get("parameters", [])
        request_body = event.get("requestBody", {})

        # Convert parameters list to dict for easier access
        params_dict = {}
        if parameters:
            for param in parameters:
                params_dict[param.get("name")] = param.get("value")

        # Route to appropriate function based on API path
        result = None

        if api_path == "/employees" and http_method == "GET":
            filters = {}
            if params_dict.get("department"):
                filters["department"] = params_dict["department"]
            if params_dict.get("min_salary"):
                filters["min_salary"] = float(params_dict["min_salary"])
            result = get_employees(filters if filters else None)

        elif api_path == "/employees/{id}" and http_method == "GET":
            employee_id = int(params_dict.get("id", 0))
            result = get_employee_by_id(employee_id)

        elif api_path == "/employees" and http_method == "POST":
            # Extract from request body
            body = request_body.get("content", {}).get("application/json", {})
            result = add_employee(
                name=body.get("name"),
                email=body.get("email"),
                department=body.get("department"),
                salary=float(body.get("salary")),
                hire_date=body.get("hire_date"),
            )

        elif api_path == "/projects" and http_method == "GET":
            status = params_dict.get("status")
            result = get_projects(status)

        elif api_path == "/departments/summary" and http_method == "GET":
            result = get_department_summary()

        else:
            result = {
                "error": "Unknown API path or method",
                "path": api_path,
                "method": http_method,
            }

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

    except Exception as e:
        print(f"Error: {e!s}")

        # Return error response in Bedrock Agent format
        error_response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get("actionGroup", ""),
                "apiPath": event.get("apiPath", ""),
                "httpMethod": event.get("httpMethod", "GET"),
                "httpStatusCode": 500,
                "responseBody": {
                    "application/json": {"body": json.dumps({"error": str(e)})}
                },
            },
        }

        return error_response
