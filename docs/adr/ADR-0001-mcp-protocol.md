# ADR-0001: Use MCP Protocol for Tool Integration

**Date**: 2025-12-15

**Status**: Accepted

**Deciders**: @Boring206

**Tags**: architecture, integration, mcp

---

## Context

### Problem Statement
Boring-Gemini needs a standardized way to integrate with various AI coding assistants (Cursor, Claude Desktop, VS Code Copilot) and provide consistent tool interfaces across different platforms.

### Goals
- Provide consistent tool interface across multiple clients
- Enable easy discovery and invocation of capabilities
- Support both local and remote deployment
- Maintain backward compatibility with existing workflows

### Non-Goals
- Creating a custom protocol from scratch
- Supporting non-AI coding assistant integrations

## Decision

We will adopt the **Model Context Protocol (MCP)** as the primary integration method for Boring-Gemini.

### Approach
1. Implement MCP server in `src/boring/mcp/`
2. Expose all 98+ tools via MCP interfaces
3. Support both FastMCP (lite) and full MCP with vector capabilities
4. Maintain CLI compatibility for legacy workflows

### Implementation Plan
1. ✅ Create MCP server architecture
2. ✅ Implement tool router with natural language routing
3. ✅ Add Smithery deployment support
4. ✅ Document MCP configuration for all clients
5. ✅ Maintain backward compatibility with CLI mode

### Acceptance Criteria
- [x] MCP server runs successfully
- [x] All major tools accessible via MCP
- [x] Integration with Cursor/Claude Desktop works
- [x] Smithery deployment functional
- [x] Documentation complete

## Consequences

### Positive Consequences
- **Standardization**: Single protocol for all AI assistant integrations
- **Discoverability**: Tools automatically discoverable by clients
- **Community**: Benefit from growing MCP ecosystem
- **Deployment**: Easy deployment via Smithery
- **Maintenance**: Centralized tool management

### Negative Consequences
- **Dependency**: Relies on MCP protocol stability
- **Learning Curve**: Team must learn MCP protocol
- **Complexity**: Additional layer vs direct API integration
- **CLI Deprecation**: CLI mode becomes secondary

### Risks
- MCP protocol changes (Mitigation: Version pinning, adaptation layer)
- Client compatibility issues (Mitigation: Multi-client testing)
- Performance overhead (Mitigation: Caching, optimization)

## Alternatives Considered

### Alternative 1: Direct API Integration
**Pros:**
- Full control over protocol
- No external dependencies
- Maximum performance

**Cons:**
- Reimplementing standard protocols
- Multiple integrations to maintain
- No ecosystem benefits

**Why not chosen:**
MCP provides standardization benefits that outweigh custom implementation control.

### Alternative 2: LSP (Language Server Protocol)
**Pros:**
- Well-established protocol
- Excellent IDE integration
- Rich tooling ecosystem

**Cons:**
- Designed for language features, not AI tools
- Doesn't fit AI assistant use case well
- Overkill for our needs

**Why not chosen:**
LSP is optimized for different use cases; MCP is purpose-built for AI integrations.

### Alternative 3: REST API
**Pros:**
- Simple and well-understood
- Language-agnostic
- Easy to test

**Cons:**
- No standardized discovery mechanism
- Manual integration for each client
- No built-in streaming support

**Why not chosen:**
Lack of standardization and discovery makes it less suitable than MCP.

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://pypi.org/project/fastmcp/)
- [Smithery Platform](https://smithery.ai/)
- [Issue #45: MCP Integration](https://github.com/Boring206/boring-gemini/issues/45)

## Notes

This decision enabled the "Vibe Coder" experience by providing a consistent interface across all platforms. The natural language router (built on top of MCP) further enhanced usability.

---

## Changelog

| Date | Status Change | Notes |
|------|--------------|-------|
| 2025-12-15 | Proposed | Initial draft |
| 2025-12-20 | Accepted | Implemented and validated |
| 2026-01-01 | Updated | Added Smithery deployment |
