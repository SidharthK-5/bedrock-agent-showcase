# Quick Reference: Metadata Filtering

## Basic Usage

```python
from invoke_agent import invoke_agent_with_metadata_filter, create_metadata_filter

# Simple filter
filter = create_metadata_filter('equals', 'category', 'hr')

result = invoke_agent_with_metadata_filter(
    agent_id='YOUR_AGENT_ID',
    agent_alias_id='YOUR_ALIAS_ID',
    prompt='Your question here',
    metadata_filter=filter,
    kb_ids=['KB1', 'KB2']  # ALL KBs in your agent!
)

print(result['response'])
```

## Common Filters

```python
# Single category
{'equals': {'key': 'category', 'value': 'hr'}}

# Multiple categories (OR)
{'in': {'key': 'category', 'value': ['hr', 'technical']}}

# Year range
{'greaterThanOrEquals': {'key': 'year', 'value': '2024'}}

# AND combination
{
    'andAll': [
        {'equals': {'key': 'category', 'value': 'hr'}},
        {'equals': {'key': 'year', 'value': '2025'}}
    ]
}

# OR combination
{
    'orAll': [
        {'equals': {'key': 'category', 'value': 'hr'}},
        {'equals': {'key': 'documentType', 'value': 'policy-info'}}
    ]
}
```

## Metadata File Format

**File**: `document.pdf.metadata.json`

```json
{
  "metadataAttributes": {
    "category": "hr",
    "documentType": "policy-info",
    "year": "2025"
  }
}
```

## Checklist

**Document Upload**:

- [ ] Create `.metadata.json` file for each document
- [ ] Use `metadataAttributes` wrapper
- [ ] Use camelCase keys (not kebab-case)
- [ ] Upload to same S3 location as document
- [ ] Sync data source in AWS Console

**Agent Invocation**:

- [ ] Include metadata filter in sessionState
- [ ] Specify ALL KB IDs configured in agent
- [ ] Use correct metadata key names (case-sensitive)

## Troubleshooting

**No filtering happening?**

- Check if filter is applied to ALL KBs in agent
- Verify metadata exists on documents (enable trace)
- Confirm data source is synced

**Wrong documents returned?**

- Verify metadata key names match exactly (case-sensitive)
- Check metadata file format (needs `metadataAttributes` wrapper)

**ValidationException?**

- Ensure `knowledgeBaseId` is provided with filter
- Verify KB IDs are correct for your agent alias

## AWS Resources

- **Region**: us-east-1
- **Agent**: YOURAGENTID
- **Alias**: YOURALIASID
- **KBs**: YOURKBID1, YOURKBID2
- **Bucket**: your-kb-data-bucket

## Files

- `invoke_agent.py` - Production code
- `test_metadata_with_console_kbs.py` - Test suite
- `upload_docs_with_metadata.py` - Upload script
- `README.md` - Full documentation
