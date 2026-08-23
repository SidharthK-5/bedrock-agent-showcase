"""
Example usage script for Bedrock Agent POC
"""


from bedrock_agent_client import BedrockAgentClient
from config import BedrockConfig


def example_usage():
    """Example of how to use the Bedrock Agent Client."""

    print("🚀 Bedrock Agent POC - Example Usage")
    print("=" * 50)

    try:
        # Load configuration
        config = BedrockConfig()
        print(f"📋 Configuration: {config}")

        # Validate configuration
        missing = config.validate()
        if missing:
            print(f"❌ Missing configuration: {', '.join(missing)}")
            print("Please set up your .env file with the required values.")
            return

        # Initialize client
        print("\n🔌 Initializing Bedrock Agent Client...")
        client = BedrockAgentClient(config)

        # Example single invocation
        print("\n💬 Example: Single Question")
        question = "What is artificial intelligence?"
        print(f"Question: {question}")

        response = client.single_invocation(question)
        print(f"Response: {response}")

        print("\n✅ Example completed successfully!")
        print("\nTo run the interactive mode, execute:")
        print("uv run python main.py")

    except Exception as e:
        print(f"❌ Error: {e!s}")


if __name__ == "__main__":
    example_usage()
