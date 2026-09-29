# Architecture Diagram - Bedrock Agent with Local Database

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                               │
│                                                                 │
│  ┌──────────────────┐                                           │
│  │  Amazon Bedrock  │                                           │
│  │     Agent        │                                           │
│  │                  │                                           │
│  │  • Claude Model  │                                           │
│  │  • NL Interface  │                                           │
│  │  • Action Groups │                                           │
│  └────────┬─────────┘                                           │
│           │ HTTPS                                               │
│           │ Invokes                                             │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │  AWS Lambda      │                                           │
│  │  Function        │                                           │
│  │                  │                                           │
│  │  • DB Proxy      │                                           │
│  │  • Query Builder │                                           │
│  │  • psycopg2      │                                           │
│  └────────┬─────────┘                                           │
│           │ TCP/5432                                            │
│           │ via Tunnel                                          │
└───────────┼─────────────────────────────────────────────────────┘
            │
            │ Internet
            │
┌───────────▼──────────────────────────────────────────────────────┐
│                    Local Machine                                 │
│                                                                  │
│  ┌──────────────────┐                                            │
│  │  Localtunnel     │  (Optional - for dev/testing)              │
│  │  or VPN Service  │                                            │
│  │                  │                                            │
│  │  • Public URL    │                                            │
│  │  • Port Forward  │                                            │
│  └────────┬─────────┘                                            │
│           │ localhost:5432                                       │
│           ▼                                                      │
│  ┌──────────────────┐                                            │
│  │  Docker          │                                            │
│  │  Container       │                                            │
│  │                  │                                            │
│  │  PostgreSQL 15   │                                            │
│  │  • bedrockdb     │                                            │
│  │  • employees     │                                            │
│  │  • projects      │                                            │
│  └──────────────────┘                                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Request Flow

### User Query Flow

```
1. User Input
   │
   ├─> "List all employees in Engineering"
   │
   ▼
2. Bedrock Agent
   │
   ├─> Parses natural language
   ├─> Identifies intent: query employees
   ├─> Determines action: GET /employees
   ├─> Extracts parameters: department=Engineering
   │
   ▼
3. Lambda Function (via API Gateway)
   │
   ├─> Receives event from Bedrock
   ├─> Validates parameters
   ├─> Builds SQL query
   │   └─> SELECT * FROM employees WHERE department = 'Engineering'
   │
   ▼
4. Database (via Tunnel)
   │
   ├─> Executes query
   ├─> Returns results
   │   └─> [{id: 1, name: "John Doe", ...}, ...]
   │
   ▼
5. Lambda Response
   │
   ├─> Formats results as JSON
   ├─> Returns to Bedrock Agent
   │
   ▼
6. Bedrock Agent Response
   │
   ├─> Converts JSON to natural language
   └─> "I found 2 employees in the Engineering department:
       1. John Doe - john.doe@example.com - Salary: $85,000
       2. Bob Johnson - bob.johnson@example.com - Salary: $95,000"
```

## Component Breakdown

### 1. Local Database (Docker Container)

```
┌────────────────────────────────────────┐
│  PostgreSQL Container                  │
├────────────────────────────────────────┤
│  Port: 5432                            │
│  Database: bedrockdb                   │
│  User: dbuser                          │
│                                        │
│  Tables:                               │
│  ┌─────────────────┐                   │
│  │  employees      │                   │
│  ├─────────────────┤                   │
│  │  • id           │                   │
│  │  • name         │                   │
│  │  • email        │                   │
│  │  • department   │                   │
│  │  • salary       │                   │
│  │  • hire_date    │                   │
│  └─────────────────┘                   │
│                                        │
│  ┌─────────────────┐                   │
│  │  projects       │                   │
│  ├─────────────────┤                   │
│  │  • id           │                   │
│  │  • name         │                   │
│  │  • description  │                   │
│  │  • budget       │                   │
│  │  • status       │                   │
│  └─────────────────┘                   │
└────────────────────────────────────────┘
```

### 2. Lambda Function

```
┌──────────────────────────────────────────┐
│  Lambda Function                         │
├──────────────────────────────────────────┤
│  Runtime: Python 3.11                    │
│  Handler: lambda_function.lambda_handler │
│  Timeout: 30s                            │
│  Memory: 256 MB                          │
│                                          │
│  Functions:                              │
│  ├─ get_employees()                      │
│  ├─ get_employee_by_id()                 │
│  ├─ add_employee()                       │
│  ├─ get_projects()                       │
│  └─ get_department_summary()             │
│                                          │
│  Environment Variables:                  │
│  ├─ DB_HOST                              │
│  ├─ DB_PORT                              │
│  ├─ DB_NAME                              │
│  ├─ DB_USER                              │
│  └─ DB_PASSWORD                          │
└──────────────────────────────────────────┘
```

### 3. Bedrock Agent

```
┌────────────────────────────────────────────┐
│  Bedrock Agent                             │
├────────────────────────────────────────────┤
│  Model: Claude 3 Sonnet                    │
│  Name: employee-database-agent             │
│                                            │
│  Action Group: database-actions            │
│  ├─ GET /employees                         │
│  ├─ GET /employees/{id}                    │
│  ├─ POST /employees                        │
│  ├─ GET /projects                          │
│  └─ GET /departments/summary               │
│                                            │
│  Instructions:                             │
│  "You are an AI assistant that helps       │
│   users query an employee database..."     │
└────────────────────────────────────────────┘
```

## Network Options Comparison

### Option 1: Localtunnel (Development)

```
Local DB ─┬─> localhost:5432
          │
          └─> Localtunnel Client
              │
              ├─> Internet
              │
              └─> https://your-name.loca.lt
                  │
                  └─> AWS Lambda can access
```

