from fastapi import APIRouter, HTTPException, Request
import clickhouse_connect
import base64
import json

router = APIRouter(prefix="/reports", tags=["reports"])


def get_user_email_from_token(request: Request):
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        token = auth_header.replace("Bearer ", "")

        # Декодируем JWT payload
        payload = token.split('.')[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.b64decode(payload)
        data = json.loads(decoded)

        return data.get("email")
    except Exception:
        return None


@router.get("/{user_email}")
async def get_report(user_email: str, request: Request):
    current_email = get_user_email_from_token(request)

    if not current_email:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if current_email.lower() != user_email.lower():
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        client = clickhouse_connect.get_client(
            host="clickhouse",
            port=8123,
            database="bionicpro"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    result = client.query("""
        SELECT
            user_email,
            user_name,
            total_sessions,
            total_gestures,
            avg_confidence,
            avg_battery
        FROM reports_datamart
        WHERE user_email = %(email)s
    """, parameters={"email": user_email})

    if not result.result_rows:
        return {
            "email": user_email,
            "name": "-",
            "sessions": 0,
            "gestures": 0,
            "accuracy": 0,
            "battery": 0
        }

    row = result.result_rows[0]
    return {
        "email": row[0],
        "name": row[1] or "-",
        "sessions": row[2],
        "gestures": row[3],
        "accuracy": round(row[4], 1),
        "battery": round(row[5], 1)
    }


@router.get("/me/csv")
async def download_csv(request: Request):
    from fastapi.responses import Response
    import csv
    from io import StringIO

    current_email = get_user_email_from_token(request)
    if not current_email:
        raise HTTPException(status_code=401, detail="Not authenticated")

    client = clickhouse_connect.get_client(
        host="clickhouse",
        port=8123,
        database="bionicpro"
    )

    result = client.query("""
        SELECT
            user_email, user_name, total_sessions,
            total_gestures, avg_confidence, avg_battery
        FROM reports_datamart
        WHERE user_email = %(email)s
    """, parameters={"email": current_email})

    if not result.result_rows:
        raise HTTPException(status_code=404, detail="Report not found")

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Email", "Name", "Sessions", "Gestures", "Accuracy%", "Battery%"])
    writer.writerow(result.result_rows[0])

    return Response(
        content=output.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=report_{current_email}.csv"}
    )