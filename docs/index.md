# Boring Documentation

> **Boring for Gemini** - The autonomous AI development loop. Make AI development boring (in a good way).

---

## 🚀 Quick Start

Choose your path:

| You Are | Start Here |
|---------|-----------|
| 🎨 **Vibe Coder** (describe & build) | [Vibe Coder Guide](./guides/vibe-coder.md) |
| 💻 **Developer** (hands-on) | [Quick Tutorials](./guides/quick-tutorials.md) |
| 🔧 **DevOps/CI** | [Quality Gates](./features/quality-gates.md) |
| 🏢 **Team Lead** | [Pro Tips](./guides/pro-tips.md) |

### 📦 Installation Options

| Method | Profile | RAG Capability | Best For |
|--------|---------|----------------|----------|
| **Smithery (Remote)** | `lite` (default) | ⚠️ Keyword only | Quick setup, daily development |
| **Local pip `[all]`** | `standard`/`full` | ✅ Vector + Semantic | Full RAG, complete features |
| **Local pip (minimal)** | `lite` | ⚠️ Keyword only | Lightweight, CI/CD |

> 📋 **Smithery Deployment**: Uses `[mcp-lite]` (~500MB), `lite` profile by default (~20 tools). For full RAG with vector search, use local installation.
>
> 📖 **[Complete Installation Guide](../README.md#-installation)** | **[MCP Configuration Guide](./guides/mcp-configuration.md)**

---

## 📚 Documentation Structure

### Features (功能)
Core capabilities explained in depth.

| **Feature** | **Description** |
|:--------|:------------|
| [✨ Vibe Coder Experience](./features/vibe-coder.md) | **NEW**: Pure Natural Language Coding ([中文](./features/vibe-coder_zh.md)) |
| [🧠 External Intelligence](./features/external-intelligence.md) | **NEW**: Context7 (Docs) + Thinking Mode ([中文](./features/external-intelligence_zh.md)) |
| [🖥️ Monitoring Tools](./features/monitor.md) | **NEW**: TUI, Web Dashboard & Brain Explorer ([中文](./features/monitor_zh.md)) |
| [🕵️ Hybrid RAG](./features/rag.md) | **POWER**: HyDE + Cross-Encoder + Graph ([中文](./features/rag_zh.md)) |
| [🧠 Memory System](./features/memory.md) | **BRAIN**: Persistent Learning & Recall ([中文](./features/memory_zh.md)) |
| [🤖 Autonomous Agents](./features/agents.md) | **LOOP**: Planner, Coder, Reviewer Squad ([中文](./features/agents_zh.md)) |
| [MCP Toolset](./features/mcp-tools.md) | 55+ Tools, Profiles, Router ([中文](./features/mcp-tools_zh.md)) |
| [Shadow Mode](./features/shadow-mode.md) | Security Sandbox ([中文](./features/shadow-mode_zh.md)) |
| [Quality Gates](./features/quality-gates.md) | CI/CD integration and verification levels |
| [💎 Hidden Gems](./features/hidden-gems.md) | **Pro**: Advanced tips & secrets ([中文](./features/hidden-gems_zh.md)) |

### Guides (指南)
Practical how-to content.

| Guide | Description |
|-------|-------------|
| [🎯 Usage Modes](./guides/usage-modes.md) | **NEW**: MCP vs YOLO vs Autonomous ([中文](./guides/usage-modes.md)) |
| [🚀 YOLO + Boring](./guides/yolo-boring-integration.md) | **NEW**: Maximum automation guide ([中文](./guides/yolo-boring-integration.md)) |
| [🔄 Workflow Comparison](./guides/workflow-comparison.md) | **NEW**: Code-level analysis of Start vs Session ([中文](./guides/workflow-comparison_zh.md)) |
| [⚙️ MCP Configuration](./guides/mcp-configuration.md) | **NEW**: Profiles, ENV vars, Smithery vs Local ([中文](./guides/mcp-configuration.md)) |
| [🎛️ MCP Profiles](./guides/mcp-profiles-comparison.md) | **NEW**: Code-level analysis of Lite vs Standard ([中文](./guides/mcp-profiles-comparison_zh.md)) |
| [🛠️ Tool Manual](./guides/tool-manual.md) | **NEW**: Complete tool usage guide ([English](./guides/tool-manual_en.md)) |
| [📊 Evaluation Metrics](./guides/evaluation-metrics.md) | **NEW**: Kappa, Spearman, F1, Bias Monitoring ([English](./guides/evaluation-metrics_en.md)) |
| [Vibe Coder Guide](./guides/vibe-coder.md) | For description-based developers |
| [Quick Tutorials](./guides/quick-tutorials.md) | 5-minute step-by-step guides |
| [Cookbook](./guides/cookbook.md) | Ready-to-use recipes for all features |
| [Pro Tips](./guides/pro-tips.md) | Expert techniques by skill level |
| [Git Hooks](./guides/git-hooks.md) | Automated commit/push verification |
| [Agentic Workflows](./guides/workflows.md) | **Slash Commands**: `/release-prep` and SOPs |
| [Knowledge System](./guides/knowledge-system.md) | Brain, RAG & Patterns - storage and migration |
| [Plugin Guide](./guides/plugins.md) | Extend Boring with custom Python tools |
| [Knowledge & Brain](./guides/knowledge-management.md) | **Pro**: Backup & sharing intelligence |
| [Human Alignment](./guides/human-alignment.md) | **Pro**: Steer AI with Rubrics & Memory |
| [Modular Installation](./guides/modular-installation.md) | **NEW**: "Boring Diet" & Extras Guide ([中文](./guides/modular-installation_zh.md)) |
| [API Integration](./guides/api-integration.md) | Use Boring as a Python library |
| [Skills Guide](./guides/skills_guide.md) | **Learning**: Master the Boring Skill Tree |

### Tutorials (教學)
In-depth learning resources.

| Tutorial | Description |
|----------|-------------|
| [Basic Tutorial](./tutorials/TUTORIAL.md) | Getting started with Boring |
| [Advanced Tutorial](./tutorials/ADVANCED_TUTORIAL.md) | Deep dive into advanced features |
| [Practical Demo](./tutorials/PRACTICAL_DEMO.md) | Real-world project walkthrough |
| [Professional Playbook](./tutorials/PROFESSIONAL_PLAYBOOK.md) | Enterprise usage patterns |

### Reference (參考)
Deep dive technical documentation.

| Reference | Description |
|-----------|-------------|
| [Configuration](./reference/configuration.md) | **Deep Dive**: `.boring.toml` & ENV variables |
| [Troubleshooting](./reference/troubleshooting.md) | **Deep Dive**: Diagnosis & common fixes |
| [Architecture](./reference/architecture.md) | **Deep Dive**: Internals & Design |
| [Tool Reference (Appendix A)](./reference/APPENDIX_A_TOOL_REFERENCE.md) | Complete API documentation |
| [Security & Privacy](./reference/security-privacy.md) | **Deep Dive**: Data flows & protection |
| [Agent Comparison](./reference/comparison.md) | **Deep Dive**: Boring vs Cursor/Claude |
| [FAQ (Appendix B)](./reference/APPENDIX_B_FAQ.md) | Common questions answered |
| [Prompt Philosophy (Appendix C)](./reference/APPENDIX_C_PROMPT_PHILOSOPHY.md) | AI prompt design principles |
| [Architect Mode](./guides/architect_mode.md) | High-level architecture planning |

### API Documentation
| Page | Description |
|------|-------------|
| [Intelligence API](./api/intelligence_zh.md) | **NEW**: Brain, Vector Memory, Patterns |
| [Loop & Workflow API](./api/loop_zh.md) | **NEW**: Shadow Mode, Transactions |
| [Judge API](./api/judge_zh.md) | **NEW**: Rubrics, Metrics, Evaluation |
| [Security API](./api/security_zh.md) | **NEW**: Security Scanner & Guard |
| [Agents API](./api/agents.md) | Orchestrator, Coder, Reviewer logic |
| [MCP Server API](./api/mcp_server.md) | Model Context Protocol integration |

---

## 🌏 繁體中文文檔

### 功能
| 功能 | 說明 |
|------|------|
| [效能與架構](./features/performance_zh.md) | 增量驗證、快取、平行化 |
| [Vibe Coder Pro](./guides/vibe-coder_zh.md) | **最新**: 文件生成、測試生成、衝擊分析、友善審查 |
| [MCP 工具集](./features/mcp-tools_zh.md) | 所有 55+ 工具及範例 |
| [影子模式](./features/shadow-mode_zh.md) | AI 操作的安全沙箱 |
| [品質閘道](./features/quality-gates_zh.md) | CI/CD 整合和驗證級別 |

### 指南
| 指南 | 說明 |
|------|------|
| [Vibe Coder 指南](./guides/vibe-coder_zh.md) | 給描述式開發者 |
| [工作流程比較](./guides/workflow-comparison_zh.md) | **最新**: Start vs Session 的代碼級分析 |
| [快速教學](./guides/quick-tutorials_zh.md) | 5 分鐘逐步指南 |
| [Cookbook](./guides/cookbook_zh.md) | 所有功能的即用食譜 |
| [專業技巧](./guides/pro-tips_zh.md) | 按技能水平的專家技術 |
| [Git Hooks](./guides/git-hooks_zh.md) | 自動化提交/推送驗證 |
| [代理工作流](./guides/workflows_zh.md) | **斜槓指令**：`/release-prep` 與 SOP 自動化 |
| [知識系統](./guides/knowledge-system_zh.md) | Brain、RAG 與 Patterns - 儲存與遷移 |
| [插件開發指南](./guides/plugins_zh.md) | 使用自定義 Python 工具擴充 Boring |
| [知識與大腦管理](./guides/knowledge-management_zh.md) | **進階**：備份與分享學習成果 |
| [人類對齊指南](./guides/human-alignment_zh.md) | **進階**：使用 Rubrics 與記憶引導 AI |
| [API 整合指南](./guides/api-integration_zh.md) | 將 Boring 作為 Python 函式庫使用 |
| [模組化安裝指南](./guides/modular-installation_zh.md) | **最新**: "Boring Diet" 與延伸安裝說明 |
| [技能指南](./guides/skills_guide.md) | 掌握 Boring 技能樹 |

### 教學
| 教學 | 說明 |
|------|------|
| [基礎教學](./tutorials/TUTORIAL.md) | 開始使用 Boring |
| [進階教學](./tutorials/ADVANCED_TUTORIAL_zh.md) | 深入進階功能 |
| [實戰演示](./tutorials/PRACTICAL_DEMO.md) | 真實專案演練 |
| [專業手冊](./tutorials/PROFESSIONAL_PLAYBOOK.md) | 企業使用模式 |

### 參考
| 參考 | 說明 |
|------|------|
| [配置手冊](./reference/configuration_zh.md) | **深度指南**：`.boring.toml` 與環境變數 |
| [故障排除](./reference/troubleshooting_zh.md) | **深度指南**：診斷與常見修復 |
| [架構原理](./reference/architecture_zh.md) | **深度指南**：內部機制與設計 |
| [工具參考（附錄 A）](./reference/APPENDIX_A_TOOL_REFERENCE_zh.md) | 完整 API 文檔 |
| [安全與隱私白皮書](./reference/security-privacy_zh.md) | **深度指南**：資料流向與防護機制 |
| [工具對比分析](./reference/comparison_zh.md) | **深度指南**：Boring vs Cursor/Claude |
| [常見問題（附錄 B）](./reference/APPENDIX_B_FAQ_zh.md) | 常見問題解答 |
| [提示詞哲學（附錄 C）](./reference/APPENDIX_C_PROMPT_PHILOSOPHY_zh.md) | AI 提示設計原則 |
| [架構師模式](./guides/architect_mode_zh.md) | 高階架構規劃 |
 
### API 文檔
| 頁面 | 說明 |
|------|------|
| [智能 API (Intelligence)](./api/intelligence_zh.md) | **最新**: 大腦、向量記憶、模式學習 |
| [工作流 API (Loop)](./api/loop_zh.md) | **最新**: 影子模式、原子交易 |
| [評審 API (Judge)](./api/judge_zh.md) | **最新**: 評分準則、指標、自動評估 |
| [安全 API (Security)](./api/security_zh.md) | **最新**: 安全掃描與防護守衛 |
| [代理 API (Agents)](./api/agents_zh.md) | 編排器、編碼員、審核員邏輯 |
| [MCP 伺服器 API](./api/mcp_server_zh.md) | 模型內容協定 (MCP) 整合 |
 
---

## 🔗 External Links

- [GitHub Repository](https://github.com/Boring206/boring-gemini)
- [PyPI Package](https://pypi.org/project/boring-aicoding/)
- [Smithery MCP Server](https://smithery.ai/server/boring/boring)

---

## 📝 Contributing

See [Contributing Guide](./reference/contributing.md) for how to contribute to Boring.
