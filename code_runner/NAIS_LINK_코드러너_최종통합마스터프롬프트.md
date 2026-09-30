# NAIS Link `code_runner` 최종 통합 마스터 프롬프트

> main 최종 기준 · 이 문서 하나만으로 `code_runner`의 구현 범위와 판정 기준을 전달한다. 기존 세부 MD는 설계 이력으로 `part/code`에 남기되, 구현자에게는 이 프롬프트를 우선 기준으로 준다.

```text
당신은 NAIS Link의 code_runner 담당 구현자다.

## 제품 목표

사용자가 제출한 연구보고서, 분석 데이터, 분석 코드를 대상으로 다음을 검증한다.

1. 코드가 승인된 입력 데이터를 실제로 사용했는가.
2. 보고서에서 파싱된 표와 코드 재실행 결과 표의 각 셀이 같은 연구 질문·같은 계산을 의미하는가.
3. 같은 의미가 증명된 셀에 한해, 단위·반올림·지표별 허용오차를 적용했을 때 재현되는가.

핵심 원칙: 같은 위치의 숫자를 빼거나 같은 숫자라는 이유만으로 일치 처리하지 않는다.
예를 들어 평균 15, 합계 15, 15%, 15명은 값이 같아도 서로 다른 수량일 수 있다.

## 0. 작업 경계와 금지 사항

- 수정 범위는 `code_runner/`만이다. `doc_parser/`, `app/`, `main` 및 다른 파트 폴더는 수정하지 않는다.
- 문서 파싱과 웹 화면은 구현하지 않는다. 파서가 전달한 구조화된 보고서 표와 실행 어댑터가 전달한 구조화된 실행 표를 입력으로 받는다.
- Python, R, C/C++, Stata, SAS, Julia, MATLAB, SQL, 노트북 등 언어별 분석 코드는 어댑터가 공통 artifact로 변환한다. 공통 판정 엔진이 특정 언어의 변수명·AST에 의존하면 안 된다.
- LLM의 추론, 문자열 유사도, 숫자 근접성은 후보 생성의 보조 정보일 뿐 자동 `match`의 근거가 아니다.
- 코드 실행은 격리 환경에서만 수행하며, 네트워크·호스트 쓰기 권한·비승인 입력 접근을 허용하지 않는다. 실행 실패는 수치 `mismatch`가 아니다.
- 모든 결과는 사람이 재검토할 수 있는 위치·근거·reason code를 남긴다. 실패·추가·누락 후보를 삭제하거나 첫 후보로 덮어쓰지 않는다.

## 1. 세 입력의 역할과 선행 검증

입력은 세 가지다.

| 입력 | 담당 | code_runner가 확인할 것 |
|---|---|---|
| 연구보고서 | doc_parser | 보고서 표 셀, 원문 위치, 지표 의미, 보고서 선언 허용오차 |
| 분석 데이터 | 실행 어댑터/manifest | 파일 해시, 경로, 핵심 스키마·행 수 |
| 분석 코드 | 실행 어댑터 | 승인 여부, 코드 해시, 실제 입력, 격리 실행, 출력 locator |

### 1-1. 삼중 대조 선행 게이트

표의 값을 비교하기 전에 claim 또는 표 artifact에 아래 증거를 연결한다.

- 코드 ↔ 데이터: 코드가 승인된 데이터 해시·경로·스키마를 사용했는가.
- 보고서 ↔ 데이터: 보고서가 주장하는 기간·대상·분모·핵심 조건이 데이터 정의와 모순되지 않는가.
- 코드 실행: 승인된 코드·입력 계약으로 실행이 완료되고 출력 locator가 확보됐는가.

`CODE_DATA_INPUT_MISMATCH`, `CODE_DATA_SCHEMA_MISMATCH`, `CODE_NOT_APPROVED`, 실행 실패, 격리 불가, 출력 누락은 근거 부족 또는 실행 계약 실패로 기록한다. 값이 우연히 같아도 자동 `match`를 부여하지 않는다.

## 2. 언어 중립 입력 계약

공통 엔진은 최소 아래 정보가 있는 artifact만 받는다.

```text
ReportTableArtifact
  table_id, title, cells[]
  cell = coordinate(panel, row_key, column_path), value, raw_value,
         semantics, source_locator, tolerance_policy

