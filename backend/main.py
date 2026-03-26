"""FastAPI メインアプリケーション"""
import asyncio
import re
from datetime import datetime, timedelta
from dataclasses import asdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from scraper import (
    fetch_race_list,
    fetch_race_detail,
    fetch_horse_past_races,
    fetch_odds,
    fetch_jockey_info,
    fetch_race_full_data,
)
from prompt_generator import generate_prompt


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🏇 競馬予想アプリ起動!")
    yield
    print("アプリ終了")


app = FastAPI(title="競馬予想アプリ", lifespan=lifespan)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "競馬予想アプリ稼働中 🏇"}


@app.get("/api/race_dates")
async def get_race_dates(source: str = Query("jra", description="jra or nar")):
    """レース開催日一覧を返す"""
    today = datetime.now()
    weekday_names = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"}
    dates = []

    if source == "nar":
        # 地方競馬: 毎日開催なので過去3日＋今日＋未来3日
        for i in range(-3, 4):
            d = today + timedelta(days=i)
            wd = weekday_names[d.weekday()]
            label = ""
            if d.date() == today.date():
                label = " 今日"
            dates.append({
                "date": d.strftime("%Y%m%d"),
                "display": d.strftime("%m/%d") + f"({wd}){label}",
                "is_past": d.date() < today.date(),
                "is_today": d.date() == today.date(),
            })
    else:
        # JRA: 土日中心
        for i in range(-7, 8):
            d = today + timedelta(days=i)
            if d.weekday() in [5, 6]:
                wd = weekday_names[d.weekday()]
                dates.append({
                    "date": d.strftime("%Y%m%d"),
                    "display": d.strftime("%m/%d") + f"({wd})",
                    "is_past": d.date() < today.date(),
                    "is_today": d.date() == today.date(),
                })
        # 今日が土日でなくても含める
        if today.weekday() not in [5, 6]:
            wd = weekday_names[today.weekday()]
            dates.insert(0, {
                "date": today.strftime("%Y%m%d"),
                "display": today.strftime("%m/%d") + f"({wd}) 今日",
                "is_past": False,
                "is_today": True,
            })

    return {"dates": dates}


@app.get("/api/races")
async def get_races(
    date: str = Query(..., description="YYYYMMDD形式"),
    source: str = Query("jra", description="jra or nar"),
):
    """指定日のレース一覧を取得"""
    try:
        races = await fetch_race_list(date, source=source)
        return {"races": [asdict(r) for r in races]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"レース一覧取得エラー: {str(e)}")


@app.get("/api/race/{race_id}")
async def get_race_detail_api(
    race_id: str,
    source: str = Query("jra", description="jra or nar"),
):
    """レース詳細情報を取得"""
    try:
        race_info, _ = await fetch_race_detail(race_id, source=source)

        try:
            odds = await fetch_odds(race_id, source=source)
            for entry in race_info.entries:
                if entry.horse_number in odds:
                    entry.odds = odds[entry.horse_number].get("odds", "")
                    entry.popularity = odds[entry.horse_number].get("popularity", "")
        except Exception:
            pass

        return {"race": asdict(race_info)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"レース詳細取得エラー: {str(e)}")


@app.get("/api/race/{race_id}/full")
async def get_race_full(
    race_id: str,
    source: str = Query("jra", description="jra or nar"),
):
    """レース全データ（過去成績+騎手情報付き）+ GenSparkプロンプトを生成"""
    try:
        race_info, prompt = await fetch_race_full_data(race_id, source=source)
        return {
            "race": asdict(race_info),
            "prompt": prompt,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データ取得エラー: {str(e)}")


@app.get("/api/race/{race_id}/prompt")
async def get_prompt(
    race_id: str,
    source: str = Query("jra", description="jra or nar"),
):
    """GenSpark用プロンプトのみ取得"""
    try:
        _, prompt = await fetch_race_full_data(race_id, source=source)
        return {"prompt": prompt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"プロンプト生成エラー: {str(e)}")


# フロントエンドの静的ファイル配信
import os
frontend_dist = os.environ.get("FRONTEND_DIST_DIR")
if not frontend_dist:
    frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")
frontend_dist = os.path.normpath(frontend_dist)

if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
