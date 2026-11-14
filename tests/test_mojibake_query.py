"""K-04: the accent-loss (v1) detector does not read a URL query string as corruption.

P1 (KNN, IP-013): "GET /v1/partner/reports?range=2026-13" in a checklist came back as `accent-loss`
on every `doctor`. A lost accent is never followed by `name=`; `m?s` and `Decis?es` still count.
"""
from __future__ import annotations

import pytest

from sdd_cli import _mojibake


def _v1_hits(tmp_path, raw: bytes) -> int:
    path = tmp_path / "x.md"
    path.write_bytes(raw)
    return len(_mojibake.scan_file(path).v1)


@pytest.mark.parametrize("raw", [
    b"`GET /v1/partner/reports?range=2026-13` returns 500",
    b"/search?a=1&b=2",
    b"https://example.com/p?page_size=10",
    b"call(items?filter[status]=open)",
])
def test_a_query_string_is_not_accent_loss(tmp_path, raw):
    assert _v1_hits(tmp_path, raw) == 0


@pytest.mark.parametrize("raw, expected", [
    (b"o m?s atual", 1),
    (b"Decis?es de projeto", 1),
    (b"aplica??o", 1),
    (b"`reports?range=1` e tamb?m o m?s", 2),     # the URL is skipped, the two lost accents are not
    (b"pergunta?palavra sem igual", 1),           # `?` + word without `=`: still a suspect
])
def test_real_accent_loss_next_to_it_still_counts(tmp_path, raw, expected):
    assert _v1_hits(tmp_path, raw) == expected
