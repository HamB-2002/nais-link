"""숫자내력 — 화면 흐름 스켈레톤 (다크 대시보드 스타일).

파일 업로드 → 병렬 분석/실행 → 대조표 → 최종 결론, 네 화면이 이어지는
진행 방식과 시각 스타일을 확인하기 위한 목업이다. doc_parser/code_runner를
부르지 않고 고정된 예시 claim 20개로 채워져 있으며, 파일을 올리지 않아도
"검사 시작"을 누르면 곧바로 다음 화면으로 넘어간다.

실행: pip install streamlit && streamlit run app/app.py
"""

import time

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="숫자내력", page_icon="🔍", layout="centered")

MOCK_CLAIMS = [
    {"claim_id": "C-01", "metric": "처리 속도 개선 배수", "report_value": "2.7배", "evidence_value": "2.71배",
     "status": "match", "reason": "허용오차 이내 일치"},
    {"claim_id": "C-02", "metric": "정확도", "report_value": "87.5%", "evidence_value": "84.1%",
     "status": "mismatch", "reason": "허용오차를 벗어난 값 차이 — 코드 버전 또는 입력 데이터 확인 필요"},
    {"claim_id": "C-03", "metric": "표본 수", "report_value": "1,200명", "evidence_value": "1,200명",
     "status": "needs_human_review", "reason": "독립 재계산 — 원본 재현이 아니라 값이 같아도 자동 확정하지 않음"},
    {"claim_id": "C-04", "metric": "예산 증가율", "report_value": "3.5억원", "evidence_value": "3.54억원",
     "status": "match", "reason": "반올림 후 일치"},
    {"claim_id": "C-05", "metric": "평균 처리시간", "report_value": "1.2초", "evidence_value": "1.2초",
     "status": "match", "reason": "반올림 후 일치"},
    {"claim_id": "C-06", "metric": "참여 기관 수", "report_value": "12개", "evidence_value": "12개",
     "status": "match", "reason": "정확히 일치"},
    {"claim_id": "C-07", "metric": "특허 출원 건수", "report_value": "8건", "evidence_value": "8건",
     "status": "match", "reason": "정확히 일치"},
    {"claim_id": "C-08", "metric": "논문 게재 수", "report_value": "15편", "evidence_value": "15편",
     "status": "match", "reason": "정확히 일치"},
    {"claim_id": "C-09", "metric": "에너지 절감률", "report_value": "23.4%", "evidence_value": "19.8%",
     "status": "mismatch", "reason": "허용오차를 벗어난 값 차이 — 측정 기간 확인 필요"},
    {"claim_id": "C-10", "metric": "처리량 증가", "report_value": "4.1배", "evidence_value": "4.08배",
     "status": "match", "reason": "반올림 후 일치"},
    {"claim_id": "C-11", "metric": "매출 기여도", "report_value": "12.5억원", "evidence_value": "12.47억원",
     "status": "match", "reason": "반올림 후 일치"},
    {"claim_id": "C-12", "metric": "사용자 만족도", "report_value": "92.3%", "evidence_value": "92.3%",
     "status": "match", "reason": "정확히 일치"},
    {"claim_id": "C-13", "metric": "재현율", "report_value": "0.87", "evidence_value": "0.87",
     "status": "needs_human_review", "reason": "산술 검산 — 원본 재현이 아니라 값이 같아도 자동 확정하지 않음"},
    {"claim_id": "C-14", "metric": "응답 지연시간", "report_value": "850ms", "evidence_value": "0.85s",
     "status": "match", "reason": "단위 환산 후 일치"},
    {"claim_id": "C-15", "metric": "참여 연구원 수", "report_value": "34명", "evidence_value": "34명",
     "status": "match", "reason": "정확히 일치"},
    {"claim_id": "C-16", "metric": "검출 정확도", "report_value": "96.1%", "evidence_value": "96.08%",
     "status": "match", "reason": "반올림 후 일치"},
    {"claim_id": "C-17", "metric": "오류율", "report_value": "2.1%", "evidence_value": "3.4%",
     "status": "mismatch", "reason": "허용오차를 벗어난 값 차이 — 전처리 조건 확인 필요"},
    {"claim_id": "C-18", "metric": "처리 비용 절감", "report_value": "1.8배", "evidence_value": "1.79배",
     "status": "match", "reason": "반올림 후 일치"},
    {"claim_id": "C-19", "metric": "학습 시간 단축", "report_value": "45분", "evidence_value": "45분",
     "status": "match", "reason": "정확히 일치"},
    {"claim_id": "C-20", "metric": "모델 크기 감소", "report_value": "62%", "evidence_value": "61.8%",
     "status": "match", "reason": "반올림 후 일치"},
]

