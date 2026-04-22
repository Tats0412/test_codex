from app.coach import _extract_json


def test_extract_json_plain():
    text = '{"overall_score": 80, "one_point": "hi"}'
    assert _extract_json(text)["overall_score"] == 80


def test_extract_json_fenced():
    text = """```json
{
  "overall_score": 75,
  "one_point": "keep going"
}
```"""
    data = _extract_json(text)
    assert data["overall_score"] == 75
    assert data["one_point"] == "keep going"


def test_extract_json_with_preamble():
    text = 'Here is the JSON:\n\n{"overall_score": 65}\nhope this helps'
    assert _extract_json(text)["overall_score"] == 65
