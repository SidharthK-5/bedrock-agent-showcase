# Bedrock Agent with Knowledge Base - Metadata Filtering Solution

> **Status note:** This is a "war story" — a real debugging investigation carried out against a classic Amazon Bedrock Agent with two configured Knowledge Bases, in a different AWS account/engagement no longer accessible to this repo's maintainer. The problem, the failed approaches, and the working solution documented below are real and were verified at the time. It has not been (and currently cannot be) re-run or re-verified in this sandbox, since AWS no longer allows new accounts to create classic Bedrock Agents. All agent/alias/knowledge-base/data-source IDs and the S3 bucket name below have been replaced with placeholders (`YOURAGENTID`, `YOURKBID1`, etc.) — substitute your own when reproducing this.
>
> **Sample documents not included**: the original investigation used an "Employee Handbook Sample Document.pdf" (a generic HR policy document, tagged `hr` content) and an internal "Agent Execution Framework" PDF, plus an `order_enquiry.mp4` video, to prove metadata filtering worked across text and multimodal Knowledge Bases. Those files aren't included in this repo. To reproduce this test setup, supply your own sample PDF (any document works) and, if you want to exercise the multimodal/video path, any short `.mp4` — then follow the metadata-tagging steps below to tag and filter them.

## Problem Statement

**Original Issue**: Agent was fetching data from the wrong Knowledge Base despite changing the KB ID in the invocation parameters. The goal was to control which Knowledge Base the agent queries at runtime without making console changes or implementing complex context-matching logic.

## Root Cause Analysis

After extensive testing, we discovered:

1. **sessionState.knowledgeBaseConfigurations is ignored** when only specifying `knowledgeBaseId` - the agent always queries ALL Knowledge Bases configured in the console
2. **Removing console KBs and using sessionState** results in validation error: "can only provide 0 KBs"
3. **The API design requires** KBs to be configured in the agent console - runtime KB selection via sessionState alone is not supported

## Solution: Metadata-Based Document Filtering

Instead of selecting different Knowledge Bases at runtime, we filter documents **within** the configured KBs using metadata tags.

### How It Works

1. **Tag documents with metadata** during S3 upload using `.metadata.json` files
2. **Sync the data source** in the Knowledge Base after uploading documents
3. **Apply metadata filters via sessionState** at invocation time to retrieve only relevant documents

### Architecture

```txt
User Query + Metadata Filter
         ↓
   invoke_agent() with sessionState
         ↓
Agent queries ALL configured KBs
         ↓
Each KB applies metadata filter to documents
         ↓
Only documents matching filter are returned
         ↓
Agent generates response using filtered documents
```

## Implementation Guide

### Step 1: Prepare Metadata Files

Create `.metadata.json` files for each document with this structure:

**File**: `Employee Handbook Sample Document.pdf.metadata.json`

```json
{
  "metadataAttributes": {
    "category": "hr",
    "documentType": "policy-info",
    "region": "california",
    "topic": "employee-benefits",
    "year": "2025"
  }
}
```

**Critical Rules**:

- Filename must be: `<document-name>.metadata.json`
- Must wrap attributes in `metadataAttributes` object
- Use camelCase for keys (not hyphens)
- Place in same S3 location as the document

### Step 2: Upload Documents with Metadata

```python
import boto3
import json

s3 = boto3.client('s3')

# Upload document
s3.upload_file(
    'Employee Handbook Sample Document.pdf',
    'your-bucket',
    'upload/Employee Handbook Sample Document.pdf'
)

# Upload metadata file
metadata = {
    "metadataAttributes": {
        "category": "hr",
        "documentType": "policy-info",
        "region": "california",
        "topic": "employee-benefits",
        "year": "2025"
    }
}

s3.put_object(
    Bucket='your-bucket',
    Key='upload/Employee Handbook Sample Document.pdf.metadata.json',
    Body=json.dumps(metadata, indent=2),
    ContentType='application/json'
)
```

### Step 3: Sync Data Source

After uploading documents and metadata files:

1. Go to AWS Console → Bedrock → Knowledge Bases
2. Select your Knowledge Base
3. Go to Data Sources tab
4. Click "Sync" button
5. Wait for sync to complete

### Step 4: Invoke Agent with Metadata Filter

```python
import boto3
from uuid import uuid4

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

# Define metadata filter
metadata_filter = {
    'equals': {
        'key': 'category',
        'value': 'hr'
    }
}

# Invoke agent with filter
response = bedrock_agent_runtime.invoke_agent(
    agentId='YOUR_AGENT_ID',
    agentAliasId='YOUR_ALIAS_ID',
    sessionId=str(uuid4()),
    inputText='What are the leave policies?',
    enableTrace=True,
    sessionState={
        'knowledgeBaseConfigurations': [
            {
                'knowledgeBaseId': 'KB_ID_1',
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'filter': metadata_filter
                    }
                }
            },
            {
                'knowledgeBaseId': 'KB_ID_2',  # Apply to ALL KBs!
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'filter': metadata_filter
                    }
                }
            }
        ]
    }
)

# Process response
for event in response.get("completion"):
    if 'chunk' in event:
        print(event['chunk']['bytes'].decode(), end="")
```

