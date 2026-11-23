#!/usr/bin/env bash
# 외부 심사위원 실행: run_judge.sh <codex|agy> <프롬프트 파일> <결과 파일>
# - 빈 임시 폴더에서 실행해 사용자 파일에 접근하지 못하게 한다
# - 5분 제한. 실패하면 결과 파일에 "[실패] 이유"를 남긴다
# - 모델은 ~/.claude/write-with-me/config.md 에서 읽는다
set -u

judge="${1:-}"; prompt_file="${2:-}"; out_file="${3:-}"
if [[ -z "$judge" || ! -f "$prompt_file" || -z "$out_file" ]]; then
  echo "사용법: run_judge.sh <codex|agy> <프롬프트 파일> <결과 파일>" >&2; exit 2
fi

config="$HOME/.claude/write-with-me/config.md"
cfg() { [[ -f "$config" ]] && sed -n "s/^$1:[[:space:]]*\([^#]*\).*/\1/p" "$config" | head -1 | xargs; }

limit=300
run_limited() { perl -e 'alarm shift; exec @ARGV' "$limit" "$@"; }

prompt_abs="$(cd "$(dirname "$prompt_file")" && pwd)/$(basename "$prompt_file")"
mkdir -p "$(dirname "$out_file")"
out_abs="$(cd "$(dirname "$out_file")" && pwd)/$(basename "$out_file")"
sandbox="$(mktemp -d)"
err="$sandbox/stderr.txt"
cd "$sandbox" || exit 1

fail() { echo "[실패] $1" > "$out_abs"; [[ -s "$err" ]] && tail -5 "$err" >> "$out_abs"; rm -rf "$sandbox"; exit 1; }

case "$judge" in
  codex)
    command -v codex >/dev/null || fail "codex가 설치돼 있지 않음"
    model="$(cfg codex_model)"; effort="$(cfg codex_reasoning)"; effort="${effort:-medium}"
    args=(exec --skip-git-repo-check --ephemeral -s read-only -c "model_reasoning_effort=$effort" -o "$out_abs")
    [[ -n "$model" && "$model" != "기본값" ]] && args+=(-m "$model")
    run_limited codex "${args[@]}" < "$prompt_abs" > /dev/null 2> "$err"
    code=$?
    ;;
  agy)
    command -v agy >/dev/null || fail "agy(Antigravity CLI)가 설치돼 있지 않음"
    model="$(cfg agy_model)"; model="${model:-gemini-4-neon-medium}"
    run_limited agy -p "$(cat "$prompt_abs")" --model "$model" --print-timeout "$((limit - 10))s" < /dev/null > "$out_abs" 2> "$err"
    code=$?
    ;;
  *) fail "알 수 없는 심사위원: $judge" ;;
esac

if [[ $code -eq 142 ]]; then fail "시간 초과 (${limit}초)"; fi
if [[ $code -ne 0 ]]; then
  grep -qiE "auth|login|unauthor" "$err" 2>/dev/null && fail "로그인 필요: 터미널에서 '$judge'를 한 번 실행해 로그인하세요"
  fail "종료 코드 $code"
fi
[[ -s "$out_abs" ]] || fail "응답이 비어 있음"
rm -rf "$sandbox"
echo "완료: $out_abs"
