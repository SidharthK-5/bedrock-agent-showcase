# AWS Configuration Checklist

Before deploying to AWS, ensure you have the following configured:

## 1. AWS CLI Configuration

```bash
# Check if AWS CLI is installed
aws --version

# If not installed:
# macOS: brew install awscli
# Linux: sudo apt-get install awscli
# Windows: Download from https://aws.amazon.com/cli/

# Configure AWS CLI
aws configure

# You'll be prompted for:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region name (e.g., us-east-1)
# - Default output format (json)
```

## 2. Get Your AWS Account ID

```bash
aws sts get-caller-identity --query Account --output text
```

Copy this value to your `.env` file as `AWS_ACCOUNT_ID`.

## 3. Enable Amazon Bedrock

1. Log in to [AWS Console](https://console.aws.amazon.com/)
2. Navigate to Amazon Bedrock service
3. Go to "Model access" in the left sidebar
4. Click "Manage model access"
5. Enable access to **Claude 3 Sonnet** (required for the agent)
6. Submit the request (usually approved instantly)

## 4. Verify IAM Permissions

Your AWS user/role needs these permissions:

### Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:*",
        "lambda:*",
        "apigateway:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PutRolePolicy",
        "iam:GetRole",
        "iam:PassRole",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### Check Your Permissions

```bash
# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Test Lambda access
aws lambda list-functions --region us-east-1

# Test IAM access
aws iam get-user
```

## 5. Choose Your AWS Region

Bedrock is available in these regions:

- `us-east-1` (N. Virginia) - Recommended
- `us-west-2` (Oregon)
- `eu-central-1` (Frankfurt)
- `ap-southeast-1` (Singapore)
- `ap-northeast-1` (Tokyo)

Update `AWS_REGION` in your `.env` file.

## 6. Set Up Database Access Method

### Option A: Using Localtunnel (Development)

```bash
# Install localtunnel
npm install -g localtunnel

# Start tunnel (keep running)
lt --port 5432 --subdomain bedrock-db-YOUR-NAME

# Update .env with tunnel URL
DB_HOST=bedrock-db-YOUR-NAME.loca.lt
```

### Option B: Using RDS (Production)

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier bedrock-agent-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username admin \
  --master-user-password YOUR_SECURE_PASSWORD \
  --allocated-storage 20 \
  --publicly-accessible \
  --region us-east-1

# Wait 5-10 minutes for creation...

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier bedrock-agent-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text

# Update .env
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_USER=admin
DB_PASSWORD=YOUR_SECURE_PASSWORD
```

## 7. Final .env File

Your `.env` should look like:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Database Configuration
DB_HOST=bedrock-db-tunnel.loca.lt  # or RDS endpoint
DB_PORT=5432
DB_NAME=bedrockdb
DB_USER=dbuser
DB_PASSWORD=dbpassword123
```

## 8. Verify Everything

Run the checklist:

```bash
# 1. AWS credentials
aws sts get-caller-identity

# 2. Bedrock access
aws bedrock list-foundation-models --region us-east-1 | grep claude-3-sonnet

# 3. Database running
docker ps | grep postgres

# 4. Environment variables
cat .env

# 5. Python environment
source .venv/bin/activate
python --version
```

## Ready to Deploy?

Once all checks pass:

```bash
# Start the setup
./quickstart.sh

# Then deploy to AWS
python setup_infrastructure.py
```

## Troubleshooting

### "Unable to locate credentials"

```bash
# Reconfigure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### "Access Denied" for Bedrock

1. Go to AWS Console → Bedrock
2. Click "Model access" in left sidebar
3. Request access to Claude 3 Sonnet
4. Wait for approval (usually instant)

### Can't Create IAM Roles

Your AWS user needs `iam:CreateRole` permission. Contact your AWS administrator.

### Lambda Can't Connect to Database

- Verify tunnel is running: `lt --port 5432`
- Test tunnel URL: `nc -zv your-tunnel.loca.lt 5432`
- Check Security Groups if using RDS
- Verify database is running: `docker ps`

## Cost Estimate

For development/testing (monthly):

- **Bedrock**: $0.003 per 1K input tokens (~$0.50-$2)
- **Lambda**: Free tier (1M requests/month)
- **API Gateway**: Free tier (1M requests/month)
- **RDS (optional)**: $15-30 for t3.micro
- **Localtunnel**: Free

Total: **$0.50-$32/month** depending on usage and RDS choice.

## Security Best Practices

1. **Never commit `.env` file** to Git
2. **Use AWS Secrets Manager** for production credentials
3. **Enable CloudWatch logging** for debugging
4. **Set up billing alerts** to avoid surprise charges
5. **Use least-privilege IAM policies**
6. **Rotate credentials** regularly

## Need Help?

- AWS Support: https://console.aws.amazon.com/support/
- Bedrock Docs: https://docs.aws.amazon.com/bedrock/
- Community: AWS re:Post forum

---

Once everything is configured, proceed with the deployment in `STEP_BY_STEP_GUIDE.md`!
