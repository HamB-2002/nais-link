# 연구보고서 수치 수집·검증 대상 판별 파이프라인

> 검토 기준 브랜치: `part/numeric`  
> 대상: `doc_parser`의 수치 후보 추출, 명백한 비검증 수치 필터, 검증 대상 판별, 로컬 LLM adapter 및 결과표 formatter

## 1. 목적

이 파이프라인의 목적은 문서에서 숫자를 단순 수집하는 데 있지 않다. 연구보고서에 기재된 숫자 중에서 향후 분석 코드와 원데이터를 이용해 **재현·대조할 가치가 있는 수치**를 선별하고, 그 후보와 위치·문맥 정보를 다음 내력 추적 단계에 전달하는 데 있다.

따라서 숫자 원문(`raw`)과 정규화 값(`value`)을 보존하고, 초기에 제외된 값도 삭제하지 않는다. 각 후보에는 제외·판별 근거를 추가하여 이후 단계에서 추적할 수 있게 한다.

## 2. 전체 구조

```text
HWPX / DOCX / PDF
      │
      ▼
[문서 파서 → Document → CollectorBlock[]]    parser / 다른 담당 영역
      │
      ▼
[수치 후보 추출]                         doc_parser/numeric_candidates.py
      │
      ▼
[명백한 비검증 수치 필터]                doc_parser/non_verification_filter.py
      │
      ▼
[규칙 기반 검증 대상 판별]               doc_parser/verification_classifier.py
      │
      ├── VERIFY / IGNORE ─────────────── classified candidates
      │
      └── UNCERTAIN
              │
              ▼
       [로컬 Qwen3:8b 보조 판별]          doc_parser/ollama_classifier.py
              │
              ▼
          classified candidates
              │
              ▼
[수치 검증 결과표 formatter]                doc_parser/numeric_result_table.py
              │
              ▼
구조화된 결과표 list[dict]
      ├── status별 조회 (VERIFY / IGNORE / UNCERTAIN)
      └── Markdown table 보조 출력
              │
              ▼
[코드·데이터 내력 추적 및 재실행 비교]   후속 모듈 / 다른 담당 영역
```

현재 모듈에는 위 단계를 한 번에 호출하는 단일 orchestration 함수는 없다. 호출자는 blocks 추출, filter, classifier 단계를 순서대로 연결한다.

## 3. 파서와의 입력 계약

수치 수집기의 최종 입력 계약은 `list[CollectorBlock]`이다. 현재 Python 구현은 별도 `CollectorBlock` 클래스를 선언하지 않고 `Mapping[str, Any]` 형태의 block을 받는다. `extract_numeric_candidates_from_blocks(blocks)`가 blocks를 순회하며 기존 단일 block 추출 함수를 호출한다.

| 필드 | 계약 | 처리 방식 |
|---|---|---|
| `type` | `"paragraph"` / `"caption"` / `"table"` | 후보의 `type`으로 그대로 보존 |
| `text` | `str` | paragraph·caption 및 `rows=None` table의 추출 원문 |
| `page` | `int \| null` | 변환 없이 그대로 보존 |
| `order` | `int` | 배열 index로 해석하지 않고 그대로 보존 |
| `rows` | `list[list[str]] \| null` (table만) | 존재 시 table cell 추출에 사용 |

```json
{
  "type": "table",
  "text": "항목\t수치\n평균\t15",
  "page": 10,
  "order": 2,
  "rows": [
    ["항목", "수치"],
    ["평균", "15"]
  ]
}
```

문서 파서와 `Document → CollectorBlock[]` adapter는 수치 수집 담당 외의 구현 영역이다. 다만 실제 HWPX 문서의 해당 연결은 14절의 end-to-end 통합 시험으로 확인됐다. DOCX/PDF가 numeric pipeline 전체를 통과하는 실제 통합 시험은 아직 수행하지 않았다.

## 4. 수치 후보 추출

`numeric_candidates.py`는 의미 판단 없이 숫자처럼 보이는 표현을 우선 보존한다. 연도, 표 번호, 날짜 구성 숫자도 이 단계에서는 추출하며 다음 filter가 처리한다.

