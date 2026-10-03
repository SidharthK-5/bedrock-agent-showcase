# Step-by-Step Guide: Bedrock Agent with Local Docker Database

## Overview

This guide walks you through creating an Amazon Bedrock Agent that connects to a PostgreSQL database running in a local Docker container.

## The Challenge

Bedrock Agents run in AWS and can only access publicly accessible HTTPS endpoints. Your local database in Docker is not directly accessible from AWS.

## The Solution

We'll create a **Lambda function** that acts as a proxy between the Bedrock Agent and your local database:

1. **Local Docker DB** ← Connected to → **Lambda Function** ← Connected to → **Bedrock Agent**
2. Lambda connects to your database (using tunnel or VPN)
3. API Gateway exposes Lambda with HTTPS
4. Bedrock Agent calls API Gateway

---

## Prerequisites

Before starting, ensure you have:

- ✅ Docker Desktop installed and running
- ✅ AWS Account with Bedrock access enabled
- ✅ AWS CLI installed and configured (`aws configure`)
- ✅ Python 3.11+ installed
- ✅ Basic understanding of SQL and AWS

---

## Step 1: Start the Local Database

### 1.1 Start PostgreSQL in Docker

```bash
cd ~/02-postgres-db-agent/docker-local

# Start the database
docker-compose up -d

# Expected output:
# Creating network "bedrock-agent-local-db_default" with the default driver
# Creating volume "bedrock-agent-local-db_postgres_data" with default driver
# Creating local-postgres-db ... done
```

### 1.2 Verify Database is Running

```bash
# Check container status
docker ps | grep postgres

# You should see:
# local-postgres-db   postgres:15-alpine   Up X seconds   0.0.0.0:5432->5432/tcp

# Test database connection
docker exec -it local-postgres-db psql -U dbuser -d bedrockdb -c "SELECT COUNT(*) FROM employees;"

# Expected output:
#  count 
# -------
#      5
```

### 1.3 Explore Sample Data

```bash
# View all employees
docker exec -it local-postgres-db psql -U dbuser -d bedrockdb -c "SELECT * FROM employees;"

# View all projects
docker exec -it local-postgres-db psql -U dbuser -d bedrockdb -c "SELECT * FROM projects;"
```

---

## Step 2: Set Up Network Access (Critical!)

Since your database is local, AWS Lambda needs a way to reach it. Choose ONE option:

### Option A: Use Localtunnel (Easiest for Testing)

```bash
# Install localtunnel globally
npm install -g localtunnel

# Create a tunnel (keep this running in a separate terminal)
lt --port 5432 --subdomain bedrock-db-tunnel

# Output will show:
# your url is: https://bedrock-db-tunnel.loca.lt
```

**Important**: Keep this terminal open! The tunnel needs to stay active.

**Note the URL** - you'll need it in Step 4.

### Option B: Deploy Database to AWS (Recommended for Production)

Skip local setup and create an RDS instance:

```bash
aws rds create-db-instance \
  --db-instance-identifier bedrock-agent-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username admin \
  --master-user-password YourSecurePassword123 \
  --allocated-storage 20 \
  --publicly-accessible

# Get endpoint (wait 5-10 minutes for creation)
aws rds describe-db-instances \
  --db-instance-identifier bedrock-agent-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

Then import your schema:

```bash
# Connect to RDS
psql -h YOUR-RDS-ENDPOINT -U admin -d postgres -f init.sql
```

---

## Step 3: Configure AWS Environment

### 3.1 Set Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your values
nano .env
```

Edit `.env`:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012  # Replace with your AWS account ID

# Database Configuration
DB_HOST=bedrock-db-tunnel.loca.lt  # Your tunnel URL (without https://)
DB_PORT=5432
DB_NAME=bedrockdb
DB_USER=dbuser
DB_PASSWORD=dbpassword123
```

**Get your AWS Account ID:**

```bash
aws sts get-caller-identity --query Account --output text
```

### 3.2 Load Environment Variables

```bash
export $(cat .env | xargs)

# Verify
echo $AWS_ACCOUNT_ID
echo $DB_HOST
```

---

## Step 4: Test Lambda Function Locally (Optional but Recommended)

Before deploying to AWS, test the Lambda function locally:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install boto3

# Test Lambda function
python test_agent.py local
```

**Expected Output:**

