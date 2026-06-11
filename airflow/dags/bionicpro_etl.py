from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import psycopg2
import clickhouse_connect

PG_HOST = "postgres"
PG_DB = "bionicpro"
PG_USER = "postgres"
PG_PASS = "password"

CH_HOST = "clickhouse"
CH_DB = "bionicpro"


def extract_and_load(**context):
    pg_conn = psycopg2.connect(
        host=PG_HOST,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASS
    )

    query = """
        SELECT
            c.email,
            c.full_name,
            COUNT(t.id) as total_sessions,
            COALESCE(SUM(t.gestures_count), 0) as total_gestures,
            COALESCE(AVG(t.avg_battery), 0) as avg_battery
        FROM clients c
        LEFT JOIN telemetry t ON t.client_id = c.id
        WHERE t.session_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY c.id, c.email, c.full_name
    """

    with pg_conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
    pg_conn.close()

    ch_client = clickhouse_connect.get_client(
        host=CH_HOST,
        database=CH_DB
    )

    ch_client.command("""
        CREATE TABLE IF NOT EXISTS reports_datamart (
            user_email String,
            user_name String,
            total_sessions UInt32,
            total_gestures UInt64,
            avg_battery Float32,
            updated_at Date DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY user_email
    """)

    ch_client.command("TRUNCATE TABLE reports_datamart")

    if rows:
        ch_client.insert(
            "reports_datamart",
            rows,
            column_names=["user_email", "user_name", "total_sessions", "total_gestures", "avg_battery"]
        )

    print(f"Загружено {len(rows)} записей в ClickHouse")

default_args = {
    "owner": "bionicpro",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

dag = DAG(
    "bionicpro_simple_etl",
    default_args=default_args,
    description="ETL из PostgreSQL в ClickHouse",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
)

etl_task = PythonOperator(
    task_id="run_etl",
    python_callable=extract_and_load,
    dag=dag,
)

etl_task