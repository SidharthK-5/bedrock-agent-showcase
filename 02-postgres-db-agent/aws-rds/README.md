# Amazon Bedrock Agent with RDS PostgreSQL Connection

Complete guide to deploying a Bedrock Agent that connects to your PostgreSQL database on AWS RDS.

> **Status note:** This project was originally built and verified against a classic Amazon Bedrock Agent connected to a real AWS RDS PostgreSQL instance, in a different AWS account/engagement no longer accessible to this repo's maintainer. It's preserved here as reference code — the deployment steps, IAM policies, and troubleshooting notes below are real and were followed at the time — but it has not been (and currently cannot be) re-deployed or re-tested in this sandbox, since AWS no longer allows new accounts to create classic Bedrock Agents. All hostnames, credentials, account IDs, and agent IDs below have been replaced with placeholders.
See `../README.md` for how this fits into the "one pattern, three targets" pattern of `02-postgres-db-agent/`, and see `TROUBLESHOOTING.md` for a real IAM/psycopg2 deployment issue encountered during original development.

## 📋 Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.11 installed locally
- AWS Account with permissions for:
  - Lambda
  - Bedrock
  - IAM
  - RDS (already have your database)

## 🗂️ Project Structure

```
aws-rds/
├── schema.sql                      # employees/projects schema + seed data (same as docker-local/init.sql)
├── lambda_function.py              # Main Lambda handler (SQLAlchemy + psycopg2)
├── lambda-requirements.txt         # Lambda deployment package dependencies
├── bedrock-agent-schema.json       # OpenAPI schema for the Bedrock Agent action group
├── test-event.json                 # Sample event for local/CLI Lambda testing
├── deploy.sh                       # Deployment automation script (source of truth for packaging)
├── add-lambda-permissions.sh       # Grants Bedrock permission to invoke the Lambda (Step 7)
├── lambda-trust-policy.json        # IAM trust policy for the Lambda execution role
├── lambda-execution-policy.json    # IAM execution policy for the Lambda execution role
├── pyproject.toml / uv.lock        # Local dev dependencies (not the Lambda package — see lambda-requirements.txt)
├── README.md                        # This file
└── TROUBLESHOOTING.md              # Real psycopg2/IAM issue from original development
```

## 🗄️ Database Schema

This project uses the same `employees`/`projects` schema as the other two
subprojects in `02-postgres-db-agent/` (see [`../README.md`](../README.md)).
Before deploying the Lambda, create the tables and seed data on your RDS
instance:

```bash
psql "host=<rds-endpoint> port=5432 dbname=<db> user=<user>" -f schema.sql
```

## 🚀 Step-by-Step Deployment Guide

### Step 1: Create IAM Role for Lambda

The Lambda function needs an IAM role with permissions to write logs and connect to your VPC (if RDS is in a VPC).

```bash
# Create the IAM role
aws iam create-role \
  --role-name bedrock-lambda-execution-role \
  --assume-role-policy-document file://lambda-trust-policy.json

# Attach the execution policy
aws iam put-role-policy \
  --role-name bedrock-lambda-execution-role \
  --policy-name bedrock-lambda-execution-policy \
  --policy-document file://lambda-execution-policy.json

# Attach AWS managed policy for basic Lambda execution
aws iam attach-role-policy \
  --role-name bedrock-lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

Wait 10-15 seconds for IAM role propagation.

### Step 2: Create Lambda Function

Get your AWS account ID:

```bash
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

Create the Lambda function by running `./deploy.sh`. The function doesn't exist yet on a first run, so the script builds `lambda-deployment.zip` (with the platform-pinned `pip install` flags — see [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) for why those matter) and then prints the exact `aws lambda create-function` command to run, with your account ID and role ARN already filled in. Copy that printed command rather than hand-assembling one, so `--zip-file`/`--role` match what was actually just built.

### Step 3: Configure VPC Access (If RDS is in VPC)

If your RDS instance is in a VPC (which it likely is), configure Lambda VPC access:

```bash
# Get your RDS VPC, subnets, and security groups
# Replace these with your actual values

aws lambda update-function-configuration \
  --function-name bedrock-db-connector \
  --vpc-config SubnetIds=subnet-xxxxx,subnet-yyyyy,SecurityGroupIds=sg-zzzzz \
  --region us-east-1
```

**Important**: Ensure the Lambda security group can access RDS on port 5432, and that RDS security group allows inbound traffic from Lambda's security group.

### Step 4: Test Lambda Function

Create a test event:

```json
{
  "actionGroup": "DatabaseActions",
  "apiPath": "/employees",
  "httpMethod": "GET",
  "parameters": [
    {
      "name": "department",
      "value": "Engineering"
    }
  ]
}
```

