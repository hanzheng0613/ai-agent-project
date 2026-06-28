import json
import os
import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        port=int(os.environ.get("DB_PORT", 5432)),
        connect_timeout=5,
        sslmode="require"
    )

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
    period = parameters.get("period", "").strip()

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if period:
            cur.execute("""
                SELECT q.period, p.name, p.category, r.name, s.revenue, s.units_sold
                FROM sales s
                JOIN quarters q ON s.quarter_id = q.id
                JOIN products p ON s.product_id = p.id
                JOIN regions r ON s.region_id = r.id
                WHERE q.period = %s
                ORDER BY s.revenue DESC
            """, (period,))
            rows = cur.fetchall()

            if not rows:
                data = {"error": f"No data found for {period}"}
            else:
                total_revenue = sum(r[4] for r in rows)
                total_units = sum(r[5] for r in rows)
                products = [
                    {"product": r[1], "category": r[2], "revenue": float(r[4]), "units_sold": r[5]}
                    for r in rows
                ]
                data = {
                    "period": period,
                    "region": rows[0][3],
                    "total_revenue": float(total_revenue),
                    "total_units_sold": total_units,
                    "breakdown_by_product": products
                }
        else:
            cur.execute("""
                SELECT q.period, SUM(s.revenue), SUM(s.units_sold)
                FROM sales s
                JOIN quarters q ON s.quarter_id = q.id
                GROUP BY q.period, q.year, q.quarter
                ORDER BY q.year, q.quarter
            """)
            rows = cur.fetchall()
            data = {
                "all_quarters": [
                    {"period": r[0], "total_revenue": float(r[1]), "total_units_sold": r[2]}
                    for r in rows
                ]
            }

        cur.close()
        conn.close()

    except Exception as e:
        print("DB ERROR:", str(e))
        data = {"error": str(e)}

    response_body = {"application/json": {"body": json.dumps(data)}}

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
