# Bedrock Agent with External PostgreSQL Database - Complete Setup Guide

> See [`README.md`](./README.md) for this project's status note (preserved reference code, not re-deployable in a new AWS account) and its relationship to the rest of `02-postgres-db-agent/`.

This guide provides step-by-step instructions to set up an Amazon Bedrock Agent that connects to an external PostgreSQL database (Azure Postgres Flexible Server).

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Step 1: Prepare the Lambda Deployment Package](#step-1-prepare-the-lambda-deployment-package)
- [Step 2: Create IAM Role for Lambda](#step-2-create-iam-role-for-lambda)
- [Step 3: Create and Configure Lambda Function](#step-3-create-and-configure-lambda-function)
- [Step 4: Create Bedrock Agent](#step-4-create-bedrock-agent)
- [Step 5: Configure Action Group](#step-5-configure-action-group)
- [Step 6: Test the Agent](#step-6-test-the-agent)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

---

## Overview

This solution enables Amazon Bedrock Agents to query external databases dynamically. The agent:

1. Retrieves database schema on demand
2. Analyzes user queries to identify relevant tables
3. Routes queries to appropriate database tables
4. Returns formatted results to the user

### Key Features

- **Dynamic Schema Discovery**: No hardcoded schema required
- **Intelligent Query Routing**: Automatically identifies relevant tables
- **Flexible SQL Execution**: Supports custom SQL queries
- **Azure PostgreSQL Compatible**: Works with Azure Postgres Flexible Server

---

## Architecture

```txt
User Query → Bedrock Agent → Lambda Function → PostgreSQL Database
                ↓                    ↓
          Action Group         db_connector.py
                              query_router.py
```

**Components:**

- **Bedrock Agent**: Processes natural language queries
- **Lambda Function**: Executes database operations
- **PostgreSQL Database**: Azure Postgres Flexible Server
- **Action Group**: Defines available API operations

---

## Prerequisites

Before starting, ensure you have:

### AWS Requirements

- AWS Account with permissions to:
  - Create Lambda functions
  - Create IAM roles
  - Create Bedrock agents
  - Access Bedrock foundation models
- AWS CLI installed and configured (optional but recommended)

### Database Requirements

- Azure PostgreSQL Flexible Server connection URI
- Database credentials with read permissions
- Network access from AWS Lambda to Azure PostgreSQL:
  - Ensure Azure PostgreSQL allows connections from AWS IP ranges
  - Configure firewall rules if necessary

### Development Requirements

- Python 3.11 or higher
- pip (Python package manager)
- Git (optional)

---

## Step 1: Prepare the Lambda Deployment Package

### 1.1 Navigate to Project Directory

```bash
cd ~/02-postgres-db-agent/external-azure
```

### 1.2 Activate Virtual Environment (if using one)

```bash
source .venv/bin/activate
```

### 1.3 Build Lambda Deployment Package

**For macOS/Linux:**

```bash
chmod +x build_lambda.sh
bash build_lambda.sh
```

**For Windows:**

```cmd
build_lambda.bat
```

This script will:

- Install all dependencies from `requirements.txt`
- Copy Python code files
- Create `lambda_deployment.zip`

### 1.4 Verify Package

Check that `lambda_deployment.zip` was created:

```bash
ls -lh lambda_deployment.zip
```

**Expected size:** 10-30 MB (depending on dependencies)

> **Note:** If the package exceeds 50MB, you'll need to upload it via S3 (instructions in Step 3).

---

## Step 2: Create IAM Role for Lambda

### 2.1 Create Lambda Execution Role

1. Open the [IAM Console](https://console.aws.amazon.com/iam/)
2. Navigate to **Roles** → **Create role**
3. Select **Trusted entity type**: AWS service
4. Select **Use case**: Lambda
5. Click **Next**

### 2.2 Attach Policies

Attach the following policies:

- `AWSLambdaBasicExecutionRole` (for CloudWatch Logs)
- `AWSLambdaVPCAccessExecutionRole` (if using VPC)

### 2.3 Create Custom Policy for Bedrock (Optional)

If you want to invoke Bedrock models from Lambda, create a custom policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2.4 Name and Create Role

- **Role name**: `BedrockAgentDatabaseLambdaRole`
- **Description**: "Execution role for Bedrock Agent Lambda function"
- Click **Create role**

### 2.5 Note the Role ARN

Copy the Role ARN - you'll need it in Step 3.
Example: `arn:aws:iam::123456789012:role/BedrockAgentDatabaseLambdaRole`

---

## Step 3: Create and Configure Lambda Function

### 3.1 Create Lambda Function

1. Open [Lambda Console](https://console.aws.amazon.com/lambda/)
2. Click **Create function**
3. Choose **Author from scratch**
4. Configure:
   - **Function name**: `bedrock-agent-db-query`
   - **Runtime**: Python 3.11 or 3.12
   - **Architecture**: x86_64
   - **Execution role**: Use existing role → Select `BedrockAgentDatabaseLambdaRole`
5. Click **Create function**

### 3.2 Upload Deployment Package

#### Option A: Direct Upload (if < 50MB)

1. In the Lambda function page, scroll to **Code source**
2. Click **Upload from** → **.zip file**
3. Select `lambda_deployment.zip`
4. Click **Save**

#### Option B: S3 Upload (if ≥ 50MB)

1. Upload to S3:

   ```bash
   aws s3 cp lambda_deployment.zip s3://your-bucket-name/lambda_deployment.zip
   ```

2. In Lambda console:
   - Click **Upload from** → **Amazon S3 location**
   - Enter S3 URI: `s3://your-bucket-name/lambda_deployment.zip`
   - Click **Save**

### 3.3 Configure Handler

1. Scroll to **Runtime settings**
2. Click **Edit**
3. Set **Handler**: `main.lambda_handler`
4. Click **Save**

### 3.4 Configure Environment Variables

1. Navigate to **Configuration** → **Environment variables**
2. Click **Edit** → **Add environment variable**
3. Add:
   - **Key**: `DB_URI`
   - **Value**: `postgresql+psycopg://youruser:yourpassword@your-server.postgres.database.azure.com/yourdatabase`
4. Click **Save**

> **Important:** When using SQLAlchemy, the connection URI must include the driver specification: `postgresql+psycopg://` instead of just `postgresql://`
> **Security Note:** For production, use AWS Secrets Manager to store database credentials securely.

### 3.5 Configure Timeout and Memory

1. Navigate to **Configuration** → **General configuration**
2. Click **Edit**
3. Set:
   - **Timeout**: 30 seconds (or higher for large schemas)
   - **Memory**: 512 MB (adjust based on needs)
4. Click **Save**

### 3.6 Configure Network (If Database Requires VPC)

If your PostgreSQL database is in a VPC:

1. Navigate to **Configuration** → **VPC**
2. Click **Edit**
3. Select appropriate VPC, subnets, and security groups
4. Ensure security groups allow outbound traffic to PostgreSQL
5. Click **Save**

### 3.7 Test Lambda Function

1. Navigate to **Test** tab
2. Create new test event:
   - **Event name**: `TestGetSchema`
   - **Event JSON**:
  
   ```json
   {
     "agent": "test-agent",
     "actionGroup": "DatabaseActions",
     "apiPath": "/getSchema",
     "httpMethod": "GET",
     "parameters": [],
     "requestBody": {}
   }
   ```

3. Click **Test**
4. Verify the response contains database schema

### 3.8 Note Lambda ARN

Copy the Lambda function ARN from the top right of the page.
Example: `arn:aws:lambda:us-east-1:123456789012:function:bedrock-agent-db-query`

---

## Step 4: Create Bedrock Agent

### 4.1 Open Bedrock Console

1. Navigate to [Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Select your region (e.g., us-east-1)
3. Ensure you have access to foundation models:
   - Go to **Model access** in the left menu
   - Request access to Claude models if not already enabled

### 4.2 Create Agent

1. In the left menu, click **Agents**
2. Click **Create Agent**
3. Configure agent details:
   - **Agent name**: `DatabaseQueryAgent`
   - **Description**: "Agent for querying external PostgreSQL database"
   - **User input**: Leave enabled
4. Click **Next**

### 4.3 Select Foundation Model

1. Select model: **Anthropic Claude 3 Sonnet** (or latest version)
2. Configure instructions:

   ```txt
    You are a database query assistant. Your role is to help users query a PostgreSQL database. 

    When a user asks a question:
    1. First, retrieve the database schema to understand available tables and columns
    2. Analyze the user's query to identify relevant tables
    3. Use the appropriate API to query the database
    4. Present results in a clear, formatted manner

    Available capabilities:
    - getSchema: Retrieve complete database structure
    - queryDatabase: Query using natural language
    - executeSQL: Execute custom SQL queries

    Always explain what you're doing and provide context for the results.
   ```

3. Click **Next**

### 4.4 Configure Action Groups (Continue to Step 5)

---

## Step 5: Configure Action Group

### 5.1 Add Action Group

1. In the agent creation wizard, click **Add action group**
2. Configure:
   - **Action group name**: `DatabaseActions`
   - **Description**: "Actions for database operations"
   - **Action group type**: Define with API schemas

### 5.2 Upload API Schema

1. Select **API schema** → **Upload**
2. Click **Choose file** and select `bedrock_agent_schema.json` from your project
3. Alternatively, select **S3** and provide S3 URI if uploaded there

### 5.3 Configure Lambda Function

1. Scroll to **Lambda function**
2. Select your Lambda function: `bedrock-agent-db-query`
3. Lambda will automatically add resource-based permissions

### 5.4 Finalize Action Group

1. Click **Add**
2. Review action group configuration
3. Click **Create** to create the agent

### 5.5 Prepare Agent

1. After creation, you'll see the agent overview
2. Click **Prepare** to prepare the agent for testing
3. Wait for preparation to complete (may take 1-2 minutes)

---

## Step 6: Test the Agent

### 6.1 Test in Console

1. In the agent overview, click **Test**
2. The test interface will open on the right side

### 6.2 Example Test Queries

Try these queries:

#### Query 1: Get Schema

```txt
Show me the database schema
```

Expected response: Agent will retrieve and display all tables and columns

#### Query 2: Natural Language Query

```txt
Show me all employees in the database
```

Expected response: Agent will find the employees table and return data

#### Query 3: Custom SQL

```txt
Execute this SQL query: SELECT * FROM employees LIMIT 5
```

Expected response: Results from the custom SQL query

### 6.3 Create Alias (For Production Use)

1. In the agent overview, go to **Aliases**
2. Click **Create alias**
3. Configure:
   - **Alias name**: `production`
   - **Description**: "Production version"
4. Click **Create**

### 6.4 Invoke via AWS SDK (Optional)

Example Python code to invoke the agent:

```python
import boto3
import uuid

bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

def query_agent(prompt):
    session_id = str(uuid.uuid4())
    
    response = bedrock_agent.invoke_agent(
        agentId='YOUR_AGENT_ID',
        agentAliasId='YOUR_ALIAS_ID',
        sessionId=session_id,
        inputText=prompt
    )
    
    # Process response stream
    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            print(chunk['bytes'].decode())

# Test
query_agent("Show me the database schema")
```

---

## Troubleshooting

### Issue: Lambda timeout

**Solution:** Increase Lambda timeout in Configuration → General configuration

### Issue: Database connection failed

**Possible causes:**

- Network connectivity (check VPC configuration)
- Incorrect database URI
- Firewall rules blocking AWS IP ranges
- Database credentials incorrect

**Solutions:**

- Verify database URI in environment variables
- Check Azure PostgreSQL firewall rules
- Test connection from Lambda VPC
- Verify credentials

### Issue: Agent not finding relevant tables

**Solution:**

- Check query_router.py logic
- Ensure database schema is being retrieved correctly
- Add more keywords to improve matching

### Issue: Package too large for Lambda

**Solution:**

- Use Lambda layers for large dependencies
- Upload via S3
- Optimize dependencies (remove unused packages)

### Issue: Permission denied errors

**Solutions:**

- Verify IAM role has necessary permissions
- Check Lambda resource-based policy for Bedrock
- Ensure database user has appropriate permissions

### Viewing Logs

1. Open CloudWatch Logs Console
2. Find log group: `/aws/lambda/bedrock-agent-db-query`
3. View recent log streams
4. Look for error messages and stack traces

---

## Security Best Practices

### 1. Use AWS Secrets Manager for Database Credentials

Instead of storing DB_URI in environment variables:

1. Create secret in Secrets Manager:

   ```bash
   aws secretsmanager create-secret \
     --name prod/database/uri \
     --secret-string "postgresql+psycopg://..."
   ```

2. Modify `main.py` to retrieve from Secrets Manager:

   ```python
   import boto3
   
   def get_db_uri():
       client = boto3.client('secretsmanager')
       response = client.get_secret_value(SecretId='prod/database/uri')
       return response['SecretString']
   
   DB_URI = get_db_uri()
   ```

3. Add Secrets Manager permission to Lambda role

### 2. Use VPC for Network Isolation

- Deploy Lambda in a VPC
- Use VPC endpoints for AWS services
- Configure security groups to allow only necessary traffic

### 3. Enable Database Connection Encryption

Ensure your PostgreSQL connection uses SSL:

```python
DB_URI = "postgresql+psycopg://user:pass@host/db?sslmode=require"
```

### 4. Implement Rate Limiting

Add rate limiting to prevent abuse:

- Use API Gateway in front of Lambda
- Implement token bucket algorithm
- Monitor CloudWatch metrics

### 5. Audit and Monitoring

- Enable CloudTrail for API calls
- Set up CloudWatch alarms for errors
- Monitor Lambda execution metrics
- Review database access logs

### 6. Least Privilege Access

- Database user should have minimum required permissions
- Lambda role should only access necessary AWS services
- Use read-only database user if only querying

### 7. Input Validation

The code includes basic SQL injection protection, but always:

- Validate user inputs
- Use parameterized queries
- Sanitize data before execution
- Implement query complexity limits

---

## Next Steps

### Enhancements

1. **Add Caching**: Cache database schema to reduce queries
2. **Improve Query Router**: Use NLP or LLM to better analyze queries
3. **Add Authentication**: Implement user authentication and authorization
4. **Support Multiple Databases**: Extend to support multiple database connections
5. **Query Optimization**: Add query planning and optimization
6. **Result Pagination**: Handle large result sets with pagination

### Integration Options

- **API Gateway**: Create REST API for external access
- **Step Functions**: Orchestrate complex workflows
- **EventBridge**: Trigger queries based on events
- **S3 Export**: Export large query results to S3

### Monitoring Dashboard

Create a CloudWatch dashboard to monitor:

- Lambda invocation count
- Error rates
- Database query duration
- Agent usage metrics

---

## Support and Resources

### Documentation

- [Amazon Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [AWS Lambda](https://docs.aws.amazon.com/lambda/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### AWS Support

- [AWS Support Console](https://console.aws.amazon.com/support/)
- [AWS Forums](https://forums.aws.amazon.com/)

### Project Files

- `main.py`: Lambda handler
- `db_connector.py`: Database connection module
- `query_router.py`: Query routing logic
- `bedrock_agent_schema.json`: OpenAPI schema
- `schema.sql`: Optional employees/projects sample schema for a scratch database
- `requirements.txt`: Python dependencies
- `build_lambda.sh`: Build script (Linux/Mac)
- `build_lambda.bat`: Build script (Windows)

---

## Conclusion

You now have a fully functional Bedrock Agent that can:

- Dynamically discover database schemas
- Route natural language queries to appropriate tables
- Execute custom SQL queries
- Work with external PostgreSQL databases

This architecture is flexible and can be adapted for different databases, schemas, and use cases.

For questions or issues, refer to the troubleshooting section or AWS documentation.

---

**Last Updated:** December 3, 2025
**Version:** 1.0.0
