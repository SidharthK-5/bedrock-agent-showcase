#!/bin/bash

# Script to add Lambda permissions for Bedrock Agent
# Run this script with appropriate AWS credentials

set -e

FUNCTION_NAME="bedrock-db-connector"
REGION="us-east-1"
ACCOUNT_ID="123456789012"
AGENT_ID="YOURAGENTID"

echo "Adding Lambda permissions for Bedrock Agent..."

# Add permission for the agent itself
echo "1. Adding permission for agent..."
aws lambda add-permission \
  --function-name $FUNCTION_NAME \
  --statement-id bedrock-agent-invoke \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com \
  --source-arn "arn:aws:bedrock:$REGION:$ACCOUNT_ID:agent/$AGENT_ID" \
  --region $REGION 2>/dev/null || echo "Permission already exists or failed to add"

# Add permission for agent aliases (including test alias)
echo "2. Adding permission for agent aliases..."
aws lambda add-permission \
  --function-name $FUNCTION_NAME \
  --statement-id bedrock-agent-alias-invoke \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com \
  --source-arn "arn:aws:bedrock:$REGION:$ACCOUNT_ID:agent-alias/$AGENT_ID/*" \
  --region $REGION 2>/dev/null || echo "Permission already exists or failed to add"

echo ""
echo "✅ Permissions added successfully!"
echo ""
echo "Verifying permissions..."
aws lambda get-policy --function-name $FUNCTION_NAME --region $REGION --query Policy --output text | jq

echo ""
echo "You can now test the Bedrock Agent."
