"""PMS management MCP tools.

Tools for SynXis Property Management System:
- get_guest: Retrieve guest information
- get_room_status: Check room status
- check_in: Check in a guest
- check_out: Check out a guest
- get_folio: Get guest billing
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from synxis_pms_mcp.client import SynXisPMSClient
from synxis_pms_mcp.config import get_logger_instance
from synxis_pms_mcp.models import CheckInResult, CheckOutResult, Folio, Guest, Room

if TYPE_CHECKING:
    from fastmcp import FastMCP

logger = get_logger_instance("synxis-pms-mcp.tools")


class ToolResponse(BaseModel):
    """Standardized tool response."""

    success: bool
    message: str
    data: dict[str, Any] | None = None
    error: str | None = None
    next_steps: list[str] | None = None


def _guest_to_dict(guest: Guest) -> dict[str, Any]:
    return {
        "guest_id": guest.guest_id,
        "first_name": guest.first_name,
        "last_name": guest.last_name,
        "email": guest.email,
        "phone": guest.phone,
        "loyalty_tier": guest.loyalty_tier,
        "vip_status": guest.vip_status,
        "preferences": guest.preferences,
    }


def _room_to_dict(room: Room) -> dict[str, Any]:
    return {
        "room_id": room.room_id,
        "room_number": room.room_number,
        "room_type": room.room_type,
        "room_type_name": room.room_type_name,
        "floor": room.floor,
        "status": room.status.value,
        "features": room.features,
        "max_occupancy": room.max_occupancy,
        "current_occupancy": room.current_occupancy,
    }


def register_pms_tools(app: "FastMCP", client: SynXisPMSClient) -> None:
    """Register PMS management tools."""

    @app.tool()
    async def get_guest(guest_id: str) -> ToolResponse:
        """Get guest information by ID.

        Args:
            guest_id: Guest identifier

        Returns:
            Guest details
        """
        logger.info("Getting guest", guest_id=guest_id)

        try:
            guest = await client.get_guest(guest_id)
            if not guest:
                return ToolResponse(
                    success=False,
                    message=f"Guest {guest_id} not found",
                    next_steps=["Verify the guest ID is correct"],
                )

            return ToolResponse(
                success=True,
                message=f"Found guest: {guest.first_name} {guest.last_name}",
                data={"guest": _guest_to_dict(guest)},
                next_steps=[
                    "Use check_in to check in the guest",
                    "Use get_folio to view billing",
                ],
            )

        except Exception as e:
            return ToolResponse(
                success=False,
                message="Failed to get guest",
                error=str(e),
            )

    @app.tool()
    async def get_room_status(room_id: str) -> ToolResponse:
        """Get current room status.

        Args:
            room_id: Room identifier

        Returns:
            Room status information
        """
        logger.info("Getting room status", room_id=room_id)

        try:
            room = await client.get_room(room_id)
            if not room:
                return ToolResponse(
                    success=False,
                    message=f"Room {room_id} not found",
                )

            return ToolResponse(
                success=True,
                message=f"Room {room.room_number} status: {room.status.value}",
                data={"room": _room_to_dict(room)},
                next_steps=[
                    "Use check_in if room is available",
                    "Use check_out if room is occupied",
                ],
            )

        except Exception as e:
            return ToolResponse(
                success=False,
                message="Failed to get room status",
                error=str(e),
            )

    @app.tool()
    async def check_in(
        reservation_id: str,
        room_id: str,
    ) -> ToolResponse:
        """Check in a guest.

        Args:
            reservation_id: Reservation identifier
            room_id: Room to assign

        Returns:
            Check-in confirmation
        """
        logger.info("Checking in", reservation_id=reservation_id)

        try:
            result = await client.check_in(reservation_id, room_id)

            return ToolResponse(
                success=True,
                message=f"Checked in {result.guest_name} to room {result.room_number}",
                data={
                    "reservation_id": result.reservation_id,
                    "room_number": result.room_number,
                    "check_in_time": str(result.check_in_time),
                    "key_cards_issued": result.key_cards_issued,
                },
                next_steps=[
                    "Issue key cards to guest",
                    "Inform guest of amenities",
                    "Use get_folio to track charges",
                ],
            )

        except Exception as e:
            return ToolResponse(
                success=False,
                message="Check-in failed",
                error=str(e),
            )

    @app.tool()
    async def check_out(reservation_id: str) -> ToolResponse:
        """Check out a guest.

        Args:
            reservation_id: Reservation identifier

        Returns:
            Check-out confirmation with billing summary
        """
        logger.info("Checking out", reservation_id=reservation_id)

        try:
            result = await client.check_out(reservation_id)

            return ToolResponse(
                success=True,
                message=f"Checked out {result.guest_name} from room {result.room_number}",
                data={
                    "reservation_id": result.reservation_id,
                    "room_number": result.room_number,
                    "check_out_time": str(result.check_out_time),
                    "total_charges": result.total_charges,
                    "payments_received": result.payments_received,
                    "balance_due": result.balance_due,
                    "invoice_number": result.invoice_number,
                },
                next_steps=[
                    "Process any remaining balance",
                    "Return key cards",
                    "Mark room for cleaning",
                ],
            )

        except Exception as e:
            return ToolResponse(
                success=False,
                message="Check-out failed",
                error=str(e),
            )

    @app.tool()
    async def get_folio(reservation_id: str) -> ToolResponse:
        """Get guest folio (billing statement).

        Args:
            reservation_id: Reservation identifier

        Returns:
            Detailed billing information
        """
        logger.info("Getting folio", reservation_id=reservation_id)

        try:
            folio = await client.get_folio(reservation_id)

            return ToolResponse(
                success=True,
                message=f"Folio for {folio.guest_name} - Balance: ${folio.balance:.2f}",
                data={
                    "folio_id": folio.folio_id,
                    "guest_name": folio.guest_name,
                    "room_number": folio.room_number,
                    "charges": [
                        {
                            "description": c.description,
                            "amount": c.amount,
                            "category": c.category,
                        }
                        for c in folio.charges
                    ],
                    "payments": [
                        {
                            "amount": p.amount,
                            "method": p.method.value,
                        }
                        for p in folio.payments
                    ],
                    "total_charges": folio.total_charges,
                    "total_payments": folio.total_payments,
                    "balance": folio.balance,
                },
                next_steps=[
                    "Review charges with guest",
                    "Process payment if balance due",
                    "Print invoice",
                ],
            )

        except Exception as e:
            return ToolResponse(
                success=False,
                message="Failed to get folio",
                error=str(e),
            )

    logger.info("Registered 5 PMS management tools")