Test the function:

```bash
aws lambda invoke \
  --function-name bedrock-db-connector \
  --payload file://test-event.json \
  --region us-east-1 \
  response.json

cat response.json
```

### Step 5: Create IAM Role for Bedrock Agent

```bash
# Create trust policy for Bedrock
cat > bedrock-agent-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name bedrock-agent-role \
  --assume-role-policy-document file://bedrock-agent-trust-policy.json

# Create and attach policy to invoke Lambda
cat > bedrock-agent-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:us-east-1:${AWS_ACCOUNT_ID}:function:bedrock-db-connector"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name bedrock-agent-role \
  --policy-name bedrock-agent-policy \
  --policy-document file://bedrock-agent-policy.json
```

### Step 6: Create Bedrock Agent (AWS Console)

#### 6.1 Navigate to Amazon Bedrock

1. **Open AWS Console** → Search for "Bedrock" → Click **Amazon Bedrock**
2. In the left sidebar, click **Agents** (under Orchestration)
3. Click **Create Agent** button

#### 6.2 Provide Agent Details

1. **Agent name**: `database-query-agent`
2. **Agent description** (optional): `Agent to query employee and project information from PostgreSQL RDS`
3. **User input**: Leave enabled (allows users to provide additional instructions at runtime)
4. Click **Next**

#### 6.3 Select Foundation Model

1. **Model selection**: Choose `Anthropic Claude 3.5 Sonnet v2` (recommended) or `Claude 3 Sonnet`
2. **Agent instructions**: Paste the following:

```
  You are an AI assistant that helps users query an employee database.
  You can retrieve employee information, project details, and department statistics.

  Your capabilities include:
  1. Listing employees, optionally filtered by department or minimum salary
  2. Retrieving a single employee by ID
  3. Listing projects, optionally filtered by status (active, completed, on-hold)
  4. Getting department summary statistics (employee count, avg/min/max salary)
  5. Adding a new employee
  6. Executing custom SQL queries when needed

  When responding:
  - Present data in a clear, structured format
  - If a query returns no results, explain that clearly
  - For employee or project lists, summarize the count and key details
  - If there's an error, explain it in user-friendly terms
  - Be helpful and provide context about the data structure when relevant
  ```

1. Click **Next**

#### 6.4 Add Action Group

1. Click **Add** button in the Action groups section
2. **Action group name**: `DatabaseActions`
3. **Action group description**: `Actions to query database for employees and projects`
4. **Action group type**: Select **Define with API schemas**

5. **Action group invocation**:
   - Select **Select an existing Lambda function**
   - **Lambda function**: Select `bedrock-db-connector` from dropdown
   - **Lambda function version or alias**: Leave as `$LATEST`

6. **Action group schema**:
   - Select **Define via in-line schema editor**
   - Click **In-line OpenAPI schema editor** text area
   - Copy and paste the contents of `bedrock-agent-schema.json` file
   - Alternatively, you can select **Upload from S3** and provide S3 URI if you uploaded the schema there

7. **Action group invocation parameters** (optional):
   - Leave empty unless you need to pass additional context

8. Click **Add** at the bottom

9. You should see "DatabaseActions" added to the action groups list
10. Click **Next**

#### 6.5 Review and Create

1. Review all settings:
   - Agent name: `database-query-agent`
   - Foundation model: Claude 3.5 Sonnet v2
   - Action groups: DatabaseActions (1)
   - Lambda function: bedrock-db-connector

2. Click **Create Agent**

3. Wait for agent creation (takes 30-60 seconds)
   - Status will show "Creating..." then "Agent created successfully"

### Step 7: Grant Lambda Permission to Bedrock

The Lambda function needs permission to be invoked by Bedrock. This requires adding a resource-based policy to the Lambda function.

**⚠️ IMPORTANT**: The Lambda console's UI does not properly support adding these permissions. You MUST use AWS CLI.

#### Option 1: Use the Provided Script (Recommended)

Run the provided script with appropriate AWS credentials:

```bash
./add-lambda-permissions.sh
```

#### Option 2: Manual AWS CLI Commands

```bash
# Add permission for the agent
aws lambda add-permission \
  --function-name bedrock-db-connector \
  --statement-id bedrock-agent-invoke \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com \
  --source-arn "arn:aws:bedrock:us-east-1:123456789012:agent/YOURAGENTID" \
  --region us-east-1

# Add permission for agent aliases (required for testing)
aws lambda add-permission \
  --function-name bedrock-db-connector \
  --statement-id bedrock-agent-alias-invoke \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com \
  --source-arn "arn:aws:bedrock:us-east-1:123456789012:agent-alias/YOURAGENTID/*" \
  --region us-east-1
```

