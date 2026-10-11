"""
Production-ready Bedrock Agent invocation with metadata filtering support.

This module provides a clean interface for invoking Bedrock Agents with
optional metadata-based document filtering.
"""

from typing import Any
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError


def invoke_agent_with_metadata_filter(
    agent_id: str,
    agent_alias_id: str,
    prompt: str,
    metadata_filter: dict | None = None,
    kb_ids: list[str] | None = None,
    session_id: str | None = None,
    enable_trace: bool = False,
    region: str = "us-east-1",
) -> dict[str, Any]:
    """
    Invoke Bedrock Agent with optional metadata filtering.

    Args:
        agent_id: The ID of the Bedrock agent
        agent_alias_id: The alias ID of the agent
        prompt: The user's question/prompt
        metadata_filter: Optional metadata filter to apply to document retrieval.
                        Example: {'equals': {'key': 'category', 'value': 'hr'}}
        kb_ids: List of Knowledge Base IDs to apply filter to.
                If metadata_filter is provided, this is required.
                Should include ALL KBs configured in your agent.
        session_id: Optional session ID for conversation continuity.
                   If not provided, a new UUID will be generated.
        enable_trace: Whether to enable trace for debugging
        region: AWS region (default: us-east-1)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if invocation succeeded
        - response: The agent's text response
        - sources_used: List of data source IDs used (if trace enabled)
        - error: Error message (if failed)

    Example:
        # Without filtering (queries all documents)
        result = invoke_agent_with_metadata_filter(
            agent_id='YOURAGENTID',
            agent_alias_id='YOURALIASID',
            prompt='What are the leave policies?'
        )

        # With metadata filtering (queries only HR documents)
        result = invoke_agent_with_metadata_filter(
            agent_id='YOURAGENTID',
            agent_alias_id='YOURALIASID',
            prompt='What are the leave policies?',
            metadata_filter={'equals': {'key': 'category', 'value': 'hr'}},
            kb_ids=['YOURKBID1', 'YOURKBID2']  # Apply to ALL configured KBs
        )
    """
    client = boto3.client("bedrock-agent-runtime", region_name=region)

    if session_id is None:
        session_id = str(uuid4())

    try:
        # Build invoke parameters
        invoke_params = {
            "agentId": agent_id,
            "agentAliasId": agent_alias_id,
            "sessionId": session_id,
            "inputText": prompt,
            "enableTrace": enable_trace,
        }

        # Add metadata filter if provided
        if metadata_filter is not None:
            if kb_ids is None or len(kb_ids) == 0:
                raise ValueError(
                    "kb_ids must be provided when using metadata_filter. "
                    "Include ALL Knowledge Base IDs configured in your agent."
                )

            # Apply filter to all specified KBs
            invoke_params["sessionState"] = {
                "knowledgeBaseConfigurations": [
                    {
                        "knowledgeBaseId": kb_id,
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {"filter": metadata_filter}
                        },
                    }
                    for kb_id in kb_ids
                ]
            }

        # Invoke agent
        response = client.invoke_agent(**invoke_params)

        # Process response
        full_response = ""
        kb_sources_used = set()

        for event in response.get("completion", []):
            # Extract trace information if enabled
            if enable_trace and "trace" in event:
                trace = event["trace"].get("trace", {})
                if "orchestrationTrace" in trace:
                    orch = trace["orchestrationTrace"]
                    if "observation" in orch:
                        obs = orch["observation"]
                        if "knowledgeBaseLookupOutput" in obs:
                            kb_output = obs["knowledgeBaseLookupOutput"]
                            refs = kb_output.get("retrievedReferences", [])
                            for ref in refs:
                                metadata = ref.get("metadata", {})
                                source_id = metadata.get(
                                    "x-amz-bedrock-kb-data-source-id", "Unknown"
                                )
                                kb_sources_used.add(source_id)

            # Extract response text
            if "chunk" in event:
                chunk = event["chunk"]
                text = chunk["bytes"].decode()
                full_response += text

        return {
            "success": True,
            "response": full_response.strip(),
            "sources_used": list(kb_sources_used) if enable_trace else [],
            "session_id": session_id,
        }

    except ClientError as e:
        error_msg = str(e)
        return {"success": False, "error": error_msg, "session_id": session_id}
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {e!s}",
            "session_id": session_id,
        }


