"""
Upload documents to S3 with metadata tags for KB filtering.

This script uploads your documents with custom metadata that can be used
for filtering during agent invocation.
"""

import json
import os

import boto3

s3 = boto3.client("s3")

# Configuration
BUCKET_NAME = "your-kb-data-bucket"
DOCUMENTS = [
    {
        "local_path": "Employee Handbook Sample Document.pdf",
        "s3_key": "upload/Employee Handbook Sample Document.pdf",
        "metadata": {
            "category": "hr",
            "documentType": "policy-info",
            "region": "california",
            "topic": "employee-benefits",
            "year": "2025",
        },
    },
    {
        "local_path": "Agent Execution Framework _2025-10-31_06_34_32.pdf",
        "s3_key": "upload/Agent Execution Framework _2025-10-31_06_34_32.pdf",
        "metadata": {
            "category": "technical",
            "documentType": "framework",
            "topic": "agent-execution",
            "year": "2025",
        },
    },
]


def upload_with_metadata(local_path, s3_key, metadata):
    """
    Upload a file to S3 along with a `.metadata.json` sidecar file.

    Bedrock Knowledge Bases read document metadata from a separate
    `<key>.metadata.json` object (wrapped in `metadataAttributes`), not from
    S3's own object-level `Metadata=` headers - see README.md's "Critical
    Rules" section.
    """
    print(f"\n📤 Uploading: {local_path}")
    print(f"   S3 Key: {s3_key}")
    print(f"   Metadata: {metadata}")

    if not os.path.exists(local_path):
        print(f"   ⚠️  File not found: {local_path}")
        return False

    try:
        with open(local_path, "rb") as f:
            s3.put_object(Bucket=BUCKET_NAME, Key=s3_key, Body=f)

        metadata_key = f"{s3_key}.metadata.json"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=metadata_key,
            Body=json.dumps({"metadataAttributes": metadata}, indent=2),
            ContentType="application/json",
        )
        print(f"   ✅ Uploaded successfully (document + {metadata_key})!")
        return True
    except Exception as e:
        print(f"   ❌ Upload failed: {e!s}")
        return False


def verify_metadata(s3_key):
    """Verify that the `.metadata.json` sidecar file was uploaded and is well-formed."""
    metadata_key = f"{s3_key}.metadata.json"
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=metadata_key)
        metadata = json.loads(response["Body"].read())
        print(f"\n🔍 Verified metadata for: {s3_key}")
        print(f"   {metadata}")
        return metadata
    except Exception as e:
        print(f"   ❌ Verification failed: {e!s}")
        return None


if __name__ == "__main__":
    print("=" * 80)
    print(" UPLOADING DOCUMENTS WITH METADATA TO S3")
    print("=" * 80)
    print(f"\nBucket: {BUCKET_NAME}")
    print(f"Documents to upload: {len(DOCUMENTS)}\n")

    success_count = 0

    for doc in DOCUMENTS:
        if upload_with_metadata(doc["local_path"], doc["s3_key"], doc["metadata"]):
            success_count += 1
            verify_metadata(doc["s3_key"])

    print(f"\n{'=' * 80}")
    print("📊 UPLOAD SUMMARY")
    print(f"{'=' * 80}")
    print(f"   Successful: {success_count}/{len(DOCUMENTS)}")
    print("\n⚠️  IMPORTANT NEXT STEPS:")
    print("   1. Go to AWS Bedrock Console → Knowledge Bases")
    print("   2. Select your Knowledge Base (YOURKBID3 or YOURKBID2)")
    print("   3. Click on Data Source → Sync")
    print("   4. Wait for sync to complete")
    print("   5. Metadata will then be indexed and available for filtering")
    print("=" * 80)
