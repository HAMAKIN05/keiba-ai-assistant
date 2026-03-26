# 競馬予想 AI アシスタント 🏇

データ分析 × GenSpark で競馬予想の的中率を上げるためのWebアプリです。

中央競馬(JRA)・地方競馬(NAR) 両対応。レースデータを自動収集し、GenSparkに最適化されたプロンプトを1クリックでコピーできます。

## 機能

- **中央/地方 切り替え** - JRA（土日）と NAR（平日毎日）をタブで切替
- **レース一覧** - 日付ごとの全レースを競馬場別に表示（発走時刻付き）
- **出走馬データ** - 馬名・騎手・斤量・馬体重・オッズ・人気
- **過去5走成績** - 着順・タイム・通過順・上がり3F・馬場状態・着差・勝ち馬
- **騎手成績** - 通算騎乗数・勝利数・勝率・連対率・複勝率
- **AI分析プロンプト** - 脚質分析・展開予想・距離適性・馬場適性を含む詳細プロンプトを自動生成
- **1クリックコピー** - GenSparkにそのまま貼り付けて予想を得られる

## セットアップ

### Docker（推奨）

```bash
git clone https://github.com/YOUR_USERNAME/keiba-ai-assistant.git
cd keiba-ai-assistant

# 起動
docker compose up -d

# → http://localhost:8000 でアクセス
```

### ローカル開発

```bash
# バックエンド
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# フロントエンド（別ターミナル）
cd frontend
npm install
npm run dev    # → http://localhost:5173（開発サーバー）
npm run build  # → dist/ に本番ビルド（FastAPIが配信）
```

## 使い方

1. 中央競馬 or 地方競馬を選択
2. 日付を選択（地方なら今日、中央なら直近の土日）
3. レースを選択
4. 「GenSpark プロンプト」タブを開く
5. 「プロンプトをコピーする」ボタンをクリック
6. [GenSpark](https://www.genspark.ai) を開いて貼り付け → 送信

## プロンプトに含まれる情報

| カテゴリ | データ |
|---|---|
| レース基本 | 競馬場・距離・コース・馬場・天候・頭数 |
| 出走馬 | 馬名・性齢・斤量・騎手・調教師・馬体重・オッズ |
| 過去成績 | 直近5走（着順・タイム・通過順・上がり3F・馬場・着差・勝ち馬） |
| 騎手 | 通算成績（勝率・連対率・複勝率） |
| AI分析 | 脚質推定・展開予想・距離適性・馬場適性・馬体重推移・上がり3F統計 |

## 技術スタック

- **フロントエンド**: React + Tailwind CSS + Vite
- **バックエンド**: Python FastAPI
- **データ取得**: netkeiba.com スクレイピング (httpx + BeautifulSoup)
- **デプロイ**: Docker

## ディレクトリ構成

```
├── Dockerfile
├── docker-compose.yml
├── backend/
│   ├── main.py              # FastAPI アプリ
│   ├── scraper.py           # netkeiba スクレイパー
│   ├── prompt_generator.py  # GenSpark プロンプト生成
│   ├── models.py            # データモデル
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   └── components/
    │       ├── DateSelector.jsx
    │       ├── RaceList.jsx
    │       ├── RaceDetail.jsx
    │       └── PromptViewer.jsx
    ├── package.json
    └── index.html
```

## VPS等へのデプロイ例

```bash
# サーバーにDockerがインストールされていれば
git clone https://github.com/YOUR_USERNAME/keiba-ai-assistant.git
cd keiba-ai-assistant
docker compose up -d

# 自動起動設定（再起動後も自動で立ち上がる）
# docker-compose.yml に restart: unless-stopped が設定済み
```

## 注意事項

- データは netkeiba.com からリアルタイムで取得しています
- 個人利用の範囲でお使いください
- 馬券の購入は自己責任でお願いします
