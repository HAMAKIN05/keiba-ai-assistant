"""netkeiba.comからレースデータを取得するスクレイパー（JRA + 地方競馬対応）"""
import re
import asyncio
import httpx
from bs4 import BeautifulSoup
from models import (
    RaceInfo, HorseEntry, PastRace, JockeyInfo, RaceListItem
)

# JRA（中央競馬）
JRA_BASE_URL = "https://race.netkeiba.com"
# NAR（地方競馬）
NAR_BASE_URL = "https://nar.netkeiba.com"
# 共通DB
DB_URL = "https://db.netkeiba.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}


def get_base_url(source: str) -> str:
    return NAR_BASE_URL if source == "nar" else JRA_BASE_URL


async def get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers=HEADERS,
        timeout=30.0,
        follow_redirects=True,
    )


# ============================
# レース一覧
# ============================
async def fetch_race_list(date: str, source: str = "jra") -> list[RaceListItem]:
    base_url = get_base_url(source)
    url = f"{base_url}/top/race_list_sub.html?kaisai_date={date}"
    async with await get_client() as client:
        resp = await client.get(url)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

    races = []
    venue_blocks = soup.select("dl.RaceList_DataList")

    for block in venue_blocks:
        venue_title = block.select_one(".RaceList_DataTitle")
        venue_name = ""
        if venue_title:
            venue_text = venue_title.get_text(strip=True)
            m = re.search(r'[0-9]+回(.+?)[0-9]+日', venue_text)
            venue_name = m.group(1) if m else venue_text

        items = block.select("li.RaceList_DataItem")
        for item in items:
            link = item.select_one("a")
            if not link:
                continue
            href = link.get("href", "")
            race_id_match = re.search(r'race_id=(\d+)', href)
            if not race_id_match:
                continue
            race_id = race_id_match.group(1)

            # レース番号
            num_el = item.select_one(".Race_Num")
            race_num = ""
            if num_el:
                m = re.search(r'(\d+)R', num_el.get_text(strip=True))
                race_num = m.group(1) if m else ""

            # レース名
            title_el = item.select_one(".ItemTitle")
            race_name = title_el.get_text(strip=True) if title_el else ""

            # 時刻 - 複数のセレクターで取得を試行
            start_time = ""
            time_el = item.select_one(".RaceList_Itemtime")
            if time_el:
                start_time = time_el.get_text(strip=True)

            if not start_time:
                # RaceData内のspan等からも探す
                race_data = item.select_one(".RaceData")
                if race_data:
                    for span in race_data.select("span"):
                        t = span.get_text(strip=True)
                        if re.match(r'\d{1,2}:\d{2}', t):
                            start_time = t
                            break

            if not start_time:
                # リンク内テキストから探す
                all_text = item.get_text(" ", strip=True)
                tm = re.search(r'(\d{1,2}:\d{2})', all_text)
                if tm:
                    start_time = tm.group(1)

            # コース情報
            course_long = item.select_one(".RaceList_ItemLong")
            if not course_long:
                course_long = item.select_one("span.Dart, span.Shiba, span.Obstacle")
            course_info = course_long.get_text(strip=True) if course_long else ""

            # コース情報が無い場合、全テキストから抽出
            if not course_info:
                all_text = item.get_text(" ", strip=True)
                cm = re.search(r'([芝ダ障]\d+m)', all_text)
                if cm:
                    course_info = cm.group(1)

            # 頭数
            count_el = item.select_one(".RaceList_Itemnumber")
            horse_count = ""
            if count_el:
                horse_count = count_el.get_text(strip=True)
            else:
                race_data = item.select_one(".RaceData")
                if race_data:
                    hc_match = re.search(r'(\d+頭)', race_data.get_text(strip=True))
                    if hc_match:
                        horse_count = hc_match.group(1)
            if not horse_count:
                hc_match = re.search(r'(\d+頭)', item.get_text(strip=True))
                if hc_match:
                    horse_count = hc_match.group(1)

            # グレード
            grade = ""
            for icon in item.select("[class*='Icon_GradeType']"):
                cls = " ".join(icon.get("class", []))
                if "Grade1" in cls: grade = "G1"
                elif "Grade2" in cls: grade = "G2"
                elif "Grade3" in cls: grade = "G3"

            display_name = f"[{grade}] {race_name}" if grade else race_name

            races.append(RaceListItem(
                race_id=race_id,
                race_number=race_num,
                race_name=display_name,
                start_time=start_time,
                course_info=course_info,
                venue=venue_name,
                horse_count=horse_count,
            ))
    return races


