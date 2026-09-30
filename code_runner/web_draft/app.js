const state = {
  report: [],
  data: [],
  code: [],
};

const inputs = {
  report: document.querySelector("#report-input"),
  data: document.querySelector("#data-input"),
  code: document.querySelector("#code-input"),
};

const lists = {
  report: document.querySelector("#report-list"),
  data: document.querySelector("#data-list"),
  code: document.querySelector("#code-list"),
};

const reviewButton = document.querySelector("#review-button");
const bundleStatus = document.querySelector("#bundle-status");
const preflightNote = document.querySelector("#preflight-note");
const reviewStatus = document.querySelector("#review-status");
const resultSummary = document.querySelector("#result-summary p");

for (const [kind, input] of Object.entries(inputs)) {
  input.addEventListener("change", async () => {
    resetReviewState();
    reviewButton.disabled = true;
    const files = await prepareFiles([...input.files]);
    state[kind] = kind === "data" ? [...state.data, ...files] : files;
    if (kind === "data") input.value = "";
    renderFileList(kind);
    updateBundleState();
  });
}

reviewButton.addEventListener("click", () => {
  const dataCount = state.data.length;
  setStage("report-data", "attention", "대기", "보고서 의미 조건은 파서 연결 후 확인");
  setStage("code-data", "ready", "준비", `${dataCount}개 데이터 파일의 브라우저 해시 계산 완료`);
  setStage("report-code", "attention", "미연결", "승인 계약·Docker 실행 어댑터 연결 필요");
  reviewStatus.textContent = "실험 결과";
  reviewStatus.className = "status-badge attention";
  resultSummary.textContent = "파일 구성과 브라우저 해시는 준비됐습니다. 실제 보고서 Claim 추출, 승인 코드 확인, Docker 재실행은 아직 수행하지 않았습니다.";
});

async function prepareFiles(files) {
  return Promise.all(files.map(async (file) => ({
    file,
    digest: await sha256(file),
  })));
}

async function sha256(file) {
  const bytes = await file.arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function renderFileList(kind) {
  const list = lists[kind];
  list.replaceChildren();
  for (const entry of state[kind]) {
    const row = document.createElement("li");
    row.className = "file-row";
    const name = document.createElement("span");
    name.className = "file-name";
    name.textContent = entry.file.name;
    const meta = document.createElement("span");
    meta.className = "file-meta";
    meta.textContent = `${formatBytes(entry.file.size)} · ${entry.digest.slice(0, 12)}…`;
    row.append(name, meta);
    list.append(row);
  }
  document.querySelector(`[data-slot="${kind}"]`).classList.toggle("ready", state[kind].length > 0);
}

function updateBundleState() {
  const ready = state.report.length === 1 && state.data.length > 0 && state.code.length === 1;
  reviewButton.disabled = !ready;
  bundleStatus.textContent = ready ? "파일 준비 완료" : `${selectedGroupCount()}개 항목 준비`;
  bundleStatus.className = ready ? "status-badge ready" : "status-badge pending";
  preflightNote.textContent = ready
    ? `보고서 1개 · 데이터 ${state.data.length}개 · 코드 1개가 준비됐습니다. 브라우저 안에서만 해시를 계산했습니다.`
    : "세 자료를 선택하면 사전 점검을 시작합니다.";
}

function selectedGroupCount() {
  return [state.report.length > 0, state.data.length > 0, state.code.length > 0].filter(Boolean).length;
}

function setStage(stageName, stateName, label, detail) {
  const stage = document.querySelector(`[data-stage="${stageName}"]`);
  const status = stage.querySelector(".stage-state");
  stage.className = `stage-card ${stateName}`;
  stage.querySelector(".stage-body p").textContent = detail;
  status.textContent = label;
  status.className = `stage-state ${stateName}`;
}

function resetReviewState() {
  setStage("report-data", "pending", "대기", "기간·대상·분모·산식 조건 확인");
  setStage("code-data", "pending", "대기", "입력 해시·스키마·변환 조건 확인");
  setStage("report-code", "pending", "대기", "격리 실행 후 단위·반올림·허용오차 대조");
  reviewStatus.textContent = "점검 전";
  reviewStatus.className = "status-badge pending";
  resultSummary.textContent = "파일을 선택한 뒤 사전 점검을 시작하세요. 실제 코드 실행과 수치 판정은 수행하지 않습니다.";
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
