# Boring Registry Schema Specification

> **Version**: 1.0.0  
> **Status**: Draft  
> **Date**: 2026-01-18

This document defines the structure of `registry.json`, which is the index file for the decentralized Boring-Gemini plugin ecosystem.

## Core Philosophy
- **Index Only**: The Registry only stores indices, not code.
- **Git-Native**: Relies on Git URLs as the single "Source of Truth".
- **Decentralized**: Anyone can fork this registry and maintain their own list.

## JSON Structure

```json
{
  "schema_version": "1.0",
  "last_updated": "YYYY-MM-DD",
  "maintainer": "Boring Team",
  "plugins": [
    {
      "id": "namespace/plugin-name",
      "type": "plugin",
      "name": "Display Name",
      "description": "Short description",
      "repo": "https://github.com/user/repo",
      "branch": "main",
      "path": "/",
      "min_core_version": "15.0.0",
      "tags": ["tag1", "tag2"],
      "verified": false
    }
  ]
}
```

## Field Definitions

### Root Object
| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Registry format version (e.g. "1.0") |
| `last_updated` | string | Last updated date (ISO 8601) |
| `plugins` | array | List of plugins |

### Plugin Object
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier, format `namespace/name`. Usually corresponds to `github_user/repo_name`. |
| `type` | string | Yes | Resource type: `plugin`, `workflow`, `brain`, `theme` |
| `name` | string | Yes | Human-readable display name |
| `description` | string | Yes | Short description (suggested < 100 characters) |
| `repo` | string | Yes | Full Git Repository URL (HTTPS) |
| `branch` | string | No | Specific branch, defaults to `main` or `master` |
| `path` | string | No | Subdirectory path within the repository, defaults to root `/` |
| `min_core_version` | string | No | Minimum supported boring-gemini version (SemVer) |
| `tags` | array | No | Keywords for search |
| `verified` | bool | No | (Official use) Whether it has passed official security audit |

## Example

```json
{
  "schema_version": "1.0",
  "last_updated": "2026-01-18",
  "plugins": [
    {
      "id": "boring/security-scanner",
      "type": "plugin",
      "name": "Security Scanner",
      "description": "Advanced static analysis for Python code security.",
      "repo": "https://github.com/boring-plugins/security-scanner",
      "min_core_version": "15.0.0",
      "tags": ["security", "audit", "linter"],
      "verified": true
    }
  ]
}
```
