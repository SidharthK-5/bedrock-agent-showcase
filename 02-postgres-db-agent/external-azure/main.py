"""
AWS Lambda Handler for Bedrock Agent with PostgreSQL Integration
"""

import json
import os
from typing import Any

from db_connector import DatabaseConnector
from query_router import QueryRouter

# Database configuration from environment variables
DB_URI = os.environ.get(
    "DB_URI",
    "postgresql+psycopg://youruser:yourpassword@your-server.postgres.database.azure.com/yourdatabase",
)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Main Lambda handler for Bedrock Agent

    Args:
        event: Lambda event containing Bedrock Agent request
        context: Lambda context

    Returns:
        Response dictionary for Bedrock Agent
    """
    print(f"Received event: {json.dumps(event)}")

    # Extract information from Bedrock Agent event
    agent = event.get("agent", "")  # noqa: F841
    action_group = event.get("actionGroup", "")
    api_path = event.get("apiPath", "")
    http_method = event.get("httpMethod", "")
    parameters = event.get("parameters", [])
    request_body = event.get("requestBody", {})  # noqa: F841

    # Parse parameters into a dictionary
    params_dict = {}
    for param in parameters:
        params_dict[param.get("name")] = param.get("value")

    print(f"API Path: {api_path}, Method: {http_method}")
    print(f"Parameters: {params_dict}")

    try:
        # Route to appropriate function based on API path
        if api_path == "/getSchema":
            response_body = get_database_schema()
        elif api_path == "/queryDatabase":
            user_query = params_dict.get("query", "")
            response_body = query_database(user_query)
        elif api_path == "/executeSQL":
            sql_query = params_dict.get("sqlQuery", "")
            response_body = execute_sql_query(sql_query)
        else:
            response_body = {"error": f"Unknown API path: {api_path}"}

        # Format response for Bedrock Agent
        response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": action_group,
                "apiPath": api_path,
                "httpMethod": http_method,
                "httpStatusCode": 200,
                "responseBody": {
                    "application/json": {"body": json.dumps(response_body)}
                },
            },
        }

        return response

    except Exception as e:
        print(f"Error processing request: {e!s}")
        error_response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": action_group,
                "apiPath": api_path,
                "httpMethod": http_method,
                "httpStatusCode": 500,
                "responseBody": {
                    "application/json": {"body": json.dumps({"error": str(e)})}
                },
            },
        }
        return error_response


def get_database_schema() -> dict[str, Any]:
    """
    Get complete database schema

    Returns:
        Dictionary containing database schema
    """
    db = DatabaseConnector(DB_URI)
    try:
        db.connect()
        schema = db.get_complete_database_schema()

        # Generate a summary for better readability
        router = QueryRouter(schema)
        schema_summary = router.get_schema_summary()

        return {"success": True, "schema": schema, "summary": schema_summary}
    finally:
        db.disconnect()


def query_database(user_query: str) -> dict[str, Any]:
    """
    Process natural language query and return results

    Args:
        user_query: User's natural language query

    Returns:
        Query results dictionary
    """
    db = DatabaseConnector(DB_URI)
    try:
        db.connect()

        # Get database schema
        schema = db.get_complete_database_schema()

        # Use query router to analyze query
        router = QueryRouter(schema)
        analysis = router.analyze_query_intent(user_query)

        # If relevant tables found, query them
        results = {}
        if analysis["relevant_tables"]:
            for table_info in analysis["relevant_tables"][:3]:  # Limit to 3 tables
                table_name = table_info["table"]
                schema_name = table_info["schema"]

                # Get sample data from relevant table
                sample_data = db.get_table_sample_data(
                    table_name, schema_name, limit=10
                )
                results[f"{schema_name}.{table_name}"] = {
                    "reason": table_info["reason"],
                    "data": sample_data,
                }

        return {
            "success": True,
            "query": user_query,
            "analysis": analysis["relevant_tables"],
            "results": results,
            "schema_info": analysis["schema_summary"] if not results else None,
        }
    finally:
        db.disconnect()


def execute_sql_query(sql_query: str) -> dict[str, Any]:
    """
    Execute a custom SQL query

    Args:
        sql_query: SQL query string

    Returns:
        Query results dictionary
    """
    db = DatabaseConnector(DB_URI)
    try:
        db.connect()

        # Execute the query
        results = db.execute_custom_query(sql_query)

        return {
            "success": True,
            "query": sql_query,
            "row_count": len(results),
            "results": results,
        }
    finally:
        db.disconnect()


def main():
    """Local testing function"""
    print("Testing Bedrock Agent Lambda Handler")

    # Test event for schema retrieval
    test_event = {
        "agent": "test-agent",
        "actionGroup": "DatabaseActions",
        "apiPath": "/getSchema",
        "httpMethod": "GET",
        "parameters": [],
        "requestBody": {},
    }

    result = lambda_handler(test_event, None)
    print(f"Test Result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
