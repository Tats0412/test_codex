# AI Vocal Trainer (Karaoke Coach)

歌った録音をアップすると、その楽曲に合わせたワンポイント・改善点・
練習メニューを日本語で返してくれる AI ボーカルトレーナーです。

- `mobile/` — Expo (React Native) アプリ (iOS / Android / Web)
- `server/` — FastAPI バックエンド。`librosa` で音響特徴量を抽出し、
  Claude Sonnet 4.6 に渡してコーチングコメントを生成します。

## アーキテクチャ

```
[Expo App]  --(multipart: audio + 曲名)-->  [FastAPI]
                                                |
                                                |-- librosa: ピッチ/ビブラート/
                                                |            リズム/ダイナミクス
                                                |
                                                |-- Claude API (claude-sonnet-4-6)
                                                |     特徴量 + 曲名 → JSONアドバイス
                                                v
[Expo App]  <--(feedback JSON)----------------
```

> Claude は音声ファイルを直接は処理しません。サーバーで抽出した数値
> (音程の安定度、ビブラート速度、リズムの規則性 等) を文字情報として
> 渡し、Claude が持つ楽曲知識と突き合わせてコメントを生成します。

## クイックスタート

### 1. バックエンド

```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # ANTHROPIC_API_KEY を設定

# ffmpeg が必要
# macOS: brew install ffmpeg
# Ubuntu: sudo apt-get install ffmpeg libsndfile1

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. モバイルアプリ

```bash
cd mobile
npm install
# app.json の expo.extra.apiBaseUrl をサーバーの URL に変更
npx expo start
```

Expo Go アプリで QR を読み取るか、シミュレータで起動。

## 機能

- [x] 録音 → サーバー → AIフィードバック の一連のフロー
- [x] 曲名・アーティスト・気になっている点の入力
- [x] 4項目スコア(音程/リズム/表現/安定)+ ワンポイント
- [x] 良かった点・改善点・練習ドリル・次回の宿題の提示
- [x] **お手本音源との比較**: DTWでタイミング整列 → 自動キー合わせ → 音程ズレ区間検出
- [x] **練習履歴**: SQLiteに保存、一覧と詳細画面で再閲覧
- [x] **音程推移グラフ**: 録音のピッチ輪郭を SVG で表示
- [x] **録音再生**: 解析前に自分の声を聴き直せる

## 今後の拡張候補

- [ ] Whisper 連携で歌詞を文字起こしし、歌詞単位のフィードバック
- [ ] スコア推移グラフ / マイ課題曲登録
- [ ] 曲別の難所データベース(サビの最高音、裏拍の取り方 等)
- [ ] 複数アカウント対応 (認証)
