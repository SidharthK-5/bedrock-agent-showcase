"""
Configuration management for Bedrock Agent POC
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class BedrockConfig:
    """Configuration class for Bedrock Agent settings."""

    def __init__(self):
        """Initialize configuration with environment variables."""
        self.aws_access_key_id: str | None = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region: str = os.getenv("AWS_REGION", "us-east-1")
        self.bedrock_agent_id: str | None = os.getenv("BEDROCK_AGENT_ID")
        self.bedrock_agent_alias_id: str | None = os.getenv("BEDROCK_AGENT_ALIAS_ID")
        self.session_timeout: int = int(os.getenv("SESSION_TIMEOUT", "300"))
        self.max_retries: int = int(os.getenv("MAX_RETRIES", "3"))

    def validate(self) -> list[str]:
        """
        Validate that all required configuration values are present.

        Returns:
            list[str]: List of missing configuration keys
        """
        missing = []

        if not self.aws_access_key_id:
            missing.append("AWS_ACCESS_KEY_ID")
        if not self.aws_secret_access_key:
            missing.append("AWS_SECRET_ACCESS_KEY")
        if not self.bedrock_agent_id:
            missing.append("BEDROCK_AGENT_ID")
        if not self.bedrock_agent_alias_id:
            missing.append("BEDROCK_AGENT_ALIAS_ID")

        return missing

    def __str__(self) -> str:
        """String representation of config (without sensitive data)."""
        return f"""BedrockConfig(
    aws_region={self.aws_region},
    bedrock_agent_id={self.bedrock_agent_id},
    bedrock_agent_alias_id={self.bedrock_agent_alias_id},
    session_timeout={self.session_timeout},
    max_retries={self.max_retries}
)"""
