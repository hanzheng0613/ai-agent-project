import json
import urllib.request
import urllib.parse

def extract_parameters(event):
    params = {}
    for p in event.get("parameters", []):
        params[p["name"]] = p["value"]
    request_body = event.get("requestBody", {})
    content = request_body.get("content", {})
    app_json = content.get("application/json", {})
    for p in app_json.get("properties", []):
        params[p["name"]] = p["value"]
    return params

def lambda_handler(event, context):
    print("EVENT:", json.dumps(event))

    parameters = extract_parameters(event)
    query = parameters.get("query", "")

    try:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        result = data.get("AbstractText") or "No summary available."
    except Exception as e:
        result = f"Search error: {str(e)}"

    response_body = {
        "application/json": {
            "body": json.dumps({"result": result})
        }
    }

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event["actionGroup"],
            "apiPath": event["apiPath"],
            "httpMethod": event["httpMethod"],
            "httpStatusCode": 200,
            "responseBody": response_body
        }
    }
