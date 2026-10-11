"""Diagnose agent and KB configuration issues."""

import boto3


def check_agent_configuration():
    """Check agent and KB configuration."""
    client = boto3.client("bedrock-agent", region_name="us-east-1")

    agent_id = "YOURAGENTID"
    alias_id = "YOURALIASID"

    print("=" * 80)
    print("🔍 DIAGNOSTIC CHECK")
    print("=" * 80)

    try:
        # Get agent alias details
        print(f"\n1. Checking Agent Alias: {alias_id}")
        response = client.get_agent_alias(agentId=agent_id, agentAliasId=alias_id)

        alias_info = response["agentAlias"]
        agent_version = alias_info.get("routingConfiguration", [{}])[0].get(
            "agentVersion", "DRAFT"
        )
        print(f"   ✅ Alias Name: {alias_info.get('agentAliasName')}")
        print(f"   ✅ Agent Version: {agent_version}")

        # List KBs for this version
        print(f"\n2. Checking Knowledge Bases for version {agent_version}:")
        kb_response = client.list_agent_knowledge_bases(
            agentId=agent_id, agentVersion=agent_version
        )

        kb_summaries = kb_response.get("agentKnowledgeBaseSummaries", [])

        if kb_summaries:
            print(f"   Found {len(kb_summaries)} Knowledge Base(s):")
            for idx, kb in enumerate(kb_summaries, 1):
                print(f"\n   KB {idx}:")
                print(f"      ID: {kb['knowledgeBaseId']}")
                print(f"      Description: {kb.get('description', 'N/A')}")
                print(f"      Status: {kb.get('knowledgeBaseState', 'N/A')}")

                # Get data sources for this KB
                kb_client = boto3.client("bedrock-agent", region_name="us-east-1")
                try:
                    ds_response = kb_client.list_data_sources(
                        knowledgeBaseId=kb["knowledgeBaseId"]
                    )
                    data_sources = ds_response.get("dataSourceSummaries", [])
                    print(f"      Data Sources: {len(data_sources)}")
                    for ds in data_sources:
                        print(
                            f"         - {ds['dataSourceId']}: {ds.get('name', 'N/A')} (Status: {ds.get('status', 'N/A')})"
                        )
                except Exception as e:
                    print(f"      ⚠️  Could not list data sources: {e}")
        else:
            print("   ❌ No Knowledge Bases found!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


def test_without_filter():
    """Test agent invocation without metadata filter."""
    client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

    print("\n" + "=" * 80)
    print("3. Testing Agent WITHOUT Metadata Filter")
    print("=" * 80)

    try:
        from uuid import uuid4

        response = client.invoke_agent(
            agentId="YOURAGENTID",
            agentAliasId="YOURALIASID",
            sessionId=str(uuid4()),
            inputText="Hello, can you help me?",
            enableTrace=False,
        )

        full_response = ""
        for event in response.get("completion", []):
            if "chunk" in event:
                chunk = event["chunk"]
                text = chunk["bytes"].decode()
                full_response += text

        print("   ✅ Agent responds without filter!")
        print(f"   Response: {full_response[:100]}...")
        return True

    except Exception as e:
        print(f"   ❌ Agent fails even without filter: {e}")
        return False


def test_with_simple_filter():
    """Test with a simple filter to see if filtering is the issue."""
    client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

    print("\n" + "=" * 80)
    print("4. Testing Agent WITH Simple Metadata Filter")
    print("=" * 80)

    try:
        from uuid import uuid4

        # Try with just one KB and simple filter
        response = client.invoke_agent(
            agentId="YOURAGENTID",
            agentAliasId="YOURALIASID",
            sessionId=str(uuid4()),
            inputText="What are the leave policies?",
            enableTrace=False,
            sessionState={
                "knowledgeBaseConfigurations": [
                    {
                        "knowledgeBaseId": "YOURKBID1",
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {
                                "filter": {"equals": {"key": "category", "value": "hr"}}
                            }
                        },
                    }
                ]
            },
        )

        full_response = ""
        for event in response.get("completion", []):
            if "chunk" in event:
                chunk = event["chunk"]
                text = chunk["bytes"].decode()
                full_response += text

        print("   ✅ Agent responds with HR filter!")
        print(f"   Response: {full_response[:100]}...")

        # Now try ecommerce filter
        print("\n   Testing with ecommerce filter...")
        response2 = client.invoke_agent(
            agentId="YOURAGENTID",
            agentAliasId="YOURALIASID",
            sessionId=str(uuid4()),
            inputText="What is the order status of Mr. Smith?",
            enableTrace=False,
            sessionState={
                "knowledgeBaseConfigurations": [
                    {
                        "knowledgeBaseId": "YOURKBID1",
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {
                                "filter": {
                                    "equals": {"key": "category", "value": "ecommerce"}
                                }
                            }
                        },
                    }
                ]
            },
        )

        full_response2 = ""
        for event in response2.get("completion", []):
            if "chunk" in event:
                chunk = event["chunk"]
                text = chunk["bytes"].decode()
                full_response2 += text

        print("   ✅ Agent responds with ecommerce filter!")
        print(f"   Response: {full_response2}...")

        return True

    except Exception as e:
        print(f"   ❌ Filter test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    check_agent_configuration()

    if test_without_filter():
        test_with_simple_filter()

    print("\n" + "=" * 80)
    print("📋 DIAGNOSIS COMPLETE")
    print("=" * 80)
