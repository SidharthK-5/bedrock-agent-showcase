"""
Check what documents are actually indexed in the Knowledge Base.
This will help us understand if the ecommerce video metadata is synced.
"""

import boto3

KB_ID = "YOURKBID2"  # Multimodal KB


def query_kb_directly(query_text, category_filter=None):
    """Query the KB directly to see what's indexed."""

    client = boto3.client("bedrock-agent-runtime")

    request = {"knowledgeBaseId": KB_ID, "retrievalQuery": {"text": query_text}}

    # Add metadata filter if provided
    if category_filter:
        request["retrievalConfiguration"] = {
            "vectorSearchConfiguration": {
                "filter": {"equals": {"key": "category", "value": category_filter}}
            }
        }

    print(f"\n{'='*80}")
    print(f"Querying KB: {KB_ID}")
    print(f"Query: {query_text}")
    if category_filter:
        print(f"Filter: category={category_filter}")
    else:
        print("Filter: None (retrieve all documents)")
    print(f"{'='*80}\n")

    try:
        response = client.retrieve(**request)

        results = response.get("retrievalResults", [])
        print(f"✅ Found {len(results)} documents\n")

        for i, result in enumerate(results, 1):
            content = result.get("content", {})
            location = result.get("location", {})
            metadata = result.get("metadata", {})

            print(f"\n{i}. Document Details:")
            print(f"   Score: {result.get('score', 'N/A')}")

            # S3 location
            if "s3Location" in location:
                s3_loc = location["s3Location"]
                print(f"   S3 URI: {s3_loc.get('uri', 'N/A')}")

            # Metadata
            if metadata:
                print("   Metadata:")
                for key, value in metadata.items():
                    print(f"      {key}: {value}")

            # Content preview
            if "text" in content:
                text = content["text"]
                preview = text[:200] + "..." if len(text) > 200 else text
                print(f"   Content Preview: {preview}")

        return results

    except Exception as e:  # noqa: BLE001
        print(f"❌ Error querying KB: {type(e).__name__}: {e}")
        return []


def main():
    print("\n" + "=" * 80)
    print("KNOWLEDGE BASE DOCUMENT CHECK")
    print("=" * 80)
    print("""
This script queries the Knowledge Base directly to see what documents
are actually indexed and available for retrieval.
    """)

    # Test 1: Query without filter (all documents)
    print("\n" + "=" * 80)
    print("TEST 1: Query ALL documents (no filter)")
    print("=" * 80)
    all_docs = query_kb_directly("order information")

    # Test 2: Query with ecommerce filter
    print("\n" + "=" * 80)
    print("TEST 2: Query with category=ecommerce filter")
    print("=" * 80)
    ecommerce_docs = query_kb_directly("order information", category_filter="ecommerce")

    # Test 3: Query with hr filter (should return nothing since this is the video KB)
    print("\n" + "=" * 80)
    print("TEST 3: Query with category=hr filter (should be empty)")
    print("=" * 80)
    hr_docs = query_kb_directly("order information", category_filter="hr")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"""
Total documents indexed: {len(all_docs)}
Documents with category=ecommerce: {len(ecommerce_docs)}
Documents with category=hr: {len(hr_docs)}

Analysis:
---------""")

    if len(all_docs) == 0:
        print("❌ No documents indexed in KB. Data source needs to be synced!")
    elif len(ecommerce_docs) == 0:
        print("❌ No ecommerce documents found. Video metadata might not be synced.")
        print("   Action: Sync data source YOURDATASOURCEID in AWS Console")
    else:
        print("✅ Ecommerce documents are indexed and retrievable!")
        print("   The internal server error must be related to agent processing,")
        print("   not the KB retrieval itself.")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
