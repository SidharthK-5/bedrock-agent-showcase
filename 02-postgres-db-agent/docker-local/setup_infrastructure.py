"""
AWS Infrastructure setup using Boto3 for Bedrock Agent with local DB connection.

This script creates:
1. Lambda function
2. API Gateway
3. IAM roles and permissions
4. Bedrock Agent with action group
"""

import io
import json
import os
import zipfile

import boto3

# AWS Configuration
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID")

# Resource names
LAMBDA_FUNCTION_NAME = "bedrock-agent-db-proxy"
API_NAME = "bedrock-agent-api"
AGENT_NAME = "employee-database-agent"
AGENT_ROLE_NAME = "bedrock-agent-role"
LAMBDA_ROLE_NAME = "bedrock-agent-lambda-role"


def create_lambda_deployment_package():
    """Create a deployment package for Lambda function."""
    print("Creating Lambda deployment package...")

    # Create in-memory zip file
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Add lambda function
        zip_file.write("lambda_function.py", "lambda_function.py")

        # Note: For psycopg2, you'll need to include the compiled binary
        # You can get this from a Lambda layer or build it in a Linux environment
        print("Note: You'll need to add psycopg2 binary dependencies manually")
        print("Consider using a Lambda Layer for PostgreSQL dependencies")

    zip_buffer.seek(0)
    return zip_buffer.read()


def create_lambda_role(iam_client):
    """Create IAM role for Lambda function."""
    print(f"Creating Lambda IAM role: {LAMBDA_ROLE_NAME}")

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    try:
        response = iam_client.create_role(
            RoleName=LAMBDA_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for Bedrock Agent Lambda function",
        )

        # Attach basic Lambda execution policy
        iam_client.attach_role_policy(
            RoleName=LAMBDA_ROLE_NAME,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        )

        print(f"✓ Created Lambda role: {response['Role']['Arn']}")
        return response["Role"]["Arn"]

    except iam_client.exceptions.EntityAlreadyExistsException:
        response = iam_client.get_role(RoleName=LAMBDA_ROLE_NAME)
        print(f"✓ Lambda role already exists: {response['Role']['Arn']}")
        return response["Role"]["Arn"]


def create_lambda_function(lambda_client, role_arn, db_config):
    """Create Lambda function."""
    print(f"Creating Lambda function: {LAMBDA_FUNCTION_NAME}")

    deployment_package = create_lambda_deployment_package()

    try:
        response = lambda_client.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime="python3.11",
            Role=role_arn,
            Handler="lambda_function.lambda_handler",
            Code={"ZipFile": deployment_package},
            Description="Proxy function for Bedrock Agent to access local database",
            Timeout=30,
            MemorySize=256,
            Environment={
                "Variables": {
                    "DB_HOST": db_config["host"],
                    "DB_PORT": str(db_config["port"]),
                    "DB_NAME": db_config["database"],
                    "DB_USER": db_config["user"],
                    "DB_PASSWORD": db_config["password"],
                }
            },
        )

        print(f"✓ Created Lambda function: {response['FunctionArn']}")
        return response["FunctionArn"]

    except lambda_client.exceptions.ResourceConflictException:
        response = lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
        print(
            f"✓ Lambda function already exists: {response['Configuration']['FunctionArn']}"
        )
        return response["Configuration"]["FunctionArn"]


def create_api_gateway(apigateway_client, lambda_arn, account_id):
    """Create API Gateway REST API."""
    print(f"Creating API Gateway: {API_NAME}")

    # Create REST API
    api_response = apigateway_client.create_rest_api(
        name=API_NAME,
        description="API for Bedrock Agent to access database",
        endpointConfiguration={"types": ["REGIONAL"]},
    )

    api_id = api_response["id"]
    print(f"✓ Created API: {api_id}")

    # Get root resource
    resources = apigateway_client.get_resources(restApiId=api_id)
    root_id = resources["items"][0]["id"]

    # Create proxy resource
    proxy_resource = apigateway_client.create_resource(
        restApiId=api_id, parentId=root_id, pathPart="{proxy+}"
    )

    # Create ANY method
    apigateway_client.put_method(
        restApiId=api_id,
        resourceId=proxy_resource["id"],
        httpMethod="ANY",
        authorizationType="NONE",
    )

    # Set up Lambda integration
    lambda_uri = f"arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"

    apigateway_client.put_integration(
        restApiId=api_id,
        resourceId=proxy_resource["id"],
        httpMethod="ANY",
        type="AWS_PROXY",
        integrationHttpMethod="POST",
        uri=lambda_uri,
    )

    # Deploy API
    deployment = apigateway_client.create_deployment(restApiId=api_id, stageName="prod")

    api_url = f"https://{api_id}.execute-api.{AWS_REGION}.amazonaws.com/prod"
    print(f"✓ API deployed: {api_url}")

    return api_id, api_url


