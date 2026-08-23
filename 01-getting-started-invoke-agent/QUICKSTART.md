# Quick Start Guide

## 🚀 Getting Started with Bedrock Agent POC

This guide will help you quickly set up and run the Amazon Bedrock Agent POC project.

### Prerequisites Checklist

- [x] Python 3.8.1 or higher installed
- [x] UV package manager installed  
- [ ] AWS Account with Bedrock access
- [ ] AWS IAM user with Bedrock permissions
- [ ] Bedrock Agent created and configured

### Step 1: Install UV (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Install Dependencies

```bash
uv sync
```

### Step 3: Configure AWS Credentials

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual AWS credentials:

   ```env
   AWS_ACCESS_KEY_ID=AKIA...your_access_key
   AWS_SECRET_ACCESS_KEY=abc123...your_secret_key
   AWS_REGION=us-east-1
   BEDROCK_AGENT_ID=ABCD1234...your_agent_id
   BEDROCK_AGENT_ALIAS_ID=TESTALIASID...your_alias_id
   ```

### Step 4: Run the Application

#### Option A: Interactive Mode (Recommended)

```bash
uv run python main.py
```

#### Option B: Example Script

```bash
uv run python example.py
```

### Step 5: Test with Questions

Once running in interactive mode, try these example questions:

- "What is artificial intelligence?"
- "How can I improve my productivity?"
- "Explain machine learning in simple terms"

### AWS Setup Instructions

#### Required IAM Permissions

Your AWS IAM user needs these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeAgent",
                "bedrock:GetAgent",
                "bedrock:ListAgents"
            ],
            "Resource": "*"
        }
    ]
}
```

#### Creating a Bedrock Agent

1. Go to AWS Console → Amazon Bedrock → Agents
2. Click "Create Agent"
3. Provide a name and description
4. Choose a foundation model (e.g., Claude)
5. Configure instructions for your agent
6. Create and note the Agent ID and Alias ID

### Project Structure

```Plain Text
bedrock-agent-poc/
├── bedrock_agent_client.py    # Core InvokeAgent client
├── config.py                  # Configuration management
├── .env                        # Your environment variables
├── .env.example                # Template for environment variables
├── main.py                     # Main entry point
├── example.py                  # Example usage script
├── pyproject.toml              # UV project configuration
└── README.md                   # Detailed documentation
```

### Troubleshooting

#### Common Issues

1. **"Missing configuration" error**
   - Ensure your `.env` file exists and contains all required variables
   - Check that variable names match exactly (case-sensitive)

2. **AWS authentication errors**
   - Verify your AWS credentials are correct
   - Ensure your IAM user has the required Bedrock permissions
   - Check that your AWS region is correct

3. **Agent not found errors**
   - Verify your Agent ID and Alias ID are correct
   - Ensure the agent is in "Prepared" or "Draft" status
   - Check you're using the correct AWS region

4. **Import errors**
   - Run `uv sync` to ensure all dependencies are installed
   - Ensure you're running commands with `uv run`

### Available Commands

```bash
# Install dependencies
uv sync

# Run main application (recommended)
uv run python main.py

# Run example
uv run python example.py

# Format code (optional)
uv run black .
```

### Next Steps

1. **Customize the Agent**: Modify the agent instructions in AWS console
2. **Add Features**: Extend the client with additional functionality
3. **Integration**: Integrate the client into your applications
4. **Monitoring**: Add logging and monitoring capabilities

### Support

For issues or questions:

1. Check the troubleshooting section above
2. Review AWS Bedrock documentation
3. Check project README.md for detailed information

---

## Happy coding! 🎉
