"""SynXis PMS API client with mock mode support."""

from __future__ import annotations

import random
import uuid
from datetime import date, datetime
from typing import Any

import httpx

from .config import SynXisPMSSettings, get_logger_instance, get_settings
from .models import (
    Charge,
    CheckInResult,
    CheckOutResult,
    Folio,
    Guest,
    GuestStatus,
    Payment,
    PaymentMethod,
    Room,
    RoomAssignment,
    RoomStatus,
    SynXisPMSError,
)

logger = get_logger_instance("synxis-pms-mcp.client")


class SynXisPMSClient:
    """Async HTTP client for SynXis PMS API with mock mode support."""

    def __init__(self, settings: SynXisPMSSettings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "SynXisPMSClient":
        if not self.settings.mock_mode:
            await self._ensure_client()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            config = self.settings.http_client_config()
            self._client = httpx.AsyncClient(**config)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # =========================================================================
    # Mock Data Generation
    # =========================================================================

    def _mock_guest(self, guest_id: str) -> Guest:
        return Guest(
            guest_id=guest_id,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1-555-0100",
            address="123 Main Street",
            city="New York",
            country="US",
            loyalty_tier="Gold",
            vip_status=random.random() > 0.8,
            preferences=["High floor", "Non-smoking"],
        )

    def _mock_room(self, room_id: str) -> Room:
        room_num = f"{random.randint(1, 10)}{random.randint(1, 20):02d}"
        return Room(
            room_id=room_id,
            room_number=room_num,
            room_type="DLX",
            room_type_name="Deluxe Room",
            floor=int(room_num[:1]),
            status=random.choice(list(RoomStatus)),
            features=["WiFi", "Mini Bar", "Safe", "Iron"],
            max_occupancy=2,
            current_occupancy=random.randint(0, 2),
        )

    # =========================================================================
    # Public API Methods
    # =========================================================================

    async def get_guest(self, guest_id: str) -> Guest | None:
        """Get guest information."""
        logger.info("Getting guest", guest_id=guest_id, mock_mode=self.settings.mock_mode)

        if self.settings.mock_mode:
            return self._mock_guest(guest_id)

        raise SynXisPMSError(
            message="Real API not implemented. Use mock_mode=True.",
            status=501,
        )

    async def get_room(self, room_id: str) -> Room | None:
        """Get room information."""
        logger.info("Getting room", room_id=room_id, mock_mode=self.settings.mock_mode)

        if self.settings.mock_mode:
            return self._mock_room(room_id)

        raise SynXisPMSError(
            message="Real API not implemented. Use mock_mode=True.",
            status=501,
        )

    async def get_room_status(self, room_id: str) -> RoomStatus:
        """Get current room status."""
        logger.info("Getting room status", room_id=room_id)

        if self.settings.mock_mode:
            room = self._mock_room(room_id)
            return room.status

        raise SynXisPMSError(
            message="Real API not implemented. Use mock_mode=True.",
            status=501,
        )

    async def list_available_rooms(self) -> list[Room]:
        """List all available rooms."""
        logger.info("Listing available rooms")

        if self.settings.mock_mode:
            return [
                self._mock_room(f"ROOM{i:03d}")
                for i in range(1, 11)
                if random.random() > 0.3
            ]

        raise SynXisPMSError(
            message="Real API not implemented. Use mock_mode=True.",
            status=501,
        )

    async def check_in(
        self,
        reservation_id: str,
        room_id: str,
    ) -> CheckInResult:
        """Check in a guest."""
        logger.info(
            "Checking in guest",
            reservation_id=reservation_id,
            room_id=room_id,
        )

        if self.settings.mock_mode:
            return CheckInResult(
                success=True,
                reservation_id=reservation_id,
                room_id=room_id,
                room_number=f"{random.randint(1, 10)}{random.randint(1, 20):02d}",
                guest_name="John Doe",
                check_in_time=datetime.now(),
                key_cards_issued=2,
                message="Welcome! Your room is ready.",
            )

        raise SynXisPMSError(
            message="Real API not implemented. Use mock_mode=True.",
            status=501,
        )

    async def check_out(self, reservation_id: str) -> CheckOutResult:
        """Check out a guest."""
        logger.info("Checking out guest", reservation_id=reservation_id)

        if self.settings.mock_mode:
            total = random.uniform(200.0, 800.0)
            paid = total * random.uniform(0.5, 1.0)
            return CheckOutResult(
                success=True,
                reservation_id=reservation_id,
                room_id="ROOM001",
                room_number="305",
                guest_name="John Doe",
                check_out_time=datetime.now(),
                total_charges=round(total, 2),
                payments_received=round(paid, 2),
                balance_due=round(total - paid, 2),
                invoice_number=f"INV-{random.randint(10000, 99999)}",
            )

        raise SynXisPMSError(
            message="Real API not implemented. Use mock_mode=True.",
            status=501,
        )

    async def get_folio(self, reservation_id: str) -> Folio:
        """Get guest folio (bill)."""
        logger.info("Getting folio", reservation_id=reservation_id)

        if self.settings.mock_mode:
            charges = [
                Charge(
                    charge_id=f"CHG{i:03d}",
                    reservation_id=reservation_id,
                    description="Room Charge",
                    amount=199.99,
                    category="ROOM",
                    posted_at=datetime.now(),
                )
                for i in range(3)
            ]
            payments = [
                Payment(
                    payment_id="PAY001",
                    reservation_id=reservation_id,
                    amount=200.00,
                    method=PaymentMethod.CREDIT_CARD,
                    processed_at=datetime.now(),
                )
            ]
            total_charges = sum(c.amount for c in charges)
            total_payments = sum(p.amount for p in payments)

            return Folio(
                folio_id=f"FOLIO-{reservation_id}",
                reservation_id=reservation_id,
                guest_name="John Doe",
                room_number="305",
                charges=charges,
                payments=payments,
                total_charges=round(total_charges, 2),
                total_payments=round(total_payments, 2),
                balance=round(total_charges - total_payments, 2),
            )

        raise SynXisPMSError(
            message="Real API not implemented. Use mock_mode=True.",
            status=501,
        )


__all__ = ["SynXisPMSClient"]