# ============================
# レース詳細（出走馬 + ID取得）
# ============================
async def fetch_race_detail(race_id: str, source: str = "jra") -> tuple[RaceInfo, dict]:
    """
    レース詳細＆出走馬情報を取得。
    Returns: (RaceInfo, id_map)
    id_map = { horse_number: {"horse_id": "...", "jockey_id": "..."} }
    """
    base_url = get_base_url(source)

    url = f"{base_url}/race/shutuba.html?race_id={race_id}"
    async with await get_client() as client:
        resp = await client.get(url)
        resp.encoding = "EUC-JP"
        soup = BeautifulSoup(resp.text, "lxml")

    table = soup.select_one(".Shutuba_Table, .RaceTable01")
    is_result = False
    if not table or len(table.select("tr.HorseList")) == 0:
        url = f"{base_url}/race/result.html?race_id={race_id}"
        async with await get_client() as client:
            resp = await client.get(url)
            resp.encoding = "EUC-JP"
            soup = BeautifulSoup(resp.text, "lxml")
        table = soup.select_one(".Shutuba_Table, .RaceTable01, .ResultTable")
        is_result = True

    # --- レース基本情報 ---
    race_name_el = soup.select_one(".RaceName")
    race_name = race_name_el.get_text(strip=True) if race_name_el else ""

    race_num_el = soup.select_one(".RaceNum")
    race_num = ""
    if race_num_el:
        m = re.search(r'(\d+)', race_num_el.get_text(strip=True))
        race_num = m.group(1) if m else ""

    race_data_el = soup.select_one(".RaceData01")
    race_data_text = race_data_el.get_text(" ", strip=True) if race_data_el else ""

    course_match = re.search(r'(芝|ダ|ダート|障)(\d+)m', race_data_text)
    course_type = course_match.group(1) if course_match else ""
    if course_type == "ダ":
        course_type = "ダート"
    distance = course_match.group(2) + "m" if course_match else ""

    direction_match = re.search(r'(左|右|直線)', race_data_text)
    direction = direction_match.group(1) if direction_match else ""

    weather_match = re.search(r'天候:(\S+)', race_data_text)
    weather = weather_match.group(1) if weather_match else ""

    track_match = re.search(r'馬場:(\S+)', race_data_text)
    track_condition = track_match.group(1) if track_match else ""

    time_match = re.search(r'(\d{1,2}:\d{2})', race_data_text)
    start_time = time_match.group(1) if time_match else ""

    race_data02 = soup.select_one(".RaceData02")
    race_data02_text = race_data02.get_text(strip=True) if race_data02 else ""
    venue = ""
    venue_match = re.search(r'\d+回(.+?)\d+日', race_data02_text)
    if venue_match:
        venue = venue_match.group(1)

    grade = ""
    for icon in soup.select("[class*='Icon_GradeType']"):
        cls = " ".join(icon.get("class", []))
        if "Grade1" in cls: grade = "G1"
        elif "Grade2" in cls: grade = "G2"
        elif "Grade3" in cls: grade = "G3"

    distance_full = f"{distance}({direction})" if direction and distance else distance

    # --- 出走馬テーブル ---
    entries = []
    id_map = {}  # { horse_number: {"horse_id": "...", "jockey_id": "..."} }

    if table:
        rows = table.select("tr.HorseList")
        for row in rows:
            tds = row.select("td")
            if len(tds) < 4:
                continue

            bracket = tds[0].get_text(strip=True)
            number = tds[1].get_text(strip=True)

            # 馬名 + ID
            horse_name = ""
            horse_id = ""
            horse_link = row.select_one("td a[href*='/horse/']")
            if horse_link:
                horse_name = horse_link.get_text(strip=True)
                m = re.search(r'/horse/(\w+)', horse_link.get("href", ""))
                if m:
                    horse_id = m.group(1)

            sex_age = tds[4].get_text(strip=True) if len(tds) > 4 else ""
            jockey_weight = tds[5].get_text(strip=True) if len(tds) > 5 else ""

            # 騎手 + ID
            jockey_name = ""
            jockey_id = ""
            jockey_link = row.select_one("td a[href*='/jockey/']")
            if jockey_link:
                jockey_name = jockey_link.get_text(strip=True)
                href = jockey_link.get("href", "")
                m = re.search(r'/jockey/(?:result/recent/)?(\w+)', href)
                if m:
                    jockey_id = m.group(1)

            # 調教師
            trainer = ""
            trainer_link = row.select_one("td a[href*='/trainer/']")
            if trainer_link:
                trainer = trainer_link.get_text(strip=True)

            # 馬体重
            weight_el = row.select_one(".Weight, td:nth-of-type(9)")
            horse_weight = weight_el.get_text(strip=True) if weight_el else ""

            entries.append(HorseEntry(
                bracket_number=bracket,
                horse_number=number,
                horse_name=horse_name,
                sex_age=sex_age,
                weight=jockey_weight,
                jockey_name=jockey_name,
                trainer=trainer,
                horse_weight=horse_weight,
                odds="",
                popularity="",
            ))

            id_map[number] = {
                "horse_id": horse_id,
                "jockey_id": jockey_id,
            }

    race_info = RaceInfo(
        race_id=race_id,
        race_name=race_name,
        race_number=race_num,
        date="",
        venue=venue,
        course_type=course_type,
        distance=distance_full,
        track_condition=track_condition,
        weather=weather,
        start_time=start_time,
        race_grade=grade,
        entries=entries,
    )
    return race_info, id_map


