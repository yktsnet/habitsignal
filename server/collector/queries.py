# queries.py — 分析クエリ集
# すべての分析はここで行い、collector 側にロジックは持たない

import psycopg2
import psycopg2.extras
import os

PG_DSN = os.getenv("PG_DSN", "postgresql://habitsignal@localhost/habitsignal")


def get_conn():
    return psycopg2.connect(PG_DSN, cursor_factory=psycopg2.extras.RealDictCursor)


# ── 基本クエリ ────────────────────────────────────────────


def get_events_today():
    """今日のイベントを全件取得"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT * FROM events
            WHERE server_ts >= CURRENT_DATE
            ORDER BY ts ASC
        """
        )
        return cur.fetchall()


def get_events_by_type(event_type, days=7):
    """直近 N 日間の指定タイプのイベント"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT * FROM events
            WHERE type = %s
              AND server_ts >= NOW() - INTERVAL '%s days'
            ORDER BY ts ASC
        """,
            (event_type, days),
        )
        return cur.fetchall()


# ── 集計クエリ ────────────────────────────────────────────


def work_minutes_by_day(days=7):
    """
    日ごとの仕事モード時間（分）を集計する。
    work_on / work_off のペアを突き合わせて算出する。
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                date_trunc('day', server_ts)::date AS day,
                json_agg(json_build_object('type', type, 'ts', ts) ORDER BY ts) AS events
            FROM events
            WHERE type IN ('work_on', 'work_off')
              AND server_ts >= NOW() - INTERVAL '%s days'
            GROUP BY day
            ORDER BY day ASC
        """,
            (days,),
        )
        return cur.fetchall()


def desk_minutes_by_day(days=7):
    """日ごとの在席時間（分）を集計する"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                date_trunc('day', server_ts)::date AS day,
                json_agg(json_build_object('type', type, 'ts', ts) ORDER BY ts) AS events
            FROM events
            WHERE type IN ('desk_on', 'desk_off')
              AND server_ts >= NOW() - INTERVAL '%s days'
            GROUP BY day
            ORDER BY day ASC
        """,
            (days,),
        )
        return cur.fetchall()


def scores_with_env(days=30):
    """
    主観スコアと、その前後30分の平均温湿度を紐付ける。
    相関分析の基礎データとして使う。
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                s.ts                                          AS score_ts,
                (s.payload->>'value')::int                   AS score,
                AVG((e.payload->>'temp')::float)             AS avg_temp,
                AVG((e.payload->>'humidity')::float)         AS avg_humidity
            FROM events s
            JOIN events e
              ON e.type = 'env'
             AND e.ts BETWEEN s.ts - 1800 AND s.ts + 1800
            WHERE s.type = 'score'
              AND s.server_ts >= NOW() - INTERVAL '%s days'
            GROUP BY s.ts, s.payload->>'value'
            ORDER BY s.ts ASC
        """,
            (days,),
        )
        return cur.fetchall()


def water_count_by_day(days=7):
    """日ごとの給水回数"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                date_trunc('day', server_ts)::date AS day,
                COUNT(*) AS count
            FROM events
            WHERE type = 'water'
              AND server_ts >= NOW() - INTERVAL '%s days'
            GROUP BY day
            ORDER BY day ASC
        """,
            (days,),
        )
        return cur.fetchall()


def exercise_days(days=30):
    """運動した日の一覧"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT date_trunc('day', server_ts)::date AS day
            FROM events
            WHERE type = 'exercise_start'
              AND server_ts >= NOW() - INTERVAL '%s days'
            ORDER BY day ASC
        """,
            (days,),
        )
        return [row["day"] for row in cur.fetchall()]
