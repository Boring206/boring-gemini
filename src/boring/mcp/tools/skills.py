# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Skills Management Tools (Universal System).

Allows the Agent to autonomously install, manage, and use Agent Skills across platforms
(Gemini CLI, Claude Code, Antigravity).

Features:
- Legacy: External Catalog Search (boring_skills_install)
- New (V12.3): Universal Skill Loader (boring_skill_discover/activate)
- New (V12.3): Auto-Sync to Client directories
"""

import logging
import shutil
from pathlib import Path
from typing import Annotated

from pydantic import Field

from ...services.audit import audited
from ...skills.sync_manager import SyncManager
from ...skills.universal_loader import UniversalSkillLoader
from ...skills_catalog import (
    SKILLS_CATALOG,
    format_skill_for_display,
    is_trusted_url,
    search_skills,
)
from ..instance import mcp

logger = logging.getLogger(__name__)

# --- Legacy Catalog Tools (External Resources) ---


@mcp.tool(
    description="安裝 Agent Skill (Install skill). 適合: 'Install extensions', '我需要 Claude template'.",
    annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": False},
)
@audited
def boring_skills_install(
    name: Annotated[
        str,
        Field(description="Name of the skill to install from catalog OR a trusted URL"),
    ],
) -> dict:
    """
    Install a Skill or Extension from the catalog (External Resource).
    For Universal Skills (Markdown), use boring_skill_download instead.
    """
    # 1. Check for URL input
    if name.lower().startswith(("http://", "https://")):
        return boring_skill_download(url=name)

    # 2. Find skill in catalog
    match = None
    for skill in SKILLS_CATALOG:
        if skill.name.lower() == name.lower():
            match = skill
            break

    if not match:
        return {
            "status": "error",
            "message": f"Skill '{name}' not found in catalog. Use `boring_skills_search` to find available skills.",
        }

    # If it has a repo URL, divert to download tool
    if match.repo_url:
        return boring_skill_download(url=match.repo_url, name_override=match.name)

    return {
        "status": "success",
        "message": f"Skill **{match.name}** info:\n\n{match.description}\nURL: {match.repo_url}\n\nInstall command: `{match.install_command}`",
        "data": {"skill": match.name, "url": match.repo_url},
    }


@mcp.tool(
    description="列出可用 Skills (List skills). 適合: 'List catalog', '有什麼 extensions', 'Show skills'.",
    annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
)
@audited
def boring_skills_list(
    platform: Annotated[str, Field(description="Filter by platform")] = "all",
) -> dict:
    """List all available Agent Skills in the catalog."""
    skills = search_skills(query="", platform=platform, limit=100)
    display_text = [f"## Available Skills in Catalog ({len(skills)})", ""]
    for skill in skills:
        display_text.append(f"- **{skill.name}** (`{skill.platform}`): {skill.description}")
    return {"status": "success", "message": "\n".join(display_text)}


@mcp.tool(
    description="搜尋 Skills (Search skills). 適合: 'Search templates', '找電商 skill', 'Find extension'.",
    annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
)
@audited
def boring_skills_search(
    query: Annotated[str, Field(description="Search keywords")],
    platform: Annotated[str, Field(description="Filter by platform")] = "all",
) -> dict:
    """Search for Agent Skills in the catalog."""
    matches = search_skills(query=query, platform=platform)
    if not matches:
        return {"status": "success", "message": f"No skills found for query '{query}'."}

    display_text = [f"## Found {len(matches)} Skills for '{query}'", ""]
    for skill in matches:
        display_text.append(format_skill_for_display(skill))
    return {"status": "success", "message": "\n".join(display_text)}


@mcp.tool(
    description="智能推薦 Skills (Smart Recommend). 根據專案內容自動推薦適合的 Skills。",
    annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
)
@audited
def boring_skills_recommend(project_path: str = ".", online: bool = False) -> dict:
    """
    Recommend skills based on project analytics.

    Args:
        project_path: Path to analyze
        online: If True, uses DuckDuckGo to search GitHub for additional skills (AI Web Search).
    """
    try:
        # Lazy import
        from ...loop.workflow_evolver import ProjectContextDetector

        path = Path(project_path)
        detector = ProjectContextDetector(path)
        context = detector.analyze()

        # Build keywords
        keywords = {context.project_type}
        if "docker" in str(context.detected_files).lower():
            keywords.add("docker")
        if "package.json" in str(context.detected_files):
            keywords.add("node")
        if "pyproject.toml" in str(context.detected_files) or "requirements.txt" in str(
            context.detected_files
        ):
            keywords.add("python")

        display_text = [
            f"## 🤖 Recommended Skills for '{context.project_type}' Project",
            f"Detected Context: {', '.join(keywords)}",
            "",
        ]

        # 1. Local Catalog Search
        combined_results = {}
        for kw in keywords:
            if kw == "unknown":
                continue
            matches = search_skills(query=kw, limit=3)
            for match in matches:
                if match.name not in combined_results:
                    combined_results[match.name] = match

        if combined_results:
            display_text.append("### 📚 From Catalog")
            for skill in combined_results.values():
                display_text.append(format_skill_for_display(skill, include_install=False))
                display_text.append(f"Install: `boring_skills_install('{skill.name}')`")
                display_text.append("---")
        else:
            display_text.append("_(No exact matches in local catalog)_")

        # 2. Online Search (AI Web Search)
        if online:
            try:
                from duckduckgo_search import DDGS

                display_text.append("\n### 🌐 AI Web Search Results (DuckDuckGo)")

                # Construct Query
                # e.g. 'site:github.com "SKILL.md" python fastapi agent'
                query_terms = list(keywords)
                if "unknown" in query_terms:
                    query_terms.remove("unknown")
                query = f'site:github.com "SKILL.md" agent skill {" ".join(query_terms)}'

                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=4))

                if results:
                    for res in results:
                        title = res.get("title", "Unknown Title")
                        url = res.get("href", "#")
                        body = res.get("body", "")

                        display_text.append(f"#### {title}")
                        display_text.append(f"🔗 {url}")
                        display_text.append(f"_{body}_")
                        display_text.append(f"Install: `boring_skill_download('{url}')`")
                        display_text.append("---")
                else:
                    display_text.append("_(No relevant results found online)_")

            except ImportError:
                display_text.append("\n⚠️ `duckduckgo-search` not installed. Cannot search online.")
            except Exception as e:
                display_text.append(f"\n⚠️ Online search failed: {e}")

        return {"status": "success", "message": "\n".join(display_text)}

    except ImportError:
        return {"status": "error", "message": "Project Analysis module not available."}
    except Exception as e:
        return {"status": "error", "message": f"Recommendation failed: {str(e)}"}


@mcp.tool(description="Discover local skills across all platforms (.gemini, .claude, .boring)")
@audited
def boring_skill_discover(project_path: str = ".") -> dict:
    """Scan local skill directories and return available skills."""
    loader = UniversalSkillLoader(project_path)
    skills = loader.discover_all()

    if not skills:
        return {"status": "success", "message": "No local skills found."}

    text = ["## 🧠 Local Universal Skills", ""]
    for skill in skills:
        text.append(f"- **{skill.name}** (`{skill.platform}`): {skill.description}")

    return {
        "status": "success",
        "message": "\n".join(text),
        "data": {"skills": [s.name for s in skills]},
    }


@mcp.tool(description="Activate a Universal Skill and inject its instructions")
@audited
def boring_skill_activate(skill_name: str, project_path: str = ".") -> dict:
    """Load the content of a skill and return it for context injection."""
    loader = UniversalSkillLoader(project_path)
    skill = loader.load_by_name(skill_name)

    if not skill:
        return {"status": "error", "message": f"Skill '{skill_name}' not found."}

    return {
        "status": "success",
        "message": f"✅ Activated Skill: **{skill.name}**\n\n{skill.description}",
        "data": {"content": skill.activation_prompt, "name": skill.name},
    }


@mcp.tool(description="Download a skill from URL and sync to clients")
@audited
def boring_skill_download(
    url: str, name_override: str | None = None, project_path: str = "."
) -> dict:
    """
    Download a skill from a trusted URL (GitHub/Gist) to .boring/skills.
    Automatically syncs to .gemini/ and .claude/ directories.
    """
    if not is_trusted_url(url):
        return {
            "status": "error",
            "message": f"❌ URL not trusted: {url}. Trusted: GitHub, SkillsMP.",
        }

    # Logic to clone or download file
    dest_name = name_override or url.split("/")[-1].replace(".git", "").replace(".md", "")
    project_root = Path(project_path)
    hub_dir = project_root / ".boring" / "skills" / dest_name

    # Handle GitHub Tree URLs (Subdirectory Sparse Checkout)
    # Format: https://github.com/user/repo/tree/branch/path/to/dir
    is_sparse = False
    repo_url = url
    sparse_path = ""
    branch = "main"  # Default fallback

    # Handle GitHub Blob URLs (File Links) - Convert to Tree/Dir
    if "github.com" in url and "/blob/" in url:
        url = url.replace("/blob/", "/tree/")
        # Strip filename to get parent directory
        if url.endswith(".md") or url.endswith(".py") or url.endswith(".txt"):
            url = "/".join(url.split("/")[:-1])

    # Handle SkillsMP URLs (UX Improvement)
    if "skillsmp.com" in url:
        return {
            "status": "error",
            "message": "⚠️ **SkillsMP Download**: Direct download is protected by Cloudflare.\n👉 Please open the link, find the **'View on GitHub'** button, and use that GitHub URL instead.",
        }

    if "github.com" in url and "/tree/" in url:
        try:
            # Parse: https://github.com/user/repo /tree/ branch / path
            parts = url.split("/tree/")
            repo_url = parts[0]
            if repo_url.endswith(".git"):
                repo_url = repo_url[:-4]

            rest = parts[1].split("/", 1)
            branch = rest[0]
            if len(rest) > 1:
                sparse_path = rest[1]
                is_sparse = True
                # Update dest_name if not overridden (use subdir name)
                if not name_override:
                    # If sparse path ends with SKILL.md (shouldn't happen due to blob fix above, but safe check)
                    clean_path = sparse_path
                    if clean_path.endswith("/SKILL.md"):
                        clean_path = clean_path[:-9]

                    dest_name = clean_path.split("/")[-1]
                    # If empty (e.g. root), use repo name
                    if not dest_name:
                        dest_name = repo_url.split("/")[-1]

                    hub_dir = project_root / ".boring" / "skills" / dest_name
        except Exception as e:
            logger.warning(f"Failed to parse GitHub tree URL: {e}")

    # Early exit if skill already downloaded
    if hub_dir.exists():
        return {
            "status": "info",
            "message": f"Skill '{dest_name}' already exists. Use `boring_skill_sync('{dest_name}')` to update.",
            "data": {"path": str(hub_dir)},
        }

    try:
        import subprocess

        if is_sparse:
            # Sparse Checkout Strategy
            hub_dir.mkdir(parents=True, exist_ok=True)

            # 1. Clone with --sparse
            cmd_clone = [
                "git",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                "--branch",
                branch,
                repo_url,
                str(hub_dir),
            ]
            subprocess.run(cmd_clone, check=True, capture_output=True)

            # 2. Set sparse-checkout path
            cmd_sparse = ["git", "sparse-checkout", "set", sparse_path]
            subprocess.run(cmd_sparse, cwd=str(hub_dir), check=True, capture_output=True)

            # 3. Move contents from subdir to root of skill dir (Optional but cleaner)
            # Actually, standard sparse checkout keeps the directory structure (subdir/inside/repo)
            # We might want to "flatten" it if the user expects the skill at root.
            # But UniversalLoader scans deeply? No, it scans 1 level deep.
            # So we MUST flatten it if the skill is deep nested.

            # Move content: hub_dir/sparse_path/* -> hub_dir/
            src_subdir = hub_dir / sparse_path
            if src_subdir.exists():
                for item in src_subdir.iterdir():
                    shutil.move(str(item), str(hub_dir))
                # Remove empty parent dirs
                # (Simple approach: just leave them or try to clean up)
                shutil.rmtree(str(hub_dir / sparse_path.split("/")[0]), ignore_errors=True)

        else:
            # Standard Full Clone
            cmd = ["git", "clone", "--depth", "1", url, str(hub_dir)]
            subprocess.run(cmd, check=True, capture_output=True)

        # Auto Sync
        syncer = SyncManager(project_root)
        targets = syncer.sync_skill(dest_name)

        # Cleanup "Garbage" Files (User Requested)
        # Keep only standard skill structure + git metadata
        ALLOWED_DIRS = {"scripts", "examples", "resources", "references", "assets", ".git"}
        ALLOWED_FILES = {"SKILL.md", "README.md"}

        cleaned_items = []
        for item in hub_dir.iterdir():
            is_allowed = False
            if item.is_dir():
                if item.name in ALLOWED_DIRS:
                    is_allowed = True
            else:  # File
                if item.name in ALLOWED_FILES or item.name.startswith("LICENSE"):
                    is_allowed = True

            if not is_allowed:
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    cleaned_items.append(item.name)
                except Exception as e:
                    logger.warning(f"Failed to clean {item.name}: {e}")

        msg = f"✅ Downloaded **{dest_name}**"
        if is_sparse:
            msg += " (Sparse)"
        if cleaned_items:
            msg += f"\n🧹 Cleaned {len(cleaned_items)} garbage files."

        return {
            "status": "success",
            "message": msg + "\nSynced to:\n" + "\n".join(targets),
            "data": {"path": str(hub_dir), "synced": targets, "cleaned": cleaned_items},
        }
    except Exception as e:
        return {"status": "error", "message": f"Download failed: {str(e)}"}


@mcp.tool(description="Create a new skill from a description")
@audited
def boring_skill_create(name: str, goal: str, project_path: str = ".") -> dict:
    """Template for creating a new skill."""
    template = f"""---
