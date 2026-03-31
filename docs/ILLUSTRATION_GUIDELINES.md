# Hellowords 일러스트레이션 가이드라인

> 이 문서는 TOPIK 단어/예문 일러스트 자동 생성의 **품질 기준**을 정의한다.
> `generate_illustrations.py`의 프롬프트 설계 시 반드시 이 기준을 따른다.

---

## 1. 핵심 원칙

### 1-1. 텍스트 정책

| 구분 | 정책 | 이유 |
|------|------|------|
| **모든 텍스트** | **절대 금지** | AI 모델이 텍스트를 정확히 렌더링 못함 (깨진 글자, 중국어/한국어 혼재) |
| **말풍선, 대화** | 절대 금지 | 대화는 영상의 자막/음성이 담당 |
| **간판, 라벨, 표지판** | 텍스트 없이 아이콘/기호만 | 글자 대신 심볼(십자가=약국, 빵 아이콘=빵집)로 표현 |
| **워터마크** | 금지 | 브랜드 오염 |

**핵심 규칙:**
1. 이미지에 **어떤 언어의 텍스트도 포함하지 않는다** (영어 포함)
2. 간판/표지판은 빈 간판이거나 단순 아이콘/심볼만 사용
3. AI 이미지 모델은 텍스트를 넣으면 반드시 깨지거나 엉뚱한 언어가 나옴
4. 생성된 이미지는 **Gemini Vision 자동 검증**을 거친다 — 텍스트 존재 시 재생성

**스타일 서픽스에 포함:**
```
absolutely no visible text anywhere in the image,
no letters, no words, no signs with text, no labels with text,
no Korean text, no Chinese text, no Japanese text, no English text,
all signs and labels must be blank or use simple icons only
```

### 1-2. 대화 제거, 행동으로 표현 (Show, Don't Tell)

- 대화를 **행동**으로 대체한다
- 감정을 **표정과 몸짓**으로 표현한다
- 상황을 **환경과 소품**으로 설명한다

**나쁜 예 (현재):**
> "a scene: I bought clothes at that store" → 모델이 말풍선 "I BOUGHT CLOTHES..." 생성

**좋은 예 (개선):**
> "a happy person walking out of a clothing shop carrying colorful shopping bags, the shop window displays mannequins wearing dresses"

### 1-3. 한 이미지 = 한 메시지 (Single Message)

- 하나의 일러스트는 하나의 핵심 개념만 전달
- 주인공/주제가 화면의 50% 이상 차지
- 배경은 맥락 보조 역할만 수행

---

## 2. 품사별 시각화 전략

### 명사 (Noun)

| 전략 | 설명 | 예시 |
|------|------|------|
| **직접 묘사** | 대상을 정중앙에 크고 선명하게 | 가게 → 작은 가게, 열린 문, 진열대 |
| **사용 맥락** | 사람이 해당 물건을 사용하는 장면 | 가방 → 어깨에 가방을 멘 사람 |
| **그룹 배치** | 관련 사물을 함께 배치 | 가구 → 소파, 테이블, 책장이 거실에 배치된 모습 |

**프롬프트 패턴:**
```
[대상물] in a [맥락 장소], [시각적 특징], [보조 소품]
```

### 동사 (Verb)

| 전략 | 설명 | 예시 |
|------|------|------|
| **동작 진행형** | 동작을 수행하는 순간 포착 | 가다 → 한 발을 앞으로 내딛는 사람 |
| **전후 대비** | Before/After를 좌우로 나눔 | 열다 → 왼쪽에 닫힌 상자, 오른쪽에 열린 상자 |
| **결과 상태** | 동작의 결과가 보이는 장면 | 쓰다 → 노트 위에 펜을 올린 손, 글이 써진 노트 |

**프롬프트 패턴:**
```
a person [동작 ing] [대상], [신체 자세 설명], [환경]
```

### 형용사 (Adjective)

