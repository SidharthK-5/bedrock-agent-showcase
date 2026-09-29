"""
Bedrock Agent Local Database Integration - Main Entry Point

This project demonstrates how to create an Amazon Bedrock Agent that can
connect to a local PostgreSQL database running in a Docker container.

Usage:
    python main.py --setup     # Run setup wizard
    python main.py --test      # Test local configuration
    python main.py --deploy    # Deploy to AWS
"""

import argparse
import os


def setup_wizard():
    """Interactive setup wizard."""
    print("=" * 60)
    print("Bedrock Agent Local DB - Setup Wizard")
    print("=" * 60)
    print()

    # Check if .env exists
    if os.path.exists(".env"):
        print("✓ .env file found")
    else:
        print("⚠ Creating .env file from template...")
        if os.path.exists(".env.example"):
            import shutil

            shutil.copy(".env.example", ".env")
            print("✓ .env file created. Please edit it with your configuration.")
            return

    # Load and display configuration
    print("\nCurrent configuration:")
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    print(f"  {line.strip()}")
    except Exception as e:
        print(f"Error reading .env: {e}")
        return

    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Start Docker: docker-compose up -d")
    print("2. Test locally: python main.py --test")
    print("3. Set up tunnel: lt --port 5432")
    print("4. Deploy to AWS: python main.py --deploy")
    print("\nFor detailed instructions, see: STEP_BY_STEP_GUIDE.md")


def test_local():
    """Test local configuration."""
    print("Testing local configuration...")
    print()

    # Test 1: Check Docker
    print("1. Checking Docker container...")
    import subprocess

    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                "name=local-postgres-db",
                "--format",
                "{{.Status}}",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            print(f"   ✓ Docker container is running: {result.stdout.strip()}")
        else:
            print("   ✗ Docker container not running")
            print("   Run: docker-compose up -d")
            return False
    except Exception as e:
        print(f"   ✗ Error checking Docker: {e}")
        return False

    # Test 2: Check Python dependencies
    print("\n2. Checking Python dependencies...")
    try:
        import psycopg2

        print("   ✓ psycopg2 installed")
    except ImportError:
        print("   ✗ psycopg2 not installed")
        print("   Run: pip install -r requirements.txt")
        return False

    try:
        import boto3

        print("   ✓ boto3 installed")
    except ImportError:
        print("   ✗ boto3 not installed")
        print("   Run: pip install boto3")
        return False

    # Test 3: Test Lambda function
    print("\n3. Testing Lambda function...")
    try:
        from test_agent import test_lambda_locally

        if test_lambda_locally():
            print("   ✓ Lambda function works")
        else:
            print("   ✗ Lambda function failed")
            return False
    except Exception as e:
        print(f"   ✗ Error testing Lambda: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ All tests passed! Ready to deploy.")
    print("=" * 60)
    return True


def deploy_to_aws():
    """Deploy infrastructure to AWS."""
    print("Deploying to AWS...")
    print()

    # Check AWS credentials
    print("1. Checking AWS credentials...")
    try:
        import boto3

        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print(f"   ✓ AWS Account: {identity['Account']}")
        print(f"   ✓ User/Role: {identity['Arn']}")
    except Exception as e:
        print(f"   ✗ AWS credentials error: {e}")
        print("   Run: aws configure")
        return

    # Run deployment script
    print("\n2. Running deployment script...")
    try:
        from setup_infrastructure import main as setup_main

        setup_main()
    except Exception as e:
        print(f"   ✗ Deployment error: {e}")
        return

    print("\n" + "=" * 60)
    print("✓ Deployment complete!")
    print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bedrock Agent Local Database Integration"
    )
    parser.add_argument(
        "--setup", action="store_true", help="Run interactive setup wizard"
    )
    parser.add_argument("--test", action="store_true", help="Test local configuration")
    parser.add_argument("--deploy", action="store_true", help="Deploy to AWS")

    args = parser.parse_args()

    if args.setup:
        setup_wizard()
    elif args.test:
        test_local()
    elif args.deploy:
        deploy_to_aws()
    else:
        print("Bedrock Agent Local Database Integration")
        print()
        print("Usage:")
        print("  python main.py --setup     # Run setup wizard")
        print("  python main.py --test      # Test local configuration")
        print("  python main.py --deploy    # Deploy to AWS")
        print()
        print("Quick start:")
        print("  ./quickstart.sh")
        print()
        print("Documentation:")
        print("  README.md              - Overview and quick reference")
        print("  STEP_BY_STEP_GUIDE.md  - Detailed setup instructions")
        print("  AWS_SETUP.md           - AWS configuration guide")
        print("  ARCHITECTURE.md        - System architecture")


if __name__ == "__main__":
    main()
