# Amazon Bedrock Agent with Local Database Connection

This project demonstrates how to create an Amazon Bedrock Agent that connects to a local PostgreSQL database running in Docker.

## Architecture

```
User Query → Bedrock Agent → Lambda Function → Local PostgreSQL (Docker)
                ↑                    ↓
            API Gateway     Database Queries
```

**Key Components:**

- **Local PostgreSQL Database**: Running in Docker container
- **Lambda Function**: Acts as a proxy between Bedrock Agent and local DB
- **API Gateway**: Provides HTTPS endpoint for Bedrock Agent
- **Bedrock Agent**: Natural language interface for database queries

## Prerequisites

- Docker and Docker Compose installed
- AWS Account with Bedrock access
- AWS CLI configured with appropriate credentials
- Python 3.11+
- Your local machine accessible from AWS (see options below)

## Important: Network Connectivity Options

Since your database is running locally, Bedrock Agent (running in AWS) needs to reach it. Here are your options:

### Option 1: Use Localtunnel (Free, Easy for Testing)

```bash
# Install localtunnel
npm install -g localtunnel

# After starting your DB, create a tunnel (in a separate terminal)
lt --port 5432 --subdomain your-unique-name
```
This gives you a public URL like `https://your-unique-name.loca.lt`

### Option 2: Deploy Lambda in VPN with Site-to-Site Connection

Set up AWS Site-to-Site VPN or AWS Direct Connect (production solution)

### Option 3: Recommended - Deploy DB to AWS

- **Amazon RDS**: Managed PostgreSQL
- **EC2 Instance**: Self-managed database
- **ECS/Fargate**: Containerized database

### Option 4: Development Workaround

Use AWS Lambda with a custom runtime that includes a VPN client to connect back to your local network (complex setup).

## Quick Start

### 1. Start Local Database

```bash
# Start PostgreSQL in Docker
docker-compose up -d

# Verify it's running
docker ps

# Check database is accessible
docker exec -it local-postgres-db psql -U dbuser -d bedrockdb -c "SELECT * FROM employees;"
```

### 2. Set Up Python Environment

```bash
# Activate your virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional AWS dependencies
pip install boto3
```

### 3. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values
nano .env
```

Required variables:

```plain text
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id
DB_HOST=localhost  # or your tunnel URL
DB_PORT=5432
DB_NAME=bedrockdb
DB_USER=dbuser
DB_PASSWORD=dbpassword123
```

### 4. Test Lambda Function Locally

```bash
# Load environment variables
export $(cat .env | xargs)

# Test the Lambda function
python test_agent.py local
```

### 5. Deploy to AWS

```bash
# Package Lambda function with dependencies
chmod +x package_lambda.sh
./package_lambda.sh

# Deploy infrastructure
python setup_infrastructure.py
```

This will create:

- IAM roles for Lambda and Bedrock Agent
- Lambda function with database connection
- API Gateway REST API
- Bedrock Agent with action group

### 6. Configure Lambda for External DB Access

If using a tunnel service, update Lambda environment variables:

```bash
aws lambda update-function-configuration \
  --function-name bedrock-agent-db-proxy \
  --environment Variables="{
    DB_HOST=your-tunnel-url.loca.lt,
    DB_PORT=5432,
    DB_NAME=bedrockdb,
    DB_USER=dbuser,
    DB_PASSWORD=dbpassword123
  }"
```

### 7. Test Bedrock Agent

```bash
# Set agent ID from setup output
export BEDROCK_AGENT_ID=your-agent-id

# Test with a query
python test_agent.py agent "Show me all employees in Engineering"

