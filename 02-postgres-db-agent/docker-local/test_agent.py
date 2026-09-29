"""
Test script for Lambda function and Bedrock Agent integration.
"""

import json
import boto3
import os

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
AGENT_ID = os.environ.get("BEDROCK_AGENT_ID")
AGENT_ALIAS_ID = os.environ.get("BEDROCK_AGENT_ALIAS_ID", "TSTALIASID")


def test_lambda_locally():
    """Test Lambda function locally."""
    from lambda_function import lambda_handler

    # Sample Bedrock Agent event
    event = {
        "messageVersion": "1.0",
        "agent": {
            "name": "employee-database-agent",
            "id": "test-agent-id",
            "alias": "test-alias",
            "version": "1",
        },
        "inputText": "Get all employees in Engineering department",
        "sessionId": "test-session-123",
        "actionGroup": "database-actions",
        "apiPath": "/employees",
        "httpMethod": "GET",
        "parameters": [
            {"name": "department", "type": "string", "value": "Engineering"}
        ],
        "requestBody": {},
    }

    print("Testing Lambda function with sample event...")
    print(json.dumps(event, indent=2))

    try:
        response = lambda_handler(event, {})
        print("\n✓ Lambda Response:")
        print(json.dumps(response, indent=2))
        return True
    except Exception as e:
        print(f"\n❌ Error: {e!s}")
        return False


def test_bedrock_agent(query: str):
    """Test Bedrock Agent."""
    if not AGENT_ID:
        print("Error: Set BEDROCK_AGENT_ID environment variable")
        return

    bedrock_agent_runtime = boto3.client(
        "bedrock-agent-runtime", region_name=AWS_REGION
    )

    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")

    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId="test-session-" + str(hash(query)),
            inputText=query,
        )

        # Process streaming response
        event_stream = response["completion"]

        full_response = ""
        for event in event_stream:
            if "chunk" in event:
                chunk = event["chunk"]
                if "bytes" in chunk:
                    full_response += chunk["bytes"].decode("utf-8")

        print("\n✓ Agent Response:")
        print(full_response)

        return full_response

    except Exception as e:
        print(f"\n❌ Error: {e!s}")
        return None


def run_agent_tests():
    """Run a series of test queries."""
    test_queries = [
        "List all employees in the Engineering department",
        "What is the average salary by department?",
        "Show me all active projects",
        "Get details for employee with ID 1",
        "How many employees work in each department?",
        "What projects have a budget over $100,000?",
    ]

    for query in test_queries:
        test_bedrock_agent(query)
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "local":
            # Test Lambda function locally
            test_lambda_locally()
        elif sys.argv[1] == "agent":
            # Test Bedrock Agent
            if len(sys.argv) > 2:
                query = " ".join(sys.argv[2:])
                test_bedrock_agent(query)
            else:
                run_agent_tests()
    else:
        print("Usage:")
        print("  python test_agent.py local                    # Test Lambda locally")
        print("  python test_agent.py agent                    # Run all test queries")
        print("  python test_agent.py agent 'your question'    # Test specific query")