| 지원 표현 | 입력 예 | 주요 구조화 결과 |
|---|---|---|
| 정수·실수·부호·쉼표 | `-4.2%`, `1,248명` | `value=-4.2`, `unit="%"`; `value=1248.0`, `unit="명"` |
| 일반 단위 | `3.21초`, `2.7배` | `value=3.21`, `unit="초"`; `value=2.7`, `unit="배"` |
| 통화 단위 | `12억 원`, `3,241만원` | `value=12.0`, `unit="억 원"`; `value=3241.0`, `unit="만원"` |
| p-value 대입 | `p = 0.032` | `raw="p = 0.032"`, `value=0.032` |
| p-value 부등식 | `p < 0.05`, `p ≤ 0.01` | `operator`, `statistic="p"`, `value` |
| 오차 표현 | `87.3 ± 2.1%` | 중심 `value=87.3`, `error=2.1`, `unit="%"` |
| 범위 | `20명~30명`, `3.2~4.7%` | 시작 `value`, 끝 `range_end`, `unit` |
| 신뢰구간 | `95% CI: 1.2–2.4` | `confidence_level=95.0`, `range_start=1.2`, `range_end=2.4` |
| 과학적 표기 | `1.2×10^-3`, `1.2 × 10⁻³`, `10⁻³` | 계산 가능한 float `value`로 정규화 |

단위 정규식에는 `%`, 한국어 통화 단위, 시간·분·초, 년·월·일, 명·건·개·회·곳·쪽·배·점·원, 길이·질량·용량·저장용량·주파수·온도 표현이 포함된다. 구현되지 않은 표기(예: `1e-3`)는 지원한다고 보장하지 않는다.

모든 후보는 원문 표현을 `raw`에 유지하고, 비교용 숫자를 `value`에 float으로 저장한다. 복합 표현은 필요한 경우 `operator`, `statistic`, `error`, `range_end`, `range_start`, `confidence_level`을 추가한다.

## 5. 표(table) 수치 처리

table block은 `rows`의 존재 여부로 처리 경로를 나눈다.

| 조건 | 추출 대상 | `row` / `column` | `text` 사용 |
|---|---|---|---|
| `rows is not None` | 각 row의 각 cell | 0-based index로 추가 | 사용하지 않음 |
| `rows is None` | block의 `text` | 추가하지 않음 | fallback으로 사용 |
| `rows == []` | 없음 | 없음 | fallback하지 않음 |

rows가 있는 table은 rendered `text`와 rows를 동시에 읽지 않는다. 같은 값의 중복 후보 생성을 막기 위한 규칙이다. cell에서 숫자를 추출할 때 숫자 위치 `start`, `end`는 **원래 cell 문자열 내부** 기준으로 유지한다. 반면 `context`는 해당 행의 모든 cell을 `" | "`로 결합해, 값의 행 레이블을 classifier가 함께 볼 수 있게 한다.

`["평균", "15"]`에서 생성되는 후보의 주요 부분은 다음과 같다.

```json
{
  "raw": "15",
  "value": 15.0,
  "context": "평균 | 15",
  "type": "table",
  "page": 10,
  "order": 2,
  "row": 1,
  "column": 1
}
```

`page`와 `order`는 모든 table 후보에 원 block 값 그대로 전달된다.

## 6. 비검증 수치 필터

`non_verification_filter.py`는 명백한 구조·서지 수치만 보수적으로 표시한다. 후보를 삭제하거나 값·위치를 변경하지 않고 사본에 다음 필드를 추가한다.

```json
{
  "exclude": true,
  "exclude_reason": "table_number"
}
```

현재 구현 규칙은 다음과 같다.

| 대상 | 예 | `exclude_reason` |
|---|---|---|
| 완전한 날짜의 구성 요소 | `2026년 9월 30일` | `date` |
| 연도 표현 | `2025년`, `2025년도` | `year` |
| 표 번호 | `표 3`, `<표 2-1>` | `table_number` |
| 그림 번호 | `그림 2`, `[그림 4]`, `Figure 3`, `Fig. 2` | `figure_number` |
| 장·절·항 또는 명확한 개요 번호 | `제2장`, `제3절`, 줄 처음의 `2.1 연구방법` | `section_number` |
| 페이지 | `p. 15`, `pp. 15-17`, `15쪽`, `페이지 23` | `page_number` |
| 참고문헌형 대괄호 인용 | `[12]`, `[3, 5]`, `[7-9]` | `reference_number` |

