const journeySteps = [
  {
    id: "files",
    title: "파일 확인",
    completedLabel: "준비 완료",
    detail: "보고서 1개 · 데이터 파일 · 코드 파일 구성을 확인했습니다.",
    partial: ["3 / 3", "—", "—", "—"],
  },
  {
    id: "extract",
    title: "보고서 표 추출",
    completedLabel: "추출 완료",
    detail: "표·수치 후보와 원문 위치를 추출하는 단계입니다.",
    partial: ["3 / 3", "7개", "—", "—"],
  },
  {
    id: "prepare",
    title: "코드 실행 준비",
    completedLabel: "계약 확인",
    detail: "입력 데이터와 승인 코드 계약을 연결하는 단계입니다.",
    partial: ["3 / 3", "7개", "1개", "—"],
  },
  {
    id: "run",
    title: "코드 재실행",
    completedLabel: "실행 완료",
    detail: "격리 환경에서 출력 표를 수집하는 단계입니다.",
    partial: ["3 / 3", "7개", "1개", "—"],
  },
  {
    id: "link",
    title: "표 자동 연결",
    completedLabel: "5 / 7 연결",
    detail: "보고서 표와 실행 결과 표의 대응 후보를 정리했습니다.",
    partial: ["3 / 3", "7개", "1개", "84개"],
  },
  {
    id: "compare",
    title: "수치 대조",
    completedLabel: "84개 대조",
    detail: "의미 10기준과 허용오차를 셀 단위로 적용했습니다.",
    partial: ["3 / 3", "7개", "1개", "84개"],
  },
  {
    id: "result",
    title: "결과 정리",
    completedLabel: "결과 준비",
    detail: "5단계 판정과 확인이 필요한 항목을 준비했습니다.",
    partial: ["3 / 3", "7개", "1개", "84개"],
  },
];

const initialDetails = new Map(
  journeySteps.map((step) => [
    step.id,
    document.querySelector(`[data-progress-stage="${step.id}"] p`).textContent,
  ]),
);

const progressElements = {
  status: document.querySelector("#progress-status"),
  kicker: document.querySelector("#progress-kicker"),
  copy: document.querySelector("#progress-copy"),
  count: document.querySelector("#progress-count"),
  bar: document.querySelector("#progress-bar"),
  partial: [
    document.querySelector("#partial-files"),
    document.querySelector("#partial-tables"),
    document.querySelector("#partial-runs"),
    document.querySelector("#partial-cells"),
  ],
};

function setJourneyStage(step, stateName, label, detail) {
  const stage = document.querySelector(`[data-progress-stage="${step.id}"]`);
  const status = stage.querySelector(".stage-state");
  stage.className = `journey-stage ${stateName}`;
  stage.querySelector("p").textContent = detail;
  status.className = `stage-state ${stateName}`;
  status.textContent = label;
}

function setProgress(done, stateName, label, kicker, copy) {
  progressElements.status.className = `status-badge ${stateName}`;
  progressElements.status.textContent = label;
  progressElements.kicker.textContent = kicker;
  progressElements.copy.textContent = copy;
  progressElements.count.textContent = `${done} / ${journeySteps.length}`;
  progressElements.bar.style.width = `${(done / journeySteps.length) * 100}%`;
}

function setPartialResults(values) {
  for (const [index, element] of progressElements.partial.entries()) {
    element.textContent = values[index];
  }
}

function resetProgressJourney() {
  for (const step of journeySteps) {
    setJourneyStage(step, "pending", "대기", initialDetails.get(step.id));
  }
  setProgress(
    0,
    "pending",
    "시작 전",
    "세 파일을 선택하면 단계별 검증 현황을 보여줍니다.",
    "실제 파싱·재실행 전에도 무엇을 확인하는지와 다음 단계가 명확히 보입니다.",
  );
  setPartialResults(["—", "—", "—", "—"]);
}

function delay(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

async function runProgressDemo() {
  for (let index = 0; index < journeySteps.length; index += 1) {
    const step = journeySteps[index];
    setJourneyStage(step, "running", "진행 중", `${step.title} 단계가 진행 중입니다.`);
    setProgress(
      index,
      "attention",
      "데모 진행",
      `${step.title} 진행 중`,
      "실제 Streamlit에서는 이 단계가 백그라운드 작업 상태와 부분 결과를 갱신합니다.",
    );
    await delay(180);
    setJourneyStage(step, "ready", step.completedLabel, step.detail);
    setPartialResults(step.partial);
    setProgress(
      index + 1,
      "attention",
      "데모 진행",
      `${step.title} 완료`,
      "앞 단계 결과는 보존한 채 다음 검증 단계로 진행합니다.",
    );
  }
  setProgress(
    journeySteps.length,
    "ready",
    "결과 준비",
    "7단계 검증 흐름 데모 완료",
    "실제 파싱·재실행이 연결되면 이 값들은 서버 작업의 실시간 결과로 바뀝니다.",
  );
}

window.progressJourney = { resetProgressJourney, runProgressDemo };
