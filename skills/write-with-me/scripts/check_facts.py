#!/usr/bin/env python3
"""초안의 숫자가 근거 자료(material.md)에 있는지 기계적으로 확인한다.

사용법:
  python3 check_facts.py draft/q1.md [draft/q2.md ...] --material material.md [--notice brief.md] [--json]

- --material: 사용자 답변. 불확실 표현 옆의 숫자는 △로 본다.
- --notice: 공고·문항 원문(brief.md). 여기 있는 숫자("2주 동안")는 불확실 표현 검사 없이 근거로 친다.

- 초안에서 숫자 표현(1,200명 / 3.5% / 2025년 / 두 배 / 세 번 / 절반 등)을 뽑아
  material.md에 같은 값이 있는지 본다. 쉼표·공백은 무시하고 한국어 수사는 숫자로,
  "퍼센트"는 "%"로 바꿔 비교한다. '#'로 시작하는 제목 줄은 건너뛴다.
- ✗ 값이 material에 없음 / △ 값만 일치(단위 다름) 또는 모호한 표현 안의 값
- 종료 코드: ✗가 하나라도 있으면 1, 없으면 0, 파일이 없으면 2 (△는 0)

한계:
- 값이 우연히 일치하면 못 잡는다 (초안 "2배", material 어딘가의 "2팀").
- 숫자가 아닌 사실(회사명, 수상 여부, 역할 등)은 못 잡는다.
- 모호한 표현 안의 값: 근거 파일에서 그 값이 한 번이라도 "정확히는 모르겠어요", "대략",
  "쯤", `[수치: 모름]`, 물음표 같은 불확실 표현 근처(같은 줄 앞뒤 25자)에 나오면 일치로
  치지 않고 △(모호)로 표시한다. 다른 곳에 확실하게 나와도 마찬가지다. 단, 같은 값이
  --notice(공고·문항)에 있으면 문항이 정한 숫자로 보고 통과시킨다. 사용자 확인이 필요하다는 뜻이며 종료 코드는 바꾸지 않는다.
- "하나/둘", "수십" 같은 수사는 보지 않는다. "한 번", "한 팀"처럼 1을 뜻하는 "한"과
  "두 가지"처럼 "가지"로 세는 표현은 수량 주장이 아닌 관용 표현이 대부분이라 건너뛴다.
"""
import argparse
import json
import re
import sys

KO_NUM = {"한": 1, "두": 2, "세": 3, "네": 4, "다섯": 5, "여섯": 6, "일곱": 7,
          "여덟": 8, "아홉": 9, "열": 10, "스무": 20, "서른": 30}
KO_UNITS = ["시간", "가지", "배", "번", "명", "개", "팀", "달", "해", "주"]
AR_UNITS = ["퍼센트", "시간", "가지", "%", "명", "개", "배", "번", "회", "위", "년",
            "월", "일", "주", "분", "만", "천", "억", "팀", "건", "점", "등", "달",
            "해", "원", "대", "곳", "차", "기", "살"]
HEDGES = ["모르", "정확히는", "정확하지", "아마", "대략", "쯤", "정도", "어림", "기억", "것 같", "같아",
          "한두", "한 두", "모름", "?"]

TOKEN = re.compile(
    r"(?P<ar>(?<![A-Za-z\d])\d+(?:,\d{3})*(?:\.\d+)?)[ ]?(?P<aru>" + "|".join(AR_UNITS) + r")?"
    r"|(?P<ko>(?<![가-힣])(?:" + "|".join(KO_NUM) + r"))\s*(?P<kou>" + "|".join(KO_UNITS) + r")"
    r"|(?P<half>절반)"
)


def norm_unit(u: str) -> str:
    return "%" if u == "퍼센트" else (u or "")


def norm_num(s: str) -> str:
    s = s.replace(",", "")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.lstrip("0") or "0" if "." not in s else s