일반 문장 속 소수나 임의의 대괄호 결과값은 제거하지 않도록 좁게 구현되어 있다. 예를 들어 `모델의 평균은 2.1이고 신뢰구간은 [12.7%]였다.`의 두 숫자는 남긴다.

## 7. 검증 대상 판별

`verification_classifier.py`는 filter 결과를 받아 `verification_status`, `verification_reason`, `verification_method`를 추가한다. 기존 candidate 필드는 삭제하지 않는다.

| 상태 | 의미 |
|---|---|
| `VERIFY` | 분석 코드 또는 데이터 처리 OUTPUT으로 산출되어, 재실행·재계산 후 보고서 수치와 비교할 가치가 있는 값 |
| `IGNORE` | 명백한 비검증 구조 수치 또는 분석 결과가 아닌 메타데이터·환경·비용 등 |
| `UNCERTAIN` | 현재 문맥만으로 OUTPUT과 INPUT/SETTING/METADATA를 구분하기 어려운 값 |

처리 순서는 다음과 같다.

```text
exclude=true
    └─ IGNORE (classifier 호출 없음)

exclude=false
    ├─ 규칙으로 명백한 VERIFY / IGNORE → rule 결과 확정
    └─ 규칙상 UNCERTAIN
            ├─ classifier 미주입 → UNCERTAIN
            └─ classifier 주입 → 최소 payload로 보조 판별
```

현재 규칙 기반 `IGNORE`는 연구·조사 기간, 연구비·사업비·예산, 데이터·소프트웨어 버전, Python/Stata/SAS/MATLAB 등의 소프트웨어 환경 표현을 처리한다. `exclude=true` 후보도 즉시 `IGNORE`가 된다.

규칙 기반 `VERIFY`는 p-value, 신뢰구간, 오차가 붙은 추정치와 표본·관측·응답·평균·비율·정확도·회귀·상관·표준편차·검정·집계 등의 문맥 패턴을 처리한다. `임계값`, `threshold`, `설정` 문맥은 규칙에서 섣불리 `IGNORE`하지 않고 `UNCERTAIN`으로 남겨 주입 classifier에 전달한다.

## 8. 로컬 LLM 보조 판별

`ollama_classifier.py`는 provider-independent classifier 인터페이스에 주입할 수 있는 `OllamaClassifier` callable을 제공한다.

| 항목 | 현재 구현 |
|---|---|
| 실행 방식 | 로컬 Ollama |
| 기본 모델 | `qwen3:8b` |
| 기본 endpoint | `http://127.0.0.1:11434/api/chat` |
| endpoint 제한 | HTTP의 `localhost`, `127.0.0.1`만 허용 |
| API key | 사용하지 않음 |
| streaming | `stream=false` |
| thinking | `think=false`; 응답의 `message.content`만 사용 |
| temperature | `0` |
| 의존성 | Python 표준 라이브러리만 사용 |

LLM에는 아래 네 필드만 JSON으로 전달한다.

```json
{
  "raw": "0.5",
  "unit": "",
  "context": "임계값 | 0.5",
  "type": "table"
}
```

전체 보고서, 다른 후보, 분석 코드, 원데이터 파일은 LLM에 전달하지 않는다. `docs/USED.md`에는 수치 검증 대상 판별의 로컬 adapter 통합 시험에 `Ollama · qwen3:8b`를 사용한 사실이 기록되어 있다.

## 9. LLM 판정 기준

현재 system prompt는 다음 우선순위를 명시한다.

1. 분석 코드·데이터 처리로 계산된 OUTPUT의 적극적 근거가 있으면 `VERIFY`
2. INPUT / SETTING / METADATA의 적극적 근거가 있으면 `IGNORE`
3. 어느 근거도 충분하지 않으면 `UNCERTAIN`

OUTPUT 근거가 없거나, 숫자가 단순하거나, 분석 provenance가 불명확하다는 사실만으로 `IGNORE`하지 않는다. 이 경우는 `UNCERTAIN`이다.