**Pros:**

- Free
- Easy setup
- Good for testing

**Cons:**

- Not reliable for production
- Can be slow
- Security concerns

### Option 2: AWS RDS (Production)

```
Local DB (Docker) ─┬─> Export data
                   │
                   └─> Import to RDS
                       │
RDS Instance <─────────┘
(Direct AWS access)
│
└─> AWS Lambda (same VPC)
```

**Pros:**

- Production-ready
- Fast & reliable
- Secure (VPC)
- Managed service

**Cons:**

- Costs ~$15-30/month
- Migration required

### Option 3: VPN/Direct Connect (Enterprise)

```
Local Network ─┬─> Site-to-Site VPN
               │   or Direct Connect
               │
               └─> AWS VPC
                   │
                   └─> Lambda in VPC
                       │
                       └─> Can access local DB
```

**Pros:**

- Secure
- Direct connection
- Best for enterprise

**Cons:**

- Complex setup
- Higher cost
- Requires networking knowledge

## Data Flow Example: "Add Employee"

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ "Add employee: Jane Smith, jane@example.com, Sales, $75000, 2024-01-15"
       ▼
┌──────────────────┐
│  Bedrock Agent   │
├──────────────────┤
│ Parses request:  │
│ - Action: POST   │
│ - Path: /emp...  │
│ - Body: {        │
│   name: "Jane"   │
│   email: "jane@" │
│   dept: "Sales"  │
│   salary: 75000  │
│   hire: "2024"   │
│ }                │
└──────┬───────────┘
       │ HTTP Request
       ▼
┌──────────────────┐
│  Lambda Func     │
├──────────────────┤
│ add_employee():  │
│                  │
│ SQL:             │
│ INSERT INTO      │
│   employees      │
│ VALUES (...)     │
└──────┬───────────┘
       │ TCP Connection
       ▼
┌──────────────────┐
│  PostgreSQL      │
├──────────────────┤
│ Executes INSERT  │
│ Returns ID: 6    │
└──────┬───────────┘
       │ Result
       ▼
┌──────────────────┐
│  Lambda Func     │
├──────────────────┤
│ Returns:         │
│ {                │
│   new_employee:  │
│   {id: 6, ...}   │
│   status: "ok"   │
│ }                │
└──────┬───────────┘
       │ JSON Response
       ▼
┌──────────────────┐
│  Bedrock Agent   │
├──────────────────┤
│ "Successfully    │
│ added Jane Smith │
│ to Sales dept    │
│ with ID 6"       │
└──────┬───────────┘
       │
       ▼
┌──────────────┐
│    User      │
└──────────────┘
```

## Security Layers

```
┌────────────────────────────────────────────┐
│  Layer 1: API Gateway                      │
│  ├─ HTTPS only                             │
│  ├─ (Optional) API keys                    │
│  └─ (Optional) IAM auth                    │
└──────────────┬─────────────────────────────┘
               │
┌──────────────▼─────────────────────────────┐
│  Layer 2: Lambda Execution Role            │
│  ├─ Invoke permissions                     │
│  ├─ CloudWatch logging                     │
│  └─ Secrets Manager access                 │
└──────────────┬─────────────────────────────┘
               │
┌──────────────▼─────────────────────────────┐
│  Layer 3: Database Connection              │
│  ├─ Encrypted credentials                  │
│  ├─ VPC (if using RDS)                     │
│  └─ Security groups                        │
└────────────────────────────────────────────┘
```

## Monitoring & Logging

```
┌─────────────────────────────────────────────┐
│  CloudWatch Logs                            │
├─────────────────────────────────────────────┤
│                                             │
│  /aws/lambda/bedrock-agent-db-proxy         │
│  ├─ Function invocations                    │
│  ├─ Database queries                        │
│  ├─ Errors and exceptions                   │
│  └─ Performance metrics                     │
│                                             │
│  /aws/bedrock/agents/{agent-id}             │
│  ├─ User queries                            │
│  ├─ Agent responses                         │
│  └─ Action group invocations                │
│                                             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  CloudWatch Metrics                         │
├─────────────────────────────────────────────┤
│  Lambda:                                    │
│  ├─ Invocations                             │
│  ├─ Duration                                │
│  ├─ Errors                                  │
│  └─ Throttles                               │
│                                             │
│  Bedrock:                                   │
│  ├─ Request count                           │
│  ├─ Token usage                             │
│  └─ Latency                                 │
└─────────────────────────────────────────────┘
```

## Cost Breakdown

```
┌─────────────────────────────────────────────┐
│  Monthly Costs (Development)                │
├─────────────────────────────────────────────┤
│                                             │
│  Bedrock Agent                              │
│  └─ ~$2-5 for testing                       │
│                                             │
│  Lambda                                     │
│  └─ Free tier: 1M requests                  │
│                                             │
│  API Gateway                                │
│  └─ Free tier: 1M requests                  │
│                                             │
│  CloudWatch                                 │
│  └─ Free tier: 5GB logs                     │
│                                             │
│  Total: ~$2-5/month                         │
│                                             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Monthly Costs (Production with RDS)        │
├─────────────────────────────────────────────┤
│                                             │
│  Bedrock Agent                              │
│  └─ $10-50 (depends on usage)               │
│                                             │
│  Lambda                                     │
│  └─ $1-5 (after free tier)                  │
│                                             │
│  RDS (db.t3.micro)                          │
│  └─ $15-30                                  │
│                                             │
│  Data Transfer                              │
│  └─ $1-5                                    │
│                                             │
│  Total: ~$30-90/month                       │
│                                             │
└─────────────────────────────────────────────┘
```

This architecture allows your Bedrock Agent to interact with your local database through a secure, scalable proxy!
