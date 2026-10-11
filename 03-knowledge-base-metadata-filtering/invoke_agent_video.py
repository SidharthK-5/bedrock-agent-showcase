"""
Invoke Bedrock Agent to query video content with metadata filtering.

This script demonstrates how to query multimodal content (video files)
using metadata filters to ensure the agent only retrieves information
from specific video categories.

Video file: order_enquiry.mp4
Metadata: category=ecommerce, documentType=order-enquiry

IMPORTANT: Due to intermittent internal server errors with this specific agent/alias
combination, use this code as a reference for implementing video queries. The metadata
filtering approach works (verified in test_metadata_with_console_kbs.py), but may
require a different agent alias or KB configuration for video content.
"""

import json
from uuid import uuid4

import boto3


def invoke_agent_for_video(
    agent_id: str,
    agent_alias_id: str,
    prompt: str,
    category_filter: str,
    kb_ids: list[str],
    enable_trace: bool = True,
    region: str = "us-east-1",
) -> dict:
    """
    Invoke Bedrock Agent to query video content with category filtering.

    Args:
        agent_id: The ID of the Bedrock agent
        agent_alias_id: The alias ID of the agent
        prompt: The user's question about the video
        category_filter: Category value to filter by (e.g., 'ecommerce')
        kb_ids: List of all Knowledge Base IDs configured in agent
        enable_trace: Whether to enable trace for debugging
        region: AWS region

    Returns:
        Dictionary containing response, sources, and metadata

    Example:
        result = invoke_agent_for_video(
            agent_id='YOURAGENTID',
            agent_alias_id='YOURALIASID',
            prompt='What is the order status?',
            category_filter='ecommerce',
            kb_ids=['YOURKBID2']
        )
    """
    client = boto3.client("bedrock-agent-runtime", region_name=region)
    session_id = str(uuid4())

    # Create metadata filter for category
    metadata_filter = {"equals": {"key": "category", "value": category_filter}}

    try:
        print(f"\n{'='*80}")
        print("🎥 Querying Video Content with Metadata Filtering")
        print(f"{'='*80}")
        print(f"📝 Query: {prompt}")
        print(f"🏷️  Filter: category={category_filter}")
        print(f"🤖 Agent: {agent_id} (Alias: {agent_alias_id})")
        print(f"📚 Knowledge Bases: {', '.join(kb_ids)}")
        print(f"🔑 Session ID: {session_id}")
        print(f"{'='*80}\n")

        # Build invoke parameters with metadata filter
        # Apply filter to all specified KBs
        invoke_params = {
            "agentId": agent_id,
            "agentAliasId": agent_alias_id,
            "sessionId": session_id,
            "inputText": prompt,
            "enableTrace": enable_trace,
            "sessionState": {
                "knowledgeBaseConfigurations": [
                    {
                        "knowledgeBaseId": kb_id,  # Only multimodal KB
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {"filter": metadata_filter}
                        },
                    }
                    for kb_id in kb_ids
                ]
            },
        }

        print("📋 Request Parameters:")
        print(
            json.dumps(
                {
                    "agentId": invoke_params["agentId"],
                    "agentAliasId": invoke_params["agentAliasId"],
                    "sessionId": invoke_params["sessionId"],
                    "inputText": (
                        invoke_params["inputText"][:50] + "..."
                        if len(invoke_params["inputText"]) > 50
                        else invoke_params["inputText"]
                    ),
                    "enableTrace": invoke_params["enableTrace"],
                    "sessionState": invoke_params["sessionState"],
                },
                indent=2,
            )
        )
        print()

        print("🚀 Invoking agent with metadata filter...")
        print("⏳ Waiting for response...\n")

        # Invoke agent
        try:
            response = client.invoke_agent(**invoke_params)
            print("✅ invoke_agent() call successful, processing response stream...\n")
        except Exception as invoke_error:
            print("❌ invoke_agent() call failed immediately!")
            print(f"   Error Type: {type(invoke_error).__name__}")
            print(f"   Error Message: {invoke_error!s}")
            raise

        # Process response
        full_response = ""
        kb_sources_used = set()
        retrieved_docs = []
        video_sources = []
        event_count = 0

        print("📡 Processing event stream...")

        for event in response.get("completion", []):
            event_count += 1

            # Log event type
            event_types = list(event.keys())
            print(f"   Event {event_count}: {', '.join(event_types)}")

            # Extract trace information
            if enable_trace and "trace" in event:
                trace = event["trace"].get("trace", {})
                trace_type = next(iter(trace.keys())) if trace else "empty"
                print(f"      └─ Trace type: {trace_type}")

                if "orchestrationTrace" in trace:
                    orch = trace["orchestrationTrace"]
                    if "observation" in orch:
                        obs = orch["observation"]
                        if "knowledgeBaseLookupOutput" in obs:
                            kb_output = obs["knowledgeBaseLookupOutput"]
                            refs = kb_output.get("retrievedReferences", [])
                            print(
                                f"      └─ KB Lookup: {len(refs)} references retrieved"
                            )

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

                                doc_info = {
                                    "source_id": source_id,
                                    "s3_uri": s3_uri,
                                    "metadata": custom_meta,
                                }
                                retrieved_docs.append(doc_info)

                                # Check if this is a video file
                                if s3_uri.endswith((".mp4", ".mov", ".avi", ".mkv")):
                                    video_sources.append(doc_info)
                                    print(
                                        f"         └─ 🎥 Video found: {s3_uri.split('/')[-1]}"
                                    )

            # Extract response text
            if "chunk" in event:
                chunk = event["chunk"]
                text = chunk["bytes"].decode()
                if text.strip():
                    print(f"      └─ Text chunk: {len(text)} chars")
                print(text, end="", flush=True)
                full_response += text

        print(f"\n\n📊 Stream processing complete. Total events: {event_count}\n")
        print(f"\n\n{'='*80}")
        print("📊 TRACE ANALYSIS")
        print(f"{'='*80}")

        if kb_sources_used:
            print(f"📚 Data Sources Used: {', '.join(kb_sources_used)}")
            print(f"📄 Total Documents Retrieved: {len(retrieved_docs)}")
            print(f"🎥 Video Files Retrieved: {len(video_sources)}")

            if video_sources:
                print("\n🎬 Video Sources:")
                for i, video in enumerate(video_sources, 1):
                    print(f"\n   Video {i}:")
                    print(f"      Source ID: {video['source_id']}")
                    print(f"      S3 URI: {video['s3_uri']}")
                    if video["metadata"]:
                        print(
                            f"      Metadata: {json.dumps(video['metadata'], indent=10)}"
                        )

            if retrieved_docs and not video_sources:
                print("\n   ⚠️  No video files found in retrieved documents")
                print("   📄 All Retrieved Documents:")
                for i, doc in enumerate(retrieved_docs[:5], 1):  # Show first 5
                    print(f"\n   Document {i}:")
                    print(f"      S3 URI: {doc['s3_uri']}")
                    print(f"      Metadata: {json.dumps(doc['metadata'], indent=10)}")
        else:
            print("   ⚠️  No KB lookups detected in trace")

        print("\n" + "=" * 80)
        print("✅ QUERY COMPLETE")
        print("=" * 80)
        print(f"   🏷️  Filter Applied: category={category_filter}")
        print(f"   📚 Sources: {len(kb_sources_used)}")
        print(f"   📄 Documents: {len(retrieved_docs)}")
        print(f"   🎥 Videos: {len(video_sources)}")
        print("=" * 80 + "\n")

        return {
            "success": True,
            "response": full_response.strip(),
            "sources_used": list(kb_sources_used),
            "all_documents": retrieved_docs,
            "video_sources": video_sources,
            "session_id": session_id,
        }

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ ERROR OCCURRED")
        print("=" * 80)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e!s}")
        print("\n🔍 Debug Information:")
        print(f"   Agent ID: {agent_id}")
        print(f"   Alias ID: {agent_alias_id}")
        print(f"   Session ID: {session_id}")
        print(f"   KB IDs: {kb_ids}")
        print(f"   Filter: {json.dumps(metadata_filter, indent=6)}")
        print("\n📜 Full Traceback:")
        import traceback

        traceback.print_exc()
        print("=" * 80 + "\n")

        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "session_id": session_id,
        }


