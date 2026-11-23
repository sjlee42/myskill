#!/usr/bin/env python3
"""지원서 글자 수 세기 (한국어 지원서 기준).

사용법:
  python3 count.py draft/q1.md [draft/q2.md ...] [--limit 1000] [--no-spaces] [--count-newlines]

- 공백 포함: 띄어쓰기를 세고, 줄바꿈은 세지 않는다 (대부분의 지원 시스템 기준)
- 공백 제외: 띄어쓰기, 탭, 줄바꿈을 모두 뺀다
- --no-spaces 를 주면 limit 비교를 공백 제외 기준으로 한다
- --count-newlines 를 주면 공백 포함 수에 본문 내부 줄바꿈도 한 글자씩 더한다 (JS length 기준 폼용)
"""
import argparse
import sys


def count(text: str, count_newlines: bool = False) -> tuple[int, int]:
    body = text.strip().replace("\r", "")
    with_spaces = len(body.replace("\n", ""))
    if count_newlines:
        with_spaces += body.count("\n")
    without_spaces = len("".join(body.split()))
    return with_spaces, without_spaces


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    p.add_argument("--limit", type=int)
    p.add_argument("--no-spaces", action="store_true")
    p.add_argument("--count-newlines", action="store_true")
    a = p.parse_args()

    for f in a.files:
        try:
            with open(f, encoding="utf-8") as fh:
                w, wo = count(fh.read(), a.count_newlines)
        except OSError as e:
            print(f"{f}: 읽기 실패 ({e})")
            continue
        line = f"{f}: 공백 포함 {w}자 / 공백 제외 {wo}자"
        if a.limit:
            base = wo if a.no_spaces else w
            pct = base * 100 / a.limit
            if base > a.limit:
                status = f"초과 {base - a.limit}자"
            elif pct < 90:
                status = f"부족 ({a.limit * 9 // 10 - base}자 더 쓰면 90%)"
            else:
                status = "적정"
            label = "공백 제외" if a.no_spaces else "공백 포함"
            line += f" | 기준 {label} {a.limit}자 중 {pct:.0f}% → {status}"
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
