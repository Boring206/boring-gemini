# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Vibe Session Tools - Human-Aligned AI Coding Workflow (V10.25)

Provides stateful session management for complete AI-human collaboration.
Solves the core AI Coding problems:
1. AI vs Human expectation gap
2. Architecture drift during development
3. Quality degradation over time
4. Lack of confirmation checkpoints

Usage:
    boring_session_start(goal="Build login feature")
    # -> Returns session_id and enters Phase 1

    boring_session_confirm()
    # -> Confirms current phase and moves to next

    boring_session_status()
    # -> Shows current progress
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

from pydantic import Field as PydanticField

from ...audit import audited
from ...types import BoringResult, create_error_result, create_success_result
from ..instance import MCP_AVAILABLE, mcp
from ..utils import check_rate_limit, detect_project_root

logger = logging.getLogger(__name__)


class SessionPhase(str, Enum):
    """Vibe Session phases."""

    ALIGNMENT = "alignment"  # Phase 1: Requirement gathering
    PLANNING = "planning"  # Phase 2: Plan creation
    IMPLEMENTATION = "implementation"  # Phase 3: Step-by-step coding
    VERIFICATION = "verification"  # Phase 4: Final verification
    COMPLETED = "completed"  # Session done
    PAUSED = "paused"  # Session paused


@dataclass
class SessionStep:
    """A single implementation step."""

    id: int
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    score: Optional[float] = None
    output: Optional[str] = None
    created_at: str = ""
    completed_at: Optional[str] = None


@dataclass
class VibeSession:
    """Complete Vibe Session state."""

    session_id: str
    goal: str
    phase: SessionPhase
    created_at: str
    updated_at: str

    # Phase 1: Alignment
    requirements: dict = field(default_factory=dict)
    tech_stack: str = ""
    quality_level: str = "production"  # prototype, production, enterprise
    constraints: list = field(default_factory=list)
    exclusions: list = field(default_factory=list)

    # Phase 2: Planning
    plan: dict = field(default_factory=dict)
    checklist: list = field(default_factory=list)
    architecture_notes: list = field(default_factory=list)

    # Phase 3: Implementation
    steps: list = field(default_factory=list)
    current_step: int = 0
    auto_mode: bool = False

    # Phase 4: Verification
    verification_results: dict = field(default_factory=dict)
    final_score: Optional[float] = None

    # Learning
    learned_patterns: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data["phase"] = self.phase.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "VibeSession":
        """Create from dictionary."""
        data["phase"] = SessionPhase(data["phase"])
        return cls(**data)