# match/mismatch 둘로만 나누지 않는다. 그 외 상태(not_comparable,
# evidence_incomplete, isolation_unavailable, execution_failed,
# needs_human_review)는 전부 "판단 보류" 한 색(warning)으로 묶되, 카드마다
# 개별 reason을 그대로 보여줘 "왜 보류인지"가 뭉개지지 않게 한다.
STATUS_STYLE = {
    "match": {"tone": "good", "label": "일치"},
    "mismatch": {"tone": "critical", "label": "불일치"},
    "needs_human_review": {"tone": "warning", "label": "판단 보류"},
    "not_comparable": {"tone": "warning", "label": "판단 보류"},
    "evidence_incomplete": {"tone": "warning", "label": "판단 보류"},
    "isolation_unavailable": {"tone": "warning", "label": "판단 보류"},
    "execution_failed": {"tone": "warning", "label": "판단 보류"},
}

ICON = {
    "good": '<svg viewBox="0 0 16 16" fill="none"><path d="M3 8.5l3 3 7-7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "critical": '<svg viewBox="0 0 16 16" fill="none"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "warning": '<svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.6"/><path d="M8 5.2v3.3M8 10.8h.01" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
}

DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root {
  --bg: #0d0d0d;
  --surface: #1a1a19;
  --surface-2: #232322;
  --border: rgba(255,255,255,0.10);
  --ink: #ffffff;
  --ink-2: #c3c2b7;
  --ink-muted: #898781;
  --grid: #2c2c2a;
  --accent: #35c9ba;
  --accent-soft: rgba(53,201,186,0.14);
  --good: #0ca30c;
  --good-soft: rgba(12,163,12,0.16);
  --warning: #fab219;
  --warning-soft: rgba(250,178,25,0.16);
  --critical: #d03b3b;
  --critical-soft: rgba(208,59,59,0.16);
}

.stApp, [data-testid="stAppViewContainer"] { background: var(--bg); }
html, body, [class*="css"] { font-family: "IBM Plex Sans", system-ui, sans-serif; }
h1, h2, h3, p, span, label, div { color: var(--ink); }
.block-container { padding-top: 2.5rem; max-width: 760px; }
#MainMenu, footer, header { visibility: hidden; }

/* Streamlit이 새 엘리먼트에 기본으로 넣는 fade-in/slide 전환을 끈다.
   (fd-spinner-ring, fd-clear-out 같은 우리 자체 애니메이션은 이 선택자에
   걸리지 않으니 그대로 유지된다.) */
[data-testid="stElementContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stHorizontalBlock"],
[data-testid="stMarkdownContainer"] {
  animation: none !important;
  transition: none !important;
}

