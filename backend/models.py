"""データモデル定義"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PastRace:
    """過去レース成績"""
    date: str
    venue: str  # 開催場 (例: "2中山8")
    race_name: str
    course: str  # 例: "ダ1200"
    weather: str
    track_condition: str  # 馬場状態
    position: str  # 着順
    field_size: str  # 頭数
    bracket: str  # 枠番
    horse_number: str  # 馬番
    jockey: str
    weight: str  # 斤量
    time: str
    margin: str  # 着差
    odds: str
    popularity: str
    horse_weight: str  # 馬体重
    passing: str  # 通過順 (例: "3-3-2-1")
    pace: str  # ペース (例: "34.5-36.2")
    last_3f: str  # 上り3F
    winner: str  # 勝ち馬(2着馬)


@dataclass
class JockeyInfo:
    """騎手情報"""
    name: str
    win_rate: str  # 勝率
    place_rate: str  # 連対率
    show_rate: str  # 複勝率
    wins: str
    rides: str


@dataclass
class HorseEntry:
    """出走馬情報"""
    bracket_number: str  # 枠番
    horse_number: str  # 馬番
    horse_name: str
    sex_age: str  # 性齢
    weight: str  # 斤量
    jockey_name: str
    trainer: str  # 調教師
    horse_weight: str  # 馬体重
    odds: str  # 単勝オッズ
    popularity: str  # 人気順
    jockey_info: Optional[JockeyInfo] = None
    past_races: list[PastRace] = field(default_factory=list)


@dataclass
class RaceInfo:
    """レース情報"""
    race_id: str
    race_name: str
    race_number: str
    date: str
    venue: str  # 競馬場
    course_type: str  # 芝/ダート
    distance: str
    track_condition: str  # 馬場状態
    weather: str
    start_time: str
    race_grade: str  # G1, G2, etc.
    entries: list[HorseEntry] = field(default_factory=list)


@dataclass
class RaceListItem:
    """レース一覧の項目"""
    race_id: str
    race_number: str
    race_name: str
    start_time: str
    course_info: str  # "芝2000m" など
    venue: str
    horse_count: str
