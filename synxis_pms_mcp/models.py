"""Pydantic models for SynXis PMS API.

SynXis PMS (Property Management System) API models for:
- Guest management
- Room assignments
- Check-in/check-out operations
- Billing/invoicing

API Documentation: https://developer.synxis.com/
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RoomStatus(str, Enum):
    """Room status values."""

    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    DIRTY = "DIRTY"
    CLEANING = "CLEANING"


class GuestStatus(str, Enum):
    """Guest status values."""

    RESERVATION = "RESERVATION"
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class PaymentMethod(str, Enum):
    """Payment method types."""

    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    CASH = "CASH"
    INVOICE = "INVOICE"
    PREPAID = "PREPAID"


class Guest(BaseModel):
    """Guest information."""

    guest_id: str = Field(description="Unique guest identifier")
    first_name: str = Field(description="First name")
    last_name: str = Field(description="Last name")
    email: str | None = Field(default=None, description="Email address")
    phone: str | None = Field(default=None, description="Phone number")
    address: str | None = Field(default=None, description="Street address")
    city: str | None = Field(default=None, description="City")
    country: str | None = Field(default=None, description="Country code")
    loyalty_tier: str | None = Field(default=None, description="Loyalty program tier")
    vip_status: bool = Field(default=False, description="VIP guest flag")
    preferences: list[str] = Field(
        default_factory=list,
        description="Guest preferences",
    )
    notes: str | None = Field(default=None, description="Special notes")


class Room(BaseModel):
    """Room information."""

    room_id: str = Field(description="Unique room identifier")
    room_number: str = Field(description="Room number")
    room_type: str = Field(description="Room type code")
    room_type_name: str = Field(description="Room type name")
    floor: int | None = Field(default=None, description="Floor number")
    status: RoomStatus = Field(description="Current room status")
    features: list[str] = Field(
        default_factory=list,
        description="Room features",
    )
    max_occupancy: int = Field(default=2, description="Maximum occupancy")
    current_occupancy: int = Field(default=0, description="Current occupancy")


class RoomAssignment(BaseModel):
    """Room assignment details."""

    reservation_id: str = Field(description="Reservation identifier")
    room_id: str = Field(description="Assigned room ID")
    room_number: str = Field(description="Room number")
    guest_id: str = Field(description="Guest ID")
    guest_name: str = Field(description="Guest name")
    check_in_date: date = Field(description="Check-in date")
    check_out_date: date = Field(description="Check-out date")
    status: GuestStatus = Field(description="Current status")


class CheckInResult(BaseModel):
    """Result of check-in operation."""

    success: bool = Field(description="Whether check-in succeeded")
    reservation_id: str = Field(description="Reservation identifier")
    room_id: str = Field(description="Assigned room ID")
    room_number: str = Field(description="Room number")
    guest_name: str = Field(description="Guest name")
    check_in_time: datetime = Field(description="Check-in timestamp")
    key_cards_issued: int = Field(default=2, description="Number of key cards")
    message: str | None = Field(default=None, description="Additional message")


class CheckOutResult(BaseModel):
    """Result of check-out operation."""

    success: bool = Field(description="Whether check-out succeeded")
    reservation_id: str = Field(description="Reservation identifier")
    room_id: str = Field(description="Room ID")
    room_number: str = Field(description="Room number")
    guest_name: str = Field(description="Guest name")
    check_out_time: datetime = Field(description="Check-out timestamp")
    total_charges: float = Field(description="Total charges")
    payments_received: float = Field(description="Payments received")
    balance_due: float = Field(description="Remaining balance")
    invoice_number: str | None = Field(default=None, description="Invoice number")


class Charge(BaseModel):
    """A charge or posting."""

    charge_id: str = Field(description="Charge identifier")
    reservation_id: str = Field(description="Associated reservation")
    description: str = Field(description="Charge description")
    amount: float = Field(description="Charge amount", ge=0)
    currency: str = Field(default="USD", description="Currency code")
    category: str = Field(description="Charge category")
    posted_at: datetime = Field(description="Posting timestamp")
    posted_by: str | None = Field(default=None, description="Staff member")


class Payment(BaseModel):
    """A payment record."""

    payment_id: str = Field(description="Payment identifier")
    reservation_id: str = Field(description="Associated reservation")
    amount: float = Field(description="Payment amount", ge=0)
    currency: str = Field(default="USD", description="Currency code")
    method: PaymentMethod = Field(description="Payment method")
    reference: str | None = Field(default=None, description="Payment reference")
    processed_at: datetime = Field(description="Processing timestamp")


class Folio(BaseModel):
    """Guest folio (bill)."""

    folio_id: str = Field(description="Folio identifier")
    reservation_id: str = Field(description="Associated reservation")
    guest_name: str = Field(description="Guest name")
    room_number: str = Field(description="Room number")
    charges: list[Charge] = Field(default_factory=list, description="Charges")
    payments: list[Payment] = Field(default_factory=list, description="Payments")
    total_charges: float = Field(default=0.0, description="Total charges")
    total_payments: float = Field(default=0.0, description="Total payments")
    balance: float = Field(default=0.0, description="Balance due")


class SynXisPMSError(Exception):
    """Exception raised for SynXis PMS API errors."""

    def __init__(
        self,
        message: str,
        status: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary."""
        result: dict[str, Any] = {
            "error": self.message,
            "status": self.status,
        }
        if self.details:
            result["details"] = self.details
        return result


__all__ = [
    "RoomStatus",
    "GuestStatus",
    "PaymentMethod",
    "Guest",
    "Room",
    "RoomAssignment",
    "CheckInResult",
    "CheckOutResult",
    "Charge",
    "Payment",
    "Folio",
    "SynXisPMSError",
]
