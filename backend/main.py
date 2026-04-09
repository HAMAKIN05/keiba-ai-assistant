"""FastAPI メインアプリケーション"""
import asyncio
import re
from datetime import datetime, timedelta
from dataclasses import asdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from scraper import (
    fetch_race_list,
    fetch_race_detail,
    fetch_horse_past_races,
    fetch_odds,
    fetch_jockey_info,
    fetch_race_full_data,
    is_ip_blocked,
    reset_ip_block,
    save_html_to_cache,
    IPBlockedError,
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


# --- IPブロックエラーハンドラ ---
@app.exception_handler(IPBlockedError)
async def ip_blocked_handler(request: Request, exc: IPBlockedError):
    return JSONResponse(
        status_code=503,
        content={
            "error": "ip_blocked",
            "message": str(exc),
            "detail": "netkeiba.comからIPアドレスがブロックされています。"
                      "別のネットワークから接続するか、プロキシを設定してください。"
                      "Docker環境でHTTP_PROXY環境変数を設定することで回避できます。",
        }
    )


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "message": "競馬予想アプリ稼働中 🏇",
        "ip_blocked": is_ip_blocked(),
    }


@app.get("/api/status")
async def status():
    """接続状態を確認"""
    return {
        "ip_blocked": is_ip_blocked(),
        "message": "netkeiba.comへの接続がブロックされています" if is_ip_blocked()
                   else "正常に接続できます",
    }


@app.post("/api/reset_block")
async def reset_block():
    """IPブロックフラグをリセット"""
    reset_ip_block()
    return {"message": "IPブロックフラグをリセットしました。再度アクセスを試みます。"}


@app.post("/api/cache")
async def cache_html(request: Request):
    """外部からHTMLをキャッシュに保存（プリフェッチ用）
    
    Body: {"url": "https://...", "html": "<html>..."}
    """
    try:
        body = await request.json()
        url = body.get("url", "")
        html = body.get("html", "")
        if not url or not html:
            raise HTTPException(status_code=400, detail="url and html are required")
        save_html_to_cache(url, html)
        return {"message": f"Cached {len(html)} chars for {url}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/import_race_list")
async def import_race_list(request: Request):
    """外部からレースリストデータをインポート（プリフェッチ用）
    
    Body: {"date": "20260409", "source": "nar", "races": [...]}
    """
    from data_cache import set_cached_data
    from models import RaceListItem
    try:
        body = await request.json()
        date = body.get("date", "")
        source = body.get("source", "nar")
        races = body.get("races", [])
        if not date or not races:
            raise HTTPException(status_code=400, detail="date and races are required")
        
        key = f"race_list_{source}_{date}"
        set_cached_data(key, {"races": races})
        return {"message": f"Imported {len(races)} races for {date} ({source})"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/import_race_full")
async def import_race_full(request: Request):
    """外部からフルレースデータをインポート（プリフェッチ用）
    
    Body: {"race_id": "...", "source": "nar", "race": {...}, "prompt": "..."}
    """
    from data_cache import set_cached_data
    try:
        body = await request.json()
        race_id = body.get("race_id", "")
        source = body.get("source", "nar")
        race_data = body.get("race", {})
        prompt = body.get("prompt", "")
        if not race_id or not race_data:
            raise HTTPException(status_code=400, detail="race_id and race are required")
        
        key = f"race_full_{source}_{race_id}"
        set_cached_data(key, {"race": race_data, "prompt": prompt})
        return {"message": f"Imported full data for race {race_id}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/race_dates")
async def get_race_dates(source: str = Query("jra", description="jra or nar")):
    """レース開催日一覧を返す"""
    today = datetime.now()
    weekday_names = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"}
    dates = []

    if source == "nar":
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
        return {"races": [asdict(r) for r in races], "ip_blocked": False}
    except IPBlockedError as e:
        return JSONResponse(
            status_code=503,
            content={
                "races": [],
                "ip_blocked": True,
                "error": "ip_blocked",
                "message": str(e),
            }
        )
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
    except IPBlockedError as e:
        return JSONResponse(status_code=503, content={"error": "ip_blocked", "message": str(e)})
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
            "ip_blocked": False,
        }
    except IPBlockedError as e:
        return JSONResponse(status_code=503, content={"error": "ip_blocked", "message": str(e)})
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
    except IPBlockedError as e:
        return JSONResponse(status_code=503, content={"error": "ip_blocked", "message": str(e)})
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