ExecutionTableArtifact
  table_id, title, run_id, cells[]
  cell = coordinate(panel, row_key, column_path), value,
         semantics, code_locator, output_locator, execution evidence
```

`semantics`는 최소 다음 열 개를 보관한다. **각 항목은 단순 문자열이 아니라 근거가 있는 `SemanticEvidence`여야 한다.**

```text
metric, aggregation_or_formula, period, population, denominator,
filters, missing_value_policy, weight, transformation, unit
```

```text
SemanticEvidence
  raw_value, normalized_value, state, locator, extraction_method, reason_code
  state = exact_candidate | unknown | not_applicable_candidate
```

- `raw_value`는 보고서·코드·실행 출력에서 얻은 원문, `normalized_value`는 승인된 정규화 규칙을 적용한 비교용 값이다.
- `locator`는 해당 의미를 뒷받침하는 보고서 원문 위치, 코드 위치 또는 실행 manifest 위치다. `unknown`은 locator가 없다는 사실과 탐색 범위를 `reason_code`에 남긴다.
- 어댑터는 값만 채워 넣어 `exact`를 주장할 수 없다. 공통 엔진이 양쪽 `normalized_value`와 근거를 비교해 최종 `exact`·`mismatch`·`unknown`·`not_applicable`을 결정한다.

언어별 어댑터는 출력 후보와 그 근거만 만든다. 공통 엔진의 5단계 판정을 언어별로 복제하지 않는다.

## 3. 두 표를 연결하는 순서

### A. 표 연결

보고서 표와 실행 표를 다음 근거로 후보화한다.

- 표 ID 또는 승인된 explicit mapping
- 정규화한 제목 토큰
- 공통 행·열 구조
- 대표 셀의 지표·기간
- 코드 출력 locator·재현 주석

값이 같은 셀 수는 표 연결 점수에 사용하지 않는다. 점수는 후보 정렬과 감사 설명용일 뿐 최종 판정 기준이 아니다.

표 연결은 실행마다 같은 결과가 나와야 한다. `TableLinkPolicy`에 `policy_id`, `version`, `minimum_evidence`, `minimum_score`, `ambiguity_margin`, 허용 정규화 규칙을 고정하고, 결과와 audit ledger에 정책 ID·버전·입력 해시를 기록한다. 정책이 없거나 margin을 계산할 수 없으면 자동 연결하지 않고 `needs_human_review`로 남긴다.

- 최고 후보가 단일하고 최소 연결 근거가 있으면 `matched`.
- 1·2위 후보가 동점 또는 margin 미만이면 `ambiguous`; 자동 값 비교 금지.
- 보고서 표에 실행 대응이 없으면 `report_only_table`.
- 실행 표에 보고서 대응이 없으면 `execution_only_table`.

### B. 셀 연결

연결된 표에서 아래 키로 셀 후보를 만든다.

```text
normalized(panel) + normalized(row_key) + normalized(column_path[])
```

대소문자·공백 정리 외의 동의어는 승인 매핑 레지스트리만 사용한다. 예를 들어 `서울`, `서울시`, `Seoul`은 같은 canonical ID에 승인 매핑됐을 때만 연결한다. 매 실행 결과에는 registry version, hash, mapping ID, 양쪽 원문 alias를 기록한다.

| 셀 연결 결과 | 처리 |
|---|---|
| 보고서 1개 ↔ 실행 1개 | 의미 10기준 대조 진행 |
| 보고서 1개 ↔ 실행 여러 개 | `needs_human_review`, 모든 후보 보존 |
| 보고서 여러 개 ↔ 실행 1개 또는 여러 개 ↔ 여러 개 | `needs_human_review`, 임의 병합·분할 금지 |
| 보고서 셀만 존재 | `evidence_incomplete`, `MISSING_EXECUTION_COUNTERPART` |
| 실행 셀만 존재 | `execution_only_cell`로 보존, 보고서 불일치로 단정 금지 |

전체·소계·상세 행은 구조 역할(`TOTAL`, `SUBTOTAL`, `DETAIL`, `UNKNOWN`)을 별도로 보관한다. `DETAIL ↔ TOTAL`, `TOTAL ↔ SUBTOTAL`처럼 역할이 명시적으로 다르면 자동 값 비교를 금지하고 `not_comparable`로 남긴다. 역할이 `UNKNOWN`이면 임의 추론하지 않고 `needs_human_review`다.

## 4. 같은 셀인지 증명하는 의미 10기준

단일하게 연결된 셀에 아래 10개를 **반드시 이 순서로** 대조한다.
각 기준에는 `exact`, `mismatch`, `unknown`, `not_applicable` 중 하나와 양쪽 값·근거 위치·reason code를 저장한다.

| # | 기준 | 대조 질문 | mismatch 예 |
|---:|---|---|---|
| 1 | `metric` | 무엇을 측정하는가 | 만족도 vs 소득 |
| 2 | `aggregation_or_formula` | 어떤 계산·집계 범위인가 | 평균 vs 합계, 전체 vs 일부 소계 |
| 3 | `period` | 어느 시점·기간인가 | 2025년 vs 2024년 |
| 4 | `population` | 누구/어느 집단인가 | 서울 응답자 vs 전체 |
| 5 | `denominator` | 무엇으로 나눴는가 | 유효 응답자 vs 전체 응답자 |
| 6 | `filters` | 무엇을 포함·제외했는가 | 여성만 vs 전체 |
| 7 | `missing_value_policy` | 결측을 어떻게 처리했는가 | 제외 vs 0 대체 |
| 8 | `weight` | 가중치를 어떻게 적용했는가 | 단순평균 vs 가중평균 |
| 9 | `transformation` | 값 변환이 같은가 | 원값 vs 로그값 |
| 10 | `unit` | 차원·환산이 호환되는가 | % vs 명 |

규칙:

- `mean(score)`와 `sum(score)`는 2번 mismatch다.
- `TOTAL ↔ TOTAL` 또는 `SUBTOTAL ↔ SUBTOTAL`이어도, 집계 함수·grouping key·포함/제외 행·소계 범위가 다르면 2번 mismatch다. 구조 역할이 같다는 사실만으로 같은 수량이라고 보지 않는다.
- `%`와 ratio는 출처가 있는 변환이 가능하면 10번 exact로 만들 수 있다. `%`와 `명`, kg와 cm는 mismatch다.
- `not_applicable`은 양쪽 근거로 해당 기준이 실제 적용되지 않음이 증명될 때만 쓴다. 필드 누락을 exact 또는 not_applicable로 채우지 않는다.
- 하나라도 `mismatch`면 숫자가 같아도 같은 수량이 아니므로 값 차이를 계산하지 않는다.
- mismatch는 없지만 `unknown`이 하나라도 있으면 자동 값을 비교하지 않는다.

## 5. 파생 수치와 후보 재탐색

직접 출력 셀과 파생 후보를 구별한다.

- 코드가 보고서 셀에 대응하는 평균을 직접 출력했다면 직접 후보로 대조할 수 있다.
- 합계와 분모만 있어 평균을 재구성할 수 있더라도, 근거가 불완전하면 `DERIVED_PROVENANCE`와 `needs_human_review`로 남긴다.
- 최초 후보가 합계라 `not_comparable`이더라도, 같은 승인 실행의 직접 평균 출력 후보를 발견하면 제한적으로 재탐색할 수 있다.
- 대체 후보는 **구조 역할이 호환되고 의미 10기준 전부가 `exact` 또는 근거 있는 `not_applicable`**이며, 필수 실행 증거·TolerancePolicy까지 통과할 때만 자동 선택한다. 최초 후보·탐색 전략·탈락 사유·교체 결과는 audit ledger에 보존한다.

후보 점수는 연결 후보 순서에만 사용한다. 최고 점수가 낮거나 1·2위 차이가 ambiguity margin 미만이면 `needs_human_review`다.

## 6. 최종 5단계 판정: 절대 우선순위

최종 `decision_status`는 아래 다섯 개만 사용한다.

```text
1. 셀 연결이 단일한가?
   아니오 → needs_human_review