### Supported Filter Operators

```python
# Equals
{'equals': {'key': 'category', 'value': 'hr'}}

# Not Equals
{'notEquals': {'key': 'category', 'value': 'technical'}}

# Greater Than
{'greaterThan': {'key': 'year', 'value': '2024'}}

# Greater Than or Equal
{'greaterThanOrEquals': {'key': 'year', 'value': '2024'}}

# Less Than
{'lessThan': {'key': 'year', 'value': '2026'}}

# Less Than or Equal
{'lessThanOrEquals': {'key': 'year', 'value': '2025'}}

# In (list of values)
{'in': {'key': 'category', 'value': ['hr', 'technical']}}

# Not In
{'notIn': {'key': 'status', 'value': ['archived', 'deleted']}}

# Starts With
{'startsWith': {'key': 'documentType', 'value': 'policy'}}

# List Contains
{'listContains': {'key': 'tags', 'value': 'important'}}

# String Contains
{'stringContains': {'key': 'description', 'value': 'benefits'}}

# AND operator
{
    'andAll': [
        {'equals': {'key': 'category', 'value': 'hr'}},
        {'equals': {'key': 'year', 'value': '2025'}}
    ]
}

# OR operator
{
    'orAll': [
        {'equals': {'key': 'category', 'value': 'hr'}},
        {'equals': {'key': 'category', 'value': 'technical'}}
    ]
}
```

## Critical Implementation Notes

### 1. Apply Filter to ALL Knowledge Bases

**Problem**: If your agent has multiple KBs configured in the console and you only apply the filter to one KB, the other KBs will still return documents (unfiltered).

**Solution**: Always specify the filter for every KB configured in your agent:

```python
sessionState={
    'knowledgeBaseConfigurations': [
        {'knowledgeBaseId': 'KB1', 'retrievalConfiguration': {...}},
        {'knowledgeBaseId': 'KB2', 'retrievalConfiguration': {...}},
        # Must include ALL KBs!
    ]
}
```

### 2. knowledgeBaseId is Required

You **cannot** provide only a filter without specifying `knowledgeBaseId`. This will fail:

```python
# ❌ WRONG - Missing knowledgeBaseId
sessionState={
    'knowledgeBaseConfigurations': [{
        'retrievalConfiguration': {
            'vectorSearchConfiguration': {'filter': {...}}
        }
    }]
}
```

### 3. Metadata File Format

- Must be valid JSON
- Must wrap attributes in `metadataAttributes`
- Keys must be camelCase (not kebab-case with hyphens)
- Place in same S3 folder as document
- Must sync data source after upload

### 4. Console KB Configuration Required

You **cannot** bypass console KB configuration and provide KBs only via sessionState. The agent requires KBs to be configured in the console.

## Testing Results

### Test 1: No Filter (Baseline)

- **Query**: "what are the leave policies?"
- **Filter**: None
- **Result**: Retrieved from BOTH sources (HR + Technical)
- **Documents**: 12 total

### Test 2: HR Filter

- **Query**: "what are the leave policies?"
- **Filter**: `category=hr`
- **Result**: Retrieved ONLY from HR source
- **Documents**: 3 (all with HR metadata)
- **Response**: Listed leave policy types correctly

### Test 3: Technical Filter