아래는 현재 작업환경에서 adapter를 직접 호출한 실제 로컬 qwen3:8b 통합 확인 결과다. 이는 mock 테스트와 별도의 수동 통합 확인이며, full pipeline에서는 규칙에서 확정된 후보가 LLM으로 전달되지 않을 수 있다.

| context | 실제 로컬 LLM 결과 | full pipeline에서의 유의점 |
|---|---|---|
| `정확도 \| 87.3%` | `VERIFY` | 규칙도 정확도 문맥을 `VERIFY`로 확정하므로 일반적으로 LLM 미호출 |
| `임계값 \| 0.5` | `IGNORE` | 규칙은 `UNCERTAIN`으로 남기며, LLM 보조 판별 대상 |
| `학습률 \| 0.001` | `IGNORE` | 현재 규칙의 명시 패턴에는 없으므로 LLM 보조 판별 대상 |
| `값 \| 12` | `UNCERTAIN` | 규칙도 기본적으로 `UNCERTAIN` |

## 10. 실패 안전성

Ollama adapter는 응답의 `message.content` 전체가 유효한 JSON object인지 확인하고, `status`가 정확히 아래 셋 중 하나인지 검증한다.

```text
VERIFY
IGNORE
UNCERTAIN
```

다음 상황은 adapter 오류로 처리된다.

- Ollama 연결 실패
- timeout
- HTTP 오류
- Ollama 응답 구조 오류
- JSON 파싱 실패
- `message.content`가 문자열이 아님
- 허용되지 않은 status 또는 비어 있는 reason

`verification_classifier.py`는 주입 classifier 예외 또는 잘못된 응답을 잡아 후보를 삭제하지 않고 `UNCERTAIN`으로 보존한다. 이 fallback의 `verification_method`는 `rule`이며 reason에는 실패 또는 무효 응답 사실을 기록한다.

## 11. 최종 candidate 구조

아래는 현재 코드가 생성할 수 있는 table 후보 예시다. `모델 정확도` 문맥은 규칙 기반 `VERIFY`에 해당한다.

```json
{
  "raw": "87.3%",
  "value": 87.3,
  "unit": "%",
  "context": "모델 정확도 | 87.3%",
  "page": 10,
  "type": "table",
  "order": 2,
  "start": 0,
  "end": 5,
  "row": 2,
  "column": 1,
  "exclude": false,
  "exclude_reason": null,
  "verification_status": "VERIFY",
  "verification_reason": "rule: analysis-result language in context",
  "verification_method": "rule"
}
```

복합 수치에는 이 구조에 `operator`, `statistic`, `error`, `range_start`, `range_end`, `confidence_level` 등이 선택적으로 추가될 수 있다.

classifier는 위 classified candidate의 값·문맥·위치·판정 필드를 변경하지 않는다. 이후 결과표 formatter는 candidate를 복사한 뒤 출력 편의 필드만 추가하며, classifier의 판정 결과와 기존 추가 필드를 다시 계산하거나 대체하지 않는다.

## 12. 수치 검증 결과표 출력

`doc_parser/numeric_result_table.py`는 classified candidate를 후속 모듈과 UI가 사용하기 쉬운 구조화 결과표로 변환한다. 기준 출력은 JSON 직렬화 가능한 `list[dict]`이며, Markdown table은 사람이 확인하기 위한 보조 출력일 뿐 기준 데이터 형식이 아니다.

| 공개 함수 | 역할 |
|---|---|
| `format_numeric_results(candidates)` | 각 candidate를 복사하고 결과표 행 및 `display_location`을 생성 |
| `select_results_by_status(results, status)` | `VERIFY` / `IGNORE` / `UNCERTAIN` 중 지정 status의 행을 복사해 조회 |
| `select_verify_results(results)` | VERIFY 전용 편의 조회 |
| `to_markdown_table(results)` | 사람 검토용 Markdown 표 문자열 생성 |

formatter는 `dict(candidate)` 방식으로 기존 candidate를 복사한다. 따라서 아래 기본 필드와 후보에 이미 존재하는 추가 필드를 제거하지 않는다.

