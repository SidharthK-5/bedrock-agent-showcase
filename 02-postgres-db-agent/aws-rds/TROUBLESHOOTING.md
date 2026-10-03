# Troubleshooting: IAM Permissions & psycopg2 Import Errors

Real notes from the original development of this project, describing an actual issue hit when the Lambda function's `psycopg2` import was broken after a code update, and the IAM role attached to the function didn't have permission to update itself via CLI. Kept here (lightly edited to remove account-specific identifiers) because the underlying fix — rebuild the deployment package with `psycopg2-binary` for the correct Lambda runtime platform, then update the function code — is a real, recurring gotcha with Python Lambda + psycopg2.

## Symptom

Lambda function fails to import `psycopg2` after a code update (typically: `Unable to import module 'lambda_function': No module named 'psycopg2._psycopg'` or similar), usually because the package was installed for the wrong platform/architecture, or the deployment zip was missing binary dependencies.

## Fix

1. Navigate to the Lambda function (`bedrock-db-connector` in the original deployment) in the AWS Lambda console.

2. Scroll down to the **Code** tab and select **Upload from** > **.zip file**.

3. Create a deployment package locally:
   - Create a new directory for your project.
   - Install the `psycopg2` package and its dependencies:
  
     ```bash
      pip install psycopg2-binary -t .
     ```

   - Add your Lambda function code to this directory.
   - Zip the contents of the directory (not the directory itself).

4. Upload the zip file you created in step 3.

5. After the upload is complete, click **Save** to update the function code.

6. In the **Configuration** tab, select **General configuration** and increase the timeout to at least 10 seconds to allow for potential slow database connections.

7. If the function is part of a VPC, ensure it has access to the internet to download any additional dependencies:
   - Go to the **VPC** section in the Configuration tab.
   - Ensure the function is associated with subnets that have a route to a NAT Gateway or Internet Gateway.

8. Test the function to verify the error has been resolved.

9. If you don't have permissions to make the following changes, contact your AWS Administrator: request the addition of the following inline policy to the Lambda execution role (role name and account ID below are placeholders — substitute your own):

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "lambda:UpdateFunctionCode",
           "lambda:UpdateFunctionConfiguration"
         ],
         "Resource": "arn:aws:lambda:us-east-1:123456789012:function:bedrock-db-connector"
       }
     ]
   }
   ```

## Broader lesson

This is why `deploy.sh` in this project rebuilds the deployment package with `--platform manylinux2014_x86_64 --only-binary=:all: --python-version 311` flags on `pip install` — installing `psycopg2-binary` without pinning the target platform on a non-Linux dev machine (e.g. macOS) produces a wheel that doesn't load inside the Lambda execution environment.