class VibeSessionManager:
    """Manages Vibe Session state persistence."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.session_dir = self.project_root / ".boring_memory" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._current_session: Optional[VibeSession] = None

    def _session_path(self, session_id: str) -> Path:
        return self.session_dir / f"{session_id}.json"

    def create_session(self, goal: str) -> VibeSession:
        """Create a new Vibe Session."""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        now = datetime.now().isoformat()

        session = VibeSession(
            session_id=session_id,
            goal=goal,
            phase=SessionPhase.ALIGNMENT,
            created_at=now,
            updated_at=now,
        )

        self._current_session = session
        self.save_session(session)
        return session

    def save_session(self, session: VibeSession):
        """Save session to disk."""
        session.updated_at = datetime.now().isoformat()
        path = self._session_path(session.session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

    def load_session(self, session_id: str) -> Optional[VibeSession]:
        """Load session from disk."""
        path = self._session_path(session_id)
        if not path.exists():
            return None

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        session = VibeSession.from_dict(data)
        self._current_session = session
        return session

    def get_current_session(self) -> Optional[VibeSession]:
        """Get current active session."""
        return self._current_session

    def list_sessions(self) -> list[dict]:
        """List all sessions."""
        sessions = []
        for path in self.session_dir.glob("*.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append(
                    {
                        "session_id": data["session_id"],
                        "goal": data["goal"][:50] + "..."
                        if len(data["goal"]) > 50
                        else data["goal"],
                        "phase": data["phase"],
                        "created_at": data["created_at"][:10],
                        "updated_at": data["updated_at"][:10],
                    }
                )
            except Exception:
                continue
        return sorted(sessions, key=lambda x: x["created_at"], reverse=True)

    def advance_phase(self, session: VibeSession) -> VibeSession:
        """Move to next phase."""
        phase_order = [
            SessionPhase.ALIGNMENT,
            SessionPhase.PLANNING,
            SessionPhase.IMPLEMENTATION,
            SessionPhase.VERIFICATION,
            SessionPhase.COMPLETED,
        ]

        current_idx = phase_order.index(session.phase)
        if current_idx < len(phase_order) - 1:
            session.phase = phase_order[current_idx + 1]

        self.save_session(session)
        return session


# Global session manager (initialized per project)
_session_managers: dict[str, VibeSessionManager] = {}


def get_session_manager(project_root: Path) -> VibeSessionManager:
    """Get or create session manager for project."""
    key = str(project_root)
    if key not in _session_managers:
        _session_managers[key] = VibeSessionManager(project_root)
    return _session_managers[key]


# ==============================================================================
# MCP TOOLS
# ==============================================================================


@audited
def boring_session_start(
    goal: Annotated[
        str, PydanticField(description="你想達成什麼目標？例如：'建立用戶登入功能'")
    ] = "",
    quality_level: Annotated[
        str,
        PydanticField(
            description="品質等級: prototype(快速原型), production(生產級), enterprise(企業級)"
        ),
    ] = "production",
    project_path: Annotated[str, PydanticField(description="專案路徑（選填）")] = None,
) -> BoringResult:
    """
    🎯 啟動 Vibe Session - 完整的 AI 協作流程。

    解決 AI Coding 核心問題：
    - AI 與人類期望落差
    - 架構遺失
    - 品質下降
    - 缺乏確認點

    Returns:
        Session 啟動結果和 Phase 1 問題
    """
    allowed, msg = check_rate_limit("boring_session_start")
    if not allowed:
        return create_error_result(f"⏱️ Rate limited: {msg}")

    project_root = detect_project_root(project_path)
    if not project_root:
        return create_error_result("❌ 找不到有效的 Boring 專案。請在專案根目錄執行。")

    try:
        manager = get_session_manager(project_root)
        session = manager.create_session(goal if goal else "待確認")
        session.quality_level = quality_level
        manager.save_session(session)

        # Phase 1 prompt
        goal_display = f"**目標**: {goal}" if goal else "**目標**: 待確認"

        msg_content = f"""# 🎯 Vibe Session 已啟動

**Session ID**: `{session.session_id}`
{goal_display}
**品質等級**: {quality_level}
**當前階段**: Phase 1 - 需求對齊 (Alignment)

---

## 📋 Phase 1: 需求對齊

為了確保我 100% 理解你的需求，請回答以下問題：

### 1️⃣ 核心目標
{f"你說想要「{goal}」，可以更具體描述嗎？例如：" if goal else "你今天想達成什麼？例如："}
- 要解決什麼問題？
- 預期的結果是什麼？

### 2️⃣ 技術偏好
- 有指定的語言/框架嗎？
- 有需要整合的現有系統嗎？

### 3️⃣ 品質期望 (已選擇: {quality_level})
- 🚀 prototype: 快速驗證，可以有技術債
- 🏗️ production: 需要測試、文檔、錯誤處理
- 🏢 enterprise: 需要安全審計、性能優化、監控

### 4️⃣ 約束條件
- 有必須遵守的架構規範嗎？
- 有時間限制嗎？

### 5️⃣ 明確排除
- 有什麼是你「不要」的？

---

