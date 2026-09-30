# 숫자내력 웹 초안 디자인 시스템

## 0. Research Log

- Embedded references: Linear, Sentry, ClickHouse를 검토했고, 검증 도구의 낮은 장식성과 높은 정보 밀도에는 Linear의 어두운 luminance-stack 표면이 가장 적합하다고 선택했다.
- Layout reference: StyleGallery의 `scroll-body-shell`, `step-nav`, `supporting-pane`를 채택했다. 헤더는 고정되고 문서 본문만 스크롤하며, 업로드 순서와 결과 근거를 분리한다.
- Real-product image lane: 이 초안은 로컬 파일 입력 실험용 운영 화면이므로 마케팅 hero·외부 이미지가 필요하지 않아 이미지 초안은 적용하지 않았다.
- Lazyweb lane: 외부 제품 화면을 복제하지 않고, 위 참조에서 정보 계층과 상태 표기 원칙만 재구성한다.

## 1. Design Brief

- Primary user: 연구보고서와 분석 산출물을 제출 전에 확인하는 해커톤 팀원.
- Primary task: 공개 재현 샘플을 고르거나 보고서 1개·데이터 여러 개·분석 코드 1개를 선택하고 어느 검증 단계가 준비됐는지 한눈에 파악한다.
- Tone: 정확하고 차분하며, 자동 검증이 아직 실행되지 않은 상태를 과장하지 않는다.
- Persona constraints: 키보드만 사용하는 사용자, 작은 화면 사용자, 한국어 긴 파일명을 가진 사용자가 파일 선택·상태 확인을 마칠 수 있어야 한다.

## 2. Visual Direction

Near-black canvas와 미세한 luminance stack을 사용한다. 표면은 옅은 흰색 알파 레이어와 얇은 경계로 구분하고, 보라색은 주요 행동과 키보드 focus에만 사용한다. 검증 상태는 텍스트·아이콘·색을 함께 사용한다.

## 3. Tokens

```css
:root {
  --canvas: #08090a;
  --panel: #0f1011;
  --surface: #191a1b;
  --surface-hover: #222429;
  --ink: #f7f8f8;
  --muted: #a3a8b1;
  --subtle: #707680;
  --line: rgba(255, 255, 255, 0.09);
  --line-soft: rgba(255, 255, 255, 0.055);
  --accent: #7170ff;
  --accent-strong: #8787ff;
  --success: #42c583;
  --warning: #e6b450;
  --danger: #ed6a5e;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
}
```

## 4. Typography and Layout

- System UI sans for Korean readability; monospace only for hashes and code extensions.
- Desktop: centered 1180px grid with primary upload/results column and a 300px audit rail.
- Mobile: one column, audit rail follows results, no horizontal scrolling.
- Scroll owner: document body. Long filenames use wrapping, not clipped critical detail.

## 5. Primitives

| Primitive | States |
|---|---|
| `UploadSlot` | empty, populated, keyboard focus; validation error는 후속 구현 |
| `FileRow` | hashed; pending·removable은 후속 구현 |
| `SamplePreset` | default, selected, loading, unavailable |
| `NumberDecisionWorkbench` | match, mismatch, not-comparable, input-required |
| `AutoRecoveryTrail` | direct-recovered, no-alternative, derived-review, recovery-blocked |
| `StageCard` | pending, ready, blocked |
| `StatusBadge` | ready, pending, attention |
| `PrimaryButton` | default, hover, focus-visible, disabled; running은 후속 구현 |

## 6. Motion

File rows and result stages use only opacity/transform transitions. `prefers-reduced-motion` disables transitions. Motion indicates a new selection or a completed local preflight; it is never decorative.

## 7. Accessibility Constraints

- Native file inputs remain keyboard accessible and have explicit labels.
- Status never relies on color alone.
- Focus-visible uses the accent ring.
- Buttons have at least 44px touch height.
- Result changes announce through an `aria-live` region.
- “실험 모드” states that no code execution or report claim extraction has occurred.
- 수치 판정은 보고서 표시 단위·반올림 자릿수·허용오차와 기간·대상·분모·산식 조건을 각각 드러낸다.
- 자동 복구는 최초 후보의 불일치 이력, 탐색 근거, 대체 후보, 최종 상태를 모두 보여 준다. 상태를 색만으로 구분하지 않는다.

## 8. Accepted Debt

- 로컬 카탈로그는 고정된 `data/samples/` 공개 재현 패키지의 파일 수·보고서 크기만 읽는다. 실제 CSV 스키마 검사, 보고서 Claim 추출, 승인 실행 계약 검증, Docker 재실행은 여전히 `code_runner` 실행 어댑터 작업이다.
- 자동 복구 워크벤치는 현재 시나리오 기반 UI 프로토타입이다. 실제 Claim·Provenance 자동 연결 엔진이 반환하는 복구 이력과 아직 연결되지 않았다.
