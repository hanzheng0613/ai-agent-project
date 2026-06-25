## Live Demo

🌐 **[Try it live → hanzheng0613.github.io/ai-agent-project](https://hanzheng0613.github.io/ai-agent-project)**

Ask the agent business questions directly in your browser — no setup required.

**Example questions to try:**
- "What was the revenue growth from Q1 2024 to Q4 2024?"
- "What is 15% of Q4 2024 revenue?"
- "Compare Q2 and Q3 2024 revenue"
- "What was the total revenue across all 4 quarters of 2024?"

**API endpoint (for developers):**
POST https://h4fuklglb5.execute-api.us-east-1.amazonaws.com/prod/ask

Content-Type: application/json
{"question": "What was Q3 2024 revenue?"}


# Business Analyst AI Agent

An autonomous AI agent built on **AWS Bedrock Agents** that answers business questions by reasoning step-by-step and calling tools — a database lookup, a calculator, and a web search — to gather information and compute answers.

This project demonstrates **agentic AI design**: rather than a single prompt-response chatbot, the agent plans which tools to call, chains multiple tool calls together, and synthesizes a final answer grounded in real data.

## Example

**Question:**
> What was the revenue growth from Q1 2024 to Q4 2024 in percent?

**Agent's process (autonomous):**
1. Calls the sales data tool for `Q1 2024` → `$1,200,000`
2. Calls the sales data tool for `Q4 2024` → `$1,620,000`
3. Calls the calculator tool with `(1620000 - 1200000) / 1200000 * 100`
4. Synthesizes the final answer

**Response:**
> The revenue growth from Q1 2024 to Q4 2024 was **35%**.
>
> **Breakdown:**
> - Q1 2024 revenue: $1,200,000
> - Q4 2024 revenue: $1,620,000
> - Growth calculation: (($1,620,000 - $1,200,000) / $1,200,000) × 100 = 35%

## Architecture

```
User question
     │
     ▼
FastAPI (/ask endpoint)
     │
     ▼
AWS Bedrock Agent (Claude Haiku 4.5)
  │  reasons about which tool(s) to call
  │
  ├──► Lambda: sales-data-tool   → mock quarterly revenue/units database
  ├──► Lambda: calculator-tool   → evaluates math expressions
  └──► Lambda: web-search-tool   → DuckDuckGo instant answer API
     │
     ▼
Final answer returned to user (with session ID for follow-ups)
```

## Tech stack

| Component | Technology |
|---|---|
| Reasoning engine | AWS Bedrock Agents (Claude Haiku 4.5) |
| Tool execution | AWS Lambda (Python 3.12) |
| Tool definitions | OpenAPI 3.0 schemas (action groups) |
| API layer | FastAPI + Uvicorn |
| Infrastructure | AWS CLI / boto3 |
| IAM | Least-privilege roles for agent and Lambda execution |

## Project structure

```
ai-agent-project/
├── lambda_functions/
│   ├── calculator.py      # Evaluates math expressions safely
│   ├── db_lookup.py        # Returns mock quarterly sales data
│   └── web_search.py       # Searches the web via DuckDuckGo API
├── invoke_agent.py          # Core function to call the Bedrock Agent
├── app.py                    # FastAPI wrapper exposing /ask and /health
├── trust-policy.json         # IAM trust policy for the agent role
├── agent_schema_*.json       # OpenAPI schemas for each action group
├── .env                       # AWS region + agent IDs (not committed)
└── requirements.txt
```

## Setup

### Prerequisites
- Python 3.11+
- AWS CLI configured (`aws configure`)
- AWS account with Bedrock access in `us-east-1`

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Provision AWS resources

```bash
# Create IAM roles for the agent and Lambda functions
aws iam create-role --role-name BedrockAgentRole \
  --assume-role-policy-document file://trust-policy.json
aws iam attach-role-policy --role-name BedrockAgentRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

aws iam create-role --role-name AgentLambdaRole \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
aws iam attach-role-policy --role-name AgentLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Deploy the Lambda tools
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

### 3. Create the Bedrock Agent

In the AWS Console: **Bedrock → Agents → Create agent**
- Foundation model: Claude Haiku 4.5 (via inference profile `us.anthropic.claude-haiku-4-5-20251001-v1:0`)
- Add three action groups (`calculator-tool`, `sales-data-tool`, `web-search-tool`), each backed by its corresponding Lambda and an OpenAPI schema
- Save and prepare, then create an alias

Grant Bedrock permission to invoke each Lambda:

```bash
for tool in calculator db_lookup web_search; do
  aws lambda add-permission \
    --function-name agent-${tool} \
    --statement-id allow-bedrock-agent \
    --action lambda:InvokeFunction \
    --principal bedrock.amazonaws.com \
    --source-arn "arn:aws:bedrock:us-east-1:<ACCOUNT_ID>:agent/<AGENT_ID>" \
    --region us-east-1
done
```

### 4. Configure environment

```bash
# .env
AWS_REGION=us-east-1
BEDROCK_AGENT_ID=<your-agent-id>
BEDROCK_AGENT_ALIAS_ID=<your-alias-id>
```

### 5. Run

```bash
# Test directly
python invoke_agent.py

# Or run the API
uvicorn app:app --reload --port 8000
```

## API usage

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Compare Q2 and Q3 2024 revenue and tell me the percentage difference"}'
```

Interactive API docs available at `http://localhost:8000/docs`.

## Key design decisions

- **Action groups map 1:1 with Lambda functions.** Each tool (calculator, sales data, web search) is its own action group with its own OpenAPI schema and Lambda, keeping responsibilities isolated and easy to extend.
- **Tool descriptions drive tool selection.** The OpenAPI schema's `description` fields are what the LLM reads to decide which tool to call — clear, specific descriptions directly improve tool-selection accuracy.
- **Safe expression evaluation.** The calculator restricts input to numeric/operator characters before evaluating, avoiding arbitrary code execution.
- **Session-based memory.** Each request returns a `session_id`, allowing follow-up questions to maintain conversational context via Bedrock's built-in session memory.

## Possible extensions

- Persist tool-call logs to DynamoDB for observability and analytics
- Replace the mock sales database with a real RDS or DynamoDB table
- Add a Streamlit or React frontend for non-technical demo use
- Containerize and deploy the FastAPI app to ECS Fargate or AWS Lambda for an always-on endpoint


