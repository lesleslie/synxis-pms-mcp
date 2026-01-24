# Python Coding Standards

## Type Hints

- All functions must have type hints for parameters and return values
- Use `typing` module for complex types (Optional, List, Dict, etc.)
- Import typing aliases from `typing` (not `typing_extensions` unless needed)

```python
from typing import Optional

def get_reservation(confirmed_number: str) -> Optional[dict]:
    """Retrieve reservation by confirmation number."""
    ...
```

## Docstrings

- Use Google-style docstrings for all public functions
- Include: description, args, returns, raises (if applicable)

```python
def search_reservations(guest_name: str) -> list[dict]:
    """Search for reservations by guest name.

    Args:
        guest_name: Full or partial guest name to search for

    Returns:
        List of reservation dictionaries matching the search criteria

    Raises:
        APIConnectionError: If the API request fails
    """
    ...
```

## Error Handling

- Never use `except: pass` or `except Exception: pass`
- Catch specific exceptions
- Log errors with context
- Raise appropriate custom exceptions

```python
# Bad
try:
    api_call()
except Exception:
    pass

# Good
try:
    api_call()
except APIConnectionError as e:
    logger.error(f"API connection failed: {e}")
    raise
```

## Async/Await

- Use async functions for all I/O operations (API calls, database queries)
- Use `asyncio` properly - don't forget to await coroutines
- Use `async with` for context managers

```python
async def get_property_details(property_id: str) -> dict:
    """Retrieve property details from API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"/properties/{property_id}") as response:
            return await response.json()
```

## Code Organization

- One class per file for large classes
- Keep functions focused and small (< 50 lines)
- Use `__init__.py` to expose public API
- Follow PEP 8 naming conventions

## Dependencies

- Pin production dependencies in `dependencies`
- Put dev tools in `[dependency-groups].dev`
- Run `creosote` to detect unused dependencies
- Keep dependencies minimal

## Testing

- Write tests before fixing bugs (TDD)
- Use descriptive test names
- Follow Arrange-Act-Assert pattern
- Mock external dependencies

```python
async def test_search_reservations_by_name():
    # Arrange
    mock_api = AsyncMock()
    mock_api.search.return_value = [{"reservation_id": "123"}]

    # Act
    result = await search_reservations(mock_api, "John Doe")

    # Assert
    assert len(result) == 1
    assert result[0]["reservation_id"] == "123"
```