.stButton > button {
  background: var(--accent); color: #062421; border: none; border-radius: 8px;
  font-weight: 600; padding: 10px 0;
}
.stButton > button:hover { background: #45d6c8; color: #062421; }

[data-testid="stFileUploaderDropzone"] {
  background: var(--surface); border: 1px dashed var(--border); border-radius: 10px;
}
[data-testid="stFileUploaderDropzone"] button {
  background: transparent; color: var(--accent); border: 1px solid var(--accent);
  border-radius: 8px; font-weight: 600; transition: background .15s ease, color .15s ease;
}
[data-testid="stFileUploaderDropzone"] button:hover {
  background: var(--accent); color: #062421; border-color: var(--accent);
}

[data-testid="stExpander"], div[data-testid="stStatusWidget"] {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
}

hr { border-color: var(--grid); }

.eyebrow {
  font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
  color: var(--accent); font-weight: 600; margin: 0 0 4px;
}
.fd-caption { color: var(--ink-2); font-size: 13px; }

.fd-slot { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.fd-circle {
  width: 112px; height: 112px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: 3px solid var(--border); background: var(--surface);
}
.fd-circle.ready { border-color: var(--good); background: var(--good-soft); color: var(--good); }
.fd-circle svg { width: 46px; height: 46px; }
.fd-slot-label { font-size: 13px; color: var(--ink-2); }

.fd-spinner-wrap { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 56px 0; }
/* 링과 숫자를 부모-자식이 아니라 형제로 겹쳐 쌓는다 — 링에 준 회전
   애니메이션이 transform을 통해 자식한테까지 그대로 적용되는 걸 막기
   위해서다. 이렇게 해야 링은 빙글빙글 돌면서 안쪽 숫자는 가만히 있는다. */
.fd-spinner-stack { position: relative; width: 200px; height: 200px; margin-bottom: 12px; }
.fd-spinner-ring {
  position: absolute; inset: 0; border-radius: 50%;
  border: 6px solid var(--surface-2); border-top-color: var(--accent);
  animation: fd-spin 1s linear infinite;
}
@keyframes fd-spin { to { transform: rotate(360deg); } }
.fd-spinner-donut {
  position: absolute; inset: 15px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.2s ease;
}
.fd-spinner-core {
  width: 134px; height: 134px; border-radius: 50%; background: var(--bg);
  display: flex; align-items: center; justify-content: center;
  font-family: "IBM Plex Mono", monospace; font-size: 30px; font-weight: 600; color: var(--ink);
}
.fd-spinner-label { font-size: 16px; font-weight: 600; color: var(--ink); }
.fd-spinner-step { font-size: 14px; color: var(--ink-2); min-height: 18px; }

.fd-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.fd-card-title { font-size: 12px; color: var(--ink-muted); font-weight: 600; margin: 0 0 12px; }

.fd-meter-value { font-family: "IBM Plex Mono", monospace; font-size: 30px; font-weight: 600; line-height: 1; }
.fd-meter-value.tone-good { color: var(--good); }
.fd-meter-value.tone-warning { color: var(--warning); }
.fd-meter-value.tone-critical { color: var(--critical); }
.fd-meter-caption { font-size: 12px; color: var(--ink-2); margin-top: 4px; }
.fd-meter-track { margin-top: 12px; height: 8px; border-radius: 999px; overflow: hidden; }
.fd-meter-fill { height: 100%; border-radius: 999px; }

.fd-stat-value { font-family: "IBM Plex Mono", monospace; font-size: 30px; font-weight: 600; line-height: 1; }
.fd-stat-caption { font-size: 12px; color: var(--ink-2); margin-top: 6px; }

.fd-bar-row { display: grid; grid-template-columns: 52px 1fr 20px; align-items: center; gap: 8px; margin-bottom: 9px; }
.fd-bar-row:last-child { margin-bottom: 0; }
.fd-bar-row .label { font-size: 12px; color: var(--ink-2); }
.fd-bar-row .track { height: 7px; border-radius: 999px; background: var(--surface-2); overflow: hidden; display: block; }
.fd-bar-row .fill { height: 100%; border-radius: 999px; display: block; }
.fd-bar-row .count { font-family: "IBM Plex Mono", monospace; font-size: 12px; font-weight: 600; text-align: right; }

.fd-ledger { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
.fd-ledger-scroll { overflow-x: auto; }
table.fd-table { width: 100%; border-collapse: collapse; min-width: 480px; }
.fd-table thead th {
  text-align: left; font-size: 11px; font-weight: 600; color: var(--ink-muted);
  letter-spacing: .03em; text-transform: uppercase; padding: 11px 16px;
  background: var(--surface-2); border-bottom: 1px solid var(--grid);
}
.fd-table thead th.num, .fd-table td.num { text-align: right; }
.fd-table tbody td {
  padding: 13px 16px; font-size: 14px; border-bottom: 1px solid var(--grid);
}
.fd-table tbody tr:last-child td { border-bottom: none; }
.fd-table td.num { font-family: "IBM Plex Mono", monospace; font-variant-numeric: tabular-nums; }

.fd-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px 4px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; }
.fd-pill svg { width: 13px; height: 13px; flex: none; }
.fd-pill.good { color: var(--good); background: var(--good-soft); }
.fd-pill.critical { color: var(--critical); background: var(--critical-soft); }
.fd-pill.warning { color: var(--warning); background: var(--warning-soft); }

.fd-verdict {
  background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
  padding: 36px 28px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 4px;
}
.fd-verdict-badge {
  width: 64px; height: 64px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; margin-bottom: 10px;
}
.fd-verdict-badge svg { width: 30px; height: 30px; }
.fd-verdict h3 { margin: 0; font-size: 20px; font-weight: 700; }
.fd-verdict .sub { color: var(--ink-2); font-size: 14px; margin: 2px 0 0; }

/* 배지·제목·부제는 처음엔 안 보이다가, 일치 항목이 다 빠져나간 뒤에
   페이드인된다 (animation-delay는 Python에서 계산해 인라인으로 넣는다). */
.fd-verdict-reveal {
  display: flex; flex-direction: column; align-items: center; overflow: hidden;
  max-height: 0; opacity: 0; animation: fd-reveal 0.5s ease forwards;
}
@keyframes fd-reveal {
  0%   { max-height: 0; opacity: 0; }
  100% { max-height: 160px; opacity: 1; }
}

.fd-review-list { display: flex; flex-direction: column; margin-top: 22px; text-align: left; width: 100%; }
.fd-review-item {
  border: 1px solid var(--border); border-radius: 10px; padding: 8px 14px; background: var(--surface-2);
  overflow: hidden; margin-bottom: 6px;
}

/* 일치(초록) 항목은 화면에 뜨자마자 오른쪽으로 밀려나며 빠지고, 그 자리를
   접어서 검토가 필요한 항목만 남긴다. 간격을 부모의 gap이 아니라 각
   항목의 margin-bottom으로 주는 이유는, gap은 애니메이션으로 줄일 수
   없어서 항목이 빠져도 빈 틈이 그대로 남기 때문이다. 박스 자체를 얇게
   줄인 건 빠지는 효과가 더 잘 체감되도록 하기 위해서다. */
.fd-clear-out { animation: fd-clear-out 1.1s ease forwards; }
@keyframes fd-clear-out {
  0%   { opacity: 1; transform: translateX(0);
         max-height: 100px; margin-bottom: 6px; padding-top: 8px; padding-bottom: 8px; border-width: 1px; }
  45%  { opacity: 0; transform: translateX(140%);
         max-height: 100px; margin-bottom: 6px; padding-top: 8px; padding-bottom: 8px; border-width: 1px; }
  100% { opacity: 0; transform: translateX(140%);
         max-height: 0; margin-bottom: 0; padding-top: 0; padding-bottom: 0; border-width: 0; }
}
.fd-review-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 4px; }
.fd-review-head .metric { font-size: 14px; font-weight: 600; }
.fd-review-values { display: flex; gap: 20px; font-family: "IBM Plex Mono", monospace; font-size: 13px; color: var(--ink-2); margin-bottom: 3px; }
.fd-review-values b { color: var(--ink); font-weight: 600; }
.fd-review-reason { font-size: 13px; color: var(--ink-2); margin: 0; }
</style>
"""

if "stage" not in st.session_state:
    st.session_state.stage = "upload"

st.markdown(DARK_CSS, unsafe_allow_html=True)


def go(stage: str) -> None:
    st.session_state.stage = stage


def reset() -> None:
    st.session_state.stage = "upload"
    st.session_state.processing_done = False
    st.session_state.pop("processing_tick", None)
    for key in ("report", "data", "code"):
        st.session_state.pop(f"{key}_uploader", None)


def match_tier(rate: float) -> str:
    if rate >= 90:
        return "good"
    if rate >= 50:
        return "warning"
    return "critical"


def render_upload() -> None:
    st.markdown("<p class='eyebrow'>숫자내력</p>", unsafe_allow_html=True)
    st.markdown("<h1 style='margin:0 0 6px;font-size:26px'>보고서 수치를 재실행 결과와 대조합니다</h1>", unsafe_allow_html=True)
    st.markdown("<p class='fd-caption'>연구보고서 · 데이터 · 코드를 올리고 검사를 시작하세요.</p>", unsafe_allow_html=True)
    st.write("")

    cols = st.columns(3)
    slots = [("report", "연구보고서"), ("data", "데이터"), ("code", "코드")]
    for col, (key, label) in zip(cols, slots):
        with col:
            # 동그라미를 먼저 그리고 나중에 session_state를 읽으면, 방금 이
            # 실행에서 올라온 파일이 "다음 rerun"에야 반영돼 체크 표시가
            # 한 박자 늦게 뜬다. st.empty()로 자리만 먼저 잡아두고,
            # file_uploader의 반환값을 확인한 뒤에 그 자리를 채운다.
            circle_slot = st.empty()
            uploaded = st.file_uploader(
                label,
                key=f"{key}_uploader",
                label_visibility="collapsed",
                accept_multiple_files=(key != "report"),
            )
            ready = bool(uploaded)
            circle_class = "fd-circle ready" if ready else "fd-circle"
            icon = ICON["good"] if ready else ""
            circle_slot.markdown(
                f"<div class='fd-slot'><div class='{circle_class}'>{icon}</div>"
                f"<span class='fd-slot-label'>{label}</span></div>",
                unsafe_allow_html=True,
            )
            if ready:
                count = len(uploaded) if isinstance(uploaded, list) else 1
                if count > 1:
                    st.markdown(
                        f"<p class='fd-caption' style='text-align:center;margin-top:4px'>{count}개 파일</p>",
                        unsafe_allow_html=True,
                    )

    st.write("")
    if st.button("검사 시작", type="primary", use_container_width=True):
        st.session_state.processing_done = False
        st.session_state.pop("processing_tick", None)
        go("processing")
        st.rerun()


def render_spinner(slot, label: str, step_text: str, quarter: int, dots: int = 1) -> None:
    deg = quarter * 90
    slot.markdown(
        f"""<div class="fd-spinner-wrap">
            <div class="fd-spinner-stack">
                <div class="fd-spinner-ring"></div>
                <div class="fd-spinner-donut" style="background: conic-gradient(var(--accent) {deg}deg, var(--surface-2) 0deg)">
                    <div class="fd-spinner-core">{quarter}/4</div>
                </div>
            </div>
            <div class="fd-spinner-label">{label}</div>
            <div class="fd-spinner-step">{step_text}{"." * dots}</div>
        </div>""",
        unsafe_allow_html=True,
    )


REPORT_STEPS = ["문서 로드", "수치 후보 추출", "검증 대상 판별", "완료"]
CODE_STEPS = ["Docker 격리 확인", "승인된 스크립트 실행", "출력값 수집", "완료"]
SUB_TICK_SECONDS = 0.5
SUB_TICKS_PER_STEP = 5  # 4단계 × 5 = 총 20틱 × 0.5초 = 10초
TOTAL_TICKS = len(REPORT_STEPS) * SUB_TICKS_PER_STEP


def render_processing() -> None:
    st.markdown("<p class='eyebrow' style='text-align:center'>숫자내력 · 검사 진행 중</p>", unsafe_allow_html=True)

    # time.sleep()을 넣은 for 루프 하나로 10초를 계속 돌리면, 그 스크립트
    # 실행 "한 번"이 10초짜리로 길어진다. Streamlit은 실행이 오래 걸리는
    # 스크립트 도중엔 이전 화면 정리를 미루는 경향이 있어서, 그 10초 동안
    # 업로드 화면이 아래에 남아 보이는 현상이 있었다(실제로 겪은 버그).
    # 그래서 "한 틱만 그리고 sleep 한 번 하고 rerun"으로 쪼갰다 — 매 0.5초마다
    # 스크립트가 처음부터 짧게 다시 실행되고, 그때마다 page.empty()가 다시
    # 확실하게 정리를 하기 때문에 남는 화면이 없다.
    if not st.session_state.get("processing_done", False):
        tick = st.session_state.get("processing_tick", 0)
        step_index = min(tick // SUB_TICKS_PER_STEP, len(REPORT_STEPS) - 1)
        dots = (tick % SUB_TICKS_PER_STEP % 3) + 1

        spinner_area = st.empty()
        with spinner_area.container():
            left, right = st.columns(2)
            with left:
                report_slot = st.empty()
            with right:
                code_slot = st.empty()
            render_spinner(report_slot, "보고서 분석", REPORT_STEPS[step_index], step_index + 1, dots)
            render_spinner(code_slot, "코드 실행", CODE_STEPS[step_index], step_index + 1, dots)

        time.sleep(SUB_TICK_SECONDS)

        next_tick = tick + 1
        if next_tick >= TOTAL_TICKS:
            st.session_state.processing_done = True
            st.session_state.pop("processing_tick", None)
            spinner_area.empty()
        else:
            st.session_state.processing_tick = next_tick
            st.rerun()

    st.markdown(
        f"<h2 style='font-size:18px;margin:0 0 12px'>대조 결과 — {len(MOCK_CLAIMS)}건 join 완료</h2>",
        unsafe_allow_html=True,
    )
    render_kpi_row(MOCK_CLAIMS)
    st.write("")
    render_ledger_table(MOCK_CLAIMS)

    st.write("")
    if st.button("최종 결과 보기 →", type="primary", use_container_width=True):
        go("result")
        st.rerun()


def render_kpi_row(claims: list[dict]) -> None:
    total = len(claims)
    match_count = sum(1 for c in claims if c["status"] == "match")
    critical_count = sum(1 for c in claims if STATUS_STYLE[c["status"]]["tone"] == "critical")
    warning_count = total - match_count - critical_count
    rate = round(match_count / total * 100)
    tone = match_tier(rate)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""<div class="fd-card">
                <p class="fd-card-title">전체 일치율</p>
                <div class="fd-meter-value tone-{tone}">{rate}%</div>
                <div class="fd-meter-track" style="background:var(--{tone}-soft)">
                    <div class="fd-meter-fill" style="width:{rate}%;background:var(--{tone})"></div>
                </div>
                <p class="fd-meter-caption">{match_count} / {total}건 일치</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class="fd-card">
                <p class="fd-card-title">검증 대상</p>
                <div class="fd-stat-value">{total}건</div>
                <p class="fd-stat-caption">연구보고서 claim {total}개 확인</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        max_count = max(match_count, critical_count, warning_count, 1)
        rows = [("일치", match_count, "good"), ("불일치", critical_count, "critical"), ("판단보류", warning_count, "warning")]
        bars = "".join(
            f"""<div class="fd-bar-row">
                <span class="label">{name}</span>
                <span class="track"><span class="fill" style="width:{int(n / max_count * 100)}%;background:var(--{tone})"></span></span>
                <span class="count">{n}</span>
            </div>"""
            for name, n, tone in rows
        )
        st.markdown(f"""<div class="fd-card"><p class="fd-card-title">상태 분포</p>{bars}</div>""", unsafe_allow_html=True)


def render_ledger_table(claims: list[dict]) -> None:
    rows = []
    for c in claims:
        style = STATUS_STYLE[c["status"]]
        pill = (
            f'<span class="fd-pill {style["tone"]}">{ICON[style["tone"]]}{style["label"]}</span>'
        )
        rows.append(
            f"<tr><td>{c['metric']}</td><td class='num'>{c['report_value']}</td>"
            f"<td class='num'>{c['evidence_value']}</td><td>{pill}</td></tr>"
        )
    table_html = (
        "<div class='fd-ledger'><div class='fd-ledger-scroll'><table class='fd-table'>"
        "<thead><tr><th>지표</th><th class='num'>보고서 값</th><th class='num'>재실행 값</th><th>상태</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)


def render_result() -> None:
    # 대조 결과 화면에서 이미 match/mismatch 판정까지 끝난 데이터를 다른
    # 형태(문제 항목만 추린 결론)로 보여주는 것뿐이라, 여기서는 새로
    # 계산하는 게 없다. 그래서 로딩 스피너 없이 바로 보여준다.
    #
    # "최종 결과 보기" 버튼은 대조 결과 화면 맨 아래에 있어서, 누른 자리
    # 그대로 있으면 화면 위쪽(판정 배지)이 안 보인 채로 일치 항목이 빠지는
    # 효과만 화면 하단에서 보인다. st.markdown은 <script>를 실행하지 않아서
    # components.html로 최상단 스크롤을 강제한다.
    # Streamlit 버전에 따라 실제로 스크롤되는 요소가 window 자체가 아니라
    # 안쪽 컨테이너(section.main 등)일 수 있어서, 후보를 모두 0으로
    # 맞춘다. 아래쪽 내용이 아직 스트리밍되는 중일 수 있어 살짝 지연을
    # 주고 한 번 더 실행한다.
    components.html(
        """<script>
        function scrollTopNow() {
          try {
            var doc = window.parent.document;
            window.parent.scrollTo(0, 0);
            doc.documentElement.scrollTop = 0;
            doc.body.scrollTop = 0;
            doc.querySelectorAll('section.main, [data-testid="stMain"], [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"]')
              .forEach(function (el) { el.scrollTop = 0; });
          } catch (e) {}
        }
        scrollTopNow();
        setTimeout(scrollTopNow, 80);
        setTimeout(scrollTopNow, 250);
        </script>""",
        height=0,
    )

    st.markdown("<p class='eyebrow' style='text-align:center'>숫자내력 · 최종 판정</p>", unsafe_allow_html=True)
    st.write("")

    problems = [c for c in MOCK_CLAIMS if c["status"] != "match"]
    all_match = not problems
    total = len(MOCK_CLAIMS)
    match_count = total - len(problems)

    if all_match:
        st.markdown(
            f"""<div class="fd-verdict">
                <div class="fd-verdict-badge" style="background:var(--good-soft)">
                    <div style="color:var(--good)">{ICON["good"]}</div>
                </div>
                <h3 style="color:var(--good)">100% 일치</h3>
                <p class="sub">검증한 모든 수치가 재실행 결과와 일치합니다.</p>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        # 원인을 하나로 뭉치지 않는다: 항목마다 상태 라벨과 개별 reason을
        # 그대로 보여준다 (mismatch와 needs_human_review는 완전히 다른
        # 문제라 같은 문구로 덮으면 안 된다).
        #
        # 대조 결과 화면에 있던 항목을 전부 그대로 띄운 뒤, 일치(초록) 항목만
        # 화면에 나타나자마자 오른쪽으로 슬라이드되며 빠지게 한다 — 남는
        # 자리는 접혀서(max-height 축소) 검토가 필요한 항목들이 자연스럽게
        # 위로 붙는다. 대조 결과에서 이미 본 것과 같은 데이터이므로 이
        # 화면에서 다시 계산하지는 않는다.
        rows = []
        for i, c in enumerate(MOCK_CLAIMS):
            style = STATUS_STYLE[c["status"]]
            is_match = c["status"] == "match"
            extra_class = " fd-clear-out" if is_match else ""
            delay = f' style="animation-delay:{i * 0.15:.2f}s"' if is_match else ""
            rows.append(
                f"""<div class="fd-review-item{extra_class}"{delay}>
                    <div class="fd-review-head">
                        <span class="metric">{c['metric']}</span>
                        <span class="fd-pill {style['tone']}">{ICON[style['tone']]}{style['label']}</span>
                    </div>
                    <div class="fd-review-values">
                        <span>보고서 <b>{c['report_value']}</b></span>
                        <span>재실행 <b>{c['evidence_value']}</b></span>
                    </div>
                    <p class="fd-review-reason">{c['reason']}</p>
                </div>"""
            )
        items_html = "".join(rows)

        # "검토가 필요합니다" 배지는 날아가는 효과가 다 끝난 뒤에 나타나야
        # 하므로, 마지막으로 빠지는 일치 항목의 시차(delay) + 애니메이션
        # 길이(1.1s)만큼 지연시켜서 그 다음에 페이드인되게 한다.
        match_indices = [i for i, c in enumerate(MOCK_CLAIMS) if c["status"] == "match"]
        reveal_delay = (max(match_indices) * 0.15 + 1.1 + 0.15) if match_indices else 0.0

        st.markdown(
            f"""<div class="fd-verdict">
                <div class="fd-verdict-reveal" style="animation-delay:{reveal_delay:.2f}s">
                    <div class="fd-verdict-badge" style="background:var(--warning-soft)">
                        <div style="color:var(--warning)">{ICON["warning"]}</div>
                    </div>
                    <h3>검토가 필요합니다</h3>
                    <p class="sub">{match_count} / {total}건 일치 · {len(problems)}건 확인 필요</p>
                </div>
                <div class="fd-review-list">{items_html}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.write("")
    if st.button("처음부터 다시", use_container_width=True):
        reset()
        st.rerun()


STAGES = {
    "upload": render_upload,
    "processing": render_processing,
    "result": render_result,
}

# 화면 전체를 하나의 placeholder 안에 그린다. Streamlit은 기존 엘리먼트를
# 스크립트 실행이 "끝난 뒤"에야 정리하는 경향이 있어서, 처리 화면처럼
# 오래 걸리는(sleep이 섞인) 렌더 도중에는 이전 화면이 화면 아래에 옅게
# 남아 있는 것처럼 보일 수 있다. 그래서 새 내용을 쓰기 전에 먼저
# page.empty()를 명시적으로 호출해 "지우라"는 신호부터 즉시 보낸다.
page = st.empty()
page.empty()
with page.container():
    STAGES[st.session_state.stage]()
