import json

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
    expression = parameters.get("expression", "")

    try:
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Invalid characters in expression")
        result = eval(expression, {"__builtins__": {}}, {})
    except Exception as e:
        result = f"Error: {str(e)}"

    response_body = {
        "application/json": {
            "body": json.dumps({"result": str(result)})
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
