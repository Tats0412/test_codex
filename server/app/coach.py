"""Turns audio features + song metadata into vocal-coach feedback via Claude."""

from __future__ import annotations

import json
import os
from typing import Any

from anthropic import Anthropic

SYSTEM_PROMPT = """あなたは経験豊富なボーカルトレーナー兼カラオケコーチです。
ユーザーの歌唱録音から抽出された音響特徴量と曲情報を受け取り、
その曲の歌唱に特化した実践的なアドバイスを日本語で返します。

出力は必ず次の JSON スキーマに従ってください(前後に余計な文字を付けない):
{
  "overall_score": number,              // 0-100 の総合点
  "scores": {
    "pitch": number,                    // 0-100 音程
    "rhythm": number,                   // 0-100 リズム
    "expression": number,               // 0-100 表現力(強弱・ビブラート)
    "stability": number                 // 0-100 声の安定
  },
  "one_point": string,                  // 30-60字の今日のワンポイント
  "strengths": [string, string, ...],   // 良かった点 2-3個
  "improvements": [                     // 改善点 2-4個
    {"area": string, "detail": string, "drill": string}
  ],
  "song_specific": string,              // その曲の難所・特徴を踏まえた指摘(2-4文)
  "next_step": string                   // 次回までの具体的な練習課題 1文
}

数値の解釈目安:
- pitch_stability_cents: 10以下=非常に安定, 10-25=良い, 25-40=要改善, 40+=不安定
- in_tune_ratio: 0.85+ = 音程良好, 0.7-0.85 = 普通, 0.7未満 = 音程が甘い
- vibrato_rate_hz: 5-7Hz が自然なビブラート, 0またはそれ以下は平坦
- onset_regularity: 1.0に近いほど一定のリズム感
- dynamic_variation (dB std): 3以下=平坦, 3-6=適度, 6+=表現豊か
- longest_phrase_sec: 長いほど息が続いている

曲名からその楽曲のキー・難所(高音サビ、音域跳躍、特徴的なリズムなど)を
思い出し、具体的なセクション名や歌詞片(知っていれば)を用いてコメントしてください。
知らない曲の場合は一般論に留め、断定を避けてください。"""


USER_TEMPLATE = """曲名: {song_title}
アーティスト: {artist}
ユーザーの自己申告メモ: {user_note}

録音から抽出した特徴量 (JSON):
{features_json}

上記の特徴量とあなたがこの曲について知っていることを突き合わせ、
スキーマ通りの JSON のみを出力してください。"""


def _get_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return Anthropic(api_key=api_key)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        # Strip fenced code block if present
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip("` \n")
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object in model output: {text[:200]}")
    return json.loads(text[start : end + 1])


def generate_feedback(
    features: dict[str, Any],
    song_title: str,
    artist: str = "",
    user_note: str = "",
) -> dict[str, Any]:
    client = _get_client()
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

    user_message = USER_TEMPLATE.format(
        song_title=song_title or "(未指定)",
        artist=artist or "(未指定)",
        user_note=user_note or "(なし)",
        features_json=json.dumps(features, ensure_ascii=False, indent=2),
    )

    response = client.messages.create(
        model=model,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    return _extract_json(text)
