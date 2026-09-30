from decimal import Decimal
from typing import assert_never

from code_runner.models import (
    MetricFamily,
    NumericValue,
    Tolerance,
    TolerancePolicy,
    TolerancePolicySource,
    ToleranceUnit,
    Unit,
)
from code_runner.table_models import QuantitySemantics


def policy_for(
    semantics: QuantitySemantics,
    value: NumericValue,
    declared_policy: TolerancePolicy | None,
) -> TolerancePolicy | None:
    if declared_policy is not None:
        return declared_policy
    return catalog_policy(semantics.metric, value.unit)


def catalog_policy(metric: str | None, unit: Unit) -> TolerancePolicy | None:
    family = metric_family(metric, unit)
    if not supports_unit(family, unit):
        return None
    match family:
        case MetricFamily.BODY_HEIGHT:
            return _policy("catalog.body-height.v1", family, Decimal("0.5"), 1, "신장 측정값은 0.5cm 이내 차이를 허용합니다.")
        case MetricFamily.BODY_WEIGHT:
            return _policy("catalog.body-weight.v1", family, Decimal("0.2"), 1, "체중 측정값은 0.2kg 이내 차이를 허용합니다.")
        case MetricFamily.RATE:
            return _policy("catalog.rate.v1", family, Decimal("0.1"), 1, "비율은 0.1%p 이내 차이를 허용합니다.")
        case MetricFamily.COUNT:
            return _policy("catalog.count.v1", family, Decimal(0), 0, "정수 건수는 반올림 오차를 허용하지 않습니다.")
        case MetricFamily.MONEY:
            return None
        case MetricFamily.DURATION:
            return _policy("catalog.duration.v1", family, Decimal("0.01"), 2, "시간값은 0.01초 이내 차이를 허용합니다.")
        case MetricFamily.GENERIC:
            return None
        case unreachable:
            assert_never(unreachable)


def metric_family(metric: str | None, unit: Unit) -> MetricFamily:
    normalized = "" if metric is None else metric.casefold()
    if any(term in normalized for term in ("신장", "키", "height")):
        return MetricFamily.BODY_HEIGHT
    if any(term in normalized for term in ("체중", "몸무게", "weight")):
        return MetricFamily.BODY_WEIGHT
    if any(term in normalized for term in ("건수", "횟수", "count", "number of")):
        return MetricFamily.COUNT
    match unit:
        case Unit.PERCENT | Unit.RATIO | Unit.PERCENTAGE_POINT:
            return MetricFamily.RATE
        case Unit.WON | Unit.MILLION_WON | Unit.HUNDRED_MILLION_WON:
            return MetricFamily.MONEY
        case Unit.MILLISECOND | Unit.SECOND:
            return MetricFamily.DURATION
        case Unit.MULTIPLE | Unit.CENTIMETER | Unit.METER | Unit.KILOGRAM | Unit.GRAM:
            return MetricFamily.GENERIC
        case unreachable:
            assert_never(unreachable)


def supports_unit(family: MetricFamily, unit: Unit) -> bool:
    match family:
        case MetricFamily.BODY_HEIGHT:
            return unit in (Unit.CENTIMETER, Unit.METER)
        case MetricFamily.BODY_WEIGHT:
            return unit in (Unit.KILOGRAM, Unit.GRAM)
        case MetricFamily.RATE:
            return unit in (Unit.PERCENT, Unit.RATIO, Unit.PERCENTAGE_POINT)
        case MetricFamily.COUNT:
            return True
        case MetricFamily.MONEY:
            return False
        case MetricFamily.DURATION:
            return unit in (Unit.MILLISECOND, Unit.SECOND)
        case MetricFamily.GENERIC:
            return False
        case unreachable:
            assert_never(unreachable)


def _policy(
    policy_id: str,
    family: MetricFamily,
    absolute: Decimal,
    rounding_digits: int,
    rationale: str,
) -> TolerancePolicy:
    return TolerancePolicy(
        policy_id,
        family,
        Tolerance(absolute, None, rounding_digits, absolute_unit=ToleranceUnit.CANONICAL),
        TolerancePolicySource.APPROVED_METRIC_CATALOG,
        rationale,
        None,
    )