💬 請回答以上問題，或者說：
- `確認` - 如果目標已經足夠清楚
- `調整目標 XXX` - 修改目標
- `取消` - 取消此 Session
"""
        return create_success_result(message=msg_content, data=session.to_dict())
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        return create_error_result(f"❌ 啟動 Session 失敗: {str(e)}")


@audited
def boring_session_confirm(
    notes: Annotated[str, PydanticField(description="補充說明或確認訊息")] = "",
    project_path: Annotated[str, PydanticField(description="專案路徑（選填）")] = None,
) -> BoringResult:
    """
    ✅ 確認當前階段並進入下一階段。

    Returns:
        下一階段的指引
    """
    allowed, msg = check_rate_limit("boring_session_confirm")
    if not allowed:
        return create_error_result(f"⏱️ Rate limited: {msg}")

    project_root = detect_project_root(project_path)
    if not project_root:
        return create_error_result("❌ 找不到有效的 Boring 專案。")

    try:
        manager = get_session_manager(project_root)
        session = manager.get_current_session()

        if not session:
            return create_error_result("❌ 沒有進行中的 Session。請先執行 `boring_session_start`。")

        current_phase = session.phase

        # Update notes if provided
        if notes:
            if current_phase == SessionPhase.ALIGNMENT:
                session.requirements["user_notes"] = notes
            elif current_phase == SessionPhase.PLANNING:
                session.architecture_notes.append(notes)

        # Advance to next phase
        session = manager.advance_phase(session)

        # Return appropriate prompt for new phase
        if session.phase == SessionPhase.PLANNING:
            prompt = _get_planning_prompt(session)
        elif session.phase == SessionPhase.IMPLEMENTATION:
            prompt = _get_implementation_prompt(session)
        elif session.phase == SessionPhase.VERIFICATION:
            prompt = _get_verification_prompt(session)
        elif session.phase == SessionPhase.COMPLETED:
            prompt = _get_completion_prompt(session)
        else:
            prompt = f"✅ 已確認。當前階段: {session.phase.value}"

        return create_success_result(message=prompt, data=session.to_dict())

    except Exception as e:
        logger.error(f"Failed to confirm session: {e}")
        return create_error_result(f"❌ 確認失敗: {str(e)}")


@audited
def boring_session_status(
    project_path: Annotated[str, PydanticField(description="專案路徑（選填）")] = None,
) -> BoringResult:
    """
    📊 查看當前 Vibe Session 狀態。

    Returns:
        Session 狀態報告
    """
    allowed, msg = check_rate_limit("boring_session_status")
    if not allowed:
        return create_error_result(f"⏱️ Rate limited: {msg}")

    project_root = detect_project_root(project_path)
    if not project_root:
        return create_error_result("❌ 找不到有效的 Boring 專案。")

    try:
        manager = get_session_manager(project_root)
        session = manager.get_current_session()

        if not session:
            # List available sessions
            sessions = manager.list_sessions()
            if not sessions:
                return create_success_result(
                    "📭 沒有任何 Session 記錄。使用 `boring_session_start` 開始新的 Session。",
                    data={"sessions": []},
                )

            session_list = "\n".join(
                [f"  • `{s['session_id']}` - {s['goal']} ({s['phase']})" for s in sessions[:5]]
            )
            msg_content = f"""# 📊 Vibe Session 列表

最近的 Sessions:
{session_list}

使用 `boring_session_load(session_id='...')` 載入特定 Session。
或使用 `boring_session_start` 開始新的 Session。
"""
            return create_success_result(message=msg_content, data={"sessions": sessions})

        # Calculate progress
        phase_progress = {
            SessionPhase.ALIGNMENT: 20,
            SessionPhase.PLANNING: 40,
            SessionPhase.IMPLEMENTATION: 70,
            SessionPhase.VERIFICATION: 90,
            SessionPhase.COMPLETED: 100,
            SessionPhase.PAUSED: 0,
        }

        progress = phase_progress.get(session.phase, 0)
        if session.phase == SessionPhase.IMPLEMENTATION and session.steps:
            total_steps = len(session.steps)
            completed = sum(1 for s in session.steps if s.get("status") == "completed")
            progress = 40 + int(30 * completed / total_steps) if total_steps > 0 else 40

        progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)

        # Build status display
        phase_emoji = {
            SessionPhase.ALIGNMENT: "📋",
            SessionPhase.PLANNING: "📐",
            SessionPhase.IMPLEMENTATION: "🔨",
            SessionPhase.VERIFICATION: "✅",
            SessionPhase.COMPLETED: "🎉",
            SessionPhase.PAUSED: "⏸️",
        }

        msg_content = f"""# 📊 Vibe Session 狀態

```
┌─────────────────────────────────────────────────┐
│  🎯 目標: {session.goal[:40]}{"..." if len(session.goal) > 40 else ""}
├─────────────────────────────────────────────────┤
│  {phase_emoji.get(session.phase, "❓")} 當前階段: {session.phase.value.upper()}
│  📈 進度: [{progress_bar}] {progress}%
├─────────────────────────────────────────────────┤
│  📅 創建時間: {session.created_at[:10]}
│  🔄 更新時間: {session.updated_at[:16]}
│  🎚️ 品質等級: {session.quality_level}
│  🤖 自動模式: {"開啟" if session.auto_mode else "關閉"}
└─────────────────────────────────────────────────┘
```

