from fastapi import APIRouter, HTTPException, Depends
from typing import List
import clickhouse_connect

from app.database import get_clickhouse_client
from app.models import ReportResponse, ErrorResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{user_email}", response_model=ReportResponse)
async def get_report(
    user_email: str,
    db: clickhouse_connect.client.Client = Depends(get_clickhouse_client)
):
    query = """
        SELECT
            user_email,
            user_name,
            total_sessions,
            total_gestures,
            avg_confidence,
            avg_battery,
            first_activity,
            last_activity,
            updated_at
        FROM reports_datamart
        WHERE user_email = %(email)s
        LIMIT 1
    """

    try:
        result = db.query(query, parameters={"email": user_email})

        if not result.result_rows:
            raise HTTPException(
                status_code=404,
                detail=f"Отчёт для пользователя {user_email} не найден"
            )

        row = result.result_rows[0]
        return ReportResponse(
            user_email=row[0],
            user_name=row[1],
            total_sessions=row[2],
            total_gestures=row[3],
            avg_confidence=row[4],
            avg_battery=row[5],
            first_activity=row[6],
            last_activity=row[7],
            updated_at=row[8]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ReportResponse])
async def get_all_reports(
    limit: int = 100,
    db: clickhouse_connect.client.Client = Depends(get_clickhouse_client)
):
    query = """
        SELECT
            user_email,
            user_name,
            total_sessions,
            total_gestures,
            avg_confidence,
            avg_battery,
            first_activity,
            last_activity,
            updated_at
        FROM reports_datamart
        LIMIT %(limit)s
    """

    try:
        result = db.query(query, parameters={"limit": limit})

        reports = []
        for row in result.result_rows:
            reports.append(ReportResponse(
                user_email=row[0],
                user_name=row[1],
                total_sessions=row[2],
                total_gestures=row[3],
                avg_confidence=row[4],
                avg_battery=row[5],
                first_activity=row[6],
                last_activity=row[7],
                updated_at=row[8]
            ))

        return reports

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_email}/csv")
async def get_report_csv(
    user_email: str,
    db: clickhouse_connect.client.Client = Depends(get_clickhouse_client)
):
    from fastapi.responses import Response
    import csv
    from io import StringIO

    query = """
        SELECT
            user_email,
            user_name,
            total_sessions,
            total_gestures,
            avg_confidence,
            avg_battery,
            first_activity,
            last_activity,
            updated_at
        FROM reports_datamart
        WHERE user_email = %(email)s
        LIMIT 1
    """

    try:
        result = db.query(query, parameters={"email": user_email})

        if not result.result_rows:
            raise HTTPException(
                status_code=404,
                detail=f"Отчёт для пользователя {user_email} не найден"
            )

        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Email пользователя", "Имя пользователя", "Всего сессий",
            "Всего жестов", "Средняя точность", "Средний заряд батареи",
            "Первая активность", "Последняя активность", "Дата обновления"
        ])

        # Данные
        row = result.result_rows[0]
        writer.writerow(row)

        return Response(
            content=output.getvalue().encode("utf-8"),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=report_{user_email}.csv"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {"status": "ok"}