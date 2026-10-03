@echo off
REM Script to create Lambda deployment package for Windows
REM This script packages the Python code and dependencies into a ZIP file for AWS Lambda

echo Starting Lambda deployment package creation...

REM Clean up previous builds
echo Cleaning up previous builds...
if exist package rmdir /s /q package
if exist lambda_deployment.zip del lambda_deployment.zip

REM Create package directory
echo Creating package directory...
mkdir package

REM Install dependencies to package directory
echo Installing Python dependencies...
pip install -r requirements.txt -t package/

REM Copy Lambda function code to package directory
echo Copying Lambda function code...
copy main.py package\
copy db_connector.py package\
copy query_router.py package\

REM Create ZIP file
echo Creating deployment ZIP file...
cd package
powershell Compress-Archive -Path * -DestinationPath ..\lambda_deployment.zip -Force
cd ..

echo Deployment package created successfully!
echo File: lambda_deployment.zip
echo.
echo You can now upload this file to AWS Lambda.
echo Note: If the file is larger than 50MB, you'll need to upload it via S3.
pause
