import time
import uuid
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
AGENT_ID = os.getenv("BEDROCK_AGENT_ID")
AGENT_ALIAS_ID = os.getenv("BEDROCK_AGENT_ALIAS_ID")

TEST_CASES = [
    {
        "question": "What was the revenue growth from Q1 2024 to Q4 2024 in percent?",
        "expected_keywords": ["35", "1,200,000", "1,620,000"],
        "tools_expected": ["db_lookup", "calculator"],
    },
    {
        "question": "Compare Q2 and Q3 2024 revenue and tell me the percentage difference",
        "expected_keywords": ["1,450,000", "1,380,000", "4.83", "4.8"],
        "tools_expected": ["db_lookup", "calculator"],
    },
    {
        "question": "What is 15% of Q4 2024 revenue?",
        "expected_keywords": ["243,000", "1,620,000"],
        "tools_expected": ["db_lookup", "calculator"],
    },
    {
        "question": "Looking at Q1 2024, Q2 2024, Q3 2024, and Q4 2024, which quarter had the highest units sold and how many units was that?",
        "expected_keywords": ["Q4", "5,800"],
        "tools_expected": ["db_lookup"],
    },
    {
        "question": "What was the total revenue across all 4 quarters of 2024?",
        "expected_keywords": ["5,650,000", "5650000"],
        "tools_expected": ["db_lookup", "calculator"],
    },
    {
        "question": "What was the average quarterly revenue in 2024?",
        "expected_keywords": ["1,412,500", "1412500"],
        "tools_expected": ["db_lookup", "calculator"],
    },
    {
        "question": "What was Q1 2024 units sold?",
        "expected_keywords": ["4,500", "4500"],
        "tools_expected": ["db_lookup"],
    },
    {
        "question": "What is the revenue difference between Q2 and Q4 2024?",
        "expected_keywords": ["170,000", "170000"],
        "tools_expected": ["db_lookup", "calculator"],
    },
]

def ask_agent(question, session_id):
    response = client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        inputText=question,
    )
    answer = ""
    for event in response["completion"]:
        if "chunk" in event:
            answer += event["chunk"]["bytes"].decode("utf-8")
    return answer

def run_metrics():
    print("=" * 60)
    print("Running metrics test across all queries...")
    print("=" * 60)

    response_times = []
    accuracy_results = []
    total_queries = len(TEST_CASES)

    for i, test in enumerate(TEST_CASES, 1):
        session_id = str(uuid.uuid4())
        print(f"\nQuery {i}/{total_queries}: {test['question'][:60]}...")

        start = time.time()
        answer = ask_agent(test["question"], session_id)
        elapsed = round(time.time() - start, 2)
        response_times.append(elapsed)

        answer_lower = answer.lower().replace(",", "")
        keywords_found = sum(
            1 for kw in test["expected_keywords"]
            if kw.replace(",", "") in answer_lower
        )
        accuracy = keywords_found / len(test["expected_keywords"])
        accuracy_results.append(accuracy)

        print(f"  ✅ Response time : {elapsed}s")
        print(f"  ✅ Accuracy score: {round(accuracy * 100)}%")
        print(f"  Answer preview  : {answer[:120].strip()}...")

    avg_time = round(sum(response_times) / len(response_times), 2)
    min_time = min(response_times)
    max_time = max(response_times)
    correct = sum(1 for a in accuracy_results if a >= 0.5)

    print("\n" + "=" * 60)
    print("METRICS SUMMARY")
    print("=" * 60)
    print(f"Total queries run      : {total_queries}")
    print(f"Average response time  : {avg_time}s")
    print(f"Fastest response       : {min_time}s")
    print(f"Slowest response       : {max_time}s")
    print(f"Correct answers        : {correct}/{total_queries}")
    print("=" * 60)

if __name__ == "__main__":
    run_metrics()
