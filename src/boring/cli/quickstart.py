# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Quick Start Orchestrator for Vibe Coders.

Provides a one-command experience to go from idea to working code.
"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# --- Built-in Project Templates ---
TEMPLATES = {
    "fastapi-auth": {
        "name": "FastAPI 認證服務",
        "description": "包含 JWT 認證、用戶管理的 REST API",
        "stack": "FastAPI + SQLAlchemy + PostgreSQL",
        "prompt_template": """建立一個 FastAPI 認證服務，包含：
1. 用戶註冊和登入 API
2. JWT Token 認證
3. 密碼雜湊 (bcrypt)
4. SQLAlchemy ORM 模型
5. Pydantic schemas
6. 基本的 CRUD 操作""",
    },
    "nextjs-dashboard": {
        "name": "Next.js 管理後台",
        "description": "現代化的管理儀表板 UI",
        "stack": "Next.js 14 + Tailwind CSS + shadcn/ui",
        "prompt_template": """建立一個 Next.js 管理後台，包含：
1. App Router 結構
2. 響應式側邊欄導航
3. 儀表板首頁 (統計卡片)
4. 數據表格頁面
5. 暗色模式支援
6. Tailwind CSS 樣式""",
    },
    "cli-tool": {
        "name": "Python CLI 工具",
        "description": "使用 Typer 的命令列工具",
        "stack": "Python + Typer + Rich",
        "prompt_template": """建立一個 Python CLI 工具，包含：
1. Typer CLI 框架
2. Rich 美化輸出
3. 多個子命令
4. 配置檔支援 (TOML/YAML)
5. 完整的 --help 說明
6. 單元測試""",
    },
    "vue-spa": {
        "name": "Vue 3 單頁應用",
        "description": "現代化的 Vue 3 + Vite 應用",
        "stack": "Vue 3 + Vite + Pinia + Vue Router",
        "prompt_template": """建立一個 Vue 3 單頁應用，包含：
1. Vite 建構工具
2. Vue Router 路由
3. Pinia 狀態管理
4. Composition API
5. 基本頁面結構
6. API 調用示範""",
    },
}


