# Business Analyst AI Agent

🌐 **[Try the Live Demo → hanzheng0613.github.io/ai-agent-project](https://hanzheng0613.github.io/ai-agent-project)**

> A production-style multi-agent AI system that answers complex business questions by autonomously routing to specialized sub-agents, querying a real PostgreSQL database, running calculations, and searching the web — with full tool-call tracing visible in the UI.

---

## Architecture

```
User question
      ↓
Supervisor Agent (Claude Haiku 4.5)
  SUPERVISOR_ROUTER pattern
      ├──► Finance Sub-Agent
      │         ├── db_lookup → RDS PostgreSQL
      │         └── calculator
      └──► Research Sub-Agent
                └── web_search → DuckDuckGo API
      ↓
FastAPI (AWS Lambda + API Gateway)
      ↓
Live frontend (GitHub Pages)
```

## Tech Stack

| Layer | Technology |
|---|---|
| AI orchestration | AWS Bedrock Agents — multi-agent SUPERVISOR_ROUTER |
| Reasoning model | Claude Haiku 4.5 (`us.anthropic.claude-haiku-4-5-20251001-v1:0`) |
| Tool execution | AWS Lambda (Python 3.12) |
| Tool definitions | OpenAPI 3.0 action group schemas |
| Database | Amazon RDS PostgreSQL (`db.t4g.micro`) |
| API layer | FastAPI + Mangum (serverless) |
| API Gateway | AWS API Gateway (CORS enabled) |
| Frontend | HTML/JS hosted on GitHub Pages |
| CI/CD | GitHub Actions — auto-deploys Lambdas on push to main |
| IAM | Least-privilege roles — separate roles for agent, Lambda, and collaboration |

---

## Live Demo

🌐 **[hanzheng0613.github.io/ai-agent-project](https://hanzheng0613.github.io/ai-agent-project)**

The frontend shows the agent's full reasoning chain — which tools were called, in what order, with result previews — before displaying the final answer.

**API endpoint (for developers):**
```
POST https://h4fuklglb5.execute-api.us-east-1.amazonaws.com/prod/ask
Content-Type: application/json

{"question": "What was Q1 2024 revenue broken down by product?"}
```

**Example questions to try:**
- "What was Q1 2024 revenue broken down by product?" → finance sub-agent → PostgreSQL query
- "What are the latest SaaS revenue growth trends?" → research sub-agent → web search
- "How does our Q4 2024 revenue compare to industry benchmarks?" → both agents chained

---

## Multi-Agent System

This project uses AWS Bedrock's **SUPERVISOR_ROUTER** collaboration pattern — three agents working together:

| Agent | ID | Role | Tools |
|---|---|---|---|
| `supervisor-agent` | `SLRJHEY4NB` | Routes questions to specialists | None (orchestrator only) |
| `finance-sub-agent` | `SNCZZ9YFGT` | Sales data and calculations | `db_lookup`, `calculator` |
| `research-sub-agent` | `28WMQPOJDH` | Web research and benchmarks | `web_search` |

The supervisor autonomously decides which sub-agent(s) to invoke based on the question. Complex questions trigger both agents and synthesize results.

---

## Database Schema

Real PostgreSQL database on Amazon RDS with a normalized relational schema:

```sql
quarters  (id, period, year, quarter)
regions   (id, name)
products  (id, name, category)
sales     (id, quarter_id, region_id, product_id, revenue, units_sold)
```

6 quarters of data (Q1 2024 – Q2 2025), 3 products, 3 regions — enabling rich multi-dimensional queries that were impossible with the original hardcoded dict.

---

## Project Structure

```
ai-agent-project/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD — auto-deploys Lambdas on push
├── lambda_functions/
│   ├── calculator.py           # Evaluates math expressions safely
│   ├── db_lookup.py            # Queries RDS PostgreSQL with joins
│   └── web_search.py           # DuckDuckGo instant answer API
├── docs/
│   └── index.html              # Live demo frontend (GitHub Pages)
├── invoke_agent.py             # Calls Bedrock Agent with trace enabled
├── app.py                      # FastAPI wrapper + Mangum Lambda handler
├── measure_metrics.py          # Metrics validation (8/8 queries, 4.44s avg)
├── agent_schema_*.json         # OpenAPI schemas for each action group
├── .env                        # AWS credentials + agent IDs (not committed)
└── requirements.txt
```

---

## CI/CD Pipeline

GitHub Actions automatically rebuilds and redeploys all 4 Lambda functions on every push to `main` that touches `lambda_functions/`, `app.py`, or `invoke_agent.py`:

```
git push origin main
      ↓
GitHub Actions triggers
      ↓
Builds Linux-compatible packages (manylinux2014_x86_64)
      ↓
Deploys: agent-db_lookup, agent-calculator, agent-web_search, business-analyst-api
      ↓
Live in ~2 minutes
```

No manual zip, no manual upload — push code and it's live.

---

## Setup

### Prerequisites
- Python 3.11+
- AWS CLI configured (`aws configure`)
- AWS account with Bedrock access in `us-east-1`
- PostgreSQL client (`psql`) for database setup

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Provision AWS resources

```bash
# Create IAM roles
aws iam create-role --role-name BedrockAgentRole \
  --assume-role-policy-document file://trust-policy.json
aws iam attach-role-policy --role-name BedrockAgentRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# Deploy Lambda tools
for tool in calculator db_lookup web_search; do
  cd lambda_functions && zip ${tool}.zip ${tool}.py && cd ..
  aws lambda create-function \
    --function-name agent-${tool} \
    --runtime python3.12 \
    --role arn:aws:iam::<ACCOUNT_ID>:role/AgentLambdaRole \
    --handler ${tool}.lambda_handler \
    --zip-file fileb://lambda_functions/${tool}.zip \
    --timeout 10 --region us-east-1
done
```

### 3. Set up RDS PostgreSQL

```bash
aws rds create-db-instance \
  --db-instance-identifier business-analyst-db \
  --db-instance-class db.t4g.micro \
  --engine postgres \
  --engine-version 16.3 \
  --master-username <username> \
  --master-user-password <password> \
  --allocated-storage 20 \
  --publicly-accessible \
  --no-multi-az \
  --backup-retention-period 0 \
  --region us-east-1
```

Connect and run the schema in `schema.sql` to create tables and seed data.

### 4. Create multi-agent system

```bash
# Create supervisor agent
SUPERVISOR_ID=$(aws bedrock-agent create-agent \
  --agent-name supervisor-agent \
  --agent-resource-role-arn arn:aws:iam::<ACCOUNT_ID>:role/BedrockAgentRole \
  --foundation-model us.anthropic.claude-haiku-4-5-20251001-v1:0 \
  --agent-collaboration SUPERVISOR_ROUTER \
  --region us-east-1 \
  --query "agent.agentId" --output text)

# Associate sub-agents
aws bedrock-agent associate-agent-collaborator \
  --agent-id $SUPERVISOR_ID --agent-version DRAFT \
  --agent-descriptor '{"aliasArn":"arn:aws:bedrock:us-east-1:<ACCOUNT_ID>:agent-alias/<FINANCE_ID>/<FINANCE_ALIAS>"}' \
  --collaborator-name "finance-sub-agent" \
  --collaboration-instruction "Use for sales data, revenue, calculations" \
  --region us-east-1

aws bedrock-agent associate-agent-collaborator \
  --agent-id $SUPERVISOR_ID --agent-version DRAFT \
  --agent-descriptor '{"aliasArn":"arn:aws:bedrock:us-east-1:<ACCOUNT_ID>:agent-alias/<RESEARCH_ID>/<RESEARCH_ALIAS>"}' \
  --collaborator-name "research-sub-agent" \
  --collaboration-instruction "Use for web search, industry trends, benchmarks" \
  --region us-east-1

aws bedrock-agent prepare-agent --agent-id $SUPERVISOR_ID --region us-east-1
```

### 5. Configure environment

```bash
# .env
AWS_REGION=us-east-1
BEDROCK_AGENT_ID=<supervisor-agent-id>
BEDROCK_AGENT_ALIAS_ID=<supervisor-alias-id>
DB_HOST=<rds-endpoint>
DB_NAME=postgres
DB_USER=<username>
DB_PASSWORD=<password>
DB_PORT=5432
```

### 6. Run locally

```bash
python invoke_agent.py
# or
uvicorn app:app --reload --port 8000
```

---

## Metrics

Validated via `measure_metrics.py`:

- **8/8 queries answered correctly**
- **4.44s average end-to-end response latency**
- **3+ tool calls chained autonomously per complex query**
- **Multi-agent routing validated** across finance-only, research-only, and combined queries

---

## Key Design Decisions

- **SUPERVISOR_ROUTER pattern** — supervisor routes to the best specialist rather than synthesizing everything itself, keeping responses faster and more accurate
- **One action group per Lambda** — each tool is isolated, independently deployable, and easy to extend
- **OpenAPI schema descriptions drive tool selection** — the LLM reads `description` fields to decide which tool to call; clear descriptions directly improve accuracy
- **Normalized PostgreSQL schema** — 4 joined tables enable product/region/quarter breakdowns impossible with a flat dict
- **CORS on API Gateway** — allows the GitHub Pages frontend to call the Lambda endpoint from the browser
- **enableTrace=True** — exposes the full reasoning chain (tool calls, parameters, results) for observability
- **CI/CD via GitHub Actions** — push to main auto-deploys all Lambdas, no manual steps
- **IAM least-privilege** — separate roles for agent execution, Lambda execution, and agent collaboration

---

## Possible Extensions

- Add more sub-agents (HR analyst, operations analyst) under the same supervisor
- Replace DuckDuckGo with a premium search API (Tavily, Serper) for better research results
- Add Bedrock Guardrails for content filtering and PII redaction
- Persist tool-call traces to DynamoDB for analytics and audit logging
- Add Bedrock Knowledge Base connecting Project 1's RAG chatbot as a document retrieval tool
