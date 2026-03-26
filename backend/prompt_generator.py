"""GenSpark用プロンプト生成 - 予想精度向上のため情報量を大幅拡充"""
from models import RaceInfo, HorseEntry


def _analyze_running_style(past_races) -> str:
    """通過順位から脚質を推定"""
    if not past_races:
        return "不明"
    
    styles = []
    for pr in past_races:
        if not pr.passing:
            continue
        positions = pr.passing.split("-")
        if not positions:
            continue
        try:
            first_pos = int(positions[0])
            field = int(pr.field_size) if pr.field_size else 16
            ratio = first_pos / max(field, 1)
            if ratio <= 0.2:
                styles.append("逃げ")
            elif ratio <= 0.4:
                styles.append("先行")
            elif ratio <= 0.7:
                styles.append("差し")
            else:
                styles.append("追込")
        except (ValueError, IndexError):
            continue
    
    if not styles:
        return "不明"
    
    # 最も多い脚質
    from collections import Counter
    counter = Counter(styles)
    main_style = counter.most_common(1)[0][0]
    return main_style


def _analyze_weight_trend(past_races) -> str:
    """馬体重の推移を分析"""
    weights = []
    for pr in past_races:
        if pr.horse_weight:
            import re
            m = re.match(r'(\d+)', pr.horse_weight)
            if m:
                weights.append(int(m.group(1)))
    
    if len(weights) < 2:
        return ""
    
    # 最新から古い順 (past_racesは新しい順)
    latest = weights[0]
    oldest = weights[-1]
    diff = latest - oldest
    
    if diff > 10:
        return f"増加傾向(+{diff}kg / {len(weights)}走)"
    elif diff < -10:
        return f"減少傾向({diff}kg / {len(weights)}走)"
    else:
        return f"安定({latest}kg前後)"


def _analyze_distance_aptitude(past_races, target_distance: str) -> str:
    """距離適性を分析"""
    import re
    target_m = re.search(r'(\d+)', target_distance)
    if not target_m:
        return ""
    target_dist = int(target_m.group(1))
    
    results_at_dist = []
    results_shorter = []
    results_longer = []
    
    for pr in past_races:
        dist_m = re.search(r'(\d+)', pr.course)
        if not dist_m:
            continue
        dist = int(dist_m.group(1))
        try:
            pos = int(pr.position)
        except (ValueError, TypeError):
            continue
        
        if abs(dist - target_dist) <= 200:
            results_at_dist.append(pos)
        elif dist < target_dist - 200:
            results_shorter.append(pos)
        else:
            results_longer.append(pos)
    
    parts = []
    if results_at_dist:
        avg = sum(results_at_dist) / len(results_at_dist)
        parts.append(f"同距離帯: {len(results_at_dist)}走 平均{avg:.1f}着")
    if results_shorter:
        avg = sum(results_shorter) / len(results_shorter)
        parts.append(f"短距離: {len(results_shorter)}走 平均{avg:.1f}着")
    if results_longer:
        avg = sum(results_longer) / len(results_longer)
        parts.append(f"長距離: {len(results_longer)}走 平均{avg:.1f}着")
    
    return " / ".join(parts) if parts else ""


def _analyze_track_aptitude(past_races, target_condition: str) -> str:
    """馬場状態別成績"""
    good = []  # 良
    soft = []  # 稍重/重/不良
    
    for pr in past_races:
        try:
            pos = int(pr.position)
        except (ValueError, TypeError):
            continue
        
        if pr.track_condition in ("良",):
            good.append(pos)
        elif pr.track_condition in ("稍重", "稍", "重", "不良", "不"):
            soft.append(pos)
    
    parts = []
    if good:
        avg = sum(good) / len(good)
        parts.append(f"良馬場: {len(good)}走 平均{avg:.1f}着")
    if soft:
        avg = sum(soft) / len(soft)
        parts.append(f"道悪: {len(soft)}走 平均{avg:.1f}着")
    
    return " / ".join(parts) if parts else ""


def _get_last3f_stats(past_races) -> str:
    """上がり3Fの統計"""
    times = []
    for pr in past_races:
        if pr.last_3f:
            try:
                times.append(float(pr.last_3f))
            except ValueError:
                continue
    if not times:
        return ""
    
    best = min(times)
    avg = sum(times) / len(times)
    return f"最速{best:.1f}秒 / 平均{avg:.1f}秒 ({len(times)}走)"