| 필드 | 의미 |
|---|---|
| `raw`, `value`, `unit` | 원문 수치, 정규화 값, 단위 |
| `context`, `type`, `page`, `order` | 원문 문맥과 block 위치 정보 |
| `start`, `end` | 원래 추출 문자열 내부의 위치 |
| `row`, `column` | table cell의 내부 0-based 위치; 없는 경우 `null`로 안정화 |
| `display_location` | 사람 검토용 위치 문자열 |
| `exclude`, `exclude_reason` | 명백한 비검증 수치 filter 결과 |
| `verification_status`, `verification_reason`, `verification_method` | 최종 판별 결과 및 근거 |

복합 수치의 `operator`, `statistic`, `error`, `range_start`, `range_end`, `confidence_level`도 그대로 보존된다. 미래 확장 candidate의 알 수 없는 추가 필드 역시 화이트리스트 방식으로 삭제하지 않는다.

`row`와 `column`의 내부 값은 계속 0-based다. `display_location`에서만 사람에게 보여주는 행·열을 1-based로 변환한다. `order`는 실제 문서의 표 번호가 아니라 block 순서이므로 표시는 `표 #23`이 아니라 `표 block #23`을 사용한다.

| block 조건 | `display_location` 예 |
|---|---|
| page 없는 paragraph | `문단 #45` |
| page 있는 paragraph | `p.10 · 문단 #45` |
| page 없는 caption | `캡션 #8` |
| 좌표 있는 table | `표 block #23 · 2행 3열` |
| page·좌표 있는 table | `p.10 · 표 block #23 · 2행 3열` |
| 좌표 없는 table | `표 block #23` |

`to_markdown_table()`은 기본적으로 `display_location`, `raw`, `value`, `unit`, `context`, `verification_status`, `verification_method`을 표시하고 pipe 및 줄바꿈을 escape한다. 원본 structured 결과를 Markdown으로 대체하지 않는다.

## 13. 테스트 현황

아래 명령을 현재 `part/numeric` 브랜치에서 실행했다.

```bash
python3 -m unittest \
  doc_parser.test_numeric_candidates \
  doc_parser.test_compound_numeric_candidates \
  doc_parser.test_non_verification_filter \
  doc_parser.test_verification_classifier \
  doc_parser.test_collector_blocks \
  doc_parser.test_ollama_classifier -v
```

결과는 **40건 실행, 모두 성공**이다.

| 범주 | 테스트 파일 | 테스트 수 | 확인 범위 |
|---|---|---:|---|
| 기본 숫자 추출 | `test_numeric_candidates.py` | 4 | 원문·값·단위·위치, 날짜·절 번호 후보 보존 |
| 복합 통계 표현 | `test_compound_numeric_candidates.py` | 5 | 부등식, ±, 범위, 신뢰구간, Unicode 과학 표기 |
| 비검증 필터 | `test_non_verification_filter.py` | 10 | 연도·날짜·표/그림·절·쪽·참고문헌, 보수적 보존 |
| 규칙 기반 classifier | `test_verification_classifier.py` | 7 | VERIFY/IGNORE/UNCERTAIN, 최소 payload, fallback |
| CollectorBlock·table rows | `test_collector_blocks.py` | 8 | caption, `page=None`, rows, 좌표·context·batch·필드 보존 |
| Ollama adapter mock | `test_ollama_classifier.py` | 6 | localhost 설정, 최소 payload, thinking 무시, 실패 fallback, 호출 조건 |

Ollama adapter 테스트는 transport mock을 사용하며 외부 또는 실제 서버를 호출하지 않는다. 위 9절의 실제 qwen3:8b 결과는 별도 로컬 통합 확인이며, 현재 자동화 테스트 파일에는 실제 모델 호출을 포함하지 않는다.

별도로 `.venv` 환경에서 다음 테스트 계열이 각각 통과했다.

| 테스트 계열 | 실행 결과 | 범위 |
|---|---:|---|
| numeric pipeline | **40 passed** | 위 표의 수치 추출·필터·classifier·CollectorBlock·Ollama mock 테스트 |
| parser | **69 passed** | `doc_parser/tests/` parser 단위 테스트 |
| numeric result formatter | **8 passed** | `test_numeric_result_table.py`: 위치 표시, status 조회, 복합 필드 보존, 원본 불변성, Markdown escape |

