"""User roles (FR-A1, FR-A5)."""

from __future__ import annotations

import enum


class Role(enum.StrEnum):
    TENANT = "TENANT"
    LANDLORD = "LANDLORD"
