"""
FINAL TEST: Metadata filtering with console-configured KBs + actual metadata on documents

Testing if metadata filtering works when:
1. KBs ARE configured in agent console (reverting the disable)
2. Documents have actual metadata tags
3. We use sessionState to provide ONLY filters (not KB selection)
"""

import json
from uuid import uuid4

import boto3

bedrock_agent_runtime = boto3.client("bedrock-agent-runtime")


def test_metadata_filter_with_console_kbs(
    prompt, metadata_filter=None, agent_id="YOURAGENTID", agent_alias_id="YOURALIASID"
):
    """
    Test if metadata filtering works when KBs are console-configured.

    Key difference from previous tests: Documents now have actual metadata.
    """
    print(f"\n{'='*80}")
    print("🧪 FINAL TEST: Metadata Filter with Console KBs")
    print(f"{'='*80}")
    print(f"   📝 Query: {prompt}")
    print(
        f"   🏷️  Metadata Filter: {metadata_filter if metadata_filter else 'None (baseline)'}"
    )
    print(f"   🤖 Agent: {agent_id} (Alias: {agent_alias_id})")
    print(f"{'='*80}\n")

    print("📋 TEST SETUP:")
    print("   1. ✅ KBs are configured in agent console")
    print("   2. ✅ Documents have metadata tags")
    print("   3. ✅ Using sessionState to provide metadata filter ONLY\n")

    try:
        session_id = str(uuid4())

        # Build invoke parameters
        invoke_params = {
            "agentId": agent_id,
            "agentAliasId": agent_alias_id,
            "sessionId": session_id,
            "inputText": prompt,
            "enableTrace": True,
        }

        # Add sessionState with metadata filter if provided
        if metadata_filter:
            print("🏷️  Applying metadata filter via sessionState:")
            print(json.dumps(metadata_filter, indent=2))
            print()

            # CRITICAL: Must provide filter for ALL KBs configured in agent console
            # Otherwise, unfiltered KBs will still return documents
            invoke_params["sessionState"] = {
                "knowledgeBaseConfigurations": [
                    {
                        "knowledgeBaseId": "YOURKBID1",  # KB with metadata documents
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {"filter": metadata_filter}
                        },
                    },
                    {
                        "knowledgeBaseId": "YOURKBID2",  # Other KB - apply same filter
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {"filter": metadata_filter}
                        },
                    },
                ]
            }

        print("🚀 Calling invoke_agent...")
        response = bedrock_agent_runtime.invoke_agent(**invoke_params)

        print(f"\n{'='*80}")
        print("💬 AGENT RESPONSE:")
        print(f"{'='*80}\n")

        full_response = ""
        kb_sources_used = set()
        retrieved_docs = []

        for event in response.get("completion"):
            # Check for trace events
            if "trace" in event:
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

                                # Extract S3 location and custom metadata
                                location = ref.get("location", {})
                                s3_uri = location.get("s3Location", {}).get(
                                    "uri", "N/A"
                                )
                                custom_meta = {
                                    k: v
                                    for k, v in metadata.items()
                                    if not k.startswith("x-amz-bedrock")
                                }

                                retrieved_docs.append(
                                    {
                                        "source_id": source_id,
                                        "s3_uri": s3_uri,
                                        "metadata": custom_meta,
                                    }
                                )

            # Check for response chunks
            if "chunk" in event:
                chunk = event["chunk"]
                text = chunk["bytes"].decode()
                print(text, end="")
                full_response += text

        print(f"\n\n{'='*80}")
        print("📊 TRACE ANALYSIS:")
        print(f"{'='*80}")

        if kb_sources_used:
            print(f"   📚 Data Sources Used: {', '.join(kb_sources_used)}")
            print("\n   📄 Documents Retrieved:")
            for i, doc in enumerate(retrieved_docs, 1):
                print(f"\n   Document {i}:")
                print(f"      Source ID: {doc['source_id']}")
                print(f"      S3: {doc['s3_uri']}")
                if doc["metadata"]:
                    print(f"      Metadata: {json.dumps(doc['metadata'], indent=10)}")
                else:
                    print(
                        "      Metadata: None (documents don't have custom metadata yet)"
                    )
        else:
            print("   ⚠️  No KB lookups detected in trace")

        print(f"\n{'='*80}")
        print("✅ SUCCESS!")
        print(f"{'='*80}")
        print("   🏷️  Filter Applied: {metadata_filter is not None}")
        print("   📚 Sources: {len(kb_sources_used)}")
        print("   📄 Documents: {len(retrieved_docs)}")
        print("="*80 + "\n")

        return {
            "success": True,
            "response": full_response,
            "sources_used": list(kb_sources_used),
            "documents": retrieved_docs,
            "has_metadata": any(doc["metadata"] for doc in retrieved_docs),
        }

    except Exception as e:
        print(f"\n❌ ERROR: {e!s}")
        print(f"   Error Type: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" FINAL TEST: Metadata Filtering with Console-Configured KBs")
    print("=" * 80)
    print("""
NEW HYPOTHESIS:
---------------
Metadata filtering via sessionState MIGHT work when:
1. KBs ARE configured in agent console (old alias YOURALIASID)
2. Documents have actual metadata tags (after upload)
3. We provide ONLY metadata filters in sessionState (not KB selection)

PREVIOUS FAILED ATTEMPTS:
-------------------------
❌ Attempt 1: Console KBs + sessionState filters → Ignored (docs had no metadata)
❌ Attempt 2: No console KBs + sessionState KB config → Error (0 KBs allowed)

THIS ATTEMPT:
-------------
✅ Console KBs enabled
✅ Documents uploaded with metadata
✅ Testing if filters work now

METADATA TAGS APPLIED:
----------------------
HR Document (Employee Handbook Sample Document.pdf):
  - category: hr
  - document-type: policy-info
  - region: california
  - topic: employee-benefits
  - year: 2025

Agent Framework Document (Agent Execution Framework PDF):
  - category: technical
  - document-type: framework
  - topic: agent-execution
  - year: 2025

NOTE: You must upload docs with metadata and sync the data source first!
""")
    print("=" * 80)

    # Use OLD alias (YOURALIASID) which has console KBs configured
    AGENT_ID = "YOURAGENTID"
    AGENT_ALIAS_OLD = "YOURALIASID"  # This alias has KBs configured in console
    QUERY = "what are the leave policies?"

    # Test 1: Baseline - no filter
    print("\n" + "=" * 80)
    print("TEST 1: BASELINE - No metadata filter")
    print("=" * 80)
    print("Expected: Should retrieve from BOTH documents")
    result1 = test_metadata_filter_with_console_kbs(
        QUERY, agent_alias_id=AGENT_ALIAS_OLD
    )

    # Test 2: Filter for HR category only
    print("\n" + "=" * 80)
    print("TEST 2: Filter for HR documents only")
    print("=" * 80)
    print("Expected: Should retrieve ONLY from HR document")

    hr_filter = {"equals": {"key": "category", "value": "hr"}}

    result2 = test_metadata_filter_with_console_kbs(
        QUERY, metadata_filter=hr_filter, agent_alias_id=AGENT_ALIAS_OLD
    )

    # Test 3: Filter for technical category only
    print("\n" + "=" * 80)
    print("TEST 3: Filter for Technical documents only")
    print("=" * 80)
    print(
        "Expected: Should retrieve ONLY from Agent Framework document (should say no leave policy info)"
    )

    tech_filter = {"equals": {"key": "category", "value": "technical"}}

    result3 = test_metadata_filter_with_console_kbs(
        QUERY, metadata_filter=tech_filter, agent_alias_id=AGENT_ALIAS_OLD
    )

    # Analysis
    print("\n" + "=" * 80)
    print("📊 FINAL VERDICT")
    print("=" * 80)

    sources1 = set(result1.get("sources_used", []))
    sources2 = set(result2.get("sources_used", []))
    sources3 = set(result3.get("sources_used", []))

    print(f"\nTest 1 (No filter): {sources1}")
    print(f"Test 2 (HR filter): {sources2}")
    print(f"Test 3 (Technical filter): {sources3}")

    # Check if documents have metadata
    has_meta1 = result1.get("has_metadata", False)
    has_meta2 = result2.get("has_metadata", False)
    has_meta3 = result3.get("has_metadata", False)

    print("\nDocuments have metadata:")
    print(f"  Test 1: {has_meta1}")
    print(f"  Test 2: {has_meta2}")
    print(f"  Test 3: {has_meta3}")

    if not (has_meta1 or has_meta2 or has_meta3):
        print("""
⚠️  DOCUMENTS DON'T HAVE METADATA YET!

You need to:
1. Run: python upload_docs_with_metadata.py
2. Go to AWS Console → Bedrock → Knowledge Bases
3. Sync the data source
4. Wait for sync to complete
5. Run this test again
""")
    elif sources1 == sources2 == sources3:
        print("""
❌ METADATA FILTERING DOES NOT WORK

All tests used the same data sources, proving:
1. sessionState metadata filters are ignored
2. Agent queries all console-configured KBs regardless of filters
3. Even with metadata on documents, filters don't work

CONCLUSION:
-----------
Direct agent invocation with metadata filtering is NOT possible with
current Bedrock Agent architecture when KBs are console-configured.

YOUR ONLY OPTIONS:
------------------
1. Use retrieve_and_generate API (no agent features)
2. Use hybrid approach (with context matching - rejected by lead)
3. Accept no metadata filtering capability
""")
    else:
        print("""
✅ METADATA FILTERING WORKS!

Different data sources were used based on filters, proving:
1. sessionState metadata filters ARE respected
2. Metadata filtering works with console-configured KBs
3. This is the solution you've been looking for!

IMPLEMENTATION:
---------------
Use this approach in production:
- Keep KBs configured in agent console
- Add metadata to all documents
- Use sessionState with metadata filters at runtime
- No hybrid logic needed!
""")

    print("=" * 80)
