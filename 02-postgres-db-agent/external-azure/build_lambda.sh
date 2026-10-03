#!/bin/bash

# Script to create Lambda deployment package
# This script packages the Python code and dependencies into a ZIP file for AWS Lambda

set -e

echo "Starting Lambda deployment package creation..."

# Clean up previous builds
echo "Cleaning up previous builds..."
rm -rf package
rm -f lambda_deployment.zip

# Create package directory
echo "Creating package directory..."
mkdir -p package

# Install dependencies to package directory
echo "Installing Python dependencies..."
pip install -r requirements.txt -t package/

# Copy Lambda function code to package directory
echo "Copying Lambda function code..."
cp main.py package/
cp db_connector.py package/
cp query_router.py package/

# Create ZIP file
echo "Creating deployment ZIP file..."
cd package
zip -r ../lambda_deployment.zip . -x "*.pyc" -x "*__pycache__*" -x "*.dist-info*"
cd ..

# Get the size of the ZIP file
ZIP_SIZE=$(du -h lambda_deployment.zip | cut -f1)
echo "Deployment package created successfully!"
echo "File: lambda_deployment.zip"
echo "Size: $ZIP_SIZE"
echo ""
echo "You can now upload this file to AWS Lambda."
echo "Note: If the file is larger than 50MB, you'll need to upload it via S3."