**Session ID**: `{session.session_id}`

---

**可用指令**:
- `boring_session_confirm` - 確認並進入下一階段
- `boring_session_pause` - 暫停 Session
- `boring_session_auto(enable=True)` - 開啟自動模式
"""
        return create_success_result(message=msg_content, data=session.to_dict())

    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        return create_error_result(f"❌ 取得狀態失敗: {str(e)}")


@audited
def boring_session_load(
    session_id: Annotated[str, PydanticField(description="要載入的 Session ID")],
    project_path: Annotated[str, PydanticField(description="專案路徑（選填）")] = None,
) -> BoringResult:
    """
    📂 載入之前的 Vibe Session。

    Returns:
        Session 狀態和繼續提示
    """
    allowed, msg = check_rate_limit("boring_session_load")
    if not allowed:
        return create_error_result(f"⏱️ Rate limited: {msg}")

    project_root = detect_project_root(project_path)
    if not project_root:
        return create_error_result("❌ 找不到有效的 Boring 專案。")

    try:
        manager = get_session_manager(project_root)
        session = manager.load_session(session_id)

        if not session:
            return create_error_result(f"❌ 找不到 Session: {session_id}")

        msg_content = f"""# 📂 Session 已載入

**Session ID**: `{session.session_id}`
**目標**: {session.goal}
**當前階段**: {session.phase.value}
**品質等級**: {session.quality_level}

---

使用 `boring_session_status` 查看詳細狀態。
使用 `boring_session_confirm` 繼續下一步。
"""
        return create_success_result(message=msg_content, data=session.to_dict())

    except Exception as e:
        logger.error(f"Failed to load session: {e}")
        return create_error_result(f"❌ 載入失敗: {str(e)}")


@audited
def boring_session_pause(
    project_path: Annotated[str, PydanticField(description="專案路徑（選填）")] = None,
) -> BoringResult:
    """
    ⏸️ 暫停當前 Vibe Session。

    Returns:
        暫停確認
    """
    allowed, msg = check_rate_limit("boring_session_pause")
    if not allowed:
        return create_error_result(f"⏱️ Rate limited: {msg}")

    project_root = detect_project_root(project_path)
    if not project_root:
        return create_error_result("❌ 找不到有效的 Boring 專案。")

    try:
        manager = get_session_manager(project_root)
        session = manager.get_current_session()

        if not session:
            return create_error_result("❌ 沒有進行中的 Session。")

        previous_phase = session.phase
        session.phase = SessionPhase.PAUSED
        manager.save_session(session)

        msg_content = f"""# ⏸️ Session 已暫停

**Session ID**: `{session.session_id}`
**暫停前階段**: {previous_phase.value}

進度已保存。稍後使用以下指令繼續：
```
boring_session_load(session_id='{session.session_id}')
```
"""
        return create_success_result(message=msg_content, data=session.to_dict())

    except Exception as e:
        logger.error(f"Failed to pause session: {e}")
        return create_error_result(f"❌ 暫停失敗: {str(e)}")


@audited
def boring_session_auto(
    enable: Annotated[bool, PydanticField(description="是否啟用自動模式")] = True,
    project_path: Annotated[str, PydanticField(description="專案路徑（選填）")] = None,
) -> BoringResult:
    """
    🤖 切換自動模式 - 自動確認並執行所有步驟。

    Returns:
        模式切換確認
    """
    allowed, msg = check_rate_limit("boring_session_auto")
    if not allowed:
        return create_error_result(f"⏱️ Rate limited: {msg}")

    project_root = detect_project_root(project_path)
    if not project_root:
        return create_error_result("❌ 找不到有效的 Boring 專案。")

    try:
        manager = get_session_manager(project_root)
        session = manager.get_current_session()

        if not session:
            return create_error_result("❌ 沒有進行中的 Session。")

        session.auto_mode = enable
        manager.save_session(session)

        if enable:
            msg_content = """# 🤖 自動模式已啟用

⚠️ **警告**: 自動模式下，我將：
- 自動確認每個步驟
- 自動修復遇到的問題
- 只在嚴重錯誤時暫停

使用 `boring_session_auto(enable=False)` 關閉自動模式。
"""
        else:
            msg_content = """# 🎮 手動模式已啟用