| 전략 | 설명 | 예시 |
|------|------|------|
| **대비법** | 반대 속성을 나란히 배치 | 크다 → 큰 곰 인형 옆에 작은 곰 인형 |
| **극단 표현** | 속성을 과장해서 명확하게 | 뜨겁다 → 컵에서 김이 모락모락, 손이 뜨거워 흔드는 장면 |
| **감정 표현** | 표정과 몸짓으로 감정 전달 | 기쁘다 → 양팔 벌리고 활짝 웃는 사람, 주변에 꽃잎 |

**프롬프트 패턴:**
```
[주체] showing [속성] by [시각적 증거], contrasted with [반대/기준]
```

### 부사 (Adverb)

| 전략 | 설명 | 예시 |
|------|------|------|
| **속도감** | 모션 블러, 잔상, 속도선 | 빨리 → 달리는 사람, 뒤로 날리는 머리카락 |
| **빈도** | 반복 패턴으로 표현 | 자주 → 달력에 많은 체크 표시 (글자 없이 기호만) |
| **정도** | 크기 차이로 강약 표현 | 매우 → 산더미처럼 쌓인 책 |

### 추상 개념 (Abstract)

| 전략 | 설명 | 예시 |
|------|------|------|
| **은유** | 보편적 상징 활용 | 사랑 → 하트 모양 풍선을 든 커플 |
| **상황 재현** | 개념이 발현되는 구체적 장면 | 약속 → 두 사람이 새끼손가락을 걸고 있는 클로즈업 |
| **아이콘화** | 단순 기호로 치환 | 시간 → 모래시계, 해가 이동하는 궤적 |

---

## 3. 예문 일러스트 프롬프트 변환 규칙

### 3-1. 변환 프로세스

```
영어 문장 → Claude API(시각 장면 변환) → 시각 묘사 프롬프트 → Imagen API
```

현재 `build_sentence_prompt()`가 영어 문장을 그대로 넣어서 모델이 말풍선/텍스트를 생성하는 문제가 있다.
**영어 문장을 시각적 장면 설명으로 먼저 변환**한 후 Imagen에 전달해야 한다.

### 3-2. 문장 → 장면 변환 (Claude API 시스템 프롬프트)

```
You are a visual scene designer for language learning illustrations.

Convert the following sentence into a VISUAL SCENE DESCRIPTION for an illustrator.

Rules:
- Describe ONLY what can be seen: actions, objects, expressions, settings
- NEVER include speech bubbles, dialogue, or floating text
- Replace conversations with body language and gestures
- Replace "someone said X" with the physical action implied
- Signs and shop names must NOT contain any text — use blank signs or simple icons/symbols instead
- Be specific about body positions, facial expressions, and surroundings
- Keep it to 1-2 sentences, under 50 words
- The scene must make the sentence's meaning understandable without dialogue

Korean: {ko}
English: {en}
Target word: {word} ({meaning})

Visual scene description:
```

### 3-3. 변환 예시

| 원문 | 현재 프롬프트 (문제) | 개선된 프롬프트 |
|------|---------------------|----------------|
| "가게가 어디에 있어요?" | "a scene: Where is the store?" | "a person on a street corner looking around with a puzzled expression, hand shading their eyes, searching for something" |
| "그 가게에서 옷을 샀어요" | "a scene: I bought clothes at that store" | "a person exiting a clothing shop holding shopping bags, satisfied smile, dresses visible in the display window" |
| "이 가게는 유명해요" | "a scene: This store is famous" | "a popular small shop with a long queue of customers waiting outside, warm lights glowing from inside" |
| "가게 문을 열었어요" | "a scene: I opened the store door" | "a hand pushing open a glass shop door, the warm shop interior visible behind it" |
| "가게에 사람이 많아요" | "a scene: There are many people in the store" | "a bustling small shop packed with customers browsing shelves, a lively crowded atmosphere" |

### 3-4. 절대 금지 변환

| 금지 | 대안 |
|------|------|
| 영어 문장을 scene 설명에 그대로 사용 | 동작/장면으로 분해해서 설명 |
| "a person saying..." / "telling..." | "a person gesturing/doing..." |
| 말풍선, 생각구름 묘사 | 표정과 몸짓으로 감정 전달 |
| "speech bubble with..." | 해당 내용을 행동으로 시각화 |

