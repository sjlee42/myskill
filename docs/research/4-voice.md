# 4. 목소리 보존과 생각 발견: AI 공동집필 연구와 글쓰기 교육의 근거

조사일 2026-11-23. 직접 열어 확인한 출처만 URL을 붙였다. 초록만 본 경우는 "(초록)"으로 적었다.

## 1. AI와 함께 쓰면 무엇이 줄어드나

- **내용 다양성이 준다.** Padmakumar & He(ICLR 2024)는 논증 에세이를 세 조건(GPT-3, InstructGPT, 도움 없음)으로 쓰게 했다. "writing with InstructGPT (but not the GPT3) results in a statistically significant reduction in diversity." 서로 다른 사람의 글이 비슷해졌고, 원인은 주로 모델이 넣은 텍스트였다. 사용자가 직접 쓴 부분은 다양성이 줄지 않았다. https://arxiv.org/abs/2309.05196 (초록)
- **개인 글은 좋아지고 집단 다양성은 줄어든다.** Doshi & Hauser(Science Advances 2024)는 작가 293명과 평가자 600명으로 실험했다. GPT-4 아이디어 5개를 받은 조건에서 참신성이 8.1% 올랐고, 원래 창의성이 낮은 작가는 10.7% 올랐다. 대신 AI를 쓴 이야기끼리 더 비슷해졌다. https://pmc.ncbi.nlm.nih.gov/articles/PMC11244532
- **의견이 바뀐다.** Jakesch et al.(CHI 2023, N=1,506, 별도 평가자 500명)에서 한쪽으로 치우친 LM과 쓰자 "affected the opinions expressed in participants' writing". 이후 설문에 답한 태도까지 바뀌었다. https://arxiv.org/abs/2302.00560 (초록). 참가자가 이 편향을 알아챘는지는 초록에서 확인하지 못했다(미확인).
- **소유감 없이 저자로 표기한다.** Draxler et al.(n=30, n=96)은 이를 "AI Ghostwriter Effect"라 불렀다. 사용자는 AI가 생성한 글을 자기 것으로 여기지 않으면서도 AI 저작을 밝히지 않았다. 반면 "higher levels of participants' influence on texts increased their sense of ownership." AI 글을 개인화해도 이 효과는 그대로였다. https://arxiv.org/abs/2303.03283
- **문화적 균질화가 일어난다.** Agarwal, Naaman & Vashistha(CHI 2025, 인도·미국 118명)에서 "AI suggestions led Indian participants to adopt Western writing styles." 내용과 형식이 모두 바뀌었고, 효율 향상도 미국인에게 더 컸다. https://arxiv.org/abs/2409.11360 (초록)
- **자기 글을 기억하지 못한다.** Kosmyna et al.(MIT, 2025)은 54명을 LLM·검색·도구 없음 세 집단으로 나눴다. 자기보고 소유감은 LLM 집단이 가장 낮았다. "LLM users also struggled to accurately quote their own work." EEG 연결성도 LLM 집단이 가장 약했다. https://arxiv.org/abs/2506.08872 (초록, 동료심사 전)
- **도움이 클수록 소유감이 준다.** Dhillon et al.(CHI 2024, 131명, 피험자 내 설계)은 다음 문장 제안과 다음 문단 제안을 비교했다. 문단 제안은 품질을 올렸지만 텍스트 소유감과 만족도가 중간 정도 떨어졌다. https://arxiv.org/abs/2402.11723v1 (초록)

## 2. 소유감을 지키는 상호작용 설계

- **질문형·사용자 주도가 소유감을 지킨다.** Maier, Schneider & Feuerriegel(CHI 2026, N=486, 검증 실험 N=640)에서 LLM이 아이디어를 직접 고쳐 쓰는 모드는 "substantially improved idea quality but reduced idea diversity and users' perceived idea ownership". 질문이나 제안으로 사용자가 스스로 다듬게 하는 모드는 품질을 올리면서 "preserving diversity and ownership" 했다. https://arxiv.org/abs/2510.23324 (초록)
- **스타일 개인화는 효과가 부분적이다.** Zhang, Bu & Dhillon(2026, N=176)에서 AI 도움을 받으면 소유감이 7점 척도로 0.85~1.0점 떨어졌다. 페르소나 코칭은 이 하락을 막지 못했다. 사용자 글 샘플로 스타일을 맞추자 약 0.43점 회복됐다. 연구진이 제안한 설계 패턴은 다섯 가지다. 사용자가 요청할 때만 제안하기("Let users explicitly request suggestions"), 짧은 단위로 제안하기, 사용자 이전 글로 목소리 고정하기, AI를 공저자가 아니라 코치로 두기, 채택 시점에 AI 문장을 표시하기. https://arxiv.org/abs/2601.10236 , https://arxiv.org/html/2601.10236v1
- **도구보다 상호작용 방식이 중요하다.** Umarova et al.(2025)은 아이디어를 적극 탐색한 학생은 어떤 도구를 써도 새 아이디어를 얻었다고 보고했다. 반대로 오래 기계적으로 다듬기만 한 학생은 소크라테스식 AI를 써도 아이디어가 적었다. https://arxiv.org/abs/2503.11915 (초록)
- **단계마다 원하는 개입 정도가 다르다.** Reza et al.(CSCW 2025)은 논문 109편을 검토하고 작가 15명을 인터뷰했다. "content-focused writers (e.g., academics) prioritize ownership during planning." 즉 무엇을 말할지 정하는 단계의 소유감이 핵심이다. https://arxiv.org/abs/2504.12488 (초록)