# ============================
# オッズ取得
# ============================
async def fetch_odds(race_id: str, source: str = "jra") -> dict[str, dict]:
    base_url = get_base_url(source)

    url = f"{base_url}/race/result.html?race_id={race_id}"
    async with await get_client() as client:
        resp = await client.get(url)
        resp.encoding = "EUC-JP"
        soup = BeautifulSoup(resp.text, "lxml")

    odds_data = {}
    for row in soup.select("tr.HorseList"):
        tds = row.select("td")
        if len(tds) < 12:
            continue
        number = tds[2].get_text(strip=True)
        popularity = tds[9].get_text(strip=True)
        odds_val = tds[10].get_text(strip=True)
        if number and number.isdigit():
            odds_data[number] = {"odds": odds_val, "popularity": popularity}

    if not odds_data:
        try:
            url2 = f"{base_url}/odds/index.html?race_id={race_id}&type=b1"
            async with await get_client() as client:
                resp2 = await client.get(url2)
                resp2.encoding = "EUC-JP"
                soup2 = BeautifulSoup(resp2.text, "lxml")
            for row in soup2.select("tr.HorseList"):
                tds = row.select("td")
                if len(tds) < 4:
                    continue
                number = tds[1].get_text(strip=True)
                odds_el = row.select_one(".Odds")
                pop_el = row.select_one(".Popular")
                if number and number.isdigit():
                    odds_data[number] = {
                        "odds": odds_el.get_text(strip=True) if odds_el else "",
                        "popularity": pop_el.get_text(strip=True) if pop_el else "",
                    }
        except Exception:
            pass
    return odds_data


# ============================
# 馬の過去成績（直近5走）- 正確なカラムマッピング
# ============================
async def fetch_horse_past_races(horse_id: str, limit: int = 5) -> list[PastRace]:
    """
    db.netkeiba.com/horse/result/{horse_id}/ から過去成績を取得。
    
    テーブルカラム(33列):
    [0]日付 [1]開催 [2]天気 [3]R [4]レース名 [5]映像 [6]頭数
    [7]枠番 [8]馬番 [9]オッズ [10]人気 [11]着順 [12]騎手 [13]斤量
    [14]距離 [15]水分量 [16]馬場 [17]馬場指数 [18]タイム [19]着差
    [20]タイム指数 [21]タイム指数M [22]スタート指数 [23]追走指数 [24]上がり指数
    [25]通過 [26]ペース [27]上り [28]馬体重 [29]厩舎コメント [30]備考
    [31]勝ち馬(2着馬) [32]賞金
    """
    url = f"{DB_URL}/horse/result/{horse_id}/"
    async with await get_client() as client:
        resp = await client.get(url)
        resp.encoding = "EUC-JP"
        soup = BeautifulSoup(resp.text, "lxml")

    past_races = []
    table = soup.select_one("table.db_h_race_results, table.nk_tb_common")
    if not table:
        return past_races

    rows = table.select("tr")[1:]  # ヘッダースキップ
    for row in rows[:limit]:
        tds = row.select("td")
        if len(tds) < 19:
            continue

        def safe_get(idx):
            return tds[idx].get_text(strip=True) if idx < len(tds) else ""

        past_races.append(PastRace(
            date=safe_get(0),
            venue=safe_get(1),
            race_name=safe_get(4),
            course=safe_get(14),
            weather=safe_get(2),
            track_condition=safe_get(16),
            position=safe_get(11),
            field_size=safe_get(6),
            bracket=safe_get(7),
            horse_number=safe_get(8),
            jockey=safe_get(12),
            weight=safe_get(13),
            time=safe_get(18),
            margin=safe_get(19),
            odds=safe_get(9),
            popularity=safe_get(10),
            horse_weight=safe_get(28),
            passing=safe_get(25),
            pace=safe_get(26),
            last_3f=safe_get(27),
            winner=safe_get(31),
        ))
    return past_races


