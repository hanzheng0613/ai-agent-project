import json

SALES_DATA = {
    "Q1 2024": {"revenue": 1200000, "units_sold": 4500, "region": "North America"},
    "Q2 2024": {"revenue": 1450000, "units_sold": 5200, "region": "North America"},
    "Q3 2024": {"revenue": 1380000, "units_sold": 4900, "region": "North America"},
    "Q4 2024": {"revenue": 1620000, "units_sold": 5800, "region": "North America"},
}

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
    period = parameters.get("period", "")

    data = SALES_DATA.get(period, {"error": f"No data found for {period}"})

    response_body = {
        "application/json": {
            "body": json.dumps(data)
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
