# JIRA Ticket Update: Metadata Filtering for Multimodal Content

**Date**: January 12, 2026  
**Updated By**: Development Team  
**Ticket Status**: BLOCKED - Pending AWS Support Investigation

---

## 📋 Current Status

### ✅ Completed Work

- **PDF Metadata Filtering**: Fully implemented and production-ready
- **Knowledge Base Setup**: Multimodal KB configured with video content and metadata
- **Testing & Validation**: Comprehensive test suite created and passing for PDF documents
- **Documentation**: Complete implementation guides and troubleshooting documentation delivered

### ⚠️ Blocked Items

- **Video Metadata Filtering via Agent**: Blocked by AWS Bedrock service issue (Internal Server Exception)

---

## 🎯 Summary

We successfully implemented runtime metadata filtering for PDF documents using AWS Bedrock Agents. The solution allows filtering Knowledge Base retrievals by document category (hr, technical, ecommerce) without requiring console configuration changes.

**However**, we encountered an Internal Server Exception when attempting to apply the same metadata filtering approach to multimodal (video/audio) content through the Bedrock Agent. Extensive testing and debugging confirmed this is an AWS service-level issue, not a problem with our implementation.

---

## ✅ What's Working

### 1. PDF Document Metadata Filtering

**Status**: ✅ **PRODUCTION READY**

Successfully filters PDF documents by category through Bedrock Agent:

- HR-related documents
- Technical documentation  
- E-commerce content

**Test Results**:

- All tests in `test_metadata_with_console_kbs.py` passing
- Zero cross-contamination between categories
- Proper attribution and source tracking

**Code Files**:

- `invoke_agent.py` - Production implementation
- `test_metadata_with_console_kbs.py` - Validation tests

### 2. Direct Knowledge Base API (Video Content)

**Status**: ✅ **WORKING**

Direct KB retrieval API successfully filters video content:

- 5 documents retrieved with `category=ecommerce` filter
- Includes `order_enquiry.mp4` video file
- All metadata attributes properly indexed

**Validation**: `check_kb_documents.py` confirms KB configuration is correct

### 3. Agent Access to Video KB (Without Filter)

**Status**: ✅ **WORKING**

Agent successfully queries multimodal KB when no metadata filter is applied:

- Video content accessible
- Agent responds appropriately
- No orchestration issues

---

## ❌ What's Blocked

### Video Content Metadata Filtering via Agent

**Status**: ❌ **BLOCKED BY AWS SERVICE ISSUE**

**Error**: `internalServerException` when agent processes metadata-filtered retrieval from multimodal KB

**Failure Point**:

```bash
1. ✅ Agent receives query
2. ✅ Claude decides to search KB YOURKBID2  
3. ✅ Agent initiates KB lookup
4. ❌ Internal Server Exception during retrieval
```

**Error Message**:

```bash
EventStreamError: An error occurred (internalServerException) 
when calling the InvokeAgent operation: Internal Server Exception
```

---

## 🔍 Investigation Summary

### Test Matrix Results

| Scenario | PDF KB | Video KB |
| -------- | ------ | -------- |
| Direct KB API + Filter | ✅ Works | ✅ Works |
| Agent + No Filter | ✅ Works | ✅ Works |
| Agent + Filter | ✅ Works | ❌ **FAILS** |

### Root Cause Analysis

Based on comprehensive testing, we've isolated the issue to:

**Component**: AWS Bedrock Agent Orchestration Layer  
**Trigger**: Combining all three conditions:

1. Agent-mediated KB retrieval (not direct API)
2. Knowledge Base contains multimodal (video/audio) content
3. sessionState includes metadata filter

**Evidence**:

- ✅ Direct KB API with filter works → Rules out KB configuration issues
- ✅ PDF filtering via agent works → Rules out filter syntax/structure issues  
- ✅ Agent without filter works → Rules out agent/KB integration issues
- ❌ Agent + video + filter fails → Isolated to this specific combination

### Configuration Verified

All configurations have been validated as correct:

**Knowledge Base**:

- KB ID: YOURKBID2 (Multimodal)
- Data Source: YOURDATASOURCEID (synced and indexed)
- Documents: 5 video-related documents with proper metadata
- Metadata format: Correct (metadataAttributes wrapper, camelCase keys)

**Agent**:

- Agent ID: YOURAGENTID
- Alias: YOURALIASID (version 4)
- Foundation Model: Claude 3.7 Sonnet
- KBs: YOURKBID2 (multimodal), YOURKBID1 (PDFs)

**Filter Structure**:

```json
{
  "equals": {
    "key": "category",
    "value": "ecommerce"
  }
}
```

---

## 🛠️ Troubleshooting Attempts

We systematically tested multiple approaches to isolate the issue:

### Attempt 1: Single KB Configuration