### 3-5. 문장 유형별 시각화 패턴

| 문장 유형 | 시각화 전략 | 예시 |
|-----------|-------------|------|
| **X가 Y를 했다** | 행동의 결과 장면 | "책을 읽었다" → 소파에서 펼친 책을 읽는 사람 |
| **X가 Y에 있다** | 위치 관계 시각화 | "고양이가 상자 안에 있다" → 상자 안에 웅크린 고양이 |
| **X가 Y보다 ~하다** | 대비 배치 | "형이 동생보다 크다" → 키 차이가 나는 두 사람 |
| **질문/요청** | 의문의 몸짓 | "어디예요?" → 고개 갸우뚱, 주변 둘러보는 사람 |
| **X에게 Y를 주다** | 전달 동작 | "선물을 줬다" → 한 사람이 상자를 건네는 장면 |

---

## 4. 텍스트 검증 파이프라인 (생성 후)

AI 이미지 모델은 간판, 라벨 등의 텍스트 철자를 자주 틀린다.
생성된 이미지에 텍스트가 포함된 경우, **자동 검증 → 재생성** 파이프라인을 적용한다.

### 4-1. 검증 흐름

```
이미지 생성 (Imagen)
        ↓
텍스트 검출 (Gemini Vision)
        ↓
  ┌─ 텍스트 없음 → ✅ 통과
  ├─ 텍스트 있음 + 정확함 → ✅ 통과
  └─ 텍스트 있음 + 부정확 → ❌ 재생성 (최대 2회)
        ↓
  재생성 2회 후에도 실패 → 🟡 플래그 (수동 검수 대기)
```

### 4-2. Gemini Vision 검증 프롬프트

```
Analyze this illustration and check ALL visible text elements.

For each text found:
1. Location (sign, label, book cover, etc.)
2. The text as it appears in the image
3. Is the spelling correct? (yes/no)
4. Is the text legible and well-formed? (yes/no)
5. If incorrect, what should it say?

Also check:
- Are there any speech bubbles or dialogue? (must be: NO)
- Are there any floating captions or labels? (must be: NO)

Respond in JSON:
{
  "has_dialogue": true/false,
  "texts": [
    {
      "location": "shop sign",
      "content": "BAKERY",
      "spelling_correct": true,
      "legible": true,
      "correction": null
    }
  ],
  "pass": true/false,
  "reason": "..."
}
```

### 4-3. 판정 기준

| 항목 | 통과 | 불합격 |
|------|------|--------|
| 말풍선/대화 | 없음 | 있음 → 즉시 재생성 |
| 간판/라벨 텍스트 | 없음 (아이콘만) | 어떤 언어든 텍스트 존재 → 즉시 재생성 |
| 텍스트 없는 이미지 | 자동 통과 | - |

### 4-4. 재생성 전략

첫 번째 재생성: 텍스트 금지를 더 강하게 보강
```
"... absolutely no text, no letters, no words visible anywhere ..."
```

두 번째 재생성: 텍스트 유발 요소 자체를 제거
```
"... a shop with a simple awning and blank signboard, icons only ..."
```

두 번째까지 실패 시: 플래그 → `logs/illust_flagged.json`에 기록, 수동 검수 대기

---

## 5. 프롬프트 구조 템플릿

### 5-1. 단어 일러스트 (word.png)

```
[주체/대상의 구체적 시각 묘사],
[장소/맥락 배경],
[보조 소품이나 환경 디테일],
[스타일 서픽스]
```

### 5-2. 예문 일러스트 (0~9.png)

```
[사람/캐릭터의 구체적 동작이나 자세],
[동작의 대상이나 소품],
[장소/배경 설명],
[감정 표현 (표정, 몸짓)],
[스타일 서픽스]
```

### 5-3. 스타일 서픽스 (모든 프롬프트 공통)

