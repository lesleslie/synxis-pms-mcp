---
description: Drive the SynXis PMS guest stay lifecycle — check in, check out, or review the folio for a reservation.
argument-hint: <check-in|check-out|folio> <reservation-id> [--room <room-id>] [--guest <guest-id>]
allowed-tools: mcp__synxis-pms__check_in, mcp__synxis-pms__check_out, mcp__synxis-pms__get_folio, mcp__synxis-pms__get_guest, mcp__synxis-pms__get_room_status, mcp__synxis-pms__health_check
---

# /synxis-pms-stay

Run one leg of the guest stay lifecycle against the configured SynXis PMS property.

## Usage

`/synxis-pms-stay <check-in|check-out|folio> <reservation-id> [--room <room-id>] [--guest <guest-id>]`

Arguments:

- `<check-in|check-out|folio>`: required. The stay action to perform.
- `<reservation-id>`: required. The SynXis PMS reservation identifier.
- `--room <room-id>`: required for `check-in`. The room to assign.
- `--guest <guest-id>`: optional. When supplied, guest profile details (loyalty tier, VIP status, preferences) are fetched and included in the report.

## Workflow

1. Call `mcp__synxis-pms__health_check` first. If `configured` is false and `mock_mode` is false, stop and report that no PMS backend is reachable — do not attempt a write.
2. If `--guest` was supplied, call `mcp__synxis-pms__get_guest` with `guest_id` to capture the guest profile for the report.
3. Dispatch on the requested action:
   - `check-in`: verify the target room with `mcp__synxis-pms__get_room_status` (`room_id`), then call `mcp__synxis-pms__check_in` with `reservation_id` and `room_id`. Report assigned room number, check-in time, and key cards issued.
   - `check-out`: call `mcp__synxis-pms__check_out` with `reservation_id`. Report check-out time, total charges, payments received, balance due, and invoice number.
   - `folio`: call `mcp__synxis-pms__get_folio` with `reservation_id`. Report the itemized charges by category, payments by method, totals, and the outstanding balance.
4. Treat `check-in` and `check-out` as state-changing operations: on `success: false`, report the `error` field verbatim and do not retry automatically.
5. Surface the returned `next_steps` from the tool response so downstream front-desk actions are not dropped.

## Example

`/synxis-pms-stay check-in res-88421 --room room-1201 --guest guest-7734`
