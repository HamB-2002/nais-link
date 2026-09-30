const state = {
  report: [],
  data: [],
  code: [],
  sourceMode: "manual",
  catalogDataFileCount: 0,
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
const sampleNote = document.querySelector("#sample-note");
const sampleButtons = document.querySelectorAll("[data-sample]");

for (const [kind, input] of Object.entries(inputs)) {
  input.addEventListener("change", async () => {
    resetReviewState();
    reviewButton.disabled = true;
    clearSampleSelection();
    state.sourceMode = "manual";
    state.catalogDataFileCount = 0;
    const files = await prepareFiles([...input.files]);
    state[kind] = kind === "data" ? [...state.data, ...files] : files;
    if (kind === "data") input.value = "";
    renderFileList(kind);
    updateBundleState();
  });
}

for (const button of sampleButtons) {
  button.addEventListener("click", () => loadSample(button.dataset.sample));
}

reviewButton.addEventListener("click", () => {
  const dataCount = state.sourceMode === "catalog" ? state.catalogDataFileCount : state.data.length;
  setStage("report-data", "attention", "대기", "보고서 의미 조건은 파서 연결 후 확인");
  setStage("code-data", "ready", "준비", codeDataDetail(dataCount));
  setStage("report-code", "attention", "미연결", "승인 계약·Docker 실행 어댑터 연결 필요");
  reviewStatus.textContent = "실험 결과";
  reviewStatus.className = "status-badge attention";
  resultSummary.textContent = reviewSummary();
});

async function prepareFiles(files) {
  return Promise.all(files.map(async (file) => ({
    name: file.name,
    size: file.size,
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
    name.textContent = entry.name;
    const meta = document.createElement("span");
    meta.className = "file-meta";
    meta.textContent = entry.size > 0 ? `${formatBytes(entry.size)} · ${entry.digest}` : entry.digest;
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
    ? bundleNote()
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

async function loadSample(identifier) {
  resetReviewState();
  reviewButton.disabled = true;
  sampleNote.textContent = "공개 패키지 구성을 확인하고 있습니다.";
  setSampleState(identifier, "loading");
  const response = await fetch("/api/samples");
  if (!response.ok) {
    sampleNote.textContent = "로컬 샘플 카탈로그를 불러오지 못했습니다. 수동 파일 선택을 사용하세요.";
    clearSampleSelection();
    updateBundleState();
    return;
  }
  const payload = await response.json();
  const sample = payload.samples.find((item) => item.identifier === identifier);
  if (!sample) {
    sampleNote.textContent = "요청한 공개 샘플을 찾지 못했습니다.";
    clearSampleSelection();
    updateBundleState();
    return;
  }
  state.report = [{ name: sample.report_path, size: sample.report_bytes, digest: "등록 보고서" }];
  state.data = [{ name: `${sample.data_root}/ · ${sample.data_file_count}개 파일`, size: 0, digest: "등록 데이터" }];
  state.code = [{ name: sample.code_entry, size: 0, digest: `${sample.code_file_count}개 코드 파일` }];
  state.sourceMode = "catalog";
  state.catalogDataFileCount = sample.data_file_count;
  renderFileList("report");
  renderFileList("data");
  renderFileList("code");
  setSampleState(identifier, "selected");
  sampleNote.textContent = `${sample.title} 패키지를 선택했습니다. 코드 실행 전 계약·의미 조건을 검토하세요.`;
  updateBundleState();
}

function setSampleState(identifier, stateName) {
  for (const button of sampleButtons) {
    const selected = button.dataset.sample === identifier;
    button.classList.toggle("selected", selected && stateName === "selected");
    button.classList.toggle("loading", selected && stateName === "loading");
    button.setAttribute("aria-pressed", String(selected && stateName === "selected"));
  }
}

function clearSampleSelection() {
  for (const button of sampleButtons) {
    button.classList.remove("selected", "loading");
    button.setAttribute("aria-pressed", "false");
  }
}

function codeDataDetail(dataCount) {
  if (state.sourceMode === "catalog") {
    return `${dataCount}개 데이터 파일의 등록 경로를 카탈로그에서 확인`;
  }
  return `${dataCount}개 데이터 파일의 브라우저 해시 계산 완료`;
}

function reviewSummary() {
  if (state.sourceMode === "catalog") {
    return "공개 샘플의 고정 파일 구조를 확인했습니다. 실제 보고서 Claim 추출, 승인 코드 확인, Docker 재실행은 아직 수행하지 않았습니다.";
  }
  return "파일 구성과 브라우저 해시는 준비됐습니다. 실제 보고서 Claim 추출, 승인 코드 확인, Docker 재실행은 아직 수행하지 않았습니다.";
}

function bundleNote() {
  if (state.sourceMode === "catalog") {
    return `공개 샘플: 보고서 1개 · 데이터 ${state.catalogDataFileCount}개 · 코드 경로 1개를 카탈로그에서 확인했습니다.`;
  }
  return `보고서 1개 · 데이터 ${state.data.length}개 · 코드 1개가 준비됐습니다. 브라우저 안에서만 해시를 계산했습니다.`;
}
