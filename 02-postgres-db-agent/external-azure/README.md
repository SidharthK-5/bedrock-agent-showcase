# Bedrock Agent with External PostgreSQL Database

> **Status note:** This project was originally built and verified against a classic Amazon Bedrock Agent connected to a real, externally-hosted Azure PostgreSQL Flexible Server, in a different AWS account/engagement no longer accessible to this repo's maintainer. It's preserved here as reference code — but it has not been (and currently cannot be) re-deployed or re-tested in this sandbox, since AWS no longer allows new accounts to create classic Bedrock Agents. The real database hostname and credentials that were originally hardcoded as a fallback default in `main.py` and documented in this README and `SETUP_GUIDE.md` have been replaced with placeholders.
>
> See `../README.md` for how this fits into the "one pattern, three targets" layout of `02-postgres-db-agent/`, and see `SQLALCHEMY_MIGRATION.md` for the real SQLAlchemy 1.4 → 2.0 migration story from original development.

A complete solution for creating an Amazon Bedrock Agent that connects to external PostgreSQL databases (Azure Postgres Flexible Server). The agent can dynamically discover database schemas and intelligently route queries to appropriate tables.

## Features

- **Dynamic Schema Discovery**: Automatically retrieves and understands database structure
- **Intelligent Query Routing**: Maps natural language queries to relevant database tables
- **Flexible SQL Execution**: Supports both natural language and custom SQL queries
- **Azure PostgreSQL Compatible**: Designed for Azure Postgres Flexible Server
- **AWS Lambda Ready**: Pre-configured for AWS Lambda deployment

## Quick Start

### 1. Build the Lambda Deployment Package

```bash
chmod +x build_lambda.sh
./build_lambda.sh
```

This creates `lambda_deployment.zip` ready for AWS Lambda.

### 2. Deploy to AWS Lambda

1. Create a Lambda function with Python 3.11+
2. Upload `lambda_deployment.zip`
3. Set handler to `main.lambda_handler`
4. Configure environment variable `DB_URI` with your PostgreSQL connection string

### 3. Create Bedrock Agent

1. Create a new Bedrock Agent in AWS Console
2. Add an Action Group using `bedrock_agent_schema.json`
3. Link the Action Group to your Lambda function
4. Test your agent!

## Project Structure

```
.
├── main.py                      # Lambda handler and main entry point
├── db_connector.py              # PostgreSQL connection and schema introspection
├── query_router.py              # Query analysis and routing logic
├── bedrock_agent_schema.json    # OpenAPI schema for Bedrock Agent
├── schema.sql                   # Optional: employees/projects schema + seed data for a scratch DB
├── requirements.txt             # Python dependencies
├── build_lambda.sh              # Build script (Linux/Mac)
├── build_lambda.bat             # Build script (Windows)
├── SETUP_GUIDE.md              # Complete step-by-step setup guide
└── README.md                   # This file
```

## API Operations

The agent supports three main operations:

### 1. Get Schema
Retrieves the complete database schema including all tables, columns, and data types.

**Example Query:** "Show me the database schema"

### 2. Query Database
Accepts natural language queries and automatically routes them to relevant tables.

**Example Query:** "Show me all employees in the database"

### 3. Execute SQL
Executes custom SQL queries for advanced operations.

**Example Query:** "Execute: SELECT * FROM projects WHERE status = 'active'"

## Database Connection