```json
{
  "messageVersion": "1.0",
  "response": {
    "httpStatusCode": 200,
    "responseBody": {
      "application/json": {
        "body": "{\"employees\": [{...}], \"count\": 2}"
      }
    }
  }
}
```

If you see errors, check:

- Database is running (`docker ps`)
- Environment variables are set
- Database credentials are correct

---

## Step 5: Deploy to AWS

### 5.1 Package Lambda Function

```bash
# Make script executable
chmod +x package_lambda.sh

# Create deployment package
./package_lambda.sh
```

This creates `lambda-deployment.zip` with all dependencies.

### 5.2 Deploy Infrastructure

```bash
# Deploy everything (Lambda, API Gateway, Bedrock Agent)
python setup_infrastructure.py
```

**This script will:**

1. ✅ Create IAM role for Lambda
2. ✅ Deploy Lambda function
3. ✅ Create API Gateway
4. ✅ Create IAM role for Bedrock Agent
5. ✅ Create Bedrock Agent with action group

**Expected Output:**

```plain text
====================================================
Setup Complete!
====================================================
Agent ID: ABCDEFGHIJ
API URL: https://xyz123.execute-api.us-east-1.amazonaws.com/prod
Lambda Function: arn:aws:lambda:us-east-1:123456789012:function:bedrock-agent-db-proxy
```

**⚠️ Save the Agent ID!** You'll need it for testing.

---

## Step 6: Update Lambda Configuration

If using a tunnel, update Lambda environment variables with your tunnel URL:

```bash
aws lambda update-function-configuration \
  --function-name bedrock-agent-db-proxy \
  --environment Variables="{
    DB_HOST=bedrock-db-tunnel.loca.lt,
    DB_PORT=5432,
    DB_NAME=bedrockdb,
    DB_USER=dbuser,
    DB_PASSWORD=dbpassword123
  }"
```

**Wait 30 seconds** for the update to propagate.

---

## Step 7: Test Your Bedrock Agent

### 7.1 Set Agent ID

```bash
export BEDROCK_AGENT_ID=ABCDEFGHIJ  # Replace with your agent ID from Step 5
```

### 7.2 Test with AWS Console

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Navigate to **Agents** in the left sidebar
3. Click on **employee-database-agent**
4. Click **Test** button in the top right
5. Try these queries:

**Query 1:**

```txt
List all employees in the Engineering department
```

**Query 2:**

```txt
What is the average salary by department?
```

**Query 3:**

```txt
Show me all active projects
```

### 7.3 Test with Python Script

```bash
# Test with a specific query
python test_agent.py agent "How many employees work in each department?"

# Run all test queries
python test_agent.py agent
```

---

## Step 8: Monitor and Debug

### 8.1 View Lambda Logs

```bash
# Stream Lambda logs in real-time
aws logs tail /aws/lambda/bedrock-agent-db-proxy --follow

# View recent errors
aws logs filter-events \
  --log-group-name /aws/lambda/bedrock-agent-db-proxy \
  --filter-pattern "ERROR"
```

### 8.2 Test Lambda Directly

Create a test event file:

```bash
cat > test-event.json << 'EOF'
{
  "messageVersion": "1.0",
  "agent": {
    "name": "employee-database-agent",
    "id": "test",
    "alias": "test",
    "version": "1"
  },
  "inputText": "Get all employees",
  "sessionId": "test-session",
  "actionGroup": "database-actions",
  "apiPath": "/employees",
  "httpMethod": "GET",
  "parameters": [],
  "requestBody": {}
}
EOF

# Invoke Lambda
aws lambda invoke \
  --function-name bedrock-agent-db-proxy \
  --payload file://test-event.json \
  response.json

# View response
cat response.json | python -m json.tool
```

### 8.3 Check Database Connectivity from Lambda

View CloudWatch logs to see if Lambda can connect to your database:

```bash
aws logs tail /aws/lambda/bedrock-agent-db-proxy --follow
```

Look for connection errors or successful queries.

---

## Troubleshooting

### Issue 1: Lambda Can't Connect to Database

**Symptom:** Timeout errors or connection refused

**Solutions:**

