#!/bin/bash
# Quick Start Script for Bedrock Agent with Local Database

set -e  # Exit on error

echo "=========================================="
echo "Bedrock Agent Local DB - Quick Start"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${RED}❌ Please edit .env file with your AWS credentials and settings${NC}"
    echo -e "Required: AWS_REGION, AWS_ACCOUNT_ID"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo -e "${GREEN}✓${NC} Environment variables loaded"

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker is running"

# Step 1: Start Database
echo ""
echo "Step 1: Starting PostgreSQL database..."
docker-compose up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Test database connection
if docker exec -it local-postgres-db psql -U dbuser -d bedrockdb -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Database is ready"
    
    # Show sample data
    echo ""
    echo "Sample data in database:"
    docker exec -it local-postgres-db psql -U dbuser -d bedrockdb -c "SELECT COUNT(*) as employee_count FROM employees;"
    docker exec -it local-postgres-db psql -U dbuser -d bedrockdb -c "SELECT COUNT(*) as project_count FROM projects;"
else
    echo -e "${RED}❌ Database connection failed${NC}"
    exit 1
fi

# Step 2: Install Python dependencies
echo ""
echo "Step 2: Installing Python dependencies..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo -e "${YELLOW}⚠ No virtual environment found. Creating one...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate
fi

pip install -q -r requirements.txt
pip install -q boto3

echo -e "${GREEN}✓${NC} Python dependencies installed"

# Step 3: Test Lambda locally
echo ""
echo "Step 3: Testing Lambda function locally..."
if python test_agent.py local; then
    echo -e "${GREEN}✓${NC} Lambda function works locally"
else
    echo -e "${RED}❌ Lambda test failed${NC}"
    exit 1
fi

# Step 4: Remind about network access
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "Your local database is ready! Now you need to make it accessible from AWS."
echo ""
echo "Option 1: Use Localtunnel (Easiest)"
echo "  1. Install: npm install -g localtunnel"
echo "  2. Run: lt --port 5432 --subdomain YOUR-UNIQUE-NAME"
echo "  3. Update .env with tunnel URL"
echo ""
echo "Option 2: Deploy to AWS RDS (Recommended for Production)"
echo "  See STEP_BY_STEP_GUIDE.md for instructions"
echo ""
echo -e "${YELLOW}After setting up network access:${NC}"
echo "  1. Update DB_HOST in .env"
echo "  2. Run: python setup_infrastructure.py"
echo "  3. Test: python test_agent.py agent"
echo ""
echo "For detailed instructions, see: STEP_BY_STEP_GUIDE.md"
