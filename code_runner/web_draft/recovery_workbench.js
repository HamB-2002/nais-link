const recoveryScenario = document.querySelector("#recovery-scenario");

const recovery = {
  status: document.querySelector("#recovery-status"),
  initial: stepElements("initial"),
  search: stepElements("search"),
  final: stepElements("final"),
  summary: document.querySelector("#recovery-summary"),
  initialValue: document.querySelector("#recovery-initial-value"),
  evidence: document.querySelector("#recovery-evidence"),
  finalValue: document.querySelector("#recovery-final-value"),
  outcome: document.querySelector("#recovery-outcome"),
};

const recoveryScenarios = {
  direct: {
    status: ["ready", "자동 재판정"],
    initial: ["attention", "비교 불가", "합계 15점은 평균 Claim과 비교 불가", "집계 방식·분모·산식이 달라 최초 후보를 보류하고 이력을 남깁니다."],
    search: ["ready", "후보 발견", "직접 평균 출력 후보를 발견했습니다", "`analysis/report.py:81–87`과 `/metrics/seoul_mean`에서 동일 조건의 평균 15.02점을 찾았습니다."],
    final: ["ready", "일치", "대체 후보로 재대조를 완료했습니다", "기간·대상·분모·결측 처리까지 일치해 반올림 후 15점으로 판정했습니다."],
    summary: "최초 합계 후보의 비교 불가 이력은 보존하고, 직접 평균 출력 후보를 찾아 자동 재판정했습니다.",
    values: ["sum(score) = 15", "report.py:81–87", "mean(score) = 15.02", "직접 후보로 재판정"],
  },
  none: {
    status: ["attention", "재탐색 종료"],
    initial: ["attention", "비교 불가", "합계 15점은 평균 Claim과 비교 불가", "집계 방식·분모·산식이 달라 최초 후보를 보류하고 이력을 남깁니다."],
    search: ["attention", "후보 없음", "직접 평균 출력 후보를 찾지 못했습니다", "승인 실행의 출력 locator와 집계식을 탐색했지만 같은 의미의 평균 후보가 없습니다."],
    final: ["attention", "비교 불가", "최초 후보 상태를 유지합니다", "수치 차이를 계산하지 않고, 미연결 실행값으로 검토 큐에 남깁니다."],
    summary: "대체 후보를 자동 탐색했지만 같은 의미의 직접 출력이 없어 비교 불가 상태를 유지했습니다.",
    values: ["sum(score) = 15", "출력 locator 4개 탐색", "—", "대체 후보 없음"],
  },
  derived: {
    status: ["attention", "검토 필요"],
    initial: ["attention", "비교 불가", "합계 15점은 평균 Claim과 비교 불가", "최초 후보의 집계 방식과 분모가 평균 Claim과 다릅니다."],
    search: ["ready", "재구성 가능", "합계와 유효 건수를 안전하게 확인했습니다", "동일 실행에서 `sum(score)`와 `valid_count`가 확인되어 평균 후보를 산술 재구성할 수 있습니다."],
    final: ["attention", "검토 필요", "재구성값은 직접 출력이 아닙니다", "원본 코드가 평균을 직접 출력하지 않았으므로 재구성 근거를 검토 큐로 보냅니다."],
    summary: "안전한 산술 재구성은 가능하지만 원본 직접 출력이 아니므로 자동 일치로 승격하지 않았습니다.",
    values: ["sum(score) = 15", "sum / valid_count", "derived mean = 15.00", "derived_provenance"],
  },
  blocked: {
    status: ["attention", "복구 차단"],
    initial: ["attention", "비교 불가", "합계 15점은 평균 Claim과 비교 불가", "집계 방식·분모·산식이 달라 최초 후보를 보류하고 이력을 남깁니다."],
    search: ["attention", "조건 불일치", "평균 후보는 찾았지만 필터가 다릅니다", "대체 후보는 `region=Busan` 조건이라 보고서의 `region=Seoul` Claim과 연결할 수 없습니다."],
    final: ["attention", "비교 불가", "대체 후보로 자동 복구하지 않았습니다", "필터·대상·기간·가중치 중 하나라도 다르면 최초 불일치 이력을 유지합니다."],
    summary: "비슷한 평균 후보가 있어도 필터가 달라 자동 복구를 차단했습니다. 우연한 수치 일치를 만들지 않습니다.",
    values: ["sum(score) = 15", "region=Busan 발견", "mean(score) = 15.02", "필터 불일치"],
  },
};

recoveryScenario.addEventListener("change", renderRecovery);
renderRecovery();

function stepElements(name) {
  return {
    root: document.querySelector(`#recovery-${name}-step`),
    state: document.querySelector(`#recovery-${name}-state`),
    title: document.querySelector(`#recovery-${name}-title`),
    detail: document.querySelector(`#recovery-${name}-detail`),
  };
}

function renderRecovery() {
  const scenario = recoveryScenarios[recoveryScenario.value];
  setBadge(recovery.status, scenario.status);
  setStep(recovery.initial, scenario.initial);
  setStep(recovery.search, scenario.search);
  setStep(recovery.final, scenario.final);
  recovery.summary.textContent = scenario.summary;
  [recovery.initialValue.textContent, recovery.evidence.textContent, recovery.finalValue.textContent, recovery.outcome.textContent] = scenario.values;
}

function setStep(step, values) {
  const [stateName, stateLabel, title, detail] = values;
  step.root.className = `recovery-step ${stateName}`;
  step.state.className = `stage-state ${stateName}`;
  step.state.textContent = stateLabel;
  step.title.textContent = title;
  step.detail.textContent = detail;
}

function setBadge(element, values) {
  const [stateName, label] = values;
  element.className = `status-badge ${stateName}`;
  element.textContent = label;
}