## 3. LLM 문체의 지문

- **영어 문법 특징.** Reinhart et al.(PNAS 2025)에 따르면 지시 튜닝 모델은 현재분사절을 사람의 2~5배(GPT-4o는 5.3배), 명사화를 1.5~2배 쓴다. GPT-4o는 camaraderie, tapestry, intricate 같은 단어를 사람보다 100배 넘게 쓴다. 이런 차이는 지시 튜닝 모델에서 더 크다. https://arxiv.org/html/2410.16107v2
- **어휘 특징.** Kobak et al.(Science Advances 2025)은 PubMed 초록 1,500만 편을 분석해 2024년 초록의 최소 13.5%가 LLM을 거쳤다고 추정했다. https://arxiv.org/abs/2406.07016 과잉 사용된 어휘는 "almost entirely of style words"였고, delves(r=28.0), showcasing, underscores 등이며 66%가 동사였다. https://arxiv.org/html/2406.07016v2
- **한국어 대학 과제.** 「생성형 AI 텍스트와 인간 텍스트의 내용 및 문체 비교 연구」(교양교육연구 19(6), 2025)는 과제 69편을 비교했다. AI를 쓴 글은 문장이 짧고 어휘 다양성(TTR·MATTR)이 낮았다. 조건 접속 대신 예시·강조 접속을 많이 썼고, 사고와 문체가 획일적이었으며, 허위 참고문헌이 있었다. https://scholar.kyobobook.co.kr/article/detail/4010071811913
- **한국어 개인 경험 글.** 「모어 화자와 GPT-5의 한국어 사용 양상 연구」(이중언어학 102, 2025)는 글 40편을 비교했다. GPT-5는 어휘 다양성 지표가 오히려 높았고, 품사 사용 양상이 모어 화자와 달랐다. https://scholar.kyobobook.co.kr/article/detail/4010071796014 따라서 어휘 다양성 하나로 AI 글을 판별할 수는 없다. 한국어에서 더 안정적인 신호는 '연결 방식과 구성의 획일성'으로 보인다.

## 4. 생각을 글로 발견하는 방법

- **Elbow, 자유글쓰기**(Writing Without Teachers, 1973). "The only requirement is that you never stop." 그가 짚은 문제는 이렇다. "editing goes on at the same time as producing." 이 습관은 목소리도 지운다. "Your voice is damped out by all the interruptions… In your natural way of producing words there is a sound, a texture, a rhythm--a voice." 그는 말과 비교해 설명한다. 말을 잘한 순간도 시작은 더듬었지만 계속 말하다 보니 힘이 생겼다는 것이다. https://www.research.ucsb.edu/sites/default/files/RD/docs/FREEWRITING-by-Peter-Elbow.pdf
- **Murray, 과정으로서의 글쓰기**(1972). 글쓰기는 "the process of discovery through language", 곧 "exploration of what we know and what we feel about what we know"이다. 그의 원칙은 "The student finds his own subject", "The student uses his own language"이다. 교사의 역할은 "listen carefully for those words that may reveal a truth, that may reveal a voice"이고 "be patient and wait"이다. https://compositionforum.com/issue/50/teach-writing-as-process.php (재인용)
- **Flower, 필자 중심 글과 독자 중심 글**(College English 1979). 필자 중심 글(writer-based prose)은 필자가 자신에게 말하는 글로, 시간순이나 의식의 흐름을 따른다. 생각을 만들어 내는 초기 단계로는 자연스럽다. 다만 제출 전에는 독자 중심 글로 바꿔야 한다. https://writingcommons.org/section/style/writing-styles/writer-based-prose-style/ (2차 자료이며 원문은 미확인)
- **Pennebaker, 표현적 글쓰기.** 무작위 연구 146편을 메타분석한 결과 평균 효과는 r=.075로 작지만 유의했다(Frattaroli 2006). 효과를 가장 많이 본 사람들은 글을 쓰는 동안 인과어(because)와 통찰어(know, consider)를 점점 더 많이 썼다. 의미를 만들고 경험을 구조화하는 것이 효과의 기제로 제시됐다. https://www.gwern.net/doc/psychology/2006-frattaroli.pdf
- **Lamott**(Bird by Bird, 1994). "Shitty first drafts"를 권하며 "All good writers write them"이라고 했다. 출처는 검색 결과의 발췌로만 확인했다(미확인).
- **말로 먼저 하기.** 초등 영어학습자 21명을 대상으로 한 연구에서 받아쓰기(사람에게 구술하거나 음성 인식 사용)가 손글씨보다 글의 질과 분량을 높였다. 검색 요약으로만 봤고, 성인 대상 근거는 찾지 못했다(미확인).