# Run all test queries
python test_agent.py agent
```

## Database Schema

The sample database includes two tables:

### Employees Table

- `id`: Unique identifier
- `name`: Employee full name
- `email`: Email address
- `department`: Department name
- `salary`: Annual salary
- `hire_date`: Date of hire

### Projects Table

- `id`: Unique identifier
- `name`: Project name
- `description`: Project description
- `budget`: Project budget
- `start_date`: Start date
- `end_date`: End date
- `status`: Project status (active, completed, on-hold)

## Available Queries

The Bedrock Agent can answer questions like:

- "List all employees in the Engineering department"
- "What is the average salary by department?"
- "Show me all active projects"
- "Get details for employee with ID 1"
- "How many employees work in each department?"
- "What projects have a budget over $100,000?"
- "Add a new employee: John Smith, john.smith@example.com, Sales, $75000, 2024-01-15"

## API Schema

The agent uses an OpenAPI schema (`api-schema.yaml`) that defines:

- `GET /employees` - List employees with filters
- `GET /employees/{id}` - Get employee by ID
- `POST /employees` - Add new employee
- `GET /projects` - List projects with status filter
- `GET /departments/summary` - Get department statistics

## Troubleshooting

### Database Connection Issues

```bash
# Check if Docker container is running
docker ps | grep postgres

# Check database logs
docker logs local-postgres-db

# Test direct connection
docker exec -it local-postgres-db psql -U dbuser -d bedrockdb
```

### Lambda Function Issues

```bash
# View Lambda logs
aws logs tail /aws/lambda/bedrock-agent-db-proxy --follow

# Test Lambda directly
aws lambda invoke \
  --function-name bedrock-agent-db-proxy \
  --payload file://test-event.json \
  response.json

cat response.json
```

### Bedrock Agent Issues

```bash
# Check agent status
aws bedrock-agent get-agent --agent-id YOUR_AGENT_ID

# View agent logs in CloudWatch
aws logs tail /aws/bedrock/agents/YOUR_AGENT_ID --follow
```

## Security Considerations

⚠️ **Important Security Notes:**

1. **Database Credentials**: Store in AWS Secrets Manager, not environment variables
2. **Network Access**: Use VPC and Security Groups properly
3. **API Gateway**: Add authentication (IAM, API Keys, Cognito)
4. **Lambda Function**: Enable VPC for production
5. **Database**: Never expose PostgreSQL directly to internet

### Recommended Production Setup

```python
# Use Secrets Manager for database credentials
import boto3
import json

secrets_client = boto3.client('secretsmanager')
secret = secrets_client.get_secret_value(SecretId='prod/bedrock/db')
db_config = json.loads(secret['SecretString'])
```

## Cost Estimates

- **Lambda**: Free tier includes 1M requests/month
- **API Gateway**: Free tier includes 1M requests/month
- **Bedrock Agent**: Pay per request (varies by model)
- **RDS (if used)**: ~$20-100/month for small instances
- **Tunnel Services**: Free for development, $5-20/month for production

## Alternative: Using RDS Instead of Local DB

To use Amazon RDS PostgreSQL:

1. Create RDS instance:

```bash
aws rds create-db-instance \
  --db-instance-identifier bedrock-agent-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password YourPassword123 \
  --allocated-storage 20
```

2. Get RDS endpoint:

  ```bash
  aws rds describe-db-instances \
    --db-instance-identifier bedrock-agent-db \
    --query 'DBInstances[0].Endpoint.Address'
  ```

3. Update Lambda environment variables with RDS endpoint

## Files in This Project

- `docker-compose.yml` - Docker configuration for PostgreSQL
- `init.sql` - Database schema and sample data
- `lambda_function.py` - Lambda function for database proxy
- `api-schema.yaml` - OpenAPI schema for Bedrock Agent
- `setup_infrastructure.py` - AWS infrastructure deployment script
- `test_agent.py` - Testing utilities
- `package_lambda.sh` - Lambda deployment package builder
- `requirements.txt` - Python dependencies

## Next Steps

1. **Add Authentication**: Implement API Gateway authentication
2. **Use Secrets Manager**: Store database credentials securely
3. **Add Monitoring**: Set up CloudWatch dashboards and alarms
4. **Implement Caching**: Use ElastiCache for frequently accessed data
5. **Add More Actions**: Extend the agent with UPDATE and DELETE operations
6. **Deploy to Production**: Move database to RDS or EC2

## Resources

- [Amazon Bedrock Agents Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [AWS Lambda with RDS](https://docs.aws.amazon.com/lambda/latest/dg/services-rds.html)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:

1. Check CloudWatch logs for errors
2. Verify database connectivity
3. Ensure IAM roles have correct permissions
4. Review API Gateway and Lambda configurations