name: {name}
description: {goal}
---

# {name.title()}

## Instructions
1. [Add steps here]
"""
    path = Path(project_path) / ".boring" / "skills" / name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(template, encoding="utf-8")

    syncer = SyncManager(Path(project_path))
    syncer.sync_skill(name)

    return {
        "status": "success",
        "message": f"Created template for **{name}** at {path}",
        "data": {"path": str(path)},
    }


# --- Dynamic Skill Injection (Role-Based) ---

SKILL_CATEGORIES = {
    "Architect": ["boring_speckit_plan", "boring_speckit_tasks"],
    "Surveyor": ["boring_rag_search", "boring_rag_graph"],
    "Watcher": ["boring_commit", "boring_checkpoint"],
    "Healer": ["boring_fix", "boring_verify"],
    "Sage": ["boring_skill_discover", "boring_skill_activate", "boring_skill_download"],
}


@mcp.tool(description="啟用技能角色 (Activate Skill Role).")
@audited
def boring_active_skill(skill_name: str) -> dict:
    """Activate a skill role (Architect, Surveyor, etc)."""
    skill_key = skill_name.strip().title()
    if skill_key not in SKILL_CATEGORIES:
        return {"status": "error", "message": f"Unknown role '{skill_name}'."}

    tools = SKILL_CATEGORIES[skill_key]
    injected = []
    for t in tools:
        if mcp.inject_tool(t):
            injected.append(t)

    return {"status": "success", "message": f"Activated {skill_key} with {len(injected)} tools."}


@mcp.tool(description="Reset injected skills.")
@audited
def boring_reset_skills() -> dict:
    """Clear injected tools."""
    count = mcp.reset_injected_tools()
    return {"status": "success", "message": f"Reset {count} tools."}