def create_bedrock_agent_role(iam_client, account_id):
    """Create IAM role for Bedrock Agent."""
    print(f"Creating Bedrock Agent IAM role: {AGENT_ROLE_NAME}")

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    try:
        response = iam_client.create_role(
            RoleName=AGENT_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for Bedrock Agent",
        )

        # Create inline policy for invoking Lambda
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["lambda:InvokeFunction"],
                    "Resource": f"arn:aws:lambda:{AWS_REGION}:{account_id}:function:{LAMBDA_FUNCTION_NAME}",
                },
                {"Effect": "Allow", "Action": ["bedrock:InvokeModel"], "Resource": "*"},
            ],
        }

        iam_client.put_role_policy(
            RoleName=AGENT_ROLE_NAME,
            PolicyName="BedrockAgentPolicy",
            PolicyDocument=json.dumps(policy),
        )

        print(f"✓ Created Bedrock Agent role: {response['Role']['Arn']}")
        return response["Role"]["Arn"]

    except iam_client.exceptions.EntityAlreadyExistsException:
        response = iam_client.get_role(RoleName=AGENT_ROLE_NAME)
        print(f"✓ Bedrock Agent role already exists: {response['Role']['Arn']}")
        return response["Role"]["Arn"]


def create_bedrock_agent(bedrock_agent_client, agent_role_arn, lambda_arn):
    """Create Bedrock Agent."""
    print(f"Creating Bedrock Agent: {AGENT_NAME}")

    # Read API schema
    with open("api-schema.yaml", "r") as f:
        api_schema = f.read()

    try:
        # Create agent
        agent_response = bedrock_agent_client.create_agent(
            agentName=AGENT_NAME,
            agentResourceRoleArn=agent_role_arn,
            description="Agent for querying employee database",
            foundationModel="anthropic.claude-3-sonnet-20240229-v1:0",
            instruction="""You are an AI assistant that helps users query an employee database. 
            You can retrieve employee information, project details, and department statistics.
            Always provide clear and accurate information based on the database queries.
            When users ask about employees or projects, use the available API functions to fetch the data.""",
        )

        agent_id = agent_response["agent"]["agentId"]
        print(f"✓ Created agent: {agent_id}")

        # Create action group
        action_group_response = bedrock_agent_client.create_agent_action_group(
            agentId=agent_id,
            agentVersion="DRAFT",
            actionGroupName="database-actions",
            description="Actions for querying the employee database",
            actionGroupExecutor={"lambda": lambda_arn},
            apiSchema={"payload": api_schema},
        )

        print(
            f"✓ Created action group: {action_group_response['agentActionGroup']['actionGroupId']}"
        )

        # Prepare agent
        bedrock_agent_client.prepare_agent(agentId=agent_id)
        print("✓ Agent prepared and ready to use")

        return agent_id

    except Exception as e:
        print(f"Error creating Bedrock Agent: {e!s}")
        raise


def main():
    """Main setup function."""
    print("=" * 60)
    print("Bedrock Agent Local DB Setup")
    print("=" * 60)

    if not ACCOUNT_ID:
        print("Error: Please set AWS_ACCOUNT_ID environment variable")
        return

    # Database configuration
    db_config = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", 5432)),
        "database": os.environ.get("DB_NAME", "bedrockdb"),
        "user": os.environ.get("DB_USER", "dbuser"),
        "password": os.environ.get("DB_PASSWORD", "dbpassword123"),
    }

    # Initialize AWS clients
    iam_client = boto3.client("iam", region_name=AWS_REGION)
    lambda_client = boto3.client("lambda", region_name=AWS_REGION)
    apigateway_client = boto3.client("apigateway", region_name=AWS_REGION)
    bedrock_agent_client = boto3.client("bedrock-agent", region_name=AWS_REGION)

    try:
        # Step 1: Create Lambda role
        lambda_role_arn = create_lambda_role(iam_client)

        # Wait for role to propagate
        import time

        print("Waiting for IAM role to propagate...")
        time.sleep(10)

        # Step 2: Create Lambda function
        lambda_arn = create_lambda_function(lambda_client, lambda_role_arn, db_config)

        # Step 3: Create API Gateway
        api_id, api_url = create_api_gateway(apigateway_client, lambda_arn, ACCOUNT_ID)

        # Grant API Gateway permission to invoke Lambda
        lambda_client.add_permission(
            FunctionName=LAMBDA_FUNCTION_NAME,
            StatementId="apigateway-invoke",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{AWS_REGION}:{ACCOUNT_ID}:{api_id}/*/*",
        )

        # Step 4: Create Bedrock Agent role
        agent_role_arn = create_bedrock_agent_role(iam_client, ACCOUNT_ID)

        # Wait for role to propagate
        print("Waiting for IAM role to propagate...")
        time.sleep(10)

        # Step 5: Create Bedrock Agent
        agent_id = create_bedrock_agent(
            bedrock_agent_client, agent_role_arn, lambda_arn
        )

        print("\n" + "=" * 60)
        print("Setup Complete!")
        print("=" * 60)
        print(f"Agent ID: {agent_id}")
        print(f"API URL: {api_url}")
        print(f"Lambda Function: {lambda_arn}")
        print("\nNext steps:")
        print("1. Test your Lambda function")
        print("2. Invoke your Bedrock Agent")
        print("3. Monitor CloudWatch logs for debugging")

    except Exception as e:
        print(f"\n❌ Setup failed: {e!s}")
        raise


if __name__ == "__main__":
    main()
