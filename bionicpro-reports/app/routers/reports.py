from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import clickhouse_connect
import base64
import json
import os
import uuid
from datetime import date
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import httpx
import asyncio

router = APIRouter(prefix="/reports", tags=["reports"])

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin123")
S3_BUCKET = os.getenv("S3_BUCKET", "bionicpro-reports")
CDN_BASE_URL = os.getenv("CDN_BASE_URL", "http://localhost:8083/reports")
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8081")

s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1"
)

try:
    s3_client.create_bucket(Bucket=S3_BUCKET)
except:
    pass


async def get_user_id_from_session(request: Request):
    session_id = request.cookies.get("SESSION_ID")

    if not session_id:
        session_id = request.headers.get("X-Session-Id")
        if session_id:
            print(f"DEBUG: Got session from X-Session-Id header: {session_id[:20]}...")

    if not session_id:
        print("DEBUG: No SESSION_ID found in cookies or X-Session-Id header")
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{AUTH_URL}/auth/check",
                cookies={"SESSION_ID": session_id}
            )

            print(f"DEBUG: Auth check response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                user_id = data.get("userId")
                print(f"DEBUG: Got user_id from session: {user_id}")
                return user_id
            else:
                print(f"DEBUG: Auth check failed with status {response.status_code}")
                return None

    except httpx.TimeoutException:
        print("DEBUG: Timeout connecting to auth server")
        return None
    except Exception as e:
        print(f"DEBUG: Session check error: {str(e)}")
        return None


def generate_report_file(user_email: str, report_data: dict) -> str:
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Email", "Name", "Sessions", "Gestures", "Accuracy%", "Battery%", "Date"])
    writer.writerow([
        report_data["email"],
        report_data["name"],
        report_data["sessions"],
        report_data["gestures"],
        report_data["accuracy"],
        report_data["battery"],
        date.today().isoformat()
    ])
    return output.getvalue()


def save_report_to_s3(user_email: str, content: str) -> str:
    file_key = f"{user_email}/{date.today().isoformat()}/report.csv"

    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=file_key,
        Body=content.encode("utf-8-sig"),
        ContentType="text/csv"
    )
    return file_key


def check_report_in_s3(user_email: str) -> str or None:
    prefix = f"{user_email}/{date.today().isoformat()}/"

    try:
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=prefix,
            MaxKeys=1
        )

        if "Contents" in response and len(response["Contents"]) > 0:
            return response["Contents"][0]["Key"]
        return None
    except ClientError:
        return None


def get_report_from_clickhouse(user_email: str):
    try:
        client = clickhouse_connect.get_client(
            host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
            port=8123,
            database="bionicpro"
        )

        result = client.query("""
            SELECT
                user_email,
                user_name,
                total_sessions,
                total_gestures,
                avg_confidence,
                avg_battery
            FROM reports_datamart
            WHERE user_email = %(email)s OR user_id = %(email)s
        """, parameters={"email": user_email})

        if not result.result_rows:
            return None

        row = result.result_rows[0]
        return {
            "email": row[0],
            "name": row[1] or "-",
            "sessions": row[2],
            "gestures": row[3],
            "accuracy": round(row[4], 1) if row[4] else 0,
            "battery": round(row[5], 1) if row[5] else 0
        }
    except Exception as e:
        print(f"ERROR: ClickHouse query failed: {str(e)}")
        return None


@router.get("/{user_id}")
async def get_report(user_id: str, request: Request):
    current_user_id = await get_user_id_from_session(request)

    if not current_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if current_user_id != user_id:
        print(f"DEBUG: Access denied - current_user_id={current_user_id}, requested={user_id}")
        raise HTTPException(status_code=403, detail="Access denied")

    print(f"DEBUG: Access granted for user {user_id}")

    report_data = get_report_from_clickhouse(user_id)

    if not report_data:
        print(f"DEBUG: User {user_id} not found in ClickHouse, returning empty data")
        return {
            "email": user_id,
            "name": "-",
            "sessions": 0,
            "gestures": 0,
            "accuracy": 0,
            "battery": 0
        }

    return report_data


@router.get("/me/csv")
async def download_csv(request: Request):

    from fastapi.responses import RedirectResponse

    current_user_id = await get_user_id_from_session(request)

    if not current_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    print(f"DEBUG: Downloading CSV for user {current_user_id}")

    existing_key = check_report_in_s3(current_user_id)
    if existing_key:
        cdn_url = f"{CDN_BASE_URL}/{existing_key}"
        print(f"DEBUG: Using existing report from S3: {cdn_url}")
        return RedirectResponse(url=cdn_url)

    report_data = get_report_from_clickhouse(current_user_id)
    if not report_data:
        print(f"DEBUG: No report data found for {current_user_id}")
        report_data = {
            "email": current_user_id,
            "name": "-",
            "sessions": 0,
            "gestures": 0,
            "accuracy": 0,
            "battery": 0
        }

    csv_content = generate_report_file(current_user_id, report_data)
    file_key = save_report_to_s3(current_user_id, csv_content)
    cdn_url = f"{CDN_BASE_URL}/{file_key}"

    print(f"DEBUG: Generated new report, saved to {cdn_url}")
    return RedirectResponse(url=cdn_url)


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/debug/session")
async def debug_session(request: Request):
    session_cookie = request.cookies.get("SESSION_ID")
    session_header = request.headers.get("X-Session-Id")

    user_id = await get_user_id_from_session(request)

    return {
        "has_session_cookie": session_cookie is not None,
        "session_cookie_preview": session_cookie[:20] + "..." if session_cookie else None,
        "has_session_header": session_header is not None,
        "session_header_preview": session_header[:20] + "..." if session_header else None,
        "authenticated": user_id is not None,
        "user_id": user_id
    }