# ============================
# 騎手成績
# ============================
async def fetch_jockey_info(jockey_id: str) -> JockeyInfo | None:
    """db.netkeiba.com/jockey/{jockey_id}/ から騎手プロフィール＋成績を取得"""
    url = f"{DB_URL}/jockey/{jockey_id}/"
    async with await get_client() as client:
        resp = await client.get(url)
        resp.encoding = "EUC-JP"
        soup = BeautifulSoup(resp.text, "lxml")

    name_el = soup.select_one(".db_head_name h1")
    jockey_name = ""
    if name_el:
        for child in name_el.children:
            if hasattr(child, 'name') and child.name == 'a':
                jockey_name = child.get_text(strip=True)
                break
        if not jockey_name:
            jockey_name = name_el.get_text(strip=True).split('\n')[0].strip()

    # 年度別成績テーブルを探す
    for table in soup.select("table.nk_tb_common"):
        header_row = table.select_one("tr")
        if not header_row:
            continue
        ths = [th.get_text(strip=True) for th in header_row.select("th")]
        if "勝率" in ths and "連対率" in ths:
            rows = table.select("tr")
            for row in rows[1:]:
                tds = row.select("td")
                if len(tds) < 12:
                    continue
                texts = [td.get_text(strip=True) for td in tds]
                try:
                    win_idx = ths.index("1着")
                    rides_idx = ths.index("騎乗回数")
                    wr_idx = ths.index("勝率")
                    pr_idx = ths.index("連対率")
                    sr_idx = ths.index("複勝率")
                except ValueError:
                    continue

                return JockeyInfo(
                    name=jockey_name,
                    wins=texts[win_idx] if win_idx < len(texts) else "",
                    rides=texts[rides_idx] if rides_idx < len(texts) else "",
                    win_rate=texts[wr_idx] if wr_idx < len(texts) else "",
                    place_rate=texts[pr_idx] if pr_idx < len(texts) else "",
                    show_rate=texts[sr_idx] if sr_idx < len(texts) else "",
                )
    return None


# ============================
# フルデータ取得（過去成績＋騎手情報付き）
# ============================
async def fetch_race_full_data(race_id: str, source: str = "jra") -> tuple[RaceInfo, str]:
    """
    レース全データを取得し、各馬の過去成績・騎手成績も付与する。
    並列リクエストで高速化。
    """
    from prompt_generator import generate_prompt

    # 1. レース詳細取得
    race_info, id_map = await fetch_race_detail(race_id, source)

    # 2. オッズ取得
    try:
        odds = await fetch_odds(race_id, source)
        for entry in race_info.entries:
            if entry.horse_number in odds:
                entry.odds = odds[entry.horse_number].get("odds", "")
                entry.popularity = odds[entry.horse_number].get("popularity", "")
    except Exception:
        pass

    # 3. 各馬の過去成績と騎手情報を並列取得
    async def fetch_entry_data(entry: HorseEntry):
        ids = id_map.get(entry.horse_number, {})
        horse_id = ids.get("horse_id", "")
        jockey_id = ids.get("jockey_id", "")

        tasks = []
        if horse_id:
            tasks.append(("past", fetch_horse_past_races(horse_id, limit=5)))
        if jockey_id:
            tasks.append(("jockey", fetch_jockey_info(jockey_id)))

        for label, coro in tasks:
            try:
                result = await coro
                if label == "past" and result:
                    entry.past_races = result
                elif label == "jockey" and result:
                    entry.jockey_info = result
            except Exception:
                pass

    # セマフォで同時リクエスト数を制限（サーバー負荷対策）
    sem = asyncio.Semaphore(5)

    async def limited_fetch(entry):
        async with sem:
            await fetch_entry_data(entry)

    await asyncio.gather(*[limited_fetch(e) for e in race_info.entries])

    # 4. プロンプト生成
    prompt = generate_prompt(race_info, source=source)

    return race_info, prompt