def tokens(text: str):
    """(값, 단위, 원문, 시작 위치) 목록."""
    out = []
    for m in TOKEN.finditer(text):
        if m.group("ar"):
            out.append((norm_num(m.group("ar")), norm_unit(m.group("aru")), m.group(0).strip(), m.start()))
        elif m.group("ko"):
            if m.group("ko") == "한" or m.group("kou") == "가지":
                continue  # 관용 표현(한 번, 한 팀, 두 가지)
            out.append((str(KO_NUM[m.group("ko")]), norm_unit(m.group("kou")), m.group(0), m.start()))
        else:
            out.append(("절반", "", "절반", m.start()))
    return out


def material_index(text: str, idx=None, hedge_check=True):
    """값 -> [(단위, 모호 여부)]"""
    idx = {} if idx is None else idx
    for val, unit, raw, pos in tokens(text):
        ls = text.rfind("\n", 0, pos) + 1
        le = text.find("\n", pos)
        le = len(text) if le < 0 else le
        window = text[max(ls, pos - 25): min(le, pos + len(raw) + 25)]
        hedged = hedge_check and any(h in window for h in HEDGES)
        idx.setdefault(val, []).append((unit, hedged, not hedge_check))
        if val == "50" and unit == "%":
            idx.setdefault("절반", []).append(("", hedged, not hedge_check))
    return idx


def check(draft: str, idx: dict) -> list:
    items = []
    for ln, line in enumerate(draft.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        for val, unit, raw, _ in tokens(line):
            cands = idx.get(val, [])
            same = [c for c in cands if not unit or not c[0] or c[0] == unit]
            if not cands:
                st, why = "missing", f"material.md에 {val} 없음"
            elif not same:
                st, why = "unit", f"값 {val}은 있으나 단위가 다름"
            elif any(n and u == unit for u, _, n in same):
                st, why = "ok", ""
            elif any(h for _, h, _ in same):
                st, why = "vague", f"값 {val}은 있으나 모호한 표현 안에만 있음 (사용자 확인 필요)"
            else:
                st, why = "ok", ""
            items.append({"line": ln, "text": raw, "value": val, "unit": unit, "status": st, "reason": why})
    return items


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    p.add_argument("--material", nargs="+", required=True)
    p.add_argument("--notice", nargs="*", default=[])
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    idx = {}
    for m, hedge in [(m, True) for m in a.material] + [(n, False) for n in a.notice]:
        try:
            with open(m, encoding="utf-8") as fh:
                material_index(fh.read(), idx, hedge)
        except OSError as e:
            print(f"{m}: 읽기 실패 ({e})", file=sys.stderr)
            return 2
    src = ", ".join(a.material + a.notice)
    results = {}
    for f in a.files:
        try:
            with open(f, encoding="utf-8") as fh:
                results[f] = check(fh.read(), idx)
        except OSError as e:
            print(f"{f}: 읽기 실패 ({e})", file=sys.stderr)
            return 2

    missing_total = 0
    if a.json:
        out = {}
        for f, items in results.items():
            miss = sum(i["status"] == "missing" for i in items)
            missing_total += miss
            out[f] = {"total": len(items), "missing": miss,
                      "issues": [i for i in items if i["status"] != "ok"]}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        mark = {"missing": "✗", "unit": "△", "vague": "△"}
        for f, items in results.items():
            miss = sum(i["status"] == "missing" for i in items)
            missing_total += miss
            issues = [i for i in items if i["status"] != "ok"]
            if not issues:
                print(f"{f}: 숫자 {len(items)}개 — 모든 숫자가 {src}에 있음")
                continue
            print(f"{f}: 숫자 {len(items)}개 중 {miss}개가 {src}에 없음")
            for i in issues:
                print(f'  {mark[i["status"]]} {i["line"]}행 "{i["text"]}" ← {i["reason"]}')
    return 1 if missing_total else 0


if __name__ == "__main__":
    sys.exit(main())
