# MongoDB クエリ集
# Python から pymongo で実行する想定
# すべての分析はここで行い、collector 側にロジックは持たない

from pymongo import MongoClient
from datetime import datetime, timezone, timedelta

mongo = MongoClient("mongodb://localhost:27017")
db = mongo["habitsignal"]
events = db["events"]


# ── 基本クエリ ────────────────────────────────────────────

def get_events_today():
    """今日のイベントを全件取得"""
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return list(events.find({"server_ts": {"$gte": start}}).sort("ts", 1))


def get_events_by_type(event_type, days=7):
    """直近 N 日間の指定タイプのイベント"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    return list(events.find({"type": event_type, "server_ts": {"$gte": since}}).sort("ts", 1))


# ── 集計クエリ ────────────────────────────────────────────

def work_minutes_by_day(days=7):
    """
    日ごとの仕事モード時間（分）を集計する。
    work_on / work_off のペアを突き合わせて算出する。
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    pipeline = [
        {"$match": {
            "type": {"$in": ["work_on", "work_off"]},
            "server_ts": {"$gte": since}
        }},
        {"$sort": {"ts": 1}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$server_ts"}},
            "events": {"$push": {"type": "$type", "ts": "$ts"}}
        }},
        {"$sort": {"_id": 1}}
    ]
    return list(events.aggregate(pipeline))


def desk_minutes_by_day(days=7):
    """日ごとの在席時間（分）を集計する"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    pipeline = [
        {"$match": {
            "type": {"$in": ["desk_on", "desk_off"]},
            "server_ts": {"$gte": since}
        }},
        {"$sort": {"ts": 1}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$server_ts"}},
            "events": {"$push": {"type": "$type", "ts": "$ts"}}
        }},
        {"$sort": {"_id": 1}}
    ]
    return list(events.aggregate(pipeline))


def scores_with_env(days=30):
    """
    主観スコアと、その前後30分の平均温湿度を紐付ける。
    相関分析の基礎データとして使う。
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    score_events = list(events.find({
        "type": "score",
        "server_ts": {"$gte": since}
    }).sort("ts", 1))

    results = []
    for s in score_events:
        score_ts = s["ts"]
        # スコア入力前後30分の環境データを取得
        env_data = list(events.find({
            "type": "env",
            "ts": {"$gte": score_ts - 1800, "$lte": score_ts + 1800}
        }))
        if not env_data:
            continue
        avg_temp = sum(e["payload"]["temp"] for e in env_data) / len(env_data)
        avg_hum = sum(e["payload"]["humidity"] for e in env_data) / len(env_data)
        results.append({
            "ts": score_ts,
            "score": s["payload"]["value"],
            "avg_temp": round(avg_temp, 1),
            "avg_humidity": round(avg_hum, 1),
        })
    return results


def water_count_by_day(days=7):
    """日ごとの給水回数"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    pipeline = [
        {"$match": {"type": "water", "server_ts": {"$gte": since}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$server_ts"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    return list(events.aggregate(pipeline))


def exercise_days(days=30):
    """運動した日の一覧"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    pipeline = [
        {"$match": {"type": "exercise_start", "server_ts": {"$gte": since}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$server_ts"}}
        }},
        {"$sort": {"_id": 1}}
    ]
    return [r["_id"] for r in events.aggregate(pipeline)]
