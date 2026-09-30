const fields = {
  report: document.querySelector("#report-value"),
  evidence: document.querySelector("#evidence-value"),
  unit: document.querySelector("#unit"),
  digits: document.querySelector("#rounding-digits"),
  tolerance: document.querySelector("#tolerance"),
  toleranceLabel: document.querySelector("#tolerance-label"),
  conditions: [
    document.querySelector("#period-match"),
    document.querySelector("#population-match"),
    document.querySelector("#denominator-match"),
    document.querySelector("#formula-match"),
  ],
};

const decision = {
  status: document.querySelector("#decision-status"),
  summary: document.querySelector("#decision-summary"),
  normalized: document.querySelector("#normalized-value"),
  display: document.querySelector("#display-value"),
  rounded: document.querySelector("#rounded-value"),
  difference: document.querySelector("#difference-value"),
};

for (const input of [fields.report, fields.evidence, fields.unit, fields.digits, fields.tolerance, ...fields.conditions]) {
  input.addEventListener("input", evaluateDecision);
  input.addEventListener("change", evaluateDecision);
}

evaluateDecision();

function evaluateDecision() {
  fields.toleranceLabel.textContent = fields.unit.value === "percent"
    ? "표시값 허용오차 (%p)"
    : "표시값 허용오차 (원값)";
  const report = fields.report.valueAsNumber;
  const evidence = fields.evidence.valueAsNumber;
  const digits = fields.digits.valueAsNumber;
  const tolerance = fields.tolerance.valueAsNumber;
  if (![report, evidence, digits, tolerance].every(Number.isFinite) || !Number.isInteger(digits) || digits < 0 || digits > 8 || tolerance < 0) {
    renderDecision("pending", "입력 대기", "수치와 자릿수·허용오차를 올바르게 입력하세요.", null);
    return;
  }
  const factor = fields.unit.value === "percent" ? 100 : 1;
  const displayedEvidence = evidence * factor;
  const roundedEvidence = Number(displayedEvidence.toFixed(digits));
  const difference = Math.abs(report - roundedEvidence);
  if (!fields.conditions.every((condition) => condition.checked)) {
    renderDecision("attention", "비교 불가", "기간·대상·분모·산식 중 하나 이상이 달라 수치 비교를 보류합니다.", {
      evidence,
      displayedEvidence,
      roundedEvidence,
      difference,
    });
    return;
  }
  if (isWithinTolerance(difference, tolerance)) {
    renderDecision("ready", "일치", "의미 조건이 같고, 보고서 표기 단위·반올림·허용오차 적용 후 일치합니다.", {
      evidence,
      displayedEvidence,
      roundedEvidence,
      difference,
    });
    return;
  }
  renderDecision("attention", "불일치", "의미 조건은 같지만 반올림 후 표시값 차이가 허용오차를 넘습니다.", {
    evidence,
    displayedEvidence,
    roundedEvidence,
    difference,
  });
}

function isWithinTolerance(difference, tolerance) {
  const scale = Math.max(1, Math.abs(difference), Math.abs(tolerance));
  return difference <= tolerance + Number.EPSILON * scale * 16;
}

function renderDecision(stateName, label, summary, values) {
  decision.status.className = `status-badge ${stateName}`;
  decision.status.textContent = label;
  decision.summary.textContent = summary;
  if (!values) {
    decision.normalized.textContent = "—";
    decision.display.textContent = "—";
    decision.rounded.textContent = "—";
    decision.difference.textContent = "—";
    return;
  }
  const suffix = fields.unit.value === "percent" ? "%" : "";
  const differenceSuffix = fields.unit.value === "percent" ? "%p" : "";
  decision.normalized.textContent = formatNumber(values.evidence);
  decision.display.textContent = `${formatNumber(values.displayedEvidence)}${suffix}`;
  decision.rounded.textContent = `${formatNumber(values.roundedEvidence)}${suffix}`;
  decision.difference.textContent = `${formatNumber(values.difference)}${differenceSuffix}`;
}

function formatNumber(value) {
  return Number(value.toFixed(12)).toString();
}
