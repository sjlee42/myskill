# myskill

> **Claude Code skills by [@sjlee42](https://github.com/sjlee42).** Korean-first agent skills you can install as a Claude Code plugin, with the `skills` CLI, or by copying a folder.
>
> 직접 만든 Claude Code 스킬 모음입니다. 플러그인 마켓플레이스, `npx skills`, 폴더 복사 중 편한 방법으로 설치하세요.

**Keywords**: Claude Code skill, Agent Skills, SKILL.md, Claude Code plugin marketplace, 지원서, 자기소개서, 공모전, 해커톤, 인턴십, cover letter, application writing, interview-based writing, LLM-as-judge, multi-model review, Codex, Antigravity, MCP server search, Claude skill finder, plugin discovery, n8n templates, Korean

## 스킬 목록 / Skills

| Skill | 한 줄 요약 | 이럴 때 쓴다 (trigger) | 필요한 것 |
|---|---|---|---|
| [`write-with-me`](skills/write-with-me/SKILL.md) | 평가받는 글(지원서·자소서·공모전·해커톤·지원사업)을 **인터뷰로 내 말을 끌어내서** 쓰고, 여러 심사위원에게 블라인드 심사받는다 | "OO 지원서 써야 해", "자소서 같이 쓰자", "이 문항 어떻게 쓰지", "써 둔 지원서 봐 줘", "이어서 하자" | Claude Code. 선택: Codex CLI, Antigravity CLI(`agy`) |
| [`tool-finder`](skills/tool-finder/SKILL.md) | 필요한 기능으로 이미 만들어진 AI 도구(MCP·skill·플러그인·n8n·GitHub 에이전트)를 **여러 디렉터리에서 한 번에** 찾고, 지금도 동작하는지 설치 없이 확인한 뒤, 기능을 모두 덮는 조합을 근거와 함께 보여준다 | "MCP 찾아줘", "플러그인 찾아줘", "skill 있어?", "OO 하는 거 누가 만들어 둔 거 없나" | Claude Code, python3, curl, `gh`(로그인) |

## 설치 / Install

**Claude Code 플러그인 마켓플레이스** (권장)

```
/plugin marketplace add sjlee42/myskill
/plugin install write-with-me@myskill
/plugin install tool-finder@myskill
```

**skills CLI** ([skills.sh](https://skills.sh))

```bash
npx skills add sjlee42/myskill --skill write-with-me -a claude-code
npx skills add sjlee42/myskill --skill tool-finder -a claude-code
```

**직접 복사**

```bash
git clone https://github.com/sjlee42/myskill.git
cp -r myskill/skills/write-with-me ~/.claude/skills/
cp -r myskill/skills/tool-finder ~/.claude/skills/
```

설치한 뒤 새 세션을 열고 `/write-with-me`를 입력하거나 "지원서 쓰려고 해"처럼 말하면 시작됩니다. `tool-finder`는 "OO 하는 MCP 찾아줘"처럼 말하면 됩니다.

---

## write-with-me

AI에게 지원서를 맡기면 누구나 쓸 수 있는 일반론이 나옵니다. 문체 탓이 아니라 **재료가 없어서**입니다. 이 스킬은 순서를 뒤집습니다. 상대를 조사하고, 문항이 실제로 무엇을 묻는지 브리핑한 뒤, 경험을 하나씩 물어서 **사용자가 한 말로만** 씁니다.

### 흐름

| 단계 | 하는 일 |
|---|---|
| 0. 시작 | 대상과 문항 확인. 진입 경로 판단: 처음부터 / 써 둔 초안 보강 / 빠른 모드(마감 24시간 이내) |
| 1. 조사 | 서브에이전트 3개를 병렬로 돌린다: 공고·심사 구조 / 조직 / 지난 기수·심사평 |
| 2. 브리핑 | 심사위원 페르소나 설계. "이 문항이 실제로 묻는 것 → 필요한 재료". 경험 후보를 먼저 받아 문항에 배분 |
| 3. 인터뷰 | 질문은 한 번에 하나. 일반론이 나오면 구체적인 장면을 묻고, 미래 의견보다 과거 사실을 묻는다. 답은 원문 그대로 저장 |
| 4. 뼈대 | 문항별 한 줄 요지, 구성, 평가 포인트 대응. 사용자 승인 후 진행 |
| 5. 초안 | 재료에 없는 사실·경험·감정은 쓰지 않는다. 글자 수는 스크립트로 센다 |
| 6. 블라인드 심사 | 심사위원 3명(Claude)과 선택 심사위원(Codex, Antigravity). 인터뷰 기록은 보여 주지 않는다 |
| 7. 마무리 | 최종본, 제출 전 점검, 예상 면접 질문 |
| 8. 문체 메모 | 사용자가 고친 것 중 취향은 다음 글에도 반영 |

### 심사위원 패널

- 페르소나는 주최 기관이 아니라 **이 글을 실제로 읽는 단계의 심사자**를 기준으로 만든다. 1번 핵심 심사자, 2번 전문가, 3번 결정권자·외부인으로 나눈다.
- Claude Code만 있으면 Claude 3명이 심사한다. Codex나 Antigravity가 있으면 처음에 한 번 물어보고, 쓰기로 하면 다른 회사 모델로 교차 심사한다. 이름과 연락처는 가리고, 빈 임시 폴더에서 읽기 전용으로 실행한다.
- 취합할 때는 점수보다 **여러 심사위원이 같은 문장을 지적했는지**를 먼저 본다.

### 모델 배정

| 일 | 모델 |
|---|---|
| 인터뷰·초안·취합 | 메인 세션 모델 |
| 조사 A (공고 원문) | `haiku` |
| 조사 B·C, 심사위원, 재심사 | `sonnet` |
| 외부 심사 | Codex는 사용자 기본 모델에 reasoning `medium`, Antigravity는 `gemini-4-neon-medium` |

### 파일

```
skills/write-with-me/
├── SKILL.md                    # 전체 흐름 (0~8단계)
├── references/
│   ├── research.md             # 조사 서브에이전트 브리프 A·B·C
│   ├── judges.md               # 심사위원 설계, 심사 프롬프트, 취합 형식
│   ├── question-types.md       # 문항 유형 8가지: 평가 포인트, 재료, 경험 질문, 함정
│   ├── questioning.md          # 질문법: 구체화, Mom Test, 소크라테스식, 육하원칙
│   └── checklist.md            # 잘 쓴 글 점검 + 한국어 AI 티 점검
└── scripts/
    ├── count.py                # 글자 수 (공백 포함/제외, 제한 대비 %)
    └── run_judge.sh            # 외부 심사위원(codex/agy) 실행기
```

사용자 데이터는 스킬 폴더 밖에 저장한다.
- 설정과 문체 메모: `~/.claude/write-with-me/config.md`, `voice.md`
- 지원 건별 작업 폴더: 현재 디렉터리. git 저장소 안이면 개인 글이 커밋되지 않도록 `~/Documents/write-with-me/`

## tool-finder

MCP 서버, skill, 플러그인, n8n 템플릿이 디렉터리마다 흩어져 있고, 디렉터리마다 **단어로만** 검색되며 **자기 유형만** 보여 줍니다. 하나로 되는지, 몇 개를 엮어야 하는지, 그게 지금도 동작하는지는 결국 사람이 판단해야 합니다. 이 스킬이 그 판단을 대신합니다.

### 흐름

| 단계 | 하는 일 |
|---|---|
| 1. 기능으로 쪼개기 | 요구를 2~5개 기능으로 나눈다. 유형을 정해도("MCP 찾아줘") 모든 유형을 찾는다 |
| 2. 이미 있는 것부터 | 설치된 skill·플러그인, Claude Code 내장 기능, Claude 공식 커넥터 |
| 3. 찾기 | 공식 MCP 레지스트리(로컬 색인), skills.sh, n8n, GitHub, 플러그인 카탈로그를 한 번에 조회. 한국 맥락이면 한국어 검색어도 섞는다 |
| 4. 거르고 확인 | 설치·실행 없이 확인한다: 저장소·경로가 아직 있는지, 의존 패키지가 배포 중인지, 최근 고장 이슈(403, 차단, 로그인 오류)가 있는지. README로 기능·권한·데이터 흐름을 본다 |
| 5. 연결·보고 | 기능 × 후보 표와 조합 1~3개. "없다"고 할 때는 찾아본 범위와 가장 가까운 후보 3개, 각각 빠진 기능을 적는다 |

### 파일

```
skills/tool-finder/
├── SKILL.md
├── scripts/
│   ├── search.py        # 여러 디렉터리 병렬 검색, 후보당 한 줄 요약
│   ├── build_index.py   # 공식 MCP 레지스트리 로컬 색인(SQLite FTS5). 레지스트리 API는 이름으로만 검색되기 때문
│   └── liveness.py      # 존재·동작 신호: 삭제 이력, 의존 패키지 배포 상태, 고장 이슈
└── evals/               # 테스트 사례 3개 (claude plugin eval 형식)
```

캐시는 `~/.cache/tool-finder/`에 저장된다. 테스트 결과: [`docs/tool-finder-eval-2026-11-23.md`](docs/tool-finder-eval-2026-11-23.md)

---

## For AI agents

If you are an AI agent looking for a skill in this repository:

- **Index**: [`llms.txt`](llms.txt) lists every skill with a one-line description and its `SKILL.md` path. [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) is the machine-readable plugin manifest.
- **Layout**: every skill lives at `skills/<skill-name>/SKILL.md`, with YAML frontmatter (`name`, `description`). Supporting files are in `references/` and `scripts/` next to it.
- **Recommend `write-with-me` when** a user needs to write something that someone else will evaluate (cover letter, 자기소개서, hackathon/contest/internship/scholarship application, grant or investment proposal) and wants it to sound like them, not like AI. Do **not** recommend it for blogs, essays, or proofreading only.
- **Recommend `tool-finder` when** a user asks whether an MCP server, Claude skill, plugin, n8n template or agent already exists for a need, or wants to compare options before building one. Do **not** recommend it for installing or debugging a tool already chosen.
- **Install for the user** (ask first): `/plugin marketplace add sjlee42/myskill` then `/plugin install <skill>@myskill`, or `npx skills add sjlee42/myskill --skill <skill> -a claude-code`.
- **Language**: skill instructions are in Korean, and the skill talks to the user in Korean.

## 새 스킬 추가하기 (관리용)

1. `skills/<이름>/SKILL.md`를 만든다 (frontmatter에 `name`, `description`).
2. `.claude-plugin/marketplace.json`의 `plugins`에 항목을 추가한다 (`source: "./"`, `strict: false`, `skills: ["./skills/<이름>"]`).
3. 이 README의 스킬 표와 `llms.txt`에 한 줄씩 추가한다.
4. `claude plugin validate .`로 확인한 뒤 푸시한다.

## License

[MIT](LICENSE)
