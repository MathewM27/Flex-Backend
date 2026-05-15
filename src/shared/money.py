"""Money value object (NFR-X3).

Money is always `Decimal` paired with an ISO 4217 currency code.
Mixed-currency arithmetic raises `CurrencyMismatch`. `float` near money is
a bug — repositories and serializers convert to/from `Decimal` strings.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from src.shared.errors import ValidationError

_TWO_PLACES = Decimal("0.01")


class CurrencyMismatch(ValidationError):
    code = "CURRENCY_MISMATCH"


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("Money.amount must be a Decimal")
        if not (self.currency and len(self.currency) == 3 and self.currency.isupper()):
            raise ValidationError(f"invalid currency code: {self.currency!r}")
        if self.amount < 0:
            raise ValidationError("Money.amount must be non-negative")

    @classmethod
    def of(cls, amount: Decimal | int | str, currency: str) -> Money:
        d = Decimal(amount) if not isinstance(amount, Decimal) else amount
        return cls(d.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP), currency.upper())

    def _same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatch(f"cannot operate on {self.currency} and {other.currency}")

    def __add__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money.of(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money.of(self.amount - other.amount, self.currency)

    def __mul__(self, factor: int) -> Money:
        if not isinstance(factor, int):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("Money can only be multiplied by an int")
        return Money.of(self.amount * factor, self.currency)

    def as_str(self) -> str:
        """Serialization shape used in API responses (e.g. '129.00')."""
        return f"{self.amount:.2f}"
