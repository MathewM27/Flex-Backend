"""Money value object — NFR-X3."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.shared.errors import ValidationError
from src.shared.money import CurrencyMismatch, Money


def test_money_quantizes_to_two_decimals() -> None:
    assert Money.of("129", "USD").as_str() == "129.00"
    assert Money.of("129.005", "USD").as_str() == "129.01"  # half-up


def test_money_normalizes_currency_to_upper() -> None:
    assert Money.of("10", "usd").currency == "USD"


def test_money_rejects_negative_amounts() -> None:
    with pytest.raises(ValidationError):
        Money.of("-1", "USD")


def test_money_rejects_invalid_currency() -> None:
    with pytest.raises(ValidationError):
        Money.of("1", "US")


def test_money_addition_within_currency() -> None:
    total = Money.of("100", "USD") + Money.of("29.50", "USD")
    assert total.as_str() == "129.50"


def test_money_addition_across_currencies_is_rejected() -> None:
    with pytest.raises(CurrencyMismatch):
        _ = Money.of("10", "USD") + Money.of("10", "EUR")


def test_money_times_int() -> None:
    nightly = Money.of("100", "USD")
    assert (nightly * 3).as_str() == "300.00"


def test_money_amount_is_decimal() -> None:
    m = Money.of("1.23", "USD")
    assert isinstance(m.amount, Decimal)
