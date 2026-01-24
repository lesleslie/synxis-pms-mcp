# Synxis PMS MCP Server

Claude Code guidelines for developing the Synxis Property Management System MCP server.

## Project Overview

This is an MCP (Model Context Protocol) server that integrates with the Synxis Property Management System API, enabling AI assistants to interact with hotel reservation and property management data.

## Development Guidelines

### Code Quality

- Use **type hints** for all function signatures and parameters
- Write **docstrings** for all public functions, classes, and modules
- Follow **async/await** patterns for I/O operations
- Use **decorators** for instrumentation and validation
- Implement **context managers** for resource management
- **Never suppress exceptions** - handle them appropriately or let them propagate

### MCP Server Architecture

- Use **FastMCP** for server implementation
- Define **clear tool schemas** with proper input validation
- Implement **error handling** that returns structured error responses
- Use **async functions** for all API interactions
- Provide **descriptive tool descriptions** for AI consumption

### Testing Strategy

- Write **unit tests** for individual components
- Create **integration tests** for API interactions
- Use **pytest markers** to categorize tests (unit, integration, slow, network)
- Maintain **80%+ code coverage**
- Mock external API calls in tests

### API Integration

- Store API credentials in **environment variables**
- Use **session management** for connection pooling
- Implement **rate limiting** and **retry logic**
- Cache responses where appropriate
- Log all API interactions for debugging

## Tools to Implement

The MCP server should provide tools for:

1. **Reservation Management**
   - Search reservations by guest name, confirmation number
   - Retrieve reservation details
   - Create/modify/cancel reservations

2. **Property Information**
   - List available properties/hotels
   - Get property details and amenities
   - Check room availability and rates

3. **Guest Services**
   - Retrieve guest profile information
   - View guest history and preferences

4. **Reporting**
   - Generate occupancy reports
   - Revenue and booking analytics

## Configuration

Server configuration (port, timeouts) should be managed through environment variables and MCP configuration files.
