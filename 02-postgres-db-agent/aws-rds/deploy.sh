#!/bin/bash

# Deployment script for Bedrock Agent Lambda Function
# This script packages the Lambda function with dependencies and deploys it to AWS

set -e  # Exit on error

# Configuration
LAMBDA_FUNCTION_NAME="bedrock-db-connector"
RUNTIME="python3.11"
HANDLER="lambda_function.lambda_handler"
ROLE_NAME="bedrock-lambda-execution-role"
REGION="us-east-1"
MEMORY_SIZE=256
TIMEOUT=30

echo "🚀 Starting Lambda deployment process..."

# Create package directory
echo "📦 Creating package directory..."
rm -rf package
mkdir -p package

# Install dependencies
echo "📥 Installing dependencies..."
# Use pip directly with platform flag for Lambda compatibility
python3.11 -m pip install -r lambda-requirements.txt \
    --target package/ \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --python-version 311 \
    --implementation cp

# Copy Lambda function
echo "📄 Copying Lambda function..."
cp lambda_function.py package/

# Create deployment package
echo "🗜️  Creating deployment package..."
cd package
zip -r ../lambda-deployment.zip . -q
cd ..

echo "✅ Deployment package created: lambda-deployment.zip"

# Check if Lambda function exists
echo "🔍 Checking if Lambda function exists..."
if aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "♻️  Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $LAMBDA_FUNCTION_NAME \
        --zip-file fileb://lambda-deployment.zip \
        --region $REGION
    
    echo "⚙️  Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name $LAMBDA_FUNCTION_NAME \
        --runtime $RUNTIME \
        --handler $HANDLER \
        --timeout $TIMEOUT \
        --memory-size $MEMORY_SIZE \
        --environment "Variables={
            DB_HOST=your-db-instance.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com,
            DB_PORT=5432,
            DB_NAME=your_db_name,
            DB_USER=your_db_user,
            DB_PASSWORD=your_db_password
        }" \
        --region $REGION
else
    echo "⚠️  Lambda function does not exist. Please create it first using AWS Console or provide IAM role ARN."
    echo ""
    echo "To create the function manually, run:"
    echo ""
    echo "aws lambda create-function \\"
    echo "  --function-name $LAMBDA_FUNCTION_NAME \\"
    echo "  --runtime $RUNTIME \\"
    echo "  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/$ROLE_NAME \\"
    echo "  --handler $HANDLER \\"
    echo "  --zip-file fileb://lambda-deployment.zip \\"
    echo "  --timeout $TIMEOUT \\"
    echo "  --memory-size $MEMORY_SIZE \\"
    echo "  --environment 'Variables={DB_HOST=your-db-instance.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com,DB_PORT=5432,DB_NAME=your_db_name,DB_USER=your_db_user,DB_PASSWORD=your_db_password}' \\"
    echo "  --region $REGION"
    echo ""
    exit 1
fi

echo ""
echo "✨ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Test your Lambda function"
echo "2. Create Bedrock Agent using the AWS Console"
echo "3. Configure Action Group with bedrock-agent-schema.json"