## 5. 대필 업계의 관행 (업체 자료이며 학술 근거는 아님)

- LifeBook은 인터뷰를 녹음한 뒤 대필자가 그 녹음을 직접 듣고 쓴다. 이 업체도 위험을 경고한다. "When uncontrolled, the client's words become our own on the page and the original voice gets lost. The story begins to sound more like the ghostwriter than the client." https://www.lifebookmemoirs.com/?p=15739
- 다른 업체 가이드도 말의 리듬, 어휘 수준, 관용구를 그대로 살리라고 권한다. 핵심은 "정리하되 소독하지 말라"는 것이다. 다만 검색 요약으로만 확인했다(미확인).

## 6. skill에 넣을 만한 것

1. **한 줄 요지는 사용자가 먼저 말한다.** 문항마다 초안을 쓰기 전에 "이 글에서 심사위원이 기억했으면 하는 한 가지를 한 문장으로" 묻는다. 이 답을 material.md에 ★로 원문 그대로 저장한다. 근거: 소유감은 무엇을 말할지 정하는 계획 단계에서 가장 중요하다(Reza). 영향력이 클수록 소유감이 오른다(Draxler).
2. **원문 보존 비율을 정한다.** 초안의 핵심 문장(주장, 감정, 판단)은 사용자 말을 어순만 다듬어 쓴다. 모델이 새로 만드는 것은 연결어, 문단 나누기, 순서로 한정한다. 초안 아래에 문장별 출처 표(예: 문장 3 ← Q2 답)를 붙여 확인할 수 있게 한다. 근거: 다양성 감소는 모델이 넣은 텍스트에서 생긴다(Padmakumar). 채택 시점에 AI 문장이 보여야 한다(Zhang et al.).
3. **질문은 사용자가 생각하게 만든다.** "이렇게 바꿀까요?" 대신 "그때 왜 그렇게 판단했어요?", "다른 선택지는 뭐였어요?"처럼 인과와 판단을 묻는다. 근거: 질문형 모드는 소유감과 다양성을 유지했다(Maier). 인과어와 통찰어가 늘어나는 것이 의미 형성의 신호다(Pennebaker).
4. **인터뷰 단계에서는 다듬지 않는다.** 답을 받을 때 맞춤법이나 문장을 고쳐 보여 주지 않는다. 말하듯 길게 답하도록 권하고, 음성 입력도 허용한다. 근거: 생산과 편집을 동시에 하면 목소리가 지워진다(Elbow). 기다림과 경청이 필요하다(Murray).
5. **초안은 두 단계로 쓴다.** 먼저 사용자 말의 순서대로 놓은 필자 중심 초안을 보여 주고 "이게 당신 이야기 맞나요?"를 확인한다. 그다음에 문항과 심사 기준에 맞춘 독자 중심 재구성을 한다(Flower).
6. **사용자 확인 지점은 세 곳이다.** (a) 한 줄 요지 (b) 문장 출처 표에서 "내가 안 한 말" 찾기 (c) 최종본에서 "자기 글이라 소리 내어 말할 수 있는가"를 묻기. 근거: LLM 사용자는 자기 글을 인용하지 못했다(Kosmyna).
7. **피해야 할 개입이 있다.** 모델 의견이나 가치 판단을 끼워 넣지 않는다(Jakesch). 문단 단위로 통째 다시 쓰지 않는다(Dhillon). 사용자가 요청하지 않은 제안을 밀어붙이지 않는다(Zhang et al.). 모범 자소서 틀에 맞춰 고르게 만들지 않는다(Doshi, Agarwal). 한국어 AI 티를 점검한다. 예시·강조 접속어("특히", "이를 통해") 반복, 짧고 고른 문장, 근거 없는 수치나 참고문헌, '-함으로써' 같은 명사화 과다가 대상이다(교양교육연구 2025, Reinhart).
8. **voice.md는 실제 문장으로 쌓는다.** 사용자 원문 샘플 2~3개와 ★ 표현을 함께 저장하고, 초안을 쓸 때마다 참조한다. 근거: 스타일 개인화로 소유감이 일부 회복됐다(+0.43). 다만 완전히 회복되지는 않으므로 1~7번이 우선이다.
