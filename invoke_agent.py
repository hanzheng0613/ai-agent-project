import boto3
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

AGENT_ID = os.getenv("BEDROCK_AGENT_ID")        # from console
AGENT_ALIAS_ID = os.getenv("BEDROCK_AGENT_ALIAS_ID")

def ask_agent(question: str, session_id: str = None):
    session_id = session_id or str(uuid.uuid4())

    response = client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        inputText=question,
    )

    # Response is a stream of events - concatenate the text chunks
    answer = ""
    for event in response["completion"]:
        if "chunk" in event:
            answer += event["chunk"]["bytes"].decode("utf-8")

    return answer, session_id

if __name__ == "__main__":
    answer, sid = ask_agent(
        "What was the revenue growth from Q1 2024 to Q4 2024 in percent?"
    )
    print("Agent:", answer)