```
hand-drawn illustration with soft watercolor textures,
gentle ink outlines, warm pastel color palette,
light cream background with subtle paper grain,
centered composition, charming expressive characters,
delicate brushstroke details,
no speech bubbles, no dialogue, no floating text,
no captions, no watermark,
absolutely no visible text anywhere in the image,
no letters, no words, no signs with text, no labels with text,
no Korean text, no Chinese text, no Japanese text, no English text,
all signs and labels must be blank or use simple icons only,
square format, high quality
```

**핵심:**
- 이미지 내 **모든 형태의 텍스트 완전 금지** (영어 포함)
- 간판/표지판은 빈 간판 또는 아이콘/심볼만 허용
- 텍스트 존재 시 **자동 검증 → 재생성**

---

## 6. 이미지 유형별 차이

| 구분 | word.png (단어) | 0~9.png (예문) |
|------|----------------|----------------|
| 목적 | 단어의 핵심 의미 전달 | 예문의 상황/맥락 전달 |
| 초점 | 대상 자체 (명사) 또는 동작 (동사) | 사람이 상황에서 행동하는 장면 |
| 구도 | 대상 중심, 심플 | 장면 중심, 맥락 풍부 |
| 캐릭터 | 있을 수도 없을 수도 | 거의 항상 사람 포함 |
| 배경 | 최소화 또는 연관 배경 | 문장의 장소/상황 반영 |
| 간판 | 텍스트 없이 아이콘만 | 텍스트 없이 아이콘만 |

---

## 7. 특수 상황 처리

### 7-1. 대화/질문 문장 → 몸짓으로 대체

| 대화 유형 | 시각적 대체 |
|-----------|-------------|
| 질문 | 고개 갸우뚱, 손바닥 위로, 주변 둘러보기 |
| 제안 | 한 방향을 가리키는 손, 밝은 표정 |
| 거절 | 손을 앞으로 내밀어 막는 제스처, 고개 젓기 |
| 동의 | 고개 끄덕임, 엄지 척 |
| 감사 | 허리 숙여 인사 |
| 인사 | 손 흔들기, 밝은 미소 |

### 7-2. 추상적 문장 → 상징물 활용

- "오랜만이에요" → 두 사람이 반갑게 포옹, 배경에 계절 변화 암시
- "약속했어요" → 새끼손가락을 걸고 있는 두 손 클로즈업
- "걱정이에요" → 이마에 손을 짚고 걱정스러운 표정

### 7-3. 복합 장면 → 핵심 한 장면만

여러 동작이 포함된 문장은 **가장 핵심적인 하나의 동작**만 선택:
- "가게에 가서 빵을 사서 집에 돌아왔어요"
  → 빵집에서 빵 봉투를 받는 장면 (가장 핵심적인 순간)

---

## 부록: 전문가 관점 요약

### 만화가 관점
- 말풍선 없이 감정과 상황을 전달하는 것은 "사일런트 코믹" 기법
- 눈의 크기, 입 모양, 팔의 각도만으로 감정의 90%를 전달 가능
- 배경선의 방향(방사형=놀람, 물결=불안)으로 분위기 조성

### 일러스트레이터 관점
- 시각적 계층 구조: 가장 중요한 요소가 가장 크고 밝아야 함
- 색상으로 감정 유도: 따뜻한 색=긍정, 차가운 색=부정/차분
- 간판은 텍스트 대신 아이콘/심볼로 표현 (AI가 텍스트를 정확히 못 그림)

### 언어학자 관점
- 학습자는 이미지를 보고 0.5초 안에 단어를 연상할 수 있어야 함
- 문화적 보편성 중요: 글로벌하게 이해 가능한 이미지
- 동사는 "진행 중인 동작"이 가장 기억에 잘 남음 (Dual Coding Theory)
- 하나의 이미지에 너무 많은 정보 → 인지 부하 증가 → 학습 효과 감소

### 아동 교육 전문가 관점
- 시각적 단서만으로 의미를 유추할 수 있어야 함
- 과장된 표정과 동작이 이해도를 높임
- 일관된 캐릭터 스타일이 친밀감과 학습 몰입도를 높임
