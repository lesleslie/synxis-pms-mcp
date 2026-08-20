---
description: Inspect SynXis PMS room status, type, floor, features, and occupancy for a given room ID.
argument-hint: <room-id>
allowed-tools: mcp__synxis-pms__get_room_status, mcp__synxis-pms__health_check
---

# /synxis-pms-room

Look up the current status and metadata for a room in the configured SynXis PMS property.

## Usage

`/synxis-pms-room <room-id>`

Arguments:

- `<room-id>`: required. The SynXis PMS room identifier (not the guest-facing room number).

## Workflow

1. Call `mcp__synxis-pms__health_check` to confirm the server is reachable and note whether `mock_mode` is active, so the caller knows if the result is live property data.
2. Call `mcp__synxis-pms__get_room_status` with `room_id` set to `<room-id>`.
3. On `success: false`, report the `message` and `error` fields verbatim — a missing room usually means the identifier is a room *number* rather than a room *ID*.
4. On success, report room number, room type and type name, floor, status, feature list, and `current_occupancy` against `max_occupancy`.
5. Surface the returned `next_steps` (typically pointing at check-in when the room is available, or check-out when it is occupied).

## Example

`/synxis-pms-room room-1201`
