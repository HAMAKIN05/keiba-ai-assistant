"""JSONベースのレースデータキャッシュ
   
   crawlerツール等で取得したデータを解析済みJSONとしてキャッシュし、
   IPブロック時のフォールバックとして使用する。
"""
import json
import time
from pathlib import Path
from models import RaceInfo, HorseEntry, PastRace, JockeyInfo, RaceListItem
from dataclasses import asdict

CACHE_DIR = Path("/tmp/keiba_data_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# キャッシュ有効期限（秒）
CACHE_TTL = 3600 * 12  # 12時間


def _cache_path(key: str) -> Path:
    # key例: "race_list_nar_20260409", "race_detail_202645040904"
    safe_key = key.replace("/", "_").replace(":", "_")
    return CACHE_DIR / f"{safe_key}.json"


def get_cached_data(key: str) -> dict | None:
    """キャッシュからデータを取得"""
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # TTLチェック
        if time.time() - data.get("_cached_at", 0) > CACHE_TTL:
            return None
        return data
    except Exception:
        return None


def set_cached_data(key: str, data: dict):
    """データをキャッシュに保存"""
    data["_cached_at"] = time.time()
    path = _cache_path(key)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cache_race_list(date: str, source: str, races: list[RaceListItem]):
    """レース一覧をキャッシュ"""
    key = f"race_list_{source}_{date}"
    data = {
        "races": [asdict(r) for r in races],
    }
    set_cached_data(key, data)


def get_cached_race_list(date: str, source: str) -> list[RaceListItem] | None:
    """キャッシュからレース一覧を取得"""
    key = f"race_list_{source}_{date}"
    data = get_cached_data(key)
    if not data:
        return None
    try:
        return [
            RaceListItem(**r) for r in data.get("races", [])
        ]
    except Exception:
        return None


def cache_race_full_data(race_id: str, source: str, race_info: RaceInfo, prompt: str):
    """レースフルデータをキャッシュ"""
    key = f"race_full_{source}_{race_id}"
    data = {
        "race": asdict(race_info),
        "prompt": prompt,
    }
    set_cached_data(key, data)


def get_cached_race_full_data(race_id: str, source: str) -> tuple[dict, str] | None:
    """キャッシュからフルレースデータを取得"""
    key = f"race_full_{source}_{race_id}"
    data = get_cached_data(key)
    if not data:
        return None
    try:
        return data["race"], data["prompt"]
    except (KeyError, Exception):
        return None


def list_cached_keys() -> list[str]:
    """キャッシュ済みのキー一覧"""
    return [p.stem for p in CACHE_DIR.glob("*.json")]
