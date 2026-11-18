from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "reflow_srt_entries.py"

_spec = importlib.util.spec_from_file_location("reflow_srt_entries", SCRIPT)
reflow = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
sys.modules["reflow_srt_entries"] = reflow
_spec.loader.exec_module(reflow)


def clean(text: str, replacements: list[tuple[str, str]] | None = None) -> str:
    return reflow.clean_text(text, replacements or [], {})


def entry(text: str, start_ms: int = 0, end_ms: int = 4000):
    return reflow.Entry(index=1, start_ms=start_ms, end_ms=end_ms, text=text)


# --- 語助詞刪除 ---------------------------------------------------------------


def test_delete_list_contains_previously_missing_words():
    for word in ["耶", "啦", "的相關", "的這樣"]:
        assert word in reflow.WORDS_TO_DELETE


@pytest.mark.parametrize("word", reflow.WORDS_TO_DELETE)
def test_every_filler_word_is_deleted(word):
    result = clean(f"今天大盤{word}上漲")
    assert word not in result
    assert result == "今天大盤上漲"


def test_multiple_fillers_in_one_line():
    assert clean("嗯今天啦大盤耶然後上漲") == "今天大盤上漲"


# --- 開頭「那」的處理 -----------------------------------------------------------


def test_leading_na_is_trimmed():
    assert clean("那我們來看台積電") == "我們來看台積電"


@pytest.mark.parametrize("prefix", reflow.KEEP_NA_PREFIXES)
def test_kept_na_prefixes_are_preserved(prefix):
    assert clean(f"{prefix}股票") == f"{prefix}股票"


def test_na_in_middle_is_untouched():
    assert clean("我們看那檔股票") == "我們看那檔股票"


# --- words.csv 替換 ------------------------------------------------------------


def test_replacements_are_applied():
    assert clean("台機電漲停", [("台機電", "台積電")]) == "台積電漲停"


def test_load_replacements_skips_invalid_rows(tmp_path):
    csv_path = tmp_path / "words.csv"
    csv_path.write_text("台機電,台積電\n只有一欄\n相同,相同\n,空白\n", encoding="utf-8")
    assert reflow.load_replacements(csv_path) == [("台機電", "台積電")]


# --- 字幕拆分與丟棄 -------------------------------------------------------------


def test_entry_becomes_empty_is_dropped():
    stats: dict[str, int] = {}
    assert reflow.split_entry(entry("嗯啊"), [], stats) == []
    assert stats["drop:empty"] == 1


def test_single_char_entry_is_dropped():
    stats: dict[str, int] = {}
    assert reflow.split_entry(entry("嗯好"), [], stats) == []
    assert stats["drop:single_char"] == 1


def test_short_entry_keeps_original_timing():
    result = reflow.split_entry(entry("台積電今天上漲", 1000, 3000), [], {})
    assert [(e.start_ms, e.end_ms, e.text) for e in result] == [(1000, 3000, "台積電今天上漲")]


def test_long_entry_is_split_with_proportional_timing():
    text = "一二三四五六七八九十" * 5  # 50 字
    result = reflow.split_entry(entry(text, 1000, 6000), [], {})
    assert len(result) == 3
    assert all(len(e.text) <= reflow.MAX_CHARS for e in result)
    assert "".join(e.text for e in result) == text
    assert result[0].start_ms == 1000
    assert result[-1].end_ms == 6000
    for prev, nxt in zip(result, result[1:]):
        assert prev.end_ms == nxt.start_ms
    # 20 字 / 50 字 * 5000ms = 2000ms
    assert result[0].end_ms - result[0].start_ms == 2000


def test_english_words_are_not_broken():
    text = "今天 NVIDIA 和 Apple 都大漲而且 Microsoft 也跟著上漲"
    result = reflow.split_entry(entry(text), [], {})
    joined = " ".join(e.text for e in result)
    for word in ["NVIDIA", "Apple", "Microsoft"]:
        assert word in joined
    assert all(len(e.text) <= reflow.MAX_CHARS for e in result)


# --- 功能測試：完整 CLI 流程 ----------------------------------------------------


def test_cli_end_to_end(tmp_path):
    srt = tmp_path / "input.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\n嗯\n\n"
        "2\n00:00:02,000 --> 00:00:04,000\n那台機電今天漲啦\n\n"
        "3\n00:00:04,000 --> 00:00:10,000\n"
        + "一二三四五六七八九十" * 3
        + "耶\n",
        encoding="utf-8",
    )
    words = tmp_path / "words.csv"
    words.write_text("台機電,台積電\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(srt), str(words)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Entries: 3 -> 3" in proc.stdout

    entries = reflow.parse_srt(srt)
    assert [e.text for e in entries] == ["台積電今天漲", "一二三四五六七八九十" * 2, "一二三四五六七八九十"]
    assert [e.index for e in entries] == [1, 2, 3]
    assert entries[1].start_ms == 4000
    assert entries[-1].end_ms == 10000
