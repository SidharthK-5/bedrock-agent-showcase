#!/bin/bash

# Script to package Lambda function with dependencies for deployment

echo "Creating Lambda deployment package..."

# Create a directory for the package
rm -rf package
mkdir -p package

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t package/

# Copy Lambda function
cp lambda_function.py package/

# Create zip file
cd package
zip -r ../lambda-deployment.zip .
cd ..

echo "✓ Deployment package created: lambda-deployment.zip"
echo "Upload this to your Lambda function or use AWS CLI:"
echo "aws lambda update-function-code --function-name bedrock-agent-db-proxy --zip-file fileb://lambda-deployment.zip"