2. 구조 역할 또는 의미 10기준 중 명백한 mismatch가 있는가?
   예 → not_comparable

3. 필수 실행 증거(승인 코드·입력 계약·실행·출력 locator)가 있는가?
   아니오 → evidence_incomplete

4. mismatch는 없지만 구조 역할/의미 10기준 중 unknown이 있는가?
   예 → needs_human_review

5. 해당 셀의 TolerancePolicy가 있는가?
   아니오 → needs_human_review

6. 단위 환산 → 보고서 표기 자릿수 반올림 → 절대/상대 허용오차 비교
   이내 → match
   초과 → mismatch
```

| 상태 | 정확한 의미 |
|---|---|
| `match` | 같은 수량임이 증명됐고 값 차이가 정책 이내 |
| `mismatch` | 같은 수량임이 증명됐지만 값 차이가 정책 초과 |
| `not_comparable` | 수량의 의미·구조가 달라 값 비교 자체가 무의미 |
| `evidence_incomplete` | 실행·입력·출력·근거가 부족해 안전한 비교 불가 |
| `needs_human_review` | 후보 경합, 의미 unknown, 정책 부재 등 자동 선택 불가 |

명확한 기간·산식 mismatch와 실행 실패가 함께 있으면, 이미 두 수량이 다르다는 사실이 더 강하므로 `not_comparable`을 최종 상태로 두고 실행 실패를 보조 reason code로 보존한다.

## 7. 수치 비교와 허용오차

- 변환 가능한 단위만 변환하고 변환식·원단위·변환 후 단위를 기록한다.
- 계산은 `Decimal` 등 10진 정밀도 기준으로 수행한다. locale 표기·천 단위 구분자·결측 표기는 입력 경계에서 명시적으로 정규화하고, 파싱 불가 값은 `unknown`으로 남긴다.
- 순서는 **단위 환산 → 보고서 표시 자릿수 반올림 → 차이 계산 → 허용오차 평가**로 고정한다. 상대오차의 분모가 0이면 상대오차는 `null`로 남기고, 정책의 절대오차 규칙이 있을 때만 그 규칙으로 판정한다. 둘 다 없으면 `needs_human_review`다.
- `TolerancePolicy`는 `absolute_limit`, `relative_limit`, `combination_rule`(`absolute_only` | `relative_only` | `either` | `both`), `rounding_mode`, `policy_id`, `version`을 명시한다. `either`는 둘 중 하나 이내, `both`는 둘 다 이내일 때만 통과한다.
- 정책 우선순위는 **승인된** `report_declared` > `approved_metric_catalog` > 없음이다. 보고서 선언값은 허용된 상한을 초과하거나 승인되지 않았으면 정책이 아니라 근거 정보로만 보존한다.
- 정책 없음은 0 허용오차가 아니다. `needs_human_review`다.
- 신장·체중·비율·정수 건수 등 승인 카탈로그가 있는 지표만 공통 정책을 쓴다. 금액·종합지수에는 임의 기본값을 적용하지 않는다.
- `absolute_difference`, `relative_difference`는 `match`/`mismatch`일 때만 채운다. 나머지 세 상태는 `null`이다.

## 8. 결과 계약과 감사 기록

각 보고서 셀 결과에 최소 아래를 반환한다.

```json
{
  "report_coordinate": {"panel": "전체", "row_key": "서울", "column_path": ["만족도", "평균"]},
  "execution_coordinate": {"panel": "전체", "row_key": "서울", "column_path": ["만족도", "평균"]},
  "table_link_evidence": ["TABLE_MAPPING:report-table-3:summary-table"],
  "cell_link_evidence": ["ROW_KEY_EXACT", "COLUMN_PATH_MAPPING:metric.satisfaction-mean.v1"],
  "mapping_registry": {"version": "v2026.01", "hash": "...", "mapping_ids": ["geo.seoul.v1"]},
  "table_link_policy": {"policy_id": "table-link.default", "version": "v1", "minimum_score": 80, "ambiguity_margin": 10},
  "structural_role_check": {"report": "DETAIL", "execution": "DETAIL", "state": "exact"},
  "semantic_checks": [
    {
      "criterion": "aggregation_or_formula",
      "state": "exact",
      "report_value": "mean(score)",
      "execution_value": "mean(score)",
      "report_locator": "보고서 12쪽 표 3 각주",
      "execution_locator": "analysis/main.R:81-87",
      "reason_code": null
    }
  ],
  "numeric_check": {
    "unit_conversion": "ratio_to_percent",
    "rounding_digits": 1,
    "absolute_difference": "0.02",
    "relative_difference": null,
    "tolerance_policy_id": "report.table3.rate.v1",
    "tolerance_policy_version": "v1",
    "combination_rule": "absolute_only"
  },
  "decision_status": "match",
  "reason_codes": ["VALUE_WITHIN_TOLERANCE"],
  "reason_summary": "의미 10기준과 구조 역할이 확인됐고 0.1%p 허용오차 이내입니다.",
  "code_locator": "analysis/main.R:81-87",
  "output_locator": "outputs/summary.json#/rows/seoul/mean_satisfaction",
  "next_action": null
}
```

후보가 여러 개라면 선택 후보만 남기지 말고 `candidate_assessments`에 전체 후보, 점수 세부내역, hard-gate 결과, 선택·탈락 사유, recovery history를 보존한다. API/UI는 이 결과를 표시만 하고 판정 규칙을 재계산하지 않는다.

## 9. 필수 테스트

아래는 외부 API나 실제 Docker 없이 fixture로 자동화한다.

1. 평균 15와 합계 15 → `not_comparable`, `AGGREGATION_OPERATOR_MISMATCH`
2. 2025년 평균과 2024년 평균 → `not_comparable`, `PERIOD_MISMATCH`
3. 15%와 15명 → `not_comparable`, `UNIT_DIMENSION_MISMATCH`
4. 필터·결측 처리·가중치 중 하나가 다름 → 각각 `not_comparable`
5. 의미 10기준이 전부 맞고 15.0%/15.02%, 0.1%p 정책 → `match`
6. 의미 10기준이 전부 맞고 15.0%/15.2%, 0.1%p 정책 → `mismatch`
7. 10기준 중 하나가 unknown → `needs_human_review`, 차이 `null`
8. 대응 실행 셀·출력 locator가 없음 → `evidence_incomplete`
9. 같은 좌표의 실행 후보가 둘 이상 → `needs_human_review`, 둘 다 보존
10. 승인된 서울/서울시 매핑은 연결, 승인되지 않은 유사 표기는 자동 연결 금지
11. %/ratio, cm/m, kg/g은 환산 근거를 남기고 비교
12. DETAIL/TOTAL 또는 TOTAL/SUBTOTAL → `not_comparable`; 역할 unknown → `needs_human_review`
13. 직접 평균 출력 후보로 복구 가능할 때 최초 합계 후보 이력 보존
14. 코드 데이터 해시·스키마 불일치와 실행 실패가 `mismatch`로 잘못 분류되지 않음
15. 기존 `code_runner` 전체 회귀 테스트 통과
16. 대체 후보가 metric·formula·denominator 중 하나라도 다르면 자동 선택되지 않고 전체 후보 이력이 보존됨
17. 같은 `TOTAL`이라도 grouping key 또는 포함 행이 다르면 `not_comparable`
18. 0 분모 상대오차, `either`/`both`, 승인되지 않은 보고서 허용오차가 정책대로 판정됨
19. TableLinkPolicy 버전·margin이 없거나 후보 점수 차가 margin 미만이면 자동 연결되지 않음

## 10. 완료 조건

- 5개 최종 상태가 서로 배타적인 우선순위로 반환된다.
- 모든 결과에는 reason code, 사람이 읽는 설명, 보고서·코드·출력 위치 또는 부재 사유가 있다.
- 추가·누락 표/셀, 후보 경합, 대체 후보 탐색 이력이 사라지지 않는다.
- 새 언어가 추가돼도 공통 판정 엔진을 수정하지 않고 어댑터만 추가하면 된다.
- 구현 후 수정 파일, 테스트 결과, 아직 파서/실행 어댑터가 제공해야 할 입력 필드를 간결히 보고한다.
```

## main에 함께 올릴 필요가 없는 기존 설계 이력

아래 파일은 버리지 않고 `part/code`에 남긴다. 다만 main의 최종 산출물로는 위 프롬프트 하나를 우선한다.

- `재실행대조_최종코드생성프롬프트.md`
- `삼중대조_실행프롬프트.md`
- `실행어댑터_코드생성프롬프트.md`
- `후보상태_판정엔진_구현마스터프롬프트.md`
- `자동수치연결_코드생성_마스터프롬프트.md`
- `전체소계_구조역할_구현프롬프트.md`
- `두표대조_통합구현_최종프롬프트.md`
- `표대조_5단계판정_구현명세.md`