```bash
# 1. Verify tunnel is running
lt --port 5432 --subdomain bedrock-db-tunnel

# 2. Test connection from your machine
nc -zv bedrock-db-tunnel.loca.lt 5432

# 3. Check Lambda environment variables
aws lambda get-function-configuration \
  --function-name bedrock-agent-db-proxy \
  --query 'Environment.Variables'

# 4. Update if needed
aws lambda update-function-configuration \
  --function-name bedrock-agent-db-proxy \
  --environment Variables="{
    DB_HOST=your-new-tunnel.loca.lt,
    DB_PORT=5432,
    DB_NAME=bedrockdb,
    DB_USER=dbuser,
    DB_PASSWORD=dbpassword123
  }"
```

### Issue 2: Bedrock Agent Not Responding

**Symptom:** Agent doesn't answer or gives generic responses

**Solutions:**

```bash
# 1. Check agent status
aws bedrock-agent get-agent --agent-id YOUR_AGENT_ID

# 2. Prepare agent (if status is DRAFT)
aws bedrock-agent prepare-agent --agent-id YOUR_AGENT_ID

# 3. Wait 1-2 minutes and try again
```

### Issue 3: Permission Errors

**Symptom:** Lambda can't be invoked or Agent can't call Lambda

**Solutions:**

```bash
# Grant API Gateway permission to invoke Lambda
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
API_ID=YOUR_API_GATEWAY_ID  # From setup output

aws lambda add-permission \
  --function-name bedrock-agent-db-proxy \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*/*"
```

### Issue 4: Database Container Not Running

```bash
# Check if container is running
docker ps | grep postgres

# If not running, start it
docker-compose up -d

# Check logs for errors
docker logs local-postgres-db

# Restart if needed
docker-compose restart
```

---

## What You Can Ask the Agent

### Employee Queries

- "List all employees"
- "Show me employees in the Engineering department"
- "Find employees with salary over $80,000"
- "Get details for employee ID 3"
- "How many employees work here?"

### Project Queries

- "Show all active projects"
- "What projects have been completed?"
- "List projects with budget over $100,000"

### Analytics Queries

- "What is the average salary by department?"
- "Show me department statistics"
- "Which department has the most employees?"

### Data Modification

- "Add a new employee: Sarah Johnson, [sarah.j@example.com](mailto:sarah.j@example.com), Marketing, $78000, 2024-12-01"

---

## Next Steps

### 1. Secure Your Credentials

Use AWS Secrets Manager instead of environment variables:

```bash
# Store database credentials
aws secretsmanager create-secret \
  --name bedrock/database/credentials \
  --secret-string '{
    "host":"bedrock-db-tunnel.loca.lt",
    "port":"5432",
    "database":"bedrockdb",
    "username":"dbuser",
    "password":"dbpassword123"
  }'

# Grant Lambda access
aws iam attach-role-policy \
  --role-name bedrock-agent-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```

Update `lambda_function.py` to read from Secrets Manager.

### 2. Add Authentication to API Gateway

```bash
# Create API key
aws apigateway create-api-key \
  --name bedrock-agent-key \
  --enabled

# Create usage plan and associate with API
```

### 3. Move to Production Database

Deploy to RDS for production:

- High availability
- Automated backups
- Better security
- No tunnel required

### 4. Add More Capabilities

Extend the agent with:

- UPDATE and DELETE operations
- Complex joins and aggregations
- Report generation
- Data exports

---

## Clean Up (Optional)

To remove all AWS resources:

```bash
# Delete Bedrock Agent
aws bedrock-agent delete-agent --agent-id YOUR_AGENT_ID

# Delete Lambda function
aws lambda delete-function --function-name bedrock-agent-db-proxy

# Delete API Gateway (get API ID first)
aws apigateway delete-rest-api --rest-api-id YOUR_API_ID

# Delete IAM roles
aws iam delete-role --role-name bedrock-agent-lambda-role
aws iam delete-role --role-name bedrock-agent-role

# Stop local database
docker-compose down -v  # -v removes volumes
```

---

## Summary

You've successfully created:

✅ Local PostgreSQL database in Docker  
✅ Lambda function as database proxy  
✅ API Gateway with HTTPS endpoint  
✅ Bedrock Agent with natural language interface  
✅ Complete testing setup  

Your Bedrock Agent can now query your local database using natural language!

---

## Support Resources

- [AWS Bedrock Docs](https://docs.aws.amazon.com/bedrock/)
- [Lambda with Databases](https://docs.aws.amazon.com/lambda/latest/dg/services-rds.html)
- [Localtunnel](https://theboroer.github.io/localtunnel-www/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

For issues, check CloudWatch logs and verify each component is working individually before testing the full integration.