세 결과는 서로 다른 테스트 계열에서 각각 통과한 것이다. 합계 117건을 하나의 단일 test suite에서 `117 passed`로 실행한 결과는 아니다.

## 14. 실제 HWPX End-to-End 통합 검증

실제 문서 `data/samples/sample-10-hwpx/report.hwpx`를 아래 경로로 실행했다.

```text
parse_document(path)
→ CollectorBlock[]
→ extract_numeric_candidates_from_blocks()
→ filter_obvious_non_verification_candidates()
→ classify_candidates(..., classifier=OllamaClassifier())
→ format_numeric_results()
→ select_verify_results()
```

| 항목 | 실제 결과 |
|---|---:|
| 입력 문서 | `data/samples/sample-10-hwpx/report.hwpx` |
| CollectorBlock | 82개 |
| paragraph / caption / table | 74 / 0 / 8개 |
| `rows`가 존재하는 table | 8개 |
| classified candidate | 438개 |
| formatter 결과표 | 438행 |
| VERIFY 결과표 | 147행 |
| `exclude=true` / `exclude=false` | 7 / 431개 |
| VERIFY | 147개 |
| IGNORE | 36개 |
| UNCERTAIN | 255개 |
| `verification_method=rule` | 89개 |
| `verification_method=llm` | 349개 |
| 실제 Ollama 호출 | 352개 |
| 최종 결과 | 통과 |

HWPX의 page 값은 모두 `null`로 유지됐다. table 후보에서는 `row`, `column`, 행 전체 context가 formatter 결과표까지 보존됐고, `display_location`이 추가됐다. `1,488개`, `26.5%`, `97.78%`은 모두 VERIFY 결과표에서 확인됐다.

| raw | status / method | context 및 내부 위치 | 대표 `display_location` |
|---|---|---|---|
| `1,488개` | VERIFY / `rule` | 문단 후보 | `문단 #45` |
| `26.5%` | VERIFY / `llm` | `해외일반 \| 82 \| 26.5%`, `row=1`, `column=2` | `표 block #23 · 2행 3열` |
| `97.78%` | VERIFY / `llm` | `전체 percent agreement (이진 셀 기준) \| 97.78%`, `row=2`, `column=1` | `표 block #47 · 3행 2열` |

실행은 unhandled exception, 누락 필드, 타입 불일치 없이 완료됐다. 352회의 실제 Ollama 호출 중 3개는 adapter 응답 실패 또는 무효 응답 등의 안전 fallback으로 처리됐으며, 후보를 삭제하거나 pipeline을 중단하지 않고 `UNCERTAIN`으로 보존했다.

## 15. 현재 확인된 개선 포인트

실제 HWPX 통합 시험은 후보 누락을 줄이고 안전하게 후속 단계로 전달한다는 현재 목적을 충족했다. 동시에 다음은 구현 실패가 아니라, 추가 규칙 정교화 및 LLM 호출량 최적화가 가능한 영역으로 확인됐다.

| 관찰 사례 | 현재 동작 | 개선 검토 방향 |
|---|---|---|
| 작성일 `2026-07-22` | `2026-07`, `22` 등이 별도 후보로 남음 | 날짜 형식·구분자 처리 보강 여부 검토 |
| 문단 번호 `(1)` | 숫자 후보로 남음 | 괄호형 문단 번호의 보수적 제외 규칙 검토 |
| `Claude Sonnet 4.6`, `Claude Sonnet 5` | 모델 버전 숫자가 후보로 남음 | 모델·소프트웨어 버전 문맥 규칙 확대 검토 |
| 438개 후보 중 Ollama 352회 호출 | `UNCERTAIN` 후보가 실제 LLM으로 많이 전달됨 | 규칙 기반 문맥 판별 확대, batching·호출 정책 검토 |

현재 설계는 연구 결과 수치를 잘못 제거하는 것보다 불필요한 후보를 남기는 편을 우선한다. 따라서 위 항목은 모든 false positive를 즉시 제거하는 요구가 아니라, 재현 가치가 있는 수치를 놓치지 않는 원칙을 유지한 최적화 후보로 관리한다.