The application connects to PostgreSQL using SQLAlchemy with the psycopg3
driver, so the connection URI must include the `+psycopg` driver
specification (see [`MIGRATION_QUICK_REF.md`](./MIGRATION_QUICK_REF.md#connection-uri)
for why `postgresql://` alone isn't enough):

```
postgresql+psycopg://username:password@host:port/database
```

### Example Configuration

Set the `DB_URI` environment variable in Lambda:

```bash
DB_URI=postgresql+psycopg://youruser:yourpassword@your-server.postgres.database.azure.com/yourdatabase
```

Since this agent dynamically discovers whatever schema is already on the
database it's pointed at, it works against any existing Postgres database -
you don't need to create tables for it. If you want to try it against a
scratch database using the same sample `employees`/`projects` schema as the
`docker-local` and `aws-rds` subprojects (and this README's own examples),
run [`schema.sql`](./schema.sql) against it first.

> **Note:** Special characters in passwords must be URL-encoded.

## Prerequisites

- Python 3.11 or higher
- AWS Account with Bedrock and Lambda access
- PostgreSQL database (Azure Postgres Flexible Server)
- Network connectivity from AWS Lambda to your database

## Detailed Setup

For complete step-by-step instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md)

The setup guide includes:
- IAM role configuration
- Lambda function setup
- Bedrock Agent creation
- Network configuration
- Security best practices
- Troubleshooting tips

## Architecture

```
User Query
    ↓
Amazon Bedrock Agent
    ↓
AWS Lambda Function
    ├── main.py (Handler)
    ├── db_connector.py (Database Operations)
    └── query_router.py (Query Analysis)
    ↓
PostgreSQL Database (Azure)
```

## Security Considerations

### Production Recommendations

1. **Use AWS Secrets Manager** for database credentials
2. **Enable VPC** for Lambda if database is in private network
3. **Use SSL/TLS** for database connections
4. **Implement IAM roles** with least privilege access
5. **Enable CloudWatch Logs** for monitoring
6. **Use read-only database user** for query operations

### Environment Variables

- `DB_URI`: PostgreSQL connection string (use Secrets Manager in production)

## Development

### Local Testing

Run the Lambda handler locally:

```bash
python main.py
```

This executes a test query against the configured database.

### Dependencies

Core dependencies:
- `sqlalchemy`: SQL toolkit and engine used by `db_connector.py`
- `psycopg[binary]`: PostgreSQL adapter (psycopg3 — see [`SQLALCHEMY_MIGRATION.md`](./SQLALCHEMY_MIGRATION.md) for why this replaced `psycopg2-binary`)
- `boto3`: AWS SDK for Python

## Troubleshooting

### Common Issues

**Lambda Timeout**
- Increase timeout in Lambda configuration (recommended: 30-60 seconds)

**Connection Failed**
- Verify database URI and credentials
- Check network connectivity (VPC, security groups, firewall)
- Ensure Azure PostgreSQL allows connections from AWS IP ranges

**Package Too Large**
- Upload via S3 if package exceeds 50MB
- Consider using Lambda Layers for dependencies

**Schema Not Loading**
- Verify database user has permissions to query information_schema
- Check CloudWatch Logs for detailed error messages

For more troubleshooting tips, see [SETUP_GUIDE.md](SETUP_GUIDE.md#troubleshooting)

## Examples

### Example 1: Get Schema
```
User: "What tables are in the database?"
Agent: [Retrieves schema] "The database contains the following tables..."
```

### Example 2: Natural Language Query
```
User: "Show me active projects"
Agent: [Finds projects table] "Here are the active projects from the projects table..."
```

### Example 3: Custom SQL
```
User: "Run this query: SELECT COUNT(*) FROM employees WHERE department = 'Engineering'"
Agent: [Executes query] "Query returned: 2 employees in the Engineering department"
```

## Limitations

- Query routing is keyword-based (can be enhanced with LLM-based analysis)
- Limited to 100 rows per query by default (configurable)
- No built-in query caching (can be added)
- Single database connection per invocation

## Future Enhancements

- [ ] Add query result caching
- [ ] Implement LLM-based query analysis
- [ ] Support multiple database connections
- [ ] Add query optimization hints
- [ ] Implement result pagination
- [ ] Add data visualization capabilities
- [ ] Support for stored procedures

## License

This project is provided as-is for educational and commercial use.

## Support

For issues, questions, or contributions:
1. Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions
2. Review [Troubleshooting](#troubleshooting) section
3. Check AWS Bedrock and Lambda documentation
4. Review CloudWatch Logs for error details

## Acknowledgments

Built for Amazon Bedrock Agents with support for Azure PostgreSQL Flexible Server.

---

**Version:** 1.0.0  
**Last Updated:** December 3, 2025
