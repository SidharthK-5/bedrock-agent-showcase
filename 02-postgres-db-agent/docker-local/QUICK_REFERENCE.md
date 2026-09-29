# Quick Reference Card - Bedrock Agent Local DB

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Start database
docker-compose up -d

# 2. Run setup
./quickstart.sh

# 3. Set up tunnel (separate terminal)
npm install -g localtunnel
lt --port 5432 --subdomain your-name

# 4. Update .env with tunnel URL
# DB_HOST=your-name.loca.lt

# 5. Deploy to AWS
python setup_infrastructure.py

# 6. Test
python test_agent.py agent "Show me all employees"
```

## 📁 Project Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | PostgreSQL Docker configuration |
| `init.sql` | Database schema & sample data |
| `lambda_function.py` | Lambda proxy for DB access |
| `api-schema.yaml` | OpenAPI spec for Bedrock Agent |
| `setup_infrastructure.py` | AWS deployment script |
| `test_agent.py` | Testing utilities |
| `main.py` | Main entry point with CLI |
| `quickstart.sh` | Automated setup script |
| `package_lambda.sh` | Lambda deployment packager |
| `.env` | Configuration (create from .env.example) |

## 📚 Documentation

| Document | When to Read |
| -------- | ------------ |
| `README.md` | Overview & quick reference |
| `STEP_BY_STEP_GUIDE.md` | **START HERE** - Detailed walkthrough |
| `AWS_SETUP.md` | AWS account configuration |
| `ARCHITECTURE.md` | System design & diagrams |

## 🔧 Common Commands

### Database Operations

```bash
# Start database
docker-compose up -d

# Stop database
docker-compose down

# View logs
docker logs local-postgres-db

# Connect to database
docker exec -it local-postgres-db psql -U dbuser -d bedrockdb

# Run SQL query
docker exec -it local-postgres-db psql -U dbuser -d bedrockdb -c "SELECT * FROM employees;"

# Reset database (WARNING: deletes data)
docker-compose down -v
docker-compose up -d
```

### Testing

```bash
# Test Lambda locally
python test_agent.py local

# Test Bedrock Agent with query
python test_agent.py agent "Your question here"

# Run all test queries
python test_agent.py agent

# Test with main.py
python main.py --test
```

### AWS Deployment

```bash
# Package Lambda
./package_lambda.sh

# Deploy everything
python setup_infrastructure.py

# Or use main.py
python main.py --deploy

# Update Lambda code
aws lambda update-function-code \
  --function-name bedrock-agent-db-proxy \
  --zip-file fileb://lambda-deployment.zip

# Update Lambda environment
aws lambda update-function-configuration \
  --function-name bedrock-agent-db-proxy \
  --environment Variables="{DB_HOST=new-host.com,DB_PORT=5432,...}"
```

### Monitoring

```bash
# View Lambda logs
aws logs tail /aws/lambda/bedrock-agent-db-proxy --follow

# View recent errors
aws logs filter-events \
  --log-group-name /aws/lambda/bedrock-agent-db-proxy \
  --filter-pattern "ERROR"

# Get agent info
aws bedrock-agent get-agent --agent-id YOUR_AGENT_ID

# Test Lambda directly
aws lambda invoke \
  --function-name bedrock-agent-db-proxy \
  --payload file://test-event.json \
  response.json
```

## 🌐 Network Setup Options

### Option 1: Localtunnel (Dev/Testing)

```bash
# Install
npm install -g localtunnel

# Create tunnel
lt --port 5432 --subdomain your-unique-name

# Update .env
DB_HOST=your-unique-name.loca.lt
```

### Option 2: AWS RDS (Production)

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier bedrock-agent-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password YourPassword123 \
  --allocated-storage 20

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier bedrock-agent-db \
  --query 'DBInstances[0].Endpoint.Address'

# Import schema
psql -h RDS-ENDPOINT -U admin -d postgres -f init.sql
```

## 💬 Example Queries for Your Agent

### Employee Queries

