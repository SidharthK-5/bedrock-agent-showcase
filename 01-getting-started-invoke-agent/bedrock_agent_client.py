"""
Amazon Bedrock Agent Client
A comprehensive client for interacting with Amazon Bedrock Agents.
"""

import time
import uuid
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from config import BedrockConfig
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt


class BedrockAgentClient:
    """Client for interacting with Amazon Bedrock Agents."""

    def __init__(self, config: BedrockConfig):
        """
        Initialize the Bedrock Agent client.

        Args:
            config (BedrockConfig): Configuration object with AWS and agent settings
        """
        self.config = config
        self.console = Console()

        # Validate configuration
        missing_config = config.validate()
        if missing_config:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_config)}"
            )

        # Initialize AWS Bedrock Agent Runtime client
        try:
            self.bedrock_agent_runtime = boto3.client(
                "bedrock-agent-runtime",
                aws_access_key_id=config.aws_access_key_id,
                aws_secret_access_key=config.aws_secret_access_key,
                region_name=config.aws_region,
            )
            self.console.print(
                f"✅ Connected to Bedrock in region: {config.aws_region}"
            )
        except Exception as e:
            self.console.print(f"❌ Failed to initialize Bedrock client: {e!s}")
            raise

    def invoke_agent(
        self,
        input_text: str,
        session_id: str | None = None,
        enable_trace: bool = False,
    ) -> dict[str, Any]:
        """
        Invoke the Bedrock Agent with a given input.

        Args:
            input_text (str): The input text to send to the agent
            session_id (Optional[str]): Session ID for conversation continuity
            enable_trace (bool): Whether to enable tracing for debugging

        Returns:
            Dict[str, Any]: The agent's response
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task("Invoking Bedrock Agent...", total=None)

                response = self.bedrock_agent_runtime.invoke_agent(
                    agentId=self.config.bedrock_agent_id,
                    agentAliasId=self.config.bedrock_agent_alias_id,
                    sessionId=session_id,
                    inputText=input_text,
                    enableTrace=enable_trace,
                )

                progress.update(task, description="Processing response...")

                # Process the streaming response
                full_response = self._process_streaming_response(response)
                full_response["sessionId"] = session_id

                return full_response

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            self.console.print(f"❌ AWS Client Error ({error_code}): {error_message}")
            raise
        except BotoCoreError as e:
            self.console.print(f"❌ AWS BotoCore Error: {e!s}")
            raise
        except Exception as e:
            self.console.print(f"❌ Unexpected error: {e!s}")
            raise

    def _process_streaming_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """
        Process the streaming response from Bedrock Agent.

        Args:
            response: The response object from invoke_agent

        Returns:
            Dict[str, Any]: Processed response data
        """
        completion = ""
        trace_data = []

        if "completion" in response:
            event_stream = response["completion"]

            for event in event_stream:
                if "chunk" in event:
                    chunk = event["chunk"]
                    if "bytes" in chunk:
                        completion += chunk["bytes"].decode("utf-8")

                elif "trace" in event and self.config.max_retries > 0:
                    trace_data.append(event["trace"])

        return {"completion": completion, "trace": trace_data, "timestamp": time.time()}

    def interactive_session(self):
        """Start an interactive session with the Bedrock Agent."""
        self.console.print(
            Panel.fit(
                "[bold blue]🤖 Bedrock Agent Interactive Session[/bold blue]\n"
                "Type your questions and get responses from your Bedrock Agent.\n"
                "Type 'quit', 'exit', or 'bye' to end the session.",
                border_style="blue",
            )
        )

        session_id = str(uuid.uuid4())
        self.console.print(f"Session ID: [dim]{session_id}[/dim]\n")

        while True:
            try:
                # Get user input
                user_input = Prompt.ask("🔵 [bold]You[/bold]")

                if user_input.lower() in ["quit", "exit", "bye", "q"]:
                    self.console.print("👋 Goodbye!")
                    break

                if not user_input.strip():
                    continue

                # Invoke agent
                response = self.invoke_agent(user_input, session_id)

                # Display response
                agent_text = response.get("completion", "No response received")
                self.console.print(
                    Panel(
                        agent_text,
                        title="🤖 [bold green]Agent Response[/bold green]",
                        border_style="green",
                    )
                )

                # Show trace information if available
                if response.get("trace") and len(response["trace"]) > 0:
                    self.console.print("\n[dim]📊 Trace information available[/dim]")

                self.console.print()  # Add spacing

            except KeyboardInterrupt:
                self.console.print("\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                self.console.print(f"❌ Error: {e!s}")
                continue

    def single_invocation(self, question: str) -> str:
        """
        Perform a single invocation of the agent.

        Args:
            question (str): The question to ask the agent

        Returns:
            str: The agent's response
        """
        response = self.invoke_agent(question)
        return response.get("completion", "No response received")