## 16. 현재 완료된 범위

- [x] 숫자 후보 추출
- [x] 정수·실수·부호·쉼표 숫자 정규화
- [x] 단위 보존
- [x] p-value, 부등식, ±, 범위, 신뢰구간, 과학적 표기 처리
- [x] paragraph 입력 처리
- [x] caption 입력 처리
- [x] table rows 입력 처리
- [x] table row / column 0-based 위치 보존
- [x] table 행 전체 context 보존
- [x] `rows`와 rendered `text`의 중복 추출 방지
- [x] blocks batch 입력 처리
- [x] 명백한 비검증 수치 filter
- [x] 규칙 기반 VERIFY / IGNORE / UNCERTAIN 판별
- [x] `UNCERTAIN` 후보용 provider-independent classifier 주입 구조
- [x] 로컬 Ollama qwen3:8b adapter
- [x] LLM 실패 시 후보 보존형 `UNCERTAIN` fallback
- [x] HWPX parser → CollectorBlock 연결의 실제 문서 검증
- [x] 실제 HWPX → numeric candidate 추출
- [x] 실제 HWPX table rows → row / column / context 보존
- [x] 실제 HWPX의 filter·rule classifier·로컬 qwen3:8b 연결
- [x] 실제 HWPX end-to-end 통합 시험
- [x] classified candidate → 구조화된 결과표 변환
- [x] 전체 상태 결과 보존
- [x] VERIFY-only 조회
- [x] VERIFY / IGNORE / UNCERTAIN 상태별 조회
- [x] display_location 생성
- [x] table 위치 표시
- [x] 복합 수치 필드 보존
- [x] Markdown table 보조 출력
- [x] 실제 HWPX 결과표 생성
- [x] 실제 HWPX VERIFY 결과표 생성

## 17. 아직 남은 작업 / 다른 모듈 의존성

아래 항목은 현재 수치 수집·판별 모듈에 구현되어 있지 않으며, 전체 프로젝트 연결을 위한 후속 의존성이다. 미구현 자체를 현재 모듈의 실패로 해석하지 않는다.

| 항목 | 구분 | 현재 상태 |
|---|---|---|
| HWPX / DOCX / PDF 문서 파서 | 다른 담당 영역 | parser 자체 테스트는 통과했으며, numeric pipeline 실제 통합 검증은 HWPX만 완료 |
| `Document → CollectorBlock[]` adapter | 다른 담당 영역 | HWPX 실제 연결은 확인됨; 수치 모듈은 Document를 직접 받지 않음 |
| 실제 문서 형식 end-to-end 시험 | 모듈 연결 단계 | HWPX 완료; DOCX/PDF는 numeric pipeline 전체 통합 시험이 남음 |
| 코드 후보 탐색 | 후속 모듈 / 다른 담당 영역 | 미포함 |
| 원데이터 연결 | 후속 모듈 / 다른 담당 영역 | 미포함 |
| 분석 코드 재실행 | 후속 모듈 / 다른 담당 영역 | 미포함 |
| 보고서 값과 재실행 값 비교 | 후속 모듈 / 다른 담당 영역 | 미포함 |
| 최종 검증표 생성 | 후속 모듈 / 다른 담당 영역 | 미포함 |

## 18. 팀장 검토 필요 사항

다음은 현재 구현을 전제로 팀 차원에서 확정하거나 검토하면 좋은 사항이다.

1. `CollectorBlock` 필드·type enum·rows의 오류 표현을 현재 계약대로 최종 확정할지
2. caption을 paragraph와 구분된 `type="caption"`으로 계속 보존할지
3. table 후보의 context를 cell 단독이 아니라 행 전체(`" | "` 결합)로 사용하는 방식이 내력 추적·LLM 판별에 적절한지
4. VERIFY / IGNORE / UNCERTAIN의 업무 기준과, 규칙·LLM 각각이 담당할 범위를 확정할지
5. 로컬 `qwen3:8b`를 본선 기본 보조 판별 모델로 확정하고, 실제 실행 환경에서 Ollama 가용성을 보장할지
