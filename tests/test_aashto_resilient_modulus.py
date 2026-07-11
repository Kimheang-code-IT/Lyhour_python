"""Tests for AASHTO effective resilient modulus."""
import math

from app.data.aashto_resilient_modulus import (
    compute_effective_resilient_modulus,
    relative_damage_factor,
    resilient_modulus_psi,
)


def test_resilient_modulus_from_cbr() -> None:
    assert resilient_modulus_psi(4.0) == 6000.0


def test_relative_damage_at_mr_6000() -> None:
    uf = relative_damage_factor(6000.0)
    assert uf is not None
    assert math.isclose(uf, 0.20257, rel_tol=0.002)


def test_effective_modulus_uniform_cbr() -> None:
    result = compute_effective_resilient_modulus([4.0] * 12)
    assert result.effective_mr_psi is not None
    assert math.isclose(result.effective_mr_psi, 6000.0, rel_tol=0.01)
    assert result.average_relative_damage is not None
    assert math.isclose(result.average_relative_damage, 0.203, rel_tol=0.01)
