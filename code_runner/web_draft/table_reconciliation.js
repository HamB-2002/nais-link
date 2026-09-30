const reconciliationRoot = document.querySelector("#table-reconciliation");
const reconciliationStatus = document.querySelector("#table-reconciliation-status");
const reconciliationNote = document.querySelector("#table-reconciliation-note");
const reconciliationSummary = document.querySelector("#table-reconciliation-summary");
const tablePairList = document.querySelector("#table-pair-list");

window.loadTableReconciliation = async function loadTableReconciliation() {
  reconciliationRoot.hidden = false;
  reconciliationRoot.setAttribute("aria-busy", "true");
  reconciliationStatus.textContent = "불러오는 중";
  reconciliationStatus.className = "status-badge pending";
  reconciliationNote.textContent = "구조화된 보고서 표와 코드 실행 표의 자동 연결 결과를 확인하고 있습니다.";
  reconciliationSummary.replaceChildren();
  tablePairList.replaceChildren();

  try {
    const response = await fetch("/api/table-reconciliation-demo");
    if (!response.ok) throw new Error("TABLE_RECONCILIATION_UNAVAILABLE");
    const payload = await response.json();
    renderReconciliation(payload);
    return true;
  } catch {
    reconciliationRoot.removeAttribute("aria-busy");
    reconciliationStatus.textContent = "불러오기 실패";
    reconciliationStatus.className = "status-badge attention";
    reconciliationNote.textContent = "표 대조 결과를 불러오지 못했습니다. 성공 판정으로 대체하지 않았습니다.";
    return false;
  }
};

window.resetTableReconciliation = function resetTableReconciliation() {
  reconciliationRoot.hidden = true;
  reconciliationRoot.removeAttribute("aria-busy");
  reconciliationStatus.textContent = "대기";
  reconciliationStatus.className = "status-badge pending";
  reconciliationNote.textContent = "보고서 표와 코드 실행 표의 자동 연결 결과가 여기에 표시됩니다.";
  reconciliationSummary.replaceChildren();
  tablePairList.replaceChildren();
};

function renderReconciliation(payload) {
  reconciliationRoot.removeAttribute("aria-busy");
  reconciliationStatus.textContent = "자동 대조 완료";
  reconciliationStatus.className = "status-badge ready";
  reconciliationNote.textContent = payload.mode === "structured_fixture"
    ? "현재는 구조화된 표 artifact fixture를 실제 대조 엔진에 통과시킨 결과입니다. 업로드 파일의 파싱·Docker 실행 결과는 아직 연결되지 않았습니다."
    : "서버가 반환한 표 대조 결과입니다.";
  renderSummary(payload.summary);
  for (const comparison of payload.comparisons) tablePairList.append(renderTablePair(comparison));
}

function renderSummary(summary) {
  const items = [
    ["보고서 표", summary.report_tables],
    ["자동 연결", summary.matched_tables],
    ["대조 셀", summary.cells],
    ["일치", summary.match],
    ["불일치", summary.mismatch],
    ["검토 필요", summary.review],
  ];
  for (const [label, value] of items) {
    const item = document.createElement("div");
    const term = document.createElement("span");
    term.textContent = label;
    const definition = document.createElement("strong");
    definition.textContent = String(value);
    item.append(term, definition);
    reconciliationSummary.append(item);
  }
}

function renderTablePair(comparison) {
  const article = document.createElement("article");
  article.className = "table-pair";
  const header = document.createElement("div");
  header.className = "table-pair-header";
  const title = document.createElement("h4");
  title.textContent = `${comparison.report_table_id} ↔ ${comparison.execution_table_id}`;
  const status = document.createElement("span");
  status.className = `stage-state ${comparison.status === "matched" ? "ready" : "attention"}`;
  status.textContent = comparison.status === "matched" ? "자동 연결" : "검토 필요";
  header.append(title, status);
  article.append(header);
  article.append(detail("연결 근거", comparison.pairing_reasons.join(" · ")));

  const cells = document.createElement("div");
  cells.className = "table-cell-list";
  for (const cell of comparison.cells) cells.append(renderCell(cell));
  article.append(cells);

  if (comparison.unmatched_execution_cells.length > 0) {
    article.append(detail("코드 표 전용 셀", comparison.unmatched_execution_cells.map(formatCoordinate).join(" · ")));
  }
  return article;
}

function renderCell(cell) {
  const article = document.createElement("article");
  article.className = `table-cell-result ${cell.status}`;
  const header = document.createElement("div");
  header.className = "table-cell-header";
  const title = document.createElement("h5");
  title.textContent = formatCoordinate(cell.coordinate);
  const status = document.createElement("span");
  status.className = `stage-state ${statusClass(cell.status)}`;
  status.textContent = statusLabel(cell.status);
  header.append(title, status);
  article.append(header);
  article.append(detail("보고서", formatNumeric(cell.reported)));
  article.append(detail("코드 실행", cell.execution ? formatNumeric(cell.execution) : "출력 셀 없음"));
  article.append(detail("판정 근거", cell.reason_codes.join(" · ")));
  if (cell.output_locator) article.append(detail("출력 위치", cell.output_locator));
  return article;
}

function detail(label, value) {
  const item = document.createElement("p");
  const key = document.createElement("span");
  key.textContent = `${label}: `;
  const text = document.createElement("code");
  text.textContent = value;
  item.append(key, text);
  return item;
}

function formatCoordinate(coordinate) {
  const panel = coordinate.panel ? `${coordinate.panel} / ` : "";
  return `${panel}${coordinate.row} / ${coordinate.columns.join(" > ")}`;
}

function formatNumeric(value) {
  return `${value.value}${value.unit}`;
}

function statusClass(status) {
  return status === "match" ? "ready" : "attention";
}

function statusLabel(status) {
  const labels = {
    match: "일치",
    mismatch: "불일치",
    not_comparable: "비교 불가",
    needs_human_review: "검토 필요",
    evidence_incomplete: "근거 부족",
    execution_failed: "실행 실패",
  };
  return labels[status] || status;
}