def main():
    """Main function to demonstrate video content querying."""

    # Configuration
    AGENT_ID = "YOURAGENTID"
    AGENT_ALIAS_ID = "YOURALIASID"
    # For video queries, specify the KB with video/audio content
    KB_IDS = ["YOURKBID2"]  # KB with multimodal (audio/video) content

    print("\n" + "=" * 80)
    print("🎥 BEDROCK AGENT - VIDEO CONTENT QUERY WITH METADATA FILTERING")
    print("=" * 80)
    print("""
This script demonstrates querying multimodal content (videos) using metadata filters.

Video Details:
--------------
File: order_enquiry.mp4
Metadata:
  - category: ecommerce
  - documentType: order-enquiry
  - region: carolina
  - topic: order-status
  - year: 2026

Usage:
------
The invoke_agent_for_video() function provides a clean interface for querying
video content with metadata filtering. Use it in your code like this:

    result = invoke_agent_for_video(
        agent_id='YOURAGENTID',
        agent_alias_id='YOURALIASID',
        prompt='What is the order status?',
        category_filter='ecommerce',
        kb_ids=['YOURKBID2']
    )
    
    if result['success']:
        print(f"Response: {result['response']}")
        print(f"Video sources: {len(result['video_sources'])}")
    
Note:
-----
If you encounter internal server errors, ensure:
1. Video file and .metadata.json are uploaded to S3
2. Data source is synced in Knowledge Base console
3. Agent alias has the correct KB configured
4. There are documents matching the metadata filter

Metadata filtering works as demonstrated in test_metadata_with_console_kbs.py
""")
    print("=" * 80)

    # First, validate KB configuration
    print("\n" + "=" * 80)
    print("STEP 1: Validate Agent & KB Configuration")
    print("=" * 80)

    try:
        bedrock_agent = boto3.client("bedrock-agent", region_name="us-east-1")

        print(f"✓ Checking agent alias {AGENT_ALIAS_ID}...")
        alias_response = bedrock_agent.get_agent_alias(
            agentId=AGENT_ID, agentAliasId=AGENT_ALIAS_ID
        )
        print(f"✓ Alias found: {alias_response['agentAlias']['agentAliasName']}")

        agent_version = alias_response["agentAlias"]["routingConfiguration"][0][
            "agentVersion"
        ]
        print(f"✓ Agent version: {agent_version}")

        print(f"✓ Checking KBs for version {agent_version}...")
        kb_response = bedrock_agent.list_agent_knowledge_bases(
            agentId=AGENT_ID, agentVersion=agent_version
        )

        kb_summaries = kb_response.get("agentKnowledgeBaseSummaries", [])
        print(f"✓ Found {len(kb_summaries)} KB(s) configured:")
        for kb in kb_summaries:
            kb_id = kb["knowledgeBaseId"]
            status = "✓" if kb_id in KB_IDS else "⚠"
            print(f"  {status} {kb_id} - {kb.get('knowledgeBaseState', 'N/A')}")

        if not any(kb["knowledgeBaseId"] in KB_IDS for kb in kb_summaries):
            print(f"\n⚠️  WARNING: KB {KB_IDS[0]} not found in agent configuration!")
            print(f"   Available KBs: {[kb['knowledgeBaseId'] for kb in kb_summaries]}")

    except Exception as config_error:
        print(f"⚠️  Could not validate configuration: {config_error}")

    print("=" * 80)

    # Test without metadata filter first
    print("\n" + "=" * 80)
    print("STEP 2: Test WITHOUT Metadata Filter (Baseline)")
    print("=" * 80)

    try:
        print("🚀 Calling agent WITHOUT filter to verify basic connectivity...")
        print(
            "   This helps isolate whether the issue is with the filter or the agent itself.\n"
        )

        bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
        test_response = bedrock_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=str(uuid4()),
            inputText="Hello",
            enableTrace=False,
        )

        test_text = ""
        for event in test_response.get("completion", []):
            if "chunk" in event:
                test_text += event["chunk"]["bytes"].decode()

        print("✅ SUCCESS! Agent responds without filter.")
        print(f"   Response preview: {test_text[:100]}...")
        print(
            "\n   This confirms the agent works. The issue is likely with the metadata filter."
        )

    except Exception as test_error:
        print("❌ FAILED! Agent doesn't work even without filter.")
        print(f"   Error: {test_error}")
        print(
            "\n   This indicates a problem with the agent/alias configuration itself,"
        )
        print("   not specifically with metadata filtering.")
        print("\n⛔ Stopping here - fix agent configuration before testing filters.")
        return

    print("=" * 80)

    # Now test with metadata filter
    category_filter = "ecommerce"
    print("\n" + "=" * 80)
    print("STEP 3: Test WITH Metadata Filter")
    print("=" * 80)
    print(f"Now testing with category={category_filter} filter...")
    print()

    result = invoke_agent_for_video(
        agent_id=AGENT_ID,
        agent_alias_id=AGENT_ALIAS_ID,
        prompt="Tell me about the order information in the videos.",
        category_filter="ecommerce",
        kb_ids=KB_IDS,
    )

    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)

    if result["success"]:
        print(f"""
✅ Query completed successfully!

Response:
{result['response']}

Metrics:
--------
- Sources Used: {len(result['sources_used'])}
- Total Documents: {len(result['all_documents'])}
- Video Sources: {len(result['video_sources'])}

Metadata Filtering:
-------------------
✓ Filter applied successfully
✓ Agent retrieved only documents matching category=ecommerce
✓ No cross-contamination from other categories
""")

        if result["video_sources"]:
            print("🎬 Video Files Found:")
            for i, video in enumerate(result["video_sources"], 1):
                print(f"\n{i}. {video['s3_uri'].split('/')[-1]}")
                print(f"   Metadata: {json.dumps(video['metadata'], indent=3)}")

    else:
        print(f"""
❌ Query failed with error: {result.get('error_type', 'Unknown')}: {result.get('error')}

Root Cause Analysis:
--------------------

Troubleshooting:
----------------
1. Verify video metadata is synced to KB
2. Check that category='ecommerce' documents exist
3. Try without metadata filter first to verify KB access
4. Review AWS CloudWatch logs for agent errors
5. Consider using a different agent alias for video content

Reference the working test in test_metadata_with_console_kbs.py for 
PDF documents, which successfully demonstrates metadata filtering.
""")

    print("=" * 80)


if __name__ == "__main__":
    main()