def generate_prompt(race_info: RaceInfo, source: str = "jra") -> str:
    """レース情報からGenSparkに投げるプロンプトを生成（情報量大幅拡充版）"""
    lines = []

    source_label = "地方競馬" if source == "nar" else "中央競馬(JRA)"

    # === ヘッダー ===
    lines.append(f"以下の{source_label}レースの全データを詳細に分析し、馬券の買い目を予想してください。")
    lines.append("データに基づく根拠付きで、三連複・馬連・ワイドのおすすめ買い目を提案してください。")
    lines.append("また、各馬の評価（◎本命 ○対抗 ▲単穴 △連下 ×消し）も付けてください。")
    lines.append("特に、「期待値」の観点（オッズに対して実力が上回る馬）を重視してください。")
    lines.append("")
    lines.append("=" * 60)

    # === レース基本情報 ===
    lines.append("【レース基本情報】")
    grade_str = f" ({race_info.race_grade})" if race_info.race_grade else ""
    lines.append(f"  開催: {source_label}")
    lines.append(f"  レース名: {race_info.race_name}{grade_str}")
    if race_info.date:
        lines.append(f"  日付: {race_info.date}")
    lines.append(f"  競馬場: {race_info.venue} {race_info.race_number}R")
    lines.append(f"  コース: {race_info.course_type}{race_info.distance}")
    if race_info.track_condition:
        lines.append(f"  馬場状態: {race_info.track_condition}")
    if race_info.weather:
        lines.append(f"  天候: {race_info.weather}")
    lines.append(f"  発走時刻: {race_info.start_time}")
    lines.append(f"  出走頭数: {len(race_info.entries)}頭")
    lines.append("")

    # === 展開予想用の脚質分布サマリー ===
    lines.append("=" * 60)
    lines.append("【脚質分布・展開予想材料】")
    style_counts = {"逃げ": [], "先行": [], "差し": [], "追込": [], "不明": []}
    for entry in race_info.entries:
        style = _analyze_running_style(entry.past_races)
        style_counts[style].append(f"{entry.horse_number}番{entry.horse_name}")
    
    for style_name in ["逃げ", "先行", "差し", "追込"]:
        horses = style_counts[style_name]
        if horses:
            lines.append(f"  {style_name}({len(horses)}頭): {', '.join(horses)}")
    
    escape_count = len(style_counts["逃げ"])
    front_count = len(style_counts["先行"])
    if escape_count == 0:
        lines.append("  ※ 逃げ馬不在 → スローペースの可能性")
    elif escape_count >= 3:
        lines.append("  ※ 逃げ馬多数 → ハイペースの可能性（差し・追込有利か）")
    elif escape_count == 1 and front_count <= 2:
        lines.append("  ※ 逃げ1頭のみ → マイペース逃げの可能性（逃げ馬要注意）")
    lines.append("")

    # === 出走馬詳細データ ===
    lines.append("=" * 60)
    lines.append("【出走馬 詳細データ】")
    lines.append("")

    for entry in race_info.entries:
        lines.append(f"{'='*50}")
        lines.append(f"■ {entry.bracket_number}枠{entry.horse_number}番 {entry.horse_name}")
        lines.append(f"  性齢: {entry.sex_age}  |  斤量: {entry.weight}kg  |  騎手: {entry.jockey_name}  |  調教師: {entry.trainer}")
        
        if entry.horse_weight:
            lines.append(f"  馬体重: {entry.horse_weight}")

        if entry.odds:
            lines.append(f"  単勝オッズ: {entry.odds}倍 ({entry.popularity}番人気)")

        # --- 脚質分析 ---
        style = _analyze_running_style(entry.past_races)
        lines.append(f"  推定脚質: {style}")

        # --- 上がり3F統計 ---
        last3f_stats = _get_last3f_stats(entry.past_races)
        if last3f_stats:
            lines.append(f"  上がり3F: {last3f_stats}")

        # --- 馬体重推移 ---
        weight_trend = _analyze_weight_trend(entry.past_races)
        if weight_trend:
            lines.append(f"  馬体重推移: {weight_trend}")

        # --- 距離適性 ---
        dist_apt = _analyze_distance_aptitude(entry.past_races, race_info.distance)
        if dist_apt:
            lines.append(f"  距離適性: {dist_apt}")

        # --- 馬場適性 ---
        if race_info.track_condition:
            track_apt = _analyze_track_aptitude(entry.past_races, race_info.track_condition)
            if track_apt:
                lines.append(f"  馬場適性: {track_apt}")

        # --- 騎手情報 ---
        if entry.jockey_info:
            ji = entry.jockey_info
            lines.append(f"  【騎手成績】{ji.name}")
            lines.append(f"    通算: {ji.rides}騎乗 {ji.wins}勝 | 勝率{ji.win_rate} | 連対率{ji.place_rate} | 複勝率{ji.show_rate}")

        # --- 過去成績 ---
        if entry.past_races:
            lines.append(f"  【過去成績（直近{len(entry.past_races)}走）】")
            for i, pr in enumerate(entry.past_races, 1):
                # メインライン
                line_parts = [
                    f"    {i}. {pr.date}",
                    pr.venue,
                    pr.race_name,
                    f"({pr.course}",
                    f"馬場:{pr.track_condition})",
                ]
                lines.append(" ".join(p for p in line_parts if p))
                
                # 成績ライン
                result_parts = [
                    f"       → {pr.position}着/{pr.field_size}頭",
                    f"タイム:{pr.time}",
                    f"着差:{pr.margin}",
                ]
                if pr.passing:
                    result_parts.append(f"通過:{pr.passing}")
                if pr.last_3f:
                    result_parts.append(f"上がり:{pr.last_3f}")
                lines.append("  ".join(p for p in result_parts if p))
                
                # 補足ライン
                extra_parts = []
                if pr.odds and pr.popularity:
                    extra_parts.append(f"オッズ:{pr.odds}({pr.popularity}人気)")
                extra_parts.append(f"騎手:{pr.jockey}")
                extra_parts.append(f"斤量:{pr.weight}")
                if pr.horse_weight:
                    extra_parts.append(f"馬体重:{pr.horse_weight}")
                if pr.winner:
                    extra_parts.append(f"勝ち馬:{pr.winner}")
                lines.append("       " + "  ".join(extra_parts))

        lines.append("")

    # === 分析指示 ===
    lines.append("=" * 60)
    lines.append("【予想で重視してほしいポイント】")
    lines.append("")
    lines.append("1. 展開予想:")
    lines.append("   - 上記の脚質分布から、レースのペース（ハイ/ミドル/スロー）を予想")
    lines.append("   - 逃げ馬・先行馬の数とペースが有利不利に与える影響")
    lines.append("")
    lines.append("2. 各馬の近走トレンド:")
    lines.append("   - 着順の推移（上昇/下降/安定）")
    lines.append("   - 上がり3Fタイムの推移（末脚の質）")
    lines.append("   - 馬体重の変動（仕上がり状態の判断）")
    lines.append("")
    lines.append("3. コース適性:")
    lines.append("   - 今回と同距離帯での成績")
    lines.append("   - 芝/ダート適性")
    lines.append("   - 左回り/右回り適性")
    lines.append("")
    lines.append("4. 馬場状態への適性:")
    lines.append("   - 良馬場/道悪での成績差")
    lines.append("   - 今日の馬場状態で力を発揮できるか")
    lines.append("")
    lines.append("5. 枠順の有利不利:")
    lines.append("   - 内枠/外枠の影響（特に短距離・小回りコース）")
    lines.append("   - 脚質と枠順の組み合わせ")
    lines.append("")
    lines.append("6. 騎手の腕前:")
    lines.append("   - 騎手の勝率・複勝率から信頼度を評価")
    lines.append("   - 乗り替わりの影響")
    lines.append("")
    lines.append("7. オッズとの乖離（期待値分析）:")
    lines.append("   - 実力に対してオッズが高い（過小評価されている）馬")
    lines.append("   - 過大評価されている人気馬")
    lines.append("")

    if source == "nar":
        lines.append("8. 地方競馬特有の要素:")
        lines.append("   - 小回りコースでの先行・内枠有利")
        lines.append("   - 砂質の違いによる馬場適性")
        lines.append("   - 所属厩舎の地元有利")
        lines.append("   - 地方⇔中央の転入/転出馬の実力差")
        lines.append("")

    lines.append("=" * 60)
    lines.append("【出力形式】")
    lines.append("1. レース展開予想（ペース・隊列イメージ）")
    lines.append("2. 各馬の評価（◎○▲△× + 一言コメント）")
    lines.append("3. おすすめ買い目:")
    lines.append("   - 三連複（3〜5点、各100〜300円）")
    lines.append("   - 馬連（2〜3点、各300〜500円）")
    lines.append("   - ワイド（2〜3点、各200〜500円）")
    lines.append("4. 予算: 3,000円以内")
    lines.append("5. 自信度: ★〜★★★★★")
    lines.append("")
    lines.append("データに基づいた論理的な予想をお願いします。")

    return "\n".join(lines)
