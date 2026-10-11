"""
Minimal test to see the actual trace details from the agent.
This will show us what's in those 3 trace events before the error occurs.
"""

import json
import uuid

import boto3

AGENT_ID = "YOURAGENTID"
AGENT_ALIAS_ID = "YOURALIASID"


def test_with_full_trace():
    """Test agent invocation and dump all trace details."""

    client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
    session_id = str(uuid.uuid4())

    # Build request with both KBs
    request = {
        "agentId": AGENT_ID,
        "agentAliasId": AGENT_ALIAS_ID,
        "sessionId": session_id,
        "inputText": "Tell me about the order information in the videos.",
        "enableTrace": True,
        "sessionState": {
            "knowledgeBaseConfigurations": [
                {
                    "knowledgeBaseId": "YOURKBID2",
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {
                            "filter": {
                                "equals": {"key": "category", "value": "ecommerce"}
                            }
                        }
                    },
                },
                {
                    "knowledgeBaseId": "YOURKBID1",
                    "retrievalConfiguration": {"vectorSearchConfiguration": {}},
                },
            ]
        },
    }

    print("=" * 80)
    print("INVOKING AGENT WITH ECOMMERCE FILTER")
    print("=" * 80)
    print(f"Session: {session_id}\n")

    event_num = 0
    try:
        response = client.invoke_agent(**request)

        print("✅ invoke_agent() succeeded")
        print("\nProcessing events...\n")

        for event in response.get("completion", []):
            event_num += 1
            print(f"\n{'='*80}")
            print(f"EVENT #{event_num}")
            print("=" * 80)

            # Print full event
            print(json.dumps(event, indent=2, default=str))

    except Exception as e:
        print(f"\n{'='*80}")
        print(f"❌ ERROR AT EVENT #{event_num}")
        print("=" * 80)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e!s}")

        # Try to extract more info from the exception
        if hasattr(e, "response"):
            print("\nError Response:")
            print(json.dumps(e.response, indent=2, default=str))


if __name__ == "__main__":
    test_with_full_trace()
