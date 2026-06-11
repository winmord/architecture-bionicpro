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

router = APIRouter(prefix="/reports", tags=["reports"])

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin123")
S3_BUCKET = os.getenv("S3_BUCKET", "bionicpro-reports")
CDN_BASE_URL = os.getenv("CDN_BASE_URL", "http://localhost:8083/reports")

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


def get_user_email_from_token(request: Request):
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        token = auth_header.replace("Bearer ", "")
        payload = token.split('.')[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.b64decode(payload)
        data = json.loads(decoded)
        return data.get("email")
    except Exception:
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
    """Получает данные из ClickHouse"""
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
        WHERE user_email = %(email)s
    """, parameters={"email": user_email})

    if not result.result_rows:
        return None

    row = result.result_rows[0]
    return {
        "email": row[0],
        "name": row[1] or "-",
        "sessions": row[2],
        "gestures": row[3],
        "accuracy": round(row[4], 1),
        "battery": round(row[5], 1)
    }


@router.get("/{user_email}")
async def get_report(user_email: str, request: Request):
    current_email = get_user_email_from_token(request)
    if not current_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if current_email.lower() != user_email.lower():
        raise HTTPException(status_code=403, detail="Access denied")

    existing_key = check_report_in_s3(user_email)
    if existing_key:
        cdn_url = f"{CDN_BASE_URL}/{existing_key}"
        return {
            "status": "cached",
            "report_url": cdn_url,
            "message": "Report available via CDN"
        }

    report_data = get_report_from_clickhouse(user_email)
    if not report_data:
        return {
            "email": user_email,
            "name": "-",
            "sessions": 0,
            "gestures": 0,
            "accuracy": 0,
            "battery": 0,
            "message": "No data yet"
        }

    csv_content = generate_report_file(user_email, report_data)
    file_key = save_report_to_s3(user_email, csv_content)

    cdn_url = f"{CDN_BASE_URL}/{file_key}"
    return {
        "status": "generated",
        "report_url": cdn_url,
        "message": "Report generated and cached"
    }


@router.get("/me/csv")
async def download_csv(request: Request):
    from fastapi.responses import RedirectResponse

    current_email = get_user_email_from_token(request)
    if not current_email:
        raise HTTPException(status_code=401, detail="Not authenticated")

    existing_key = check_report_in_s3(current_email)
    if existing_key:
        cdn_url = f"{CDN_BASE_URL}/{existing_key}"
        return RedirectResponse(url=cdn_url)

    report_data = get_report_from_clickhouse(current_email)
    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")

    csv_content = generate_report_file(current_email, report_data)
    file_key = save_report_to_s3(current_email, csv_content)
    cdn_url = f"{CDN_BASE_URL}/{file_key}"

    return RedirectResponse(url=cdn_url)


@router.get("/health")
async def health():
    return {"status": "ok"}