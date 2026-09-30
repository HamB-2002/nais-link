from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import assert_never

from code_runner.models import NumericValue, Unit


class Dimension(str, Enum):
    PERCENT = "percent"
    MULTIPLE = "multiple"
    MONEY = "money"
    TIME = "time"
    PERCENTAGE_POINT = "percentage_point"
    LENGTH = "length"
    MASS = "mass"


@dataclass(frozen=True, slots=True)
class CanonicalValue:
    amount: Decimal
    unit: Unit
    dimension: Dimension


def normalize(value: NumericValue) -> CanonicalValue:
    match value.unit:
        case Unit.PERCENT:
            return CanonicalValue(value.amount, Unit.PERCENT, Dimension.PERCENT)
        case Unit.RATIO:
            return CanonicalValue(
                value.amount * Decimal(100), Unit.PERCENT, Dimension.PERCENT
            )
        case Unit.MULTIPLE:
            return CanonicalValue(value.amount, Unit.MULTIPLE, Dimension.MULTIPLE)
        case Unit.WON:
            return CanonicalValue(
                value.amount / Decimal(1000000), Unit.MILLION_WON, Dimension.MONEY
            )
        case Unit.MILLION_WON:
            return CanonicalValue(value.amount, Unit.MILLION_WON, Dimension.MONEY)
        case Unit.HUNDRED_MILLION_WON:
            return CanonicalValue(
                value.amount * Decimal(100), Unit.MILLION_WON, Dimension.MONEY
            )
        case Unit.MILLISECOND:
            return CanonicalValue(
                value.amount / Decimal(1000), Unit.SECOND, Dimension.TIME
            )
        case Unit.SECOND:
            return CanonicalValue(value.amount, Unit.SECOND, Dimension.TIME)
        case Unit.PERCENTAGE_POINT:
            return CanonicalValue(
                value.amount, Unit.PERCENTAGE_POINT, Dimension.PERCENTAGE_POINT
            )
        case Unit.CENTIMETER:
            return CanonicalValue(value.amount, Unit.CENTIMETER, Dimension.LENGTH)
        case Unit.METER:
            return CanonicalValue(
                value.amount * Decimal(100), Unit.CENTIMETER, Dimension.LENGTH
            )
        case Unit.KILOGRAM:
            return CanonicalValue(value.amount, Unit.KILOGRAM, Dimension.MASS)
        case Unit.GRAM:
            return CanonicalValue(
                value.amount / Decimal(1000), Unit.KILOGRAM, Dimension.MASS
            )
        case unreachable:
            assert_never(unreachable)


def convert_to_unit(value: NumericValue, target_unit: Unit) -> NumericValue | None:
    source = normalize(value)
    target = normalize(NumericValue(Decimal(1), target_unit))
    if source.dimension is not target.dimension:
        return None
    return NumericValue(source.amount / target.amount, target_unit)


def round_report_value(value: NumericValue, digits: int) -> NumericValue:
    quantum = Decimal(1).scaleb(-digits)
    return NumericValue(
        value.amount.quantize(quantum, rounding=ROUND_HALF_UP), value.unit
    )


def relative_difference(claim: Decimal, difference: Decimal) -> Decimal | None:
    if claim == Decimal(0):
        return None
    return difference / abs(claim)
