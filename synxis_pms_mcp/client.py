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
        self._access_token: str | None = None

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

    async def _get_access_token(self) -> str:
        """Get OAuth2 access token using client credentials flow."""
        if self._access_token:
            return self._access_token

        if self.settings.mock_mode:
            self._access_token = "mock_access_token_12345"
            return self._access_token

        if not self.settings.has_credentials():
            raise SynXisPMSError(
                message="OAuth2 credentials not configured. Set SYNXIS_PMS_CLIENT_ID and SYNXIS_PMS_CLIENT_SECRET.",
                status=401,
            )

        client = await self._ensure_client()
        token_url = f"{self.settings.base_url.rsplit('/pms', 1)[0]}/oauth/token"

        try:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.settings.client_id,
                    "client_secret": self.settings.client_secret,
                    "scope": "pms:read pms:write",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 401:
                raise SynXisPMSError(message="Invalid OAuth2 credentials", status=401)

            response.raise_for_status()
            token_data = response.json()
            self._access_token = token_data.get("access_token")

            if not self._access_token:
                raise SynXisPMSError(message="No access token in OAuth2 response", status=500)

            logger.info("OAuth2 token obtained successfully")
            return self._access_token

        except httpx.HTTPStatusError as e:
            logger.error("OAuth2 token request failed", status=e.response.status_code)
            raise SynXisPMSError(
                message=f"OAuth2 authentication failed: {e.response.text}",
                status=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            logger.error("OAuth2 request error", error=str(e))
            raise SynXisPMSError(message=f"OAuth2 request failed: {e}", status=503) from e

    async def _make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated API request with retry logic."""
        import asyncio

        client = await self._ensure_client()
        token = await self._get_access_token()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        url = f"{self.settings.base_url}{endpoint}"

        for attempt in range(self.settings.max_retries):
            try:
                response = await client.request(method, url, headers=headers, **kwargs)

                # Handle token expiration
                if response.status_code == 401:
                    self._access_token = None
                    token = await self._get_access_token()
                    headers["Authorization"] = f"Bearer {token}"
                    response = await client.request(method, url, headers=headers, **kwargs)

                if response.status_code == 404:
                    return {"data": None, "status": "not_found"}

                response.raise_for_status()

                data = response.json()
                return {"data": data, "status": "success"}

            except httpx.HTTPStatusError as e:
                if attempt < self.settings.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue

                error_body = {}
                try:
                    error_body = e.response.json()
                except Exception:
                    error_body = {"message": e.response.text}

                raise SynXisPMSError(
                    message=error_body.get("message", f"API error: {e.response.status_code}"),
                    status=e.response.status_code,
                ) from e

            except httpx.RequestError as e:
                if attempt < self.settings.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue

                raise SynXisPMSError(message=f"Request failed: {e}", status=503) from e

        raise SynXisPMSError(message="Max retries exceeded", status=503)

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

        # Real API implementation
        result = await self._make_authenticated_request(
            "GET",
            f"/guests/{guest_id}",
            params={"propertyId": self.settings.property_id},
        )

        data = result.get("data")
        if not data:
            return None

        guest_data = data.get("guest", data)
        return Guest(
            guest_id=guest_data.get("guestId", guest_id),
            first_name=guest_data.get("firstName"),
            last_name=guest_data.get("lastName"),
            email=guest_data.get("email"),
            phone=guest_data.get("phone"),
            address=guest_data.get("address"),
            city=guest_data.get("city"),
            country=guest_data.get("country"),
            loyalty_tier=guest_data.get("loyaltyTier"),
            vip_status=guest_data.get("vipStatus", False),
            preferences=guest_data.get("preferences", []),
        )

    async def get_room(self, room_id: str) -> Room | None:
        """Get room information."""
        logger.info("Getting room", room_id=room_id, mock_mode=self.settings.mock_mode)

        if self.settings.mock_mode:
            return self._mock_room(room_id)

        # Real API implementation
        result = await self._make_authenticated_request(
            "GET",
            f"/rooms/{room_id}",
            params={"propertyId": self.settings.property_id},
        )

        data = result.get("data")
        if not data:
            return None

        room_data = data.get("room", data)
        return Room(
            room_id=room_data.get("roomId", room_id),
            room_number=room_data.get("roomNumber"),
            room_type=room_data.get("roomType"),
            room_type_name=room_data.get("roomTypeName"),
            floor=room_data.get("floor"),
            status=RoomStatus(room_data.get("status", "clean")),
            features=room_data.get("features", []),
            max_occupancy=room_data.get("maxOccupancy", 2),
            current_occupancy=room_data.get("currentOccupancy", 0),
        )

    async def get_room_status(self, room_id: str) -> RoomStatus:
        """Get current room status."""
        logger.info("Getting room status", room_id=room_id)

        if self.settings.mock_mode:
            room = self._mock_room(room_id)
            return room.status

        # Real API implementation
        result = await self._make_authenticated_request(
            "GET",
            f"/rooms/{room_id}/status",
            params={"propertyId": self.settings.property_id},
        )

        data = result.get("data", {})
        return RoomStatus(data.get("status", "clean"))

    async def list_available_rooms(self) -> list[Room]:
        """List all available rooms."""
        logger.info("Listing available rooms")

        if self.settings.mock_mode:
            return [
                self._mock_room(f"ROOM{i:03d}")
                for i in range(1, 11)
                if random.random() > 0.3
            ]

        # Real API implementation
        result = await self._make_authenticated_request(
            "GET",
            "/rooms",
            params={
                "propertyId": self.settings.property_id,
                "status": "available",
            },
        )

        rooms_data = result.get("data", {}).get("rooms", [])
        rooms = []
        for room_data in rooms_data:
            rooms.append(Room(
                room_id=room_data.get("roomId"),
                room_number=room_data.get("roomNumber"),
                room_type=room_data.get("roomType"),
                room_type_name=room_data.get("roomTypeName"),
                floor=room_data.get("floor"),
                status=RoomStatus(room_data.get("status", "clean")),
                features=room_data.get("features", []),
                max_occupancy=room_data.get("maxOccupancy", 2),
                current_occupancy=room_data.get("currentOccupancy", 0),
            ))

        return rooms

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

        # Real API implementation
        result = await self._make_authenticated_request(
            "POST",
            f"/reservations/{reservation_id}/checkin",
            json={
                "roomId": room_id,
                "propertyId": self.settings.property_id,
            },
        )

        data = result.get("data", {}).get("checkIn", {})

        return CheckInResult(
            success=data.get("success", True),
            reservation_id=reservation_id,
            room_id=room_id,
            room_number=data.get("roomNumber"),
            guest_name=data.get("guestName"),
            check_in_time=(
                datetime.fromisoformat(data["checkInTime"])
                if data.get("checkInTime")
                else datetime.now()
            ),
            key_cards_issued=data.get("keyCardsIssued", 2),
            message=data.get("message", "Check-in successful"),
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

        # Real API implementation
        result = await self._make_authenticated_request(
            "POST",
            f"/reservations/{reservation_id}/checkout",
            json={"propertyId": self.settings.property_id},
        )

        data = result.get("data", {}).get("checkOut", {})

        return CheckOutResult(
            success=data.get("success", True),
            reservation_id=reservation_id,
            room_id=data.get("roomId"),
            room_number=data.get("roomNumber"),
            guest_name=data.get("guestName"),
            check_out_time=(
                datetime.fromisoformat(data["checkOutTime"])
                if data.get("checkOutTime")
                else datetime.now()
            ),
            total_charges=data.get("totalCharges"),
            payments_received=data.get("paymentsReceived"),
            balance_due=data.get("balanceDue"),
            invoice_number=data.get("invoiceNumber"),
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

        # Real API implementation
        result = await self._make_authenticated_request(
            "GET",
            f"/reservations/{reservation_id}/folio",
            params={"propertyId": self.settings.property_id},
        )

        data = result.get("data", {}).get("folio", {})

        charges = []
        for charge_data in data.get("charges", []):
            charges.append(Charge(
                charge_id=charge_data.get("chargeId"),
                reservation_id=reservation_id,
                description=charge_data.get("description"),
                amount=charge_data.get("amount"),
                category=charge_data.get("category"),
                posted_at=(
                    datetime.fromisoformat(charge_data["postedAt"])
                    if charge_data.get("postedAt")
                    else datetime.now()
                ),
            ))

        payments = []
        for payment_data in data.get("payments", []):
            payments.append(Payment(
                payment_id=payment_data.get("paymentId"),
                reservation_id=reservation_id,
                amount=payment_data.get("amount"),
                method=PaymentMethod(payment_data.get("method", "credit_card")),
                processed_at=(
                    datetime.fromisoformat(payment_data["processedAt"])
                    if payment_data.get("processedAt")
                    else datetime.now()
                ),
            ))

        return Folio(
            folio_id=data.get("folioId"),
            reservation_id=reservation_id,
            guest_name=data.get("guestName"),
            room_number=data.get("roomNumber"),
            charges=charges,
            payments=payments,
            total_charges=data.get("totalCharges"),
            total_payments=data.get("totalPayments"),
            balance=data.get("balance"),
        )


__all__ = ["SynXisPMSClient"]