#### Option 3: Request Admin to Add Permissions

If you don't have CLI permissions, send this to your AWS administrator:

**Subject**: Lambda Permission Required for Bedrock Agent Integration

**Message**:

```
Please add the following resource-based policy permissions to Lambda function: bedrock-db-connector

Run these two commands:

1. For Agent:
aws lambda add-permission \
  --function-name bedrock-db-connector \
  --statement-id bedrock-agent-invoke \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com \
  --source-arn "arn:aws:bedrock:us-east-1:123456789012:agent/YOURAGENTID" \
  --region us-east-1

2. For Agent Alias (test and production):
aws lambda add-permission \
  --function-name bedrock-db-connector \
  --statement-id bedrock-agent-alias-invoke \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com \
  --source-arn "arn:aws:bedrock:us-east-1:123456789012:agent-alias/YOURAGENTID/*" \
  --region us-east-1
```

#### Verify Permissions Were Added

After permissions are added, verify by checking the Lambda resource-based policy:

```bash
aws lambda get-policy --function-name bedrock-db-connector --region us-east-1
```

**Expected Policy JSON** (for reference only - this is what the CLI creates):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "bedrock-agent-invoke",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:bedrock-db-connector",
      "Condition": {
        "ArnLike": {
          "AWS:SourceArn": "arn:aws:bedrock:us-east-1:123456789012:agent/YOURAGENTID"
        }
      }
    },
    {
      "Sid": "bedrock-agent-alias-invoke",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:bedrock-db-connector",
      "Condition": {
        "ArnLike": {
          "AWS:SourceArn": "arn:aws:bedrock:us-east-1:123456789012:agent-alias/YOURAGENTID/*"
        }
      }
    }
  ]
}
```

### Step 8: Prepare the Agent

1. In the Bedrock Agent console, click **Prepare** button (top right)
2. Wait for preparation to complete (1-2 minutes)
3. Status will change to "Prepared"

**Note**: You must prepare the agent after any changes to:

- Agent instructions
- Action groups
- Knowledge bases
- Foundation model

### Step 9: Test Your Agent

1. Click **Test** button (next to Prepare)
2. A test chat window will open on the right side

#### Test Query 1: Get employee information

```
Can you get me information about employee with ID 1?
```

Expected response format:

```
Here's the employee information:
- ID: 1
- Name: [employee name]
- Email: [email]
- Department: [department]
- Salary: [salary]
- Hire Date: [hire date]
```

#### Test Query 2: List projects by status

```
Show me all active projects
```

Expected response format:

```
I found X active projects:
1. Project Name: [name]
   - Description: [description]
   - Budget: [budget]
   - Start Date: [start date]
...
```

#### Test Query 3: Natural language

```
What is the average salary by department, and which employees are in Engineering?
```

The agent should:

1. Call `/departments/summary` for the department statistics
2. Call `/employees` with department=Engineering
3. Synthesize the results into a comprehensive response

4. **Review Trace** (optional):
   - Click **Show trace** toggle to see:
     - Agent reasoning
     - Action group invocations
     - Lambda responses
     - Final response generation

5. **Check CloudWatch Logs**:
   - Open CloudWatch Console → Log groups → `/aws/lambda/bedrock-db-connector`
   - Verify Lambda invocations and database queries

### Step 10: Create Agent Alias (Production Deployment)

Once testing is successful:

1. In the agent page, click **Aliases** tab (left sidebar)
2. Click **Create alias** button
3. **Alias name**: `production` (or `v1`, `dev`, etc.)
4. **Description**: `Production version of database query agent`
5. **Version**: Select the latest version (usually `DRAFT` or version `1`)
6. **Tags** (optional): Add tags for organization
7. Click **Create alias**

8. Wait for alias creation (30-60 seconds)
9. Note the **Alias ARN** - you'll use this for API/SDK invocations

**Alias ARN format**:

```
arn:aws:bedrock:us-east-1:ACCOUNT_ID:agent-alias/AGENT_ID/ALIAS_ID
```

### Step 11: Invoke Agent via SDK (Optional)

After creating an alias, you can invoke the agent programmatically:

```python
import boto3
import json

# Initialize Bedrock Agent Runtime client
bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

# Invoke the agent
response = bedrock_agent.invoke_agent(
    agentId='YOUR_AGENT_ID',
    agentAliasId='YOUR_ALIAS_ID',
    sessionId='test-session-123',  # Unique session identifier
    inputText='Show me employee with ID 1'
)

# Parse streaming response
for event in response['completion']:
    if 'chunk' in event:
        chunk = event['chunk']
        if 'bytes' in chunk:
            print(chunk['bytes'].decode('utf-8'), end='')
