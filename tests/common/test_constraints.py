from dataclasses import dataclass
from typing import Annotated

import pytest

from pyeeprom.common.constraints import NumberConstraints, validate_constraints


@dataclass
class NonNumberConstraint:
    string: Annotated[str, NumberConstraints()]


def test_number_constraints_invalid_type() -> None:
    non_number_constraint = NonNumberConstraint("banana")
    with pytest.raises(TypeError, match=r"\w must be a number"):
        validate_constraints(non_number_constraint)


@dataclass
class GeNumberConstraint:
    ge_value: Annotated[int, NumberConstraints(ge=0)]


def test_number_constraints_ge() -> None:
    with pytest.raises(ValueError, match=r"\w must be >="):
        validate_constraints(GeNumberConstraint(ge_value=-1))

    validate_constraints(GeNumberConstraint(ge_value=0))
    validate_constraints(GeNumberConstraint(ge_value=1))


@dataclass
class LeNumberConstraint:
    le_value: Annotated[int, NumberConstraints(le=0)]


def test_number_constraints_le() -> None:
    with pytest.raises(ValueError, match=r"\w must be <="):
        validate_constraints(LeNumberConstraint(le_value=1))

    validate_constraints(LeNumberConstraint(le_value=0))
    validate_constraints(LeNumberConstraint(le_value=-1))


@dataclass
class GtNumberConstraint:
    gt_value: Annotated[int, NumberConstraints(gt=0)]


def test_number_constraints_gt() -> None:
    with pytest.raises(ValueError, match=r"\w must be >"):
        validate_constraints(GtNumberConstraint(gt_value=-1))

    with pytest.raises(ValueError, match=r"\w must be >"):
        validate_constraints(GtNumberConstraint(gt_value=0))

    validate_constraints(GtNumberConstraint(gt_value=1))


@dataclass
class LtNumberConstraint:
    lt_value: Annotated[int, NumberConstraints(lt=0)]


def test_number_constraints_lt() -> None:
    with pytest.raises(ValueError, match=r"\w must be <"):
        validate_constraints(LtNumberConstraint(lt_value=1))

    with pytest.raises(ValueError, match=r"\w must be <"):
        validate_constraints(LtNumberConstraint(lt_value=0))

    validate_constraints(LtNumberConstraint(lt_value=-1))
