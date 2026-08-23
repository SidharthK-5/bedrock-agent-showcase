# 01 - Getting Started: Invoke a Classic Bedrock Agent

The entry-point example for this repo: the smallest possible Python client for calling an already-created **classic Amazon Bedrock Agent** (`agentId` + `agentAliasId`) via `bedrock-agent-runtime.invoke_agent`.

If you only read one project in this repo, read this one first — every other project builds on this same `InvokeAgent` call pattern, just with different action groups (Lambda, Postgres, Playwright, etc.) behind the agent.

## What this is

- A minimal `boto3` wrapper (`bedrock_agent_client.py`) around `bedrock-agent-runtime.invoke_agent`
- Environment-based configuration (`config.py`) for `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` / `BEDROCK_AGENT_ID` / `BEDROCK_AGENT_ALIAS_ID`
- An interactive CLI (`main.py`) with a Rich-based terminal UI, and a single-shot example (`example.py`)
- Managed with the [uv](https://github.com/astral-sh/uv) package manager

## Project structure

``` Plain Text
01-getting-started-invoke-agent/
├── bedrock_agent_client.py    # Core InvokeAgent client
├── config.py                  # Env-based configuration
├── main.py                    # Entry point (interactive session)
├── example.py                 # Single-question example
├── .env.example                # Copy to .env and fill in your own values
├── pyproject.toml
├── uv.lock
├── QUICKSTART.md
└── README.md
```

## Setup

1. Install [uv](https://github.com/astral-sh/uv):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:

   ```bash
   uv sync
   ```

3. Copy `.env.example` to `.env` and fill in your own AWS credentials and
   Bedrock Agent identifiers:

   ```env
   AWS_ACCESS_KEY_ID=your_access_key_here
   AWS_SECRET_ACCESS_KEY=your_secret_key_here
   AWS_REGION=us-east-1
   BEDROCK_AGENT_ID=your_agent_id_here
   BEDROCK_AGENT_ALIAS_ID=your_agent_alias_id_here
   ```

4. Run it:

   ```bash
   uv run python main.py
   ```

See `QUICKSTART.md` for a more detailed walkthrough, including required IAM permissions (`bedrock:InvokeAgent`, `bedrock:GetAgent`, `bedrock:ListAgents`) and how to create a classic Bedrock Agent in the console.

## A note on this repo's status

This project was originally built and verified against a classic Amazon Bedrock Agent in a different AWS account/engagement that is no longer accessible to this repo's maintainer. It is preserved here as reference code — the architecture and the `InvokeAgent` calling pattern are real and were working at the time — but it has not been (and currently cannot be) re-deployed or re-tested, since AWS no longer allows new accounts to create classic Bedrock Agents (only Bedrock AgentCore Runtime is available for new accounts now).

For the same project cluster rebuilt on **Bedrock AgentCore Runtime** (Strands Agents) with current, tested/working code, see the companion repo: [bedrock-agentcore-showcase](https://github.com/SidharthK-5/bedrock-agentcore-showcase).
