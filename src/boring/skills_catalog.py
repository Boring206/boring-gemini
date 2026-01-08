# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Skills Catalog - 推薦 Gemini/Claude Skills 資源的知識庫。

100分架構設計：
- 資料與邏輯分離
- 支援多語言關鍵字 (中英文)
- 按平台篩選
- 易於社群貢獻擴充
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SkillResource:
    """一個 Skill 資源的完整描述。"""

    name: str
    platform: str  # "gemini" | "claude" | "both"
    repo_url: str
    description: str
    description_zh: str
    keywords: list[str]  # 用於匹配的關鍵字
    install_command: Optional[str] = None
    stars: Optional[int] = None  # GitHub stars (optional)


# Skills 資料庫 - 社群可以 PR 擴充這個清單
SKILLS_CATALOG: list[SkillResource] = [
    # === Gemini CLI ===
    SkillResource(
        name="awesome-gemini-cli",
        platform="gemini",
        repo_url="https://github.com/Piebald-AI/awesome-gemini-cli",
        description="Curated list of Gemini CLI tools, extensions, MCP servers, and tutorials.",
        description_zh="🌟 Gemini CLI 資源大全：工具、Extensions、MCP Server、教學。",
        keywords=["gemini", "all", "general", "extensions", "mcp", "通用", "全部"],
    ),
    SkillResource(
        name="awesome-gemini-cli-extensions",
        platform="gemini",
        repo_url="https://github.com/Piebald-AI/awesome-gemini-cli-extensions",
        description="Extensions for Gemini CLI - custom prompts, commands, themes.",
        description_zh="Gemini CLI Extensions 專區，可用 `gemini extension install` 安裝。",
        keywords=["extensions", "theme", "commands", "主題", "指令"],
        install_command="gemini extension install <git-url>",
    ),
    # === Claude Skills ===
    SkillResource(
        name="awesome-claude-skills",
        platform="claude",
        repo_url="https://github.com/travisvn/awesome-claude-skills",
        description="Curated collection of Claude Skills, resources, and tools for customizing workflows.",
        description_zh="🌟 Claude Skills 資源總表，含官方與社群貢獻。",
        keywords=["claude", "all", "general", "通用", "全部"],
    ),
    SkillResource(
        name="awesome-claude-skills (VoltAgent)",
        platform="claude",
        repo_url="https://github.com/VoltAgent/awesome-claude-skills",
        description="Awesome collection with recent 2026 updates, well-categorized.",
        description_zh="分類清楚的 Claude Skills 清單，2026 年持續更新。",
        keywords=["claude", "categorized", "分類"],
    ),
    SkillResource(
        name="claude-code-templates",
        platform="claude",
        repo_url="https://github.com/davila7/claude-code-templates",
        description="CLI tool with 100+ components: agents, commands, MCPs, project templates. Has web UI!",
        description_zh="🔥 100+ 元件的 CLI 工具，含 Web 介面瀏覽器，超強！",
        keywords=["templates", "cli", "agents", "mcp", "範本", "工具"],
        install_command="npx claude-code-templates",
    ),
    SkillResource(
        name="awesome-claude-code",
        platform="claude",
        repo_url="https://github.com/hesreallyhim/awesome-claude-code",
        description="Slash-commands, CLAUDE.md files, CLI tools, workflows for Claude Code.",
        description_zh="Claude Code 專用：Slash Commands、Workflows、CLI 工具。",
        keywords=["claude code", "slash", "commands", "workflow", "工作流"],
    ),
    # === 用途導向 ===
    SkillResource(
        name="claude-crash-course-templates",
        platform="claude",
        repo_url="https://github.com/bhancockio/claude-crash-course-templates",
        description="Essential templates: Master Plan, Project Stub, Full Code Implementation.",
        description_zh="快速上手範本：專案規劃、骨架生成、完整實作。",
        keywords=["starter", "beginner", "plan", "新手", "入門", "規劃"],
    ),
    # === 專業領域 ===
    SkillResource(
        name="Document Skills (Word/Excel/PDF)",
        platform="claude",
        repo_url="https://github.com/anthropics/claude-code",
        description="Official skills for creating/editing Word, Excel, PowerPoint, PDF files.",
        description_zh="文件處理 Skills：Word、Excel、PPT、PDF 讀寫。",
        keywords=["document", "word", "excel", "pdf", "文件", "報表"],
    ),
    # === 電商/Dashboard/Chat 需求導向 ===
    SkillResource(
        name="E-commerce Skills (Search in Awesome Lists)",
        platform="both",
        repo_url="https://github.com/travisvn/awesome-claude-skills",
        description="Search 'ecommerce' or 'shop' in awesome lists for specialized skills.",
        description_zh="🛒 電商相關：請在 Awesome Lists 搜尋 'ecommerce' 或 'shop'。",
        keywords=["ecommerce", "shop", "電商", "購物", "商城"],
    ),
    SkillResource(
        name="Dashboard/Admin Skills",
        platform="both",
        repo_url="https://github.com/davila7/claude-code-templates",
        description="Use claude-code-templates CLI to browse admin/dashboard templates.",
        description_zh="🖥️ 後台管理：使用 claude-code-templates CLI 瀏覽。",
        keywords=["dashboard", "admin", "後台", "管理", "監控"],
    ),
    SkillResource(
        name="AI Chat / LLM Integration",
        platform="both",
        repo_url="https://github.com/travisvn/awesome-claude-skills",
        description="Search 'chat' or 'llm' in awesome lists for AI chat templates.",
        description_zh="🤖 AI 聊天：請在 Awesome Lists 搜尋 'chat' 或 'llm'。",
        keywords=["chat", "ai", "gpt", "llm", "聊天", "機器人", "對話"],
    ),
]


def search_skills(
    query: str,
    platform: str = "all",
    limit: int = 5,
) -> list[SkillResource]:
    """
    根據關鍵字搜尋 Skills 資源。

    Args:
        query: 搜尋關鍵字 (中英文皆可)
        platform: 篩選平台 ("gemini", "claude", "all")
        limit: 回傳數量上限

    Returns:
        匹配的 SkillResource 清單
    """
    query_lower = query.lower().strip()
    results = []

    for skill in SKILLS_CATALOG:
        # 平台篩選
        if platform != "all":
            if skill.platform != platform and skill.platform != "both":
                continue

        # 關鍵字匹配
        score = 0
        for kw in skill.keywords:
            if kw in query_lower or query_lower in kw:
                score += 2

        # 名稱/描述匹配
        if query_lower in skill.name.lower():
            score += 3
        if query_lower in skill.description.lower():
            score += 1
        if query_lower in skill.description_zh:
            score += 1

        if score > 0:
            results.append((score, skill))

    # 排序並回傳
    results.sort(key=lambda x: x[0], reverse=True)
    return [skill for _, skill in results[:limit]]


def format_skill_for_display(skill: SkillResource, include_install: bool = True) -> str:
    """格式化單一 Skill 為人類可讀的字串。"""
    lines = [
        f"### {skill.name}",
        f"📦 Platform: `{skill.platform}`",
        f"🔗 {skill.repo_url}",
        "",
        f"**{skill.description_zh}**",
        f"_{skill.description}_",
    ]

    if include_install and skill.install_command:
        lines.append(f"\n```bash\n{skill.install_command}\n```")

    return "\n".join(lines)
