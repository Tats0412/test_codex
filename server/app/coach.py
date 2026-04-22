"""Turns audio features + song metadata into vocal-coach feedback via Claude."""

from __future__ import annotations

import json
import os
from typing import Any

from anthropic import Anthropic

SYSTEM_PROMPT = """あなたは経験豊富なボーカルトレーナー兼カラオケコーチです。
ユーザーの歌唱録音から抽出された音響特徴量と曲情報、必要に応じてお手本音源との
比較結果を受け取り、その曲の歌唱に特化した実践的なアドバイスを日本語で返します。

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
  "timestamped_notes": [                // 参照音源がある場合のみ、該当セクションへのコメント
    {"start_sec": number, "end_sec": number, "comment": string}
  ],
  "next_step": string                   // 次回までの具体的な練習課題 1文
}

数値の解釈目安:
- pitch_stability_cents: 10以下=非常に安定, 10-25=良い, 25-40=要改善, 40+=不安定
- in_tune_ratio: 0.85+ = 音程良好, 0.7-0.85 = 普通, 0.7未満 = 音程が甘い
- vibrato_rate_hz: 5-7Hz が自然なビブラート, 0またはそれ以下は平坦
- onset_regularity: 1.0に近いほど一定のリズム感
- dynamic_variation (dB std): 3以下=平坦, 3-6=適度, 6+=表現豊か
- longest_phrase_sec: 長いほど息が続いている

参照音源との比較がある場合:
- key_offset_semitones が 0 以外 → 原曲と違うキーで歌っている(指摘してよい)
- avg_abs_cents_off: 20以下=非常に正確, 20-40=良い, 40-70=音程が甘い, 70+=要注意
- problem_segments: 音程が50セント以上ズレた区間。timestamped_notes で具体的に言及。
- timing_offset_sec: 正の値は「全体的に遅れ気味」、負の値は「突っ込み気味」

曲名からその楽曲のキー・難所(高音サビ、音域跳躍、特徴的なリズムなど)を
思い出し、具体的なセクション名や歌詞片(知っていれば)を用いてコメントしてください。
知らない曲の場合は一般論に留め、断定を避けてください。
timestamped_notes は参照音源がない場合は空配列にしてください。"""


USER_TEMPLATE = """曲名: {song_title}
アーティスト: {artist}
ユーザーの自己申告メモ: {user_note}

録音から抽出した特徴量 (JSON):
{features_json}
{comparison_block}
上記の情報とあなたがこの曲について知っていることを突き合わせ、
スキーマ通りの JSON のみを出力してください。"""


_CONTOUR_KEYS = {"pitch_contour_midi", "loudness_contour_db", "contour_times_sec"}


def _get_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return Anthropic(api_key=api_key)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
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
    comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    client = _get_client()
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

    # Strip time-series contours from Claude prompt (keep response compact)
    scalar_features = {k: v for k, v in features.items() if k not in _CONTOUR_KEYS}

    comparison_block = ""
    if comparison:
        comparison_block = (
            "\n\nお手本音源との比較 (JSON):\n"
            + json.dumps(comparison, ensure_ascii=False, indent=2)
            + "\n"
        )

    user_message = USER_TEMPLATE.format(
        song_title=song_title or "(未指定)",
        artist=artist or "(未指定)",
        user_note=user_note or "(なし)",
        features_json=json.dumps(scalar_features, ensure_ascii=False, indent=2),
        comparison_block=comparison_block,
    )

    response = client.messages.create(
        model=model,
        max_tokens=1800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    return _extract_json(text)