- Specified only YOURKBID2 in sessionState
- Result: ❌ Same error

### Attempt 2: Multiple KB Configuration  

- Included both KBs, applied filter only to video KB
- Result: ❌ Same error

### Attempt 3: Different Filter Values

- Tested various category values (hr, technical, ecommerce)
- Result: ❌ All fail with same error

### Attempt 4: Enhanced Logging & Tracing

- Added comprehensive event stream logging
- Captured full trace events before failure
- Result: Error consistently occurs during KB retrieval phase

**Conclusion**: Issue is not related to our configuration or implementation. All evidence points to AWS Bedrock Agent service limitation.

---

## 📊 Deliverables Status

### ✅ Delivered & Working

1. **Production Code**
   - `invoke_agent.py` - PDF metadata filtering implementation
   - `create_metadata_filter()` - Filter builder utility
   - `create_compound_filter()` - Complex filter support

2. **Test Suite**
   - `test_metadata_with_console_kbs.py` - Comprehensive validation tests
   - All test cases passing for PDF documents

3. **Documentation**
   - `README.md` - Complete implementation guide (includes an executive summary)
   - `QUICK_REFERENCE.md` - Usage guide

4. **Diagnostic Tools**
   - `check_kb_documents.py` - KB validation utility
   - `debug_trace.py` - Event stream analysis
   - `diagnose_agent.py` - Agent baseline testing

### ⏳ Completed But Blocked

- `invoke_agent_video.py` - Video filtering implementation (code complete, blocked by AWS issue)

---

## 💡 Available Workarounds

### Option 1: Direct KB API for Video Content (Recommended)

Use the retrieve() API directly for video content filtering while using the agent for PDF content:

```python
# For video content - use direct API
response = client.retrieve(
    knowledgeBaseId='YOURKBID2',
    retrievalQuery={'text': query},
    retrievalConfiguration={
        'vectorSearchConfiguration': {
            'filter': {'equals': {'key': 'category', 'value': 'ecommerce'}}
        }
    }
)
```

**Pros**: Works perfectly, proven in testing  
**Cons**: Bypasses agent orchestration, separate code path needed

### Option 2: Separate Agent for Video

Create a dedicated agent configured only with the multimodal KB.

**Pros**: Maintains agent orchestration benefits  
**Cons**: Requires managing multiple agents, added operational complexity

### Option 3: No Filtering for Video

Query video KB without metadata filters until AWS resolves the issue.

**Pros**: Simple, uses existing agent  
**Cons**: No category filtering, may return irrelevant results

---

## 🎫 AWS Support Ticket Status

### Ticket Raised: ✅ YES

We have escalated this issue to the AWS Bedrock support team for investigation.

**Issue Reported**:

- **Service**: AWS Bedrock
- **Component**: Agent Orchestration with Knowledge Bases
- **Problem**: Internal Server Exception when agent attempts to retrieve from Knowledge Base containing audio/video files with metadata filtering enabled

**Details Provided to AWS**:

- Complete trace logs showing error at KB lookup invocation
- Evidence that direct KB API works with same configuration
- Proof that PDF documents work fine with same filter approach
- Agent configuration and Knowledge Base setup details
- Event stream analysis showing failure point

**AWS Response**:
The AWS Bedrock team is currently investigating why the agent is unable to process Knowledge Bases with audio/video files when metadata filtering is applied through sessionState configuration. They are reviewing the orchestration layer's handling of multimodal content with retrieval filters.

**Status**: Under Investigation by AWS Team  
**Expected Timeline**: Pending AWS feedback  
**Tracking**: Monitoring for updates from AWS support

---

## 📝 Conclusion

**PDF metadata filtering is fully functional and ready for production use.** The solution successfully addresses the original requirement of runtime Knowledge Base filtering without console changes.

**Video metadata filtering is blocked by an AWS Bedrock service issue** that occurs specifically when agents attempt to process retrieval filters for multimodal Knowledge Bases. Our implementation is correct and complete; we're waiting for AWS to resolve the orchestration layer issue.

**Recommended Action**: Deploy PDF filtering immediately and use direct KB API workaround for video content until AWS resolves the agent orchestration issue.

---

## 📎 Reference Files

| File | Purpose | Status |
| ---- | ------- | ------ |
| `invoke_agent.py` | PDF filtering implementation | ✅ Production ready |
| `invoke_agent_video.py` | Video filtering implementation | ⏳ Complete, blocked by AWS |
| `test_metadata_with_console_kbs.py` | Test suite | ✅ All tests passing |
| `check_kb_documents.py` | KB validation tool | ✅ Confirms KB setup correct |
| `README.md` | Implementation guide | ✅ Complete |
| `VIDEO_METADATA_FILTERING_ISSUE.md` | This document | ✅ Current status update |

---

**For questions or additional details, please refer to the comprehensive documentation in the project repository.**
