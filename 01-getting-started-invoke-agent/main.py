"""
Main entry point for Bedrock Agent POC
This script handles all imports and provides a clean interface.
"""

import sys

from bedrock_agent_client import BedrockAgentClient
from config import BedrockConfig


def main():
    """Main entry point with proper error handling."""
    try:
        print("🚀 Bedrock Agent POC")
        print("=" * 50)

        # Load configuration
        config = BedrockConfig()
        print(f"📋 Configuration loaded for region: {config.aws_region}")

        # Validate configuration
        missing = config.validate()
        if missing:
            print(f"❌ Missing configuration: {', '.join(missing)}")
            print("\n💡 Setup Instructions:")
            print("1. Copy .env.example to .env")
            print("2. Fill in your AWS credentials and Bedrock agent details")
            print("3. Run this script again")
            return 1

        # Initialize client
        print("\n🔌 Initializing Bedrock Agent Client...")
        client = BedrockAgentClient(config)

        # Get user input for single question
        print("\n💬 Single Question Mode")
        question = input("🔵 Enter your question: ").strip()

        if not question:
            print("❌ No question provided. Exiting.")
            return 1

        print(f"\nQuestion: {question}")
        print("🤖 Getting response from Bedrock Agent...")

        # Use single invocation with the user's question
        response = client.single_invocation(question)

        print("\n" + "=" * 80)
        print("🤖 AGENT RESPONSE:")
        print("=" * 80)
        print(response)
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