class QuickStartOrchestrator:
    """
    Orchestrates the full Vibe Coding workflow:
    Clarify → Plan → Execute → Verify
    """

    def __init__(self, idea: str, template: Optional[str] = None, auto_approve: bool = False):
        self.idea = idea
        self.template = template
        self.auto_approve = auto_approve
        self.plan = None
        self.tasks = []

    def get_effective_prompt(self) -> str:
        """Get the prompt, using template if specified."""
        if self.template and self.template in TEMPLATES:
            template_data = TEMPLATES[self.template]
            return template_data["prompt_template"]
        return self.idea

    def show_welcome(self):
        """Display welcome message."""
        console.print()
        console.print(
            Panel.fit(
                f"[bold cyan]🚀 Vibe Coding 模式啟動[/bold cyan]\n\n"
                f"[yellow]你的想法：[/yellow] {self.idea}\n"
                + (
                    f"[green]使用模板：[/green] {TEMPLATES[self.template]['name']}"
                    if self.template and self.template in TEMPLATES
                    else ""
                ),
                title="Quick Start",
                border_style="cyan",
            )
        )
        console.print()

    def run_clarify_phase(self) -> dict:
        """Phase 1: Clarify requirements using SpecKit."""
        console.print("[bold]Phase 1: 需求釐清[/bold]")

        # Import SpecKit tools
        try:
            from boring.speckit import run_speckit_clarify

            questions = run_speckit_clarify(self.get_effective_prompt())
            return {"status": "success", "questions": questions}
        except ImportError:
            # Fallback if SpecKit not available
            console.print("  [dim]跳過釐清階段 (SpecKit 未安裝)[/dim]")
            return {"status": "skipped"}
        except Exception as e:
            console.print(f"  [yellow]釐清階段出錯: {e}[/yellow]")
            return {"status": "error", "error": str(e)}

    def run_plan_phase(self) -> dict:
        """Phase 2: Generate implementation plan."""
        console.print("[bold]Phase 2: 生成計畫[/bold]")

        try:
            from boring.speckit import run_speckit_plan

            self.plan = run_speckit_plan(self.get_effective_prompt())
            console.print("  [green]✓[/green] 實作計畫已生成")
            return {"status": "success", "plan": self.plan}
        except ImportError:
            # Generate a basic plan structure
            self.plan = {
                "goal": self.idea,
                "steps": [
                    "1. 建立專案結構",
                    "2. 實作核心功能",
                    "3. 加入測試",
                    "4. 驗證品質",
                ],
            }
            console.print("  [green]✓[/green] 基本計畫已生成")
            return {"status": "success", "plan": self.plan}
        except Exception as e:
            console.print(f"  [red]✗[/red] 計畫生成失敗: {e}")
            return {"status": "error", "error": str(e)}

    def run_execute_phase(self) -> dict:
        """Phase 3: Execute using Multi-Agent system."""
        console.print("[bold]Phase 3: 執行開發[/bold]")

        try:
            from boring.agents import MultiAgentRunner

            runner = MultiAgentRunner()
            result = runner.run(self.get_effective_prompt())
            console.print("  [green]✓[/green] 開發完成")
            return {"status": "success", "result": result}
        except ImportError:
            console.print("  [yellow]⚠[/yellow] Multi-Agent 系統未安裝，請使用 MCP 工具執行")
            console.print(f"  [dim]建議執行: boring_multi_agent(task='{self.idea}')[/dim]")
            return {"status": "manual_required"}
        except Exception as e:
            console.print(f"  [red]✗[/red] 執行失敗: {e}")
            return {"status": "error", "error": str(e)}

    def run_verify_phase(self) -> dict:
        """Phase 4: Verify the results."""
        console.print("[bold]Phase 4: 驗證結果[/bold]")

        try:
            from boring.core import CodeVerifier

            verifier = CodeVerifier()
            result = verifier.verify(level="STANDARD")
            if result.get("passed", False):
                console.print("  [green]✓[/green] 驗證通過")
            else:
                console.print("  [yellow]⚠[/yellow] 發現一些問題，建議執行 boring auto-fix")
            return {"status": "success", "result": result}
        except ImportError:
            console.print("  [dim]跳過驗證 (CodeVerifier 未安裝)[/dim]")
            return {"status": "skipped"}
        except Exception as e:
            console.print(f"  [yellow]驗證出錯: {e}[/yellow]")
            return {"status": "error", "error": str(e)}

    def run(self) -> dict:
        """Run the complete Quick Start workflow."""
        self.show_welcome()

        results = {
            "idea": self.idea,
            "template": self.template,
            "phases": {},
        }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Phase 1: Clarify
            task = progress.add_task("釐清需求...", total=None)
            results["phases"]["clarify"] = self.run_clarify_phase()
            progress.remove_task(task)

            # Phase 2: Plan
            task = progress.add_task("生成計畫...", total=None)
            results["phases"]["plan"] = self.run_plan_phase()
            progress.remove_task(task)

            # Show plan and wait for approval if not auto-approve
            if not self.auto_approve and self.plan:
                console.print()
                console.print(Panel(str(self.plan), title="實作計畫", border_style="blue"))
                # In CLI mode, we continue automatically
                # In interactive mode, this would pause for user input

            # Phase 3: Execute
            task = progress.add_task("執行開發...", total=None)
            results["phases"]["execute"] = self.run_execute_phase()
            progress.remove_task(task)

            # Phase 4: Verify
            task = progress.add_task("驗證結果...", total=None)
            results["phases"]["verify"] = self.run_verify_phase()
            progress.remove_task(task)

        # Summary
        console.print()
        console.print(
            Panel.fit(
                "[bold green]✅ Quick Start 完成！[/bold green]\n\n"
                "後續建議：\n"
                "• 執行 `boring verify --level FULL` 進行完整驗證\n"
                "• 執行 `boring auto-fix` 自動修復問題\n"
                "• 查看生成的程式碼並根據需要調整",
                title="完成",
                border_style="green",
            )
        )

        return results


def list_templates() -> list[dict]:
    """List all available templates."""
    return [
        {"id": tid, "name": t["name"], "description": t["description"], "stack": t["stack"]}
        for tid, t in TEMPLATES.items()
    ]


def get_template(template_id: str) -> Optional[dict]:
    """Get a specific template by ID."""
    return TEMPLATES.get(template_id)