```

## 🔧 Configuration Details

### Database Connection

The Lambda function connects to:

- **Host**: `your-db-instance.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com`
- **Port**: `5432`
- **Database**: `your_db_name`
- **User**: `your_db_user`
- **Password**: `your_db_password`

### Available API Endpoints

1. **GET /employees**
   - Parameters: `department` (string, optional), `min_salary` (number, optional)
   - Returns: List of employees

2. **POST /employees**
   - Body: `name`, `email`, `department`, `salary`, `hire_date`
   - Returns: The newly created employee

3. **GET /employees/{id}**
   - Parameters: `id` (integer, path)
   - Returns: A single employee

4. **GET /projects**
   - Parameters: `status` (string, optional — active/completed/on-hold)
   - Returns: List of projects

5. **GET /departments/summary**
   - Returns: Per-department employee count and salary statistics

6. **POST /executeQuery**
   - Parameters: `query` (string)
   - Returns: Query results

## 🔐 Security Best Practices

### 1. Use AWS Secrets Manager for Database Credentials

```bash
# Store credentials in Secrets Manager
aws secretsmanager create-secret \
  --name bedrock-db-credentials \
  --secret-string '{
    "username":"your_db_user",
    "password":"your_db_password",
    "host":"your-db-instance.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com",
    "port":"5432",
    "database":"your_db_name"
  }' \
  --region us-east-1
```

Update Lambda to retrieve from Secrets Manager:

```python
import boto3
import json

def get_db_credentials():
    client = boto3.client('secretsmanager', region_name='us-east-1')
    secret = client.get_secret_value(SecretId='bedrock-db-credentials')
    return json.loads(secret['SecretString'])
```

### 2. Restrict RDS Security Group

Ensure RDS security group only allows connections from Lambda security group.

### 3. Enable CloudWatch Logs

Monitor Lambda executions:

```bash
aws logs tail /aws/lambda/bedrock-db-connector --follow
```

### 4. Use Parameter Store for Non-Sensitive Config

```bash
aws ssm put-parameter \
  --name /bedrock-agent/db-host \
  --value "your-db-instance.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com" \
  --type String
```

## 📊 Monitoring and Debugging

### View Lambda Logs

```bash
aws logs tail /aws/lambda/bedrock-db-connector --follow --region us-east-1
```

### Check Lambda Metrics

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=bedrock-db-connector \
  --start-time 2025-12-01T00:00:00Z \
  --end-time 2025-12-02T23:59:59Z \
  --period 3600 \
  --statistics Sum \
  --region us-east-1
```

### Test Database Connectivity

```bash
# Update test event
cat > test-employees.json <<EOF
{
  "actionGroup": "DatabaseActions",
  "apiPath": "/employees",
  "httpMethod": "GET",
  "parameters": [
    {
      "name": "department",
      "value": "Engineering"
    }
  ]
}
EOF

aws lambda invoke \
  --function-name bedrock-db-connector \
  --payload file://test-employees.json \
  response.json && cat response.json | jq
```

## 🐛 Troubleshooting

### Issue: Lambda Cannot Connect to RDS

**Solution**:

1. Check VPC configuration
2. Verify security groups
3. Ensure RDS is publicly accessible OR Lambda is in same VPC
4. Check database credentials

### Issue: Bedrock Agent Cannot Invoke Lambda

**Solution**:

1. Verify Lambda resource policy allows Bedrock
2. Check IAM role for Bedrock Agent
3. Ensure Action Group is properly configured

### Issue: Timeout Errors

**Solution**:

1. Increase Lambda timeout (up to 15 minutes)
2. Optimize database queries
3. Add connection pooling

### Issue: Import Errors in Lambda

See [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) — this is a real, recurring `psycopg2` platform-mismatch issue hit during original development, with a step-by-step fix.

## 🔄 Updating the Lambda Function

After making changes to `lambda_function.py`:

```bash
./deploy.sh
```

`deploy.sh` is the source of truth for the exact package-build command — see it directly rather than re-typing it here, since it pins the platform/Python version flags that avoid the `psycopg2` import failure described in [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md).

## 📚 Additional Resources

- [AWS Bedrock Agents Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Lambda with VPC](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html)
- [RDS Security Groups](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.RDSSecurityGroups.html)

## 💡 Next Steps

1. Add more API endpoints as needed
2. Implement error handling and retries
3. Add connection pooling for better performance
4. Set up CloudWatch alarms for monitoring
5. Create integration tests
6. Document API usage for team members
7. Consider using AWS Lambda Layers for dependencies

## 📞 Support

For issues or questions, check:

- Lambda CloudWatch logs
- Bedrock Agent test console
- RDS connection logs
