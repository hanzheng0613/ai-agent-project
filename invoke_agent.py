import boto3
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

AGENT_ID = os.getenv("BEDROCK_AGENT_ID")
AGENT_ALIAS_ID = os.getenv("BEDROCK_AGENT_ALIAS_ID")

def extract_trace_params(action_input):
    """Safely extract parameters from trace action input."""
    try:
        request_body = action_input.get("requestBody", {})
        content = request_body.get("content", {})
        app_json = content.get("application/json", {})
        properties = app_json.get("properties", [])
        if isinstance(properties, list):
            return {p["name"]: p["value"] for p in properties}
        return {}
    except Exception:
        return {}

def ask_agent(question: str, session_id: str = None):
    session_id = session_id or str(uuid.uuid4())

    response = client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        inputText=question,
        enableTrace=True,
    )

    answer = ""
    tool_calls = []

    for event in response["completion"]:
        if "chunk" in event:
            answer += event["chunk"]["bytes"].decode("utf-8")

        if "trace" in event:
            try:
                trace = event["trace"].get("trace", {})
                orchestration = trace.get("orchestrationTrace", {})

                # Tool input — agent decided to call a tool
                tool_input = orchestration.get("invocationInput", {})
                action_input = tool_input.get("actionGroupInvocationInput", {})
                if action_input:
                    tool_name = action_input.get("actionGroupName", "unknown")
                    api_path = action_input.get("apiPath", "")
                    params = extract_trace_params(action_input)
                    tool_calls.append({
                        "tool": tool_name,
                        "action": api_path,
                        "parameters": params,
                        "status": "called"
                    })

                # Tool output — result came back
                tool_output = orchestration.get("observation", {})
                action_output = tool_output.get("actionGroupInvocationOutput", {})
                if action_output and tool_calls:
                    tool_calls[-1]["status"] = "success"
                    tool_calls[-1]["result_preview"] = str(action_output.get("text", ""))[:100]

            except Exception as e:
                print(f"Trace parse warning: {e}")
                continue

    return answer, session_id, tool_calls

if __name__ == "__main__":
    print("🤖 Business Analyst Agent ready! Type 'exit' to quit.\n")
    session_id = str(uuid.uuid4())

    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if question.lower() in ["exit", "quit", "bye"]:
            print("Agent: Goodbye!")
            break

        print("Agent: thinking...")
        answer, session_id, tool_calls = ask_agent(question, session_id)

        if tool_calls:
            print("\n🔍 Tool calls:")
            for i, t in enumerate(tool_calls, 1):
                params_str = ", ".join(f"{k}={v}" for k, v in t["parameters"].items())
                print(f"  {i}. {t['tool']}{t['action']}({params_str}) → {t['status']}")

        print(f"\nAgent: {answer}\n")
