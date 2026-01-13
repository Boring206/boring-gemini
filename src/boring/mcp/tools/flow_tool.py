# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

from pydantic import Field

from ...audit import audited
from ...core.config import settings
from ...types import BoringResult, create_error_result, create_success_result
from ..utils import check_rate_limit, detect_project_root


@audited
def boring_flow(
    instruction: Annotated[
        str, Field(description="指令或目標 (例如: '建立登入頁面', 'make a dashboard')")
    ] = None,
    project_path: Annotated[str, Field(description="專案路徑（選填）")] = None,
) -> BoringResult:
    """
    🐉 Boring Flow (One Dragon) - 究極自動化工作流。

    這是 Vibe Coder 的核心引擎，自動處理整個軟體開發生命週期：
    1. Setup: 自動初始化專案
    2. Design: 自動規劃架構與任務 (整合 Skill Advisor)
    3. Build: 自動執行開發 Loop (整合 Agent Loop)
    4. Polish: 自動驗收與優化 (整合 Vibe Check)

    使用時機:
    - 當你想把專案從頭做到尾，或者不知道下一步該做什麼時。
    - 當你有模糊的指令 (如 '弄漂亮點') 時，此工具會自動解析。

    Args:
        instruction: 您的指令。如果是 Design 階段，這就是您的目標。
    """
    allowed, msg = check_rate_limit("boring_flow")
    if not allowed:
        return create_error_result(f"⏱️ Rate limited: {msg}")

    # Detect Root
    root = detect_project_root(project_path)
    if not root:
        # Fallback to default if detection fails
        root = settings.PROJECT_ROOT

    # [ONE DRAGON WIRING]
    # Instantiate the Graph Engine
    from ...flow.graph import FlowGraph
    from ...flow.nodes.architect import ArchitectNode
    from ...flow.nodes.base import FlowContext
    from ...flow.nodes.builder import BuilderNode
    from ...flow.nodes.evolver import EvolverNode
    from ...flow.nodes.healer import HealerNode
    from ...flow.nodes.polish import PolishNode

    context = FlowContext(
        project_root=root,
        user_goal=instruction or "Improve the project"
    )

    graph = FlowGraph(context)

    # Add Nodes
    graph.add_node(ArchitectNode(), is_start=True)
    graph.add_node(BuilderNode())
    graph.add_node(HealerNode())
    graph.add_node(PolishNode())
    graph.add_node(EvolverNode())

    # Execute
    try:
        final_msg = graph.run()

        return create_success_result(
            message=final_msg,
            data={"status": "success", "graph_output": final_msg}
        )
    except Exception as e:
        return create_error_result(f"🐉 Dragon Stumbled: {str(e)}")


# Register Tool
from ..instance import MCP_AVAILABLE, mcp

if MCP_AVAILABLE and mcp is not None:
    mcp.tool(
        description="🐉 啟動 Boring Flow (One Dragon) - 究極自動化工作流",
        annotations={"readOnlyHint": False, "openWorldHint": True},  # Side effects expected
    )(boring_flow)