✅ 每個步驟都會等待你的確認後才執行。
"""
        return create_success_result(message=msg_content, data={"auto_mode": enable})

    except Exception as e:
        logger.error(f"Failed to toggle auto mode: {e}")
        return create_error_result(f"❌ 切換失敗: {str(e)}")


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


def _get_planning_prompt(session: VibeSession) -> str:
    """Generate Phase 2 planning prompt."""
    return f"""# 📐 Phase 2: 計劃制定 (Planning)

**目標**: {session.goal}
**品質等級**: {session.quality_level}

---

## 🏛️ 我正在分析你的需求...

請稍候，我將：
1. 執行 `boring_arch_check` 分析現有架構
2. 執行 `boring_speckit_plan` 生成實作計劃
3. 執行 `boring_speckit_checklist` 產生驗收清單

完成後會顯示完整計劃供你審核。

---

**提示**: 如果你有額外的架構要求，現在可以補充說明。
"""


def _get_implementation_prompt(session: VibeSession) -> str:
    """Generate Phase 3 implementation prompt."""
    total_steps = len(session.steps) if session.steps else "待確認"
    return f"""# 🔨 Phase 3: 增量實作 (Implementation)

**目標**: {session.goal}
**步驟數**: {total_steps}
**自動模式**: {"開啟" if session.auto_mode else "關閉"}

---

## 📋 實作流程

每個步驟我會：
1. 📋 說明這一步要做什麼
2. 👁️ 預覽變更
3. {"✅ 自動執行" if session.auto_mode else "⏸️ 等待你確認"}
4. 📊 自動評分

**品質閘門**: 評分 < 7 時會暫停並報告問題

---

準備開始實作。{"自動模式已開啟，我會持續執行直到完成或遇到問題。" if session.auto_mode else "每步完成後請說「確認」繼續，或「修改」調整。"}
"""


def _get_verification_prompt(session: VibeSession) -> str:
    """Generate Phase 4 verification prompt."""
    return f"""# ✅ Phase 4: 驗證與交付 (Verification)

**目標**: {session.goal}

---

## 🔍 最終驗證

我將執行：
1. `boring_verify(level='FULL')` - 完整驗證
2. `boring_test_gen` - 補充測試
3. `boring_code_review` - 最終審查
4. `boring_security_scan` - 安全掃描

請稍候...
"""


def _get_completion_prompt(session: VibeSession) -> str:
    """Generate completion prompt."""
    return f"""# 🎉 Vibe Session 完成！

**Session ID**: `{session.session_id}`
**目標**: {session.goal}

---

## 📊 完成報告

### ✅ 已實作
(根據實際執行結果填充)

### 📈 品質指標
- 最終評分: {session.final_score or "N/A"}/10
- 學習模式數: {len(session.learned_patterns)}

### 🏛️ 架構決策記錄
{chr(10).join(["- " + note for note in session.architecture_notes]) if session.architecture_notes else "- 無特殊架構決策"}

### 📚 已記錄到 Brain
{chr(10).join(["- " + p for p in session.learned_patterns]) if session.learned_patterns else "- 無新模式"}

---

🎊 感謝使用 Vibe Session！

**下一步建議**:
- `boring_commit` - 提交變更
- `boring_session_start` - 開始新的 Session
"""


# ==============================================================================
# REGISTER TOOLS
# ==============================================================================

if MCP_AVAILABLE and mcp is not None:
    mcp.tool(
        description="🎯 啟動 Vibe Session - 完整 AI 協作流程",
        annotations={"readOnlyHint": False, "openWorldHint": True},
    )(boring_session_start)

    mcp.tool(
        description="✅ 確認當前階段並進入下一階段",
        annotations={"readOnlyHint": False},
    )(boring_session_confirm)

    mcp.tool(
        description="📊 查看當前 Vibe Session 狀態",
        annotations={"readOnlyHint": True},
    )(boring_session_status)

    mcp.tool(
        description="📂 載入之前的 Vibe Session",
        annotations={"readOnlyHint": False},
    )(boring_session_load)

    mcp.tool(
        description="⏸️ 暫停當前 Vibe Session",
        annotations={"readOnlyHint": False},
    )(boring_session_pause)

    mcp.tool(
        description="🤖 切換自動模式",
        annotations={"readOnlyHint": False},
    )(boring_session_auto)