def create_metadata_filter(operator: str, key: str, value: Any) -> dict:
    """
    Helper function to create metadata filters.

    Args:
        operator: Filter operator (equals, notEquals, greaterThan, lessThan,
                 in, notIn, startsWith, listContains, stringContains)
        key: Metadata key to filter on
        value: Value to compare against

    Returns:
        Metadata filter dictionary

    Examples:
        # Equals
        filter = create_metadata_filter('equals', 'category', 'hr')

        # In (multiple values)
        filter = create_metadata_filter('in', 'category', ['hr', 'technical'])

        # Greater than
        filter = create_metadata_filter('greaterThan', 'year', '2024')
    """
    return {operator: {"key": key, "value": value}}


def create_compound_filter(operator: str, filters: list[dict]) -> dict:
    """
    Create compound filters using AND/OR operators.

    Args:
        operator: 'andAll' or 'orAll'
        filters: List of filter dictionaries to combine

    Returns:
        Compound filter dictionary

    Example:
        # AND: category=hr AND year=2025
        filter = create_compound_filter('andAll', [
            {'equals': {'key': 'category', 'value': 'hr'}},
            {'equals': {'key': 'year', 'value': '2025'}}
        ])

        # OR: category=hr OR category=technical
        filter = create_compound_filter('orAll', [
            {'equals': {'key': 'category', 'value': 'hr'}},
            {'equals': {'key': 'category', 'value': 'technical'}}
        ])
    """
    return {operator: filters}


# Example usage
if __name__ == "__main__":
    # Configuration
    AGENT_ID = "YOURAGENTID"
    AGENT_ALIAS_ID = "YOURALIASID"
    KB_IDS = ["YOURKBID1", "YOURKBID2"]  # ALL KBs configured in agent

    # Example 1: Query without filtering (uses all documents)
    print("=" * 80)
    print("Example 1: Query without metadata filter")
    print("=" * 80)
    result1 = invoke_agent_with_metadata_filter(
        agent_id=AGENT_ID,
        agent_alias_id=AGENT_ALIAS_ID,
        prompt="What are the leave policies?",
        enable_trace=True,
    )

    if result1["success"]:
        print(f"Response: {result1['response']}\n")
        print(f"Sources used: {result1['sources_used']}\n")
    else:
        print(f"Error: {result1['error']}\n")

    # Example 2: Query with HR filter (only HR documents)
    print("=" * 80)
    print("Example 2: Query with HR metadata filter")
    print("=" * 80)

    hr_filter = create_metadata_filter("equals", "category", "hr")

    result2 = invoke_agent_with_metadata_filter(
        agent_id=AGENT_ID,
        agent_alias_id=AGENT_ALIAS_ID,
        prompt="What are the leave policies?",
        metadata_filter=hr_filter,
        kb_ids=KB_IDS,
        enable_trace=True,
    )

    if result2["success"]:
        print(f"Response: {result2['response']}\n")
        print(f"Sources used: {result2['sources_used']}\n")
    else:
        print(f"Error: {result2['error']}\n")

    # Example 3: Compound filter (category=hr AND year=2025)
    print("=" * 80)
    print("Example 3: Query with compound filter")
    print("=" * 80)

    compound_filter = create_compound_filter(
        "andAll",
        [
            {"equals": {"key": "category", "value": "hr"}},
            {"equals": {"key": "year", "value": "2025"}},
        ],
    )

    result3 = invoke_agent_with_metadata_filter(
        agent_id=AGENT_ID,
        agent_alias_id=AGENT_ALIAS_ID,
        prompt="What are the leave policies for 2025?",
        metadata_filter=compound_filter,
        kb_ids=KB_IDS,
        enable_trace=True,
    )

    if result3["success"]:
        print(f"Response: {result3['response']}\n")
        print(f"Sources used: {result3['sources_used']}\n")
    else:
        print(f"Error: {result3['error']}\n")

    # Example 4: Query with technical filter (no context available)
    print("=" * 80)
    print("Example 4: Query with technical filter (no relevant context)")
    print("=" * 80)

    technical_filter = create_metadata_filter("equals", "category", "technical")

    result4 = invoke_agent_with_metadata_filter(
        agent_id=AGENT_ID,
        agent_alias_id=AGENT_ALIAS_ID,
        prompt="What are the leave policies?",
        metadata_filter=technical_filter,
        kb_ids=KB_IDS,
        enable_trace=True,
    )

    if result4["success"]:
        print(f"Response: {result4['response']}\n")
        print(f"Sources used: {result4['sources_used']}\n")
    else:
        print(f"Error: {result4['error']}\n")