```
- "List all employees"
- "Show employees in Engineering"
- "Who works in the Sales department?"
- "Find employees making over $80,000"
- "Get employee with ID 3"
```

### Project Queries

```
- "Show all active projects"
- "What projects are completed?"
- "Projects with budget over $100k"
```

### Analytics

```
- "What's the average salary by department?"
- "Show me department statistics"
- "How many people in each department?"
```

### Data Modification

```
- "Add employee: John Smith, john@example.com, Marketing, 70000, 2024-01-15"
```

## 🐛 Troubleshooting Quick Fixes

### Can't connect to database

```bash
# Check container
docker ps | grep postgres

# Restart if needed
docker-compose restart

# Check tunnel
lt --port 5432 --subdomain your-name
```

### Lambda timeout

```bash
# Increase timeout
aws lambda update-function-configuration \
  --function-name bedrock-agent-db-proxy \
  --timeout 60
```

### Permission errors

```bash
# Check AWS credentials
aws sts get-caller-identity

# Reconfigure if needed
aws configure
```

### Bedrock Agent not responding

```bash
# Prepare agent
aws bedrock-agent prepare-agent --agent-id YOUR_AGENT_ID

# Check agent status
aws bedrock-agent get-agent --agent-id YOUR_AGENT_ID
```

## ⚙️ Environment Variables

Required in `.env`:

```bash
# AWS
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Database
DB_HOST=localhost  # or tunnel URL
DB_PORT=5432
DB_NAME=bedrockdb
DB_USER=dbuser
DB_PASSWORD=dbpassword123
```

Get AWS Account ID:

```bash
aws sts get-caller-identity --query Account --output text
```

## 🔐 Security Checklist

- [ ] Never commit `.env` to Git
- [ ] Use AWS Secrets Manager for production
- [ ] Enable CloudWatch logging
- [ ] Set up billing alerts
- [ ] Use least-privilege IAM policies
- [ ] Rotate credentials regularly
- [ ] Enable VPC for Lambda (production)
- [ ] Add API Gateway authentication

## 💰 Cost Estimate

**Development (with local DB):**

- Bedrock: ~$2-5/month
- Lambda: Free tier
- API Gateway: Free tier
- **Total: $2-5/month**

**Production (with RDS):**

- Bedrock: $10-50/month
- Lambda: $1-5/month
- RDS: $15-30/month
- Data Transfer: $1-5/month
- **Total: $30-90/month**

## 🆘 Get Help

### Check Logs

```bash
# Lambda
aws logs tail /aws/lambda/bedrock-agent-db-proxy --follow

# Database
docker logs local-postgres-db

# Test connectivity
docker exec -it local-postgres-db psql -U dbuser -d bedrockdb -c "SELECT 1;"
```

### Useful Links

- [Bedrock Docs](https://docs.aws.amazon.com/bedrock/)
- [Lambda Docs](https://docs.aws.amazon.com/lambda/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

### Common Issues

1. **"Can't connect to DB"** → Check tunnel is running
2. **"Permission denied"** → Check IAM roles and policies
3. **"Agent not responding"** → Run `prepare-agent` command
4. **"Module not found"** → Run `pip install -r requirements.txt`

## 🧹 Clean Up

```bash
# Remove AWS resources
aws bedrock-agent delete-agent --agent-id YOUR_AGENT_ID
aws lambda delete-function --function-name bedrock-agent-db-proxy
aws apigateway delete-rest-api --rest-api-id YOUR_API_ID

# Remove local resources
docker-compose down -v

# Remove Python packages
deactivate
rm -rf .venv
```

## 📊 Success Checklist

- [ ] Database running in Docker
- [ ] Sample data loaded
- [ ] Python dependencies installed
- [ ] Lambda function tested locally
- [ ] Tunnel/RDS configured
- [ ] AWS credentials configured
- [ ] Infrastructure deployed
- [ ] Bedrock Agent created
- [ ] Test query successful

---

**Ready to start?** → Run `./quickstart.sh` or see `STEP_BY_STEP_GUIDE.md`