- **Query**: "what are the leave policies?"
- **Filter**: `category=technical`
- **Result**: Retrieved ONLY from Technical source
- **Documents**: 14 (all with technical metadata)
- **Response**: Said no leave policy info available (correct - technical docs don't have leave policy info)

**Conclusion**: ✅ Metadata filtering works perfectly!

## Experiments Conducted

Throughout the investigation, we tested multiple approaches:

### ❌ Failed Approach 1: sessionState KB Selection

**Hypothesis**: Provide `knowledgeBaseId` in sessionState to select KB at runtime

**Result**: FAILED - sessionState `knowledgeBaseId` is ignored; agent uses all console-configured KBs

### ❌ Failed Approach 2: No Console KBs

**Hypothesis**: Remove console KBs and provide all KB config via sessionState

**Result**: FAILED - Validation error: "can only provide 0 KBs"

### ❌ Failed Approach 3: Hybrid (Retrieve + Invoke)

**Hypothesis**: Use `retrieve()` API to get documents, then invoke agent with context

**Result**: WORKS but requires context-matching logic - rejected by lead

### ✅ Working Solution: Metadata Filtering

**Hypothesis**: Keep console KBs, add metadata to documents, filter via sessionState

**Result**: SUCCESS - Agent retrieves only documents matching metadata filter

## Files Reference

- **`test_metadata_with_console_kbs.py`**: Final working test demonstrating metadata filtering (PDF documents)
- **`upload_docs_with_metadata.py`**: Script to upload documents with `.metadata.json` sidecar files
- **`invoke_agent.py`**: Production-ready agent invocation with metadata filtering
- **`invoke_agent_video.py`**: Same approach applied to multimodal (video) content — see [`VIDEO_METADATA_FILTERING_ISSUE.md`](./VIDEO_METADATA_FILTERING_ISSUE.md) for a separate, unresolved AWS service-level issue specific to this path
- **`check_kb_documents.py`**: Queries a Knowledge Base directly (bypassing the agent) to verify what's actually indexed
- **`diagnose_agent.py`**: Checks agent/alias/KB configuration and runs baseline invocations without a filter
- **`debug_trace.py`**: Minimal script for dumping raw trace events during a filtered invocation
- **`README.md`**: This documentation
- **`QUICK_REFERENCE.md`**: Condensed cheat-sheet (code snippets, checklists) for day-to-day use
- **`VIDEO_METADATA_FILTERING_ISSUE.md`**: Status write-up of the separate, unresolved video/multimodal filtering bug

## Production Deployment

1. Tag all documents with appropriate metadata
2. Upload documents and `.metadata.json` files to S3
3. Sync data sources in all Knowledge Bases
4. Configure agent with all required KBs in console
5. Use `sessionState` with metadata filters at invocation time
6. Apply same filter to ALL KBs in sessionState configuration

## AWS Resources Used

- **Agent ID**: `YOURAGENTID`
- **Alias ID**: `YOURALIASID`
- **Knowledge Bases**:
  - `YOURKBID1` - KB with metadata-tagged documents
  - `YOURKBID2` - Additional KB for testing
- **S3 Bucket**: `your-kb-data-bucket`
- **Region**: `us-east-1`
- **Model**: `anthropic.claude-3-sonnet-20240229-v1:0`

## Troubleshooting

### Documents Don't Have Metadata in Trace

**Cause**: Metadata files not uploaded or data source not synced

**Solution**:

1. Verify `.metadata.json` files exist in S3
2. Check metadata file format (must have `metadataAttributes` wrapper)
3. Sync data source in AWS Console
4. Wait for sync to complete before testing

### Filter Not Working (Still Getting All Documents)

**Cause**: Filter not applied to all configured KBs

**Solution**: Ensure `sessionState.knowledgeBaseConfigurations` includes ALL KB IDs configured in your agent

### ValidationException: Missing knowledgeBaseId

**Cause**: Trying to provide filter without specifying KB ID

**Solution**: Always include `knowledgeBaseId` with `retrievalConfiguration`

### Wrong Documents Returned

**Cause**: Metadata keys don't match (case-sensitive)

**Solution**: Use exact key names with matching case in filter and metadata

## Summary for Leadership

**Problem Solved**: Agent now retrieves documents from specific categories based on runtime parameters without console changes or complex logic.

**Solution Implemented**: Metadata-based document filtering using sessionState configuration.

**Benefits**:

- ✅ No console changes needed for different queries
- ✅ No hybrid approach with context-matching logic
- ✅ Direct agent invocation with full agent capabilities
- ✅ Clean, maintainable code
- ✅ Scalable to multiple document categories

**Implementation Complexity**: LOW - Only requires metadata tagging during upload

**Performance Impact**: NONE - Filtering happens during vector search

**Production Ready**: YES

## Judgment calls

- Deleted `SUMMARY.md` and `knowledge_base_filtering_technique.md` (a "JIRA ticket update" write-up) — both were near-total duplicates of this same investigation (identical test results, code examples, operator list, and "what didn't work" findings) written for different audiences. This README's own "Summary for Leadership" section above already covers the same ground, so nothing unique was lost. `VIDEO_METADATA_FILTERING_ISSUE.md` referenced them under two *different*, never-actually-used names (`SUMMARY_FOR_LEAD.md`, `JIRA_UPDATE.md`) in its own deliverables list — those dangling references were fixed too.
- `invoke_agent_video.py` had a real, confirmed bug: its event-processing loop duplicated the trace-extraction and response-chunk-handling logic verbatim, so every run of this script double-counted retrieved documents and doubled the printed/returned response text. The duplicate block was removed.
- `upload_docs_with_metadata.py` didn't actually implement the metadata approach the rest of this project documents and claims is verified working: it set S3 object-level `Metadata=` headers with hyphenated keys (`document-type`), rather than uploading a separate `<key>.metadata.json` sidecar file wrapped in `metadataAttributes` with camelCase keys — exactly the format this README's own "Critical Rules" section says is required. Rewritten to upload the sidecar file correctly.
- `debug_trace.py` referenced `event_num` in its `except` block, but the variable was only initialized inside the `try` block *after* the one line that could itself raise (`client.invoke_agent(**request)`) — so a failure on that specific call would have raised a masking `NameError` instead of printing the actual error. Moved the initialization above the `try`.
- All seven `.py` files were formatted with `black`; `pyproject.toml`/`uv.lock` needed no changes (`uv sync` already worked cleanly).
