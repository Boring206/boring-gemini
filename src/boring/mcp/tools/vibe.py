# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Vibe Coder Pro Tools - 讓 Vibe Coder 程式碼達到工程師水準。

包含:
- boring_test_gen: 自動生成單元測試 (支援多語言) + RAG 風格參考
- boring_code_review: AI 程式碼審查 (支援多語言) + BrainManager Pattern 整合
- boring_vibe_check: 遊戲化健檢 (整合 Lint, Security, Doc) + Storage 歷史追蹤
- boring_impact_check: 衝擊分析 (多層依賴追蹤) + RAG 語義分析

V10.21 整合:
- BrainManager: 參考已學習的 Pattern 進行審查
- RAG: 語義搜尋現有測試風格、依賴分析
- Storage: 記錄 Vibe Score 歷史趨勢

移植自 vibe_tools.py (V10.26.0)
"""

from pathlib import Path
from typing import Annotated, Optional

from pydantic import Field

from ...paths import get_boring_path
from ...security import SecurityScanner  # Phase 14 Enhancement

# V11.2.2: Standardization
from ...types import BoringResult, create_error_result, create_success_result
from ...vibe.engine import VibeEngine
from ...vibe.handlers.generic import GenericHandler
from ...vibe.handlers.javascript import JavascriptHandler
from ...vibe.handlers.python import PythonHandler
from ..verbosity import is_minimal, is_standard, is_verbose

# Initialize Engine
vibe_engine = VibeEngine()
vibe_engine.register_handler(PythonHandler())
vibe_engine.register_handler(JavascriptHandler())
vibe_engine.register_handler(GenericHandler())


# =============================================================================
# Boring Core Integration Helpers (V10.21)
# =============================================================================
def _get_brain_manager(project_root: Path):
    """Get BrainManager instance for pattern retrieval."""
    try:
        from ...intelligence import BrainManager

        return BrainManager(project_root)
    except Exception:
        return None


def _get_storage(project_root: Path):
    """Get SQLiteStorage instance for metrics recording."""
    try:
        from ...services.storage import SQLiteStorage

        # Phase 10: Use unified path .boring/memory
        memory_dir = get_boring_path(project_root, "memory")
        storage = SQLiteStorage(memory_dir)
        return storage
    except ImportError:
        # Missing dependency (unlikely, but possible)
        return None
    except Exception as e:
        # Any other initialization error (permissions, disk space, etc.)
        # Log to stderr for debugging, but don't crash the tool
        import sys

        sys.stderr.write(f"[boring] Warning: Failed to initialize Storage: {e}\n")
        return None


def _get_rag_retriever(project_root: Path):
    """Get RAGRetriever instance for semantic search."""
    try:
        from ..rag.rag_retriever import RAGRetriever

        retriever = RAGRetriever(project_root)
        if retriever.is_available:
            return retriever
    except Exception:
        pass
    return None


def register_vibe_tools(mcp, audited, helpers, engine=None, brain_manager_factory=None):
    """
    Register Vibe Coder Pro tools with the MCP server.
    """
    _get_project_root_or_error = helpers["get_project_root_or_error"]
    global_engine = engine or vibe_engine
    _get_brain = brain_manager_factory or _get_brain_manager

    # === boring_test_gen ===
    @mcp.tool(
        description="自動生成單元測試 (Auto-generate unit tests). "
        "說: '幫我寫測試', '生成 auth.py 的測試', 'Generate tests for api.ts'. "
        "我會分析程式碼並生成 pytest/jest 測試案例！支援 Python, JS, TS. "
        "🆕 V10.21: 整合 RAG 參考現有測試風格！",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": False},
    )
    @audited
    def boring_test_gen(
        file_path: Annotated[str, Field(description="要生成測試的檔案路徑 (相對或絕對)")],
        output_dir: Annotated[
            Optional[str], Field(description="測試輸出目錄 (預設: tests/unit/ 或 tests/)")
        ] = None,
        project_path: Annotated[Optional[str], Field(description="專案根目錄 (自動偵測)")] = None,
    ) -> BoringResult:
        """
        🧪 自動生成單元測試 - 分析檔案並生成建議測試程式碼。
        支援平台: Python (pytest), JavaScript/TypeScript (jest/vitest)

        V10.21 整合:
        - RAG 搜尋現有測試，參考專案測試風格
        - 生成一致性更高的測試程式碼
        """
        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return create_error_result(error.get("message", "Unknown error"))

        # 解析檔案路徑
        target_file = Path(file_path)
        if not target_file.is_absolute():
            target_file = project_root / file_path

        if not target_file.exists():
            return create_error_result(f"❌ 找不到檔案: {file_path}")

        try:
            # 1. 使用 Engine 分析
            source = target_file.read_text(encoding="utf-8")
            result = global_engine.analyze_for_test_gen(str(target_file), source)

            if not result.functions and not result.classes:
                return create_success_result(
                    message="😅 沒有找到可測試的導出函式或類別", data={"file": str(target_file)}
                )

            # 2. V10.21: RAG 搜尋現有測試風格
            test_style_hints = []
            rag = _get_rag_retriever(project_root)
            if rag:
                try:
                    # 搜尋現有測試檔案
                    existing_tests = rag.retrieve(
                        query=f"test {target_file.stem} pytest unittest",
                        top_k=3,
                        chunk_types=["function"],
                    )
                    if existing_tests:
                        for r in existing_tests[:2]:
                            if "test_" in r.chunk.name.lower():
                                test_style_hints.append(f"# 參考現有測試: {r.chunk.name}")
                except Exception:
                    pass  # RAG is optional enhancement

            # 3. 生成測試程式碼 (with style hints)
            test_code = global_engine.generate_test_code(result, str(project_root))

            # Prepend style hints if available
            if test_style_hints:
                style_comment = "\n".join(test_style_hints)
                test_code = f"# V10.21: 已參考現有測試風格\n{style_comment}\n\n{test_code}"

            # 4. 決定輸出路徑
            if output_dir:
                test_dir = project_root / output_dir
            else:
                # 自動判斷預設目錄
                if result.source_language == "python":
                    test_dir = project_root / "tests" / "unit"
                else:
                    test_dir = project_root / "tests"

            test_dir.mkdir(parents=True, exist_ok=True)
            test_filename = (
                f"test_{target_file.stem}.py"
                if result.source_language == "python"
                else f"{target_file.stem}.test{target_file.suffix}"
            )
            test_file = test_dir / test_filename

            # 5. 寫入測試檔案
            test_file.write_text(test_code, encoding="utf-8")

            rag_status = "✅ RAG 風格參考" if test_style_hints else "⚠️ RAG 未啟用"

            return create_success_result(
                message=f"✅ 已生成 {result.source_language} 測試！\n檔案: {test_file.relative_to(project_root)}\n{rag_status}",
                data={
                    "test_file": str(test_file),
                    "functions_count": len(result.functions),
                    "classes_count": len(result.classes),
                    "rag_enhanced": bool(test_style_hints),
                    "vibe_summary": f"🧪 為 `{target_file.name}` 生成了 {len(result.functions)} 個測試\n"
                    f"📁 測試檔案: `{test_file.relative_to(project_root)}`\n"
                    f"🌐 語言: {result.source_language}\n"
                    f"🔗 {rag_status}",
                },
            )

        except ValueError as e:
            return create_error_result(
                f"❌ 不支援的檔案類型: {target_file.suffix}", error_details=str(e)
            )
        except Exception as e:
            return create_error_result(f"❌ 分析失敗: {str(e)}")

    # === boring_code_review ===
    @mcp.tool(
        description="AI 程式碼審查 (AI Code Review). "
        "說: '審查我的程式碼', 'Review my code', '幫我看看哪裡可以改進'. "
        "我會分析程式碼品質並給出改善建議！支援 Python, JS, TS. "
        "🆕 V10.21: 整合 BrainManager 參考已學習的 Pattern！",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_code_review(
        file_path: Annotated[str, Field(description="要審查的檔案路徑")],
        focus: Annotated[
            Optional[str],
            Field(
                description="審查重點: 'all', 'naming', 'error_handling', 'performance', 'security'"
            ),
        ] = "all",
        verbosity: Annotated[
            str,
            Field(
                description="Output verbosity: 'minimal' (summary only ~100 tokens), 'standard' (categorized issues ~500 tokens), 'verbose' (full details with brain patterns ~1000+ tokens). Default: 'standard'."
            ),
        ] = "standard",
        project_path: Annotated[Optional[str], Field(description="專案根目錄 (自動偵測)")] = None,
    ) -> BoringResult:
        """
        🔍 AI 程式碼審查 - 分析程式碼品質並給出改善建議。
        支援平台: Python, JavaScript, TypeScript

        V10.21 整合:
        - BrainManager: 參考專案已學習的 Pattern，審查更精準
        - 歷史錯誤模式: 識別曾經犯過的錯誤
        """
        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return create_error_result(error.get("message", "Unknown error"))

        target_file = Path(file_path)
        if not target_file.is_absolute():
            target_file = project_root / file_path

        if not target_file.exists():
            return create_error_result(f"❌ 找不到檔案: {file_path}")

        try:
            source = target_file.read_text(encoding="utf-8")
            result = global_engine.perform_code_review(str(target_file), source, focus)

            # V10.21: BrainManager 整合 - 取得相關 Pattern
            brain_patterns = []
            brain = _get_brain(project_root)
            if brain:
                try:
                    # 搜尋與審查相關的 Pattern
                    patterns = brain.get_relevant_patterns(
                        context=f"{focus} review {target_file.name}", limit=3
                    )
                    for p in patterns:
                        if p.get("pattern_type") in ["code_style", "error_solution", "code_fix"]:
                            brain_patterns.append(
                                {
                                    "type": p.get("pattern_type"),
                                    "description": p.get("description", "")[:100],
                                    "suggestion": p.get("solution", "")[:150],
                                }
                            )
                except Exception:
                    pass  # BrainManager is optional enhancement

            if not result.issues:
                brain_status = (
                    f"\n🧠 已參考 {len(brain_patterns)} 個專案 Pattern" if brain_patterns else ""
                )
                message = f"✅ 程式碼品質良好！沒有發現明顯問題。{brain_status}"

                if is_minimal(verbosity):
                    message = f"✅ {target_file.name}: 無問題"

                return create_success_result(
                    message=message,
                    data={
                        "file": str(target_file),
                        "issues_count": 0,
                        "brain_patterns_used": len(brain_patterns),
                        "vibe_summary": message,
                    },
                )

            # 按嚴重程度排序
            result.issues.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.severity, 3))

            # Format output based on verbosity
            if is_minimal(verbosity):
                # MINIMAL: Only summary statistics
                severity_counts = {"high": 0, "medium": 0, "low": 0}
                for issue in result.issues:
                    severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1

                summary_lines = [
                    f"🔍 {target_file.name}: {len(result.issues)} 問題",
                    f"🔴 High: {severity_counts['high']} | 🟡 Medium: {severity_counts['medium']} | 🟢 Low: {severity_counts['low']}",
                ]
                if brain_patterns:
                    summary_lines.append(f"🧠 {len(brain_patterns)} patterns")

                summary_lines.append("💡 Use verbosity='standard' for details")

            elif is_verbose(verbosity):
                # VERBOSE: Full details with brain patterns
                summary_lines = [f"🔍 Code Review: `{target_file.name}`", ""]
                for i, issue in enumerate(result.issues, 1):  # Show ALL issues in verbose
                    severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                        issue.severity, "⚪"
                    )
                    summary_lines.append(
                        f"{i}. {severity_icon} **{issue.category}** (Line {issue.line}): {issue.message}"
                    )
                    if issue.suggestion:
                        summary_lines.append(f"   💡 建議: {issue.suggestion}")

                # Include all brain patterns in verbose
                if brain_patterns:
                    summary_lines.append("")
                    summary_lines.append(
                        f"🧠 **專案 Pattern 建議** ({len(brain_patterns)} patterns):"
                    )
                    for bp in brain_patterns:
                        summary_lines.append(f"   - [{bp['type']}] {bp['description']}")
                        summary_lines.append(f"     → {bp['suggestion']}")
            else:
                # STANDARD: Current behavior (top 10 issues)
                summary_lines = [f"🔍 Code Review: `{target_file.name}`", ""]
                for i, issue in enumerate(result.issues[:10], 1):
                    severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                        issue.severity, "⚪"
                    )
                    summary_lines.append(
                        f"{i}. {severity_icon} **{issue.category}**: {issue.message}"
                    )
                    if issue.suggestion:
                        summary_lines.append(f"   💡 建議: {issue.suggestion}")

                # V10.21: 加入 Brain Pattern 建議
                if brain_patterns:
                    summary_lines.append("")
                    summary_lines.append("🧠 **專案 Pattern 建議**:")
                    for bp in brain_patterns[:2]:
                        summary_lines.append(f"   - {bp['description']}: {bp['suggestion']}")

            # Generate Fix Prompt
            fix_prompt = f"Please review `{target_file.name}` and fix the following {len(result.issues)} issues:\n"
            for issue in result.issues:
                fix_prompt += f"- [{issue.severity.upper()}] {issue.category}: {issue.message}\n"
                if issue.suggestion:
                    fix_prompt += f"  (Suggestion: {issue.suggestion})\n"

            # 加入 Brain Pattern 到 Fix Prompt
            if brain_patterns:
                fix_prompt += "\n🧠 Project-specific patterns to follow:\n"
                for bp in brain_patterns:
                    fix_prompt += f"- {bp['description']}: {bp['suggestion']}\n"

            fix_prompt += "\nReturn the fixed specific functions or class code blocks."

            brain_status = "✅ Brain Pattern 整合" if brain_patterns else "⚠️ BrainManager 未啟用"

            return create_success_result(
                message="\n".join(summary_lines) + f"\n\n🔗 {brain_status}",
                data={
                    "file": str(target_file),
                    "issues_count": len(result.issues),
                    "brain_patterns_used": len(brain_patterns),
                    "brain_enhanced": bool(brain_patterns),
                    "issues": [
                        {
                            "category": i.category,
                            "severity": i.severity,
                            "message": i.message,
                            "line": i.line,
                        }
                        for i in result.issues
                    ],
                    "brain_patterns": brain_patterns,
                    "suggested_fix_prompt": fix_prompt,
                },
            )

        except ValueError:
            return create_error_result(f"❌ 不支援的格式: {target_file.suffix}")
        except Exception as e:
            return create_error_result(f"❌ 審查失敗: {str(e)}")

    # === boring_perf_tips ===
    @mcp.tool(
        description="效能分析提示 (Performance Tips). "
        "說: '分析效能', '效能優化建議', 'Check performance of api.py'. "
        "我會專注檢查效能瓶頸 (如 N+1 query, I/O in loop) 並提供優化建議！支援 Py, JS, TS.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_perf_tips(
        file_path: Annotated[str, Field(description="要分析的檔案路徑")],
        project_path: Annotated[Optional[str], Field(description="專案根目錄 (自動偵測)")] = None,
        verbosity: Annotated[
            str,
            Field(description="輸出詳細程度: 'minimal', 'standard' (預設), 'verbose'"),
        ] = "standard",
    ) -> BoringResult:
        """
        ⚡ 效能分析提示 - 專注於程式碼效能瓶頸檢測。
        支援平台: Python, JavaScript, TypeScript
        """
        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return create_error_result(error.get("message", "Unknown error"))

        target_file = Path(file_path)
        if not target_file.is_absolute():
            target_file = project_root / file_path

        if not target_file.exists():
            return create_error_result(f"❌ 找不到檔案: {file_path}")

        try:
            source = target_file.read_text(encoding="utf-8")
            # 僅專注於 performance
            result = global_engine.perform_code_review(
                str(target_file), source, focus="performance"
            )

            if not result.issues:
                msg = "⚡ 效能分析完成：未發現明顯瓶頸。"
                if is_minimal(verbosity):
                    msg = f"⚡ {target_file.name}: 無效能問題"

                return create_success_result(
                    message=msg,
                    data={
                        "file": str(target_file),
                        "tips_count": 0,
                        "vibe_summary": msg,
                    },
                )

            # Generate Perf Fix Prompt
            fix_prompt = f"Please analyze performance bottlenecks in `{target_file.name}` and apply the following optimizations:\n"
            for issue in result.issues:
                fix_prompt += f"- {issue.message} (Line {issue.line})\n"
                if issue.suggestion:
                    fix_prompt += f"  Tip: {issue.suggestion}\n"

            # --- Verbosity Logic ---

            # 1. MINIMAL: Summary only
            if is_minimal(verbosity):
                severity_counts = {"high": 0, "medium": 0, "low": 0}
                for issue in result.issues:
                    severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1

                return create_success_result(
                    message=f"⚡ {target_file.name}: {len(result.issues)} 效能問題",
                    data={
                        "vibe_summary": (
                            f"⚡ {target_file.name}: {len(result.issues)} 效能問題\n"
                            f"🐌 High: {severity_counts['high']} | 🐢 Medium/Low: {severity_counts['medium'] + severity_counts['low']}\n"
                            f"💡 Use verbosity='standard' for tips"
                        ),
                        "file": str(target_file),
                        "tips_count": len(result.issues),
                    },
                )

            # 2. STANDARD: Top 5 issues
            if is_standard(verbosity):
                summary_lines = [f"⚡ Performance Tips: `{target_file.name}`", ""]
                # Show top 5
                for i, issue in enumerate(result.issues[:5], 1):
                    icon = "🐌" if issue.severity == "high" else "🐢"
                    summary_lines.append(f"{i}. {icon} **{issue.message}** (Line {issue.line})")
                    if issue.suggestion:
                        summary_lines.append(f"   🚀 優化: {issue.suggestion}")

                if len(result.issues) > 5:
                    summary_lines.append(f"\n... and {len(result.issues) - 5} more issues.")
                    summary_lines.append("💡 Use verbosity='verbose' for full list.")

                return create_success_result(
                    message="\n".join(summary_lines),
                    data={
                        "file": str(target_file),
                        "tips_count": len(result.issues),
                        "vibe_summary": "\n".join(summary_lines),
                        "suggested_fix_prompt": fix_prompt,
                    },
                )

            # 3. VERBOSE: Full list (Legacy behavior)
            summary_lines = [f"⚡ Performance Tips: `{target_file.name}`", ""]
            for i, issue in enumerate(result.issues, 1):
                icon = "🐌" if issue.severity == "high" else "🐢"
                summary_lines.append(f"{i}. {icon} **{issue.message}** (Line {issue.line})")
                if issue.suggestion:
                    summary_lines.append(f"   🚀 優化: {issue.suggestion}")

            return create_success_result(
                message="\n".join(summary_lines),
                data={
                    "file": str(target_file),
                    "tips_count": len(result.issues),
                    "tips": [
                        {"message": i.message, "line": i.line, "suggestion": i.suggestion}
                        for i in result.issues
                    ],
                    "vibe_summary": "\n".join(summary_lines),
                    "suggested_fix_prompt": fix_prompt,
                },
            )

        except ValueError:
            return create_error_result(f"❌ 不支援的格式: {target_file.suffix}")
        except Exception as e:
            return create_error_result(f"❌ 分析失敗: {str(e)}")

    # === boring_arch_check ===
    @mcp.tool(
        description="架構分析 (Architecture Analysis). "
        "說: '分析專案架構', 'Show me the dependencies', '看看誰引用誰', '該如何重構'. "
        "我會生成 Mermaid 依賴圖，讓你一目了然專案結構！",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_arch_check(
        target_path: Annotated[str, Field(description="File or directory to scan.")] = ".",
        output_format: Annotated[
            str, Field(description="Output format: 'mermaid' or 'json'.")
        ] = "mermaid",
    ) -> BoringResult:
        """
        Analyze project dependencies and architecture.

        Generates a dependency graph showing how files import each other.
        Use this to understand the structure of a codebase.
        """
        root_str, error = _get_project_root_or_error(
            None
        )  # project_path is now optional and handled by get_root
        if error:
            return create_error_result(error.get("message", "Unknown error"))

        project_root = Path(root_str)
        # Handle both absolute and relative paths
        if target_path != "." and (
            target_path.startswith("/") or (len(target_path) > 1 and target_path[1] == ":")
        ):
            target = Path(target_path)
        elif target_path == ".":
            target = project_root
        else:
            target = project_root / target_path

        files_to_scan = []
        if target.is_file():
            files_to_scan.append(target)
        elif target.is_dir():
            files_to_scan.extend(
                [
                    p
                    for p in target.rglob("*")
                    if p.is_file()
                    and p.suffix.lower() in [".py", ".js", ".ts", ".jsx", ".tsx"]
                    and not any(
                        x in p.parts for x in ["node_modules", ".git", "__pycache__", "venv"]
                    )
                ]
            )
        else:
            return create_error_result(f"❌ Target not found: {target}")

        edges = []
        nodes = set()

        for file_path in files_to_scan:
            try:
                rel_path = file_path.relative_to(project_root).as_posix()
                content = file_path.read_text(encoding="utf-8", errors="ignore")

                deps = vibe_engine.extract_dependencies(str(file_path), content)

                if deps:
                    nodes.add(rel_path)
                    for dep in deps:
                        # Simple normalization
                        dep_name = dep
                        if dep.startswith("."):
                            # Attempt simple resolve?
                            # For visualization, generic name is arguably better than huge guess
                            pass

                        edge = (rel_path, dep_name)
                        edges.append(edge)
            except Exception:
                continue

        if output_format == "json":
            return create_success_result(
                message="✅ Dependency analysis complete (JSON)",
                data={"nodes": list(nodes), "edges": edges},
            )

        # Mermaid format
        lines = ["graph TD"]
        max_edges = 100

        # Limit edges to avoid explosion
        processed_count = 0
        for src, dst in edges:
            if processed_count >= max_edges:
                lines.append(f"    %% Truncated after {max_edges} edges")
                break

            # Simple sanitization for Mermaid IDs
            def clean_id(s):
                return s.replace("/", "_").replace(".", "_").replace("-", "_").replace("@", "")

            s_id = clean_id(src)
            d_id = clean_id(dst)

            # Add node labels
            lines.append(f'    {s_id}["{src}"] --> {d_id}["{dst}"]')
            processed_count += 1

        mermaid_graph = "\n".join(lines)
        return create_success_result(
            message=mermaid_graph,
            data={"mermaid": mermaid_graph, "node_count": len(nodes), "edge_count": len(edges)},
        )

    # === boring_doc_gen ===
    @mcp.tool(
        description="自動生成文檔 (Auto-generate Documentation). "
        "說: '幫我寫文檔', 'Generate docs for api.py', 'API 文檔', '自動註解'. "
        "我會擷取 Docstrings/JSDoc 並生成 Markdown 參考文檔！",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_doc_gen(
        target_path: Annotated[str, Field(description="File or directory to scan.")] = ".",
    ) -> BoringResult:
        """
        Extract documentation comments and generate an API reference.

        Supports:
        - Python Docstrings (Module, Class, Function)
        - JavaScript/TypeScript JSDoc (/** ... */)

        Returns Markdown content.
        """
        root_str, error = _get_project_root_or_error(None)
        if error:
            return create_error_result(error.get("message", "Unknown error"))

        project_root = Path(root_str)
        # Handle both absolute and relative paths
        if target_path != "." and (
            target_path.startswith("/") or (len(target_path) > 1 and target_path[1] == ":")
        ):
            target = Path(target_path)
        elif target_path == ".":
            target = project_root
        else:
            target = project_root / target_path

        files_to_scan = []
        if target.is_file():
            files_to_scan.append(target)
        elif target.is_dir():
            files_to_scan.extend(
                [
                    p
                    for p in target.rglob("*")
                    if p.is_file()
                    and p.suffix.lower() in [".py", ".js", ".ts", ".jsx", ".tsx"]
                    and not any(
                        x in p.parts
                        for x in ["node_modules", ".git", "__pycache__", "venv", "dist", "build"]
                    )
                ]
            )
        else:
            return create_error_result(f"❌ Target not found: {target}")

        doc_output = [f"# API Documentation\n\nGenerated for: `{target_path}`\n"]

        for file_path in sorted(files_to_scan):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                rel_path = file_path.relative_to(project_root).as_posix()

                result = vibe_engine.extract_documentation(str(file_path), content)

                if not result.items and not result.module_doc:
                    continue

                doc_output.append(f"## File: `{rel_path}`\n")
                if result.module_doc:
                    doc_output.append(f"> {result.module_doc.strip()}\n")

                doc_output.append("")

                for item in result.items:
                    icon = "📦" if item.type == "class" else "ƒ"
                    doc_output.append(f"### {icon} `{item.name}`")
                    doc_output.append(f"**Signature:** `{item.signature}`\n")
                    if item.docstring:
                        doc_output.append(f"{item.docstring}\n")
                    else:
                        doc_output.append("*No documentation.*\n")
                    doc_output.append("---\n")

            except Exception as e:
                doc_output.append(f"<!-- Error processing {file_path.name}: {e} -->\n")

        doc_content = "\n".join(doc_output)
        return create_success_result(
            message=doc_content,
            data={"documentation": doc_content, "files_scanned": len(files_to_scan)},
        )

    # === boring_vibe_check ===
    @mcp.tool(
        description="Vibe Score 健檢 (Gamified Health Check). "
        "說: 'Vibe Check my project', '健檢 utils.py', 'Give me a vibe score'. "
        "我會整合 Lint, Security, Doc 檢查，計算 0-100 分數，並提供一鍵修復 Prompt！ "
        "🆕 V10.21: 整合 Storage 記錄歷史分數趨勢！",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_vibe_check(
        target_path: Annotated[str, Field(description="要健檢的檔案或目錄")] = ".",
        project_path: Annotated[Optional[str], Field(description="專案根目錄 (自動偵測)")] = None,
        max_files: Annotated[int, Field(description="最大掃描檔案數 (預設 10)")] = 10,
        verbosity: Annotated[
            str,
            Field(
                description="Output verbosity: 'minimal' (score + tier only ~50 tokens), 'standard' (score + top issues ~300 tokens), 'verbose' (full report ~800+ tokens). Default: 'standard'."
            ),
        ] = "standard",
    ) -> BoringResult:  # Forward reference or use BoringResult directly if imported
        """
        📊 Vibe Check - 全面健康度檢查與評分。
        整合多項指標 (Lint, Security, Doc)，提供遊戲化評分與一鍵修復 Prompt。

        V10.21 整合:
        - Storage: 記錄 Vibe Score 歷史，追蹤專案健康趨勢
        - 顯示與上次分數的對比
        """
        root_str, error = _get_project_root_or_error(project_path)
        if error:
            return create_error_result(error.get("message", "Unknown error"))

        project_root = Path(root_str)
        # Handle both absolute and relative paths
        if target_path.startswith("/") or (len(target_path) > 1 and target_path[1] == ":"):
            # Absolute path (Unix-style or Windows-style)
            target = Path(target_path)
        elif target_path == ".":
            target = project_root
        else:
            # Relative path
            target = project_root / target_path

        if not target.exists():
            return create_error_result(f"❌ 找不到目標: {target}")

        # 1. 收集檔案
        files_to_check = []
        if target.is_file():
            files_to_check.append(target)
        else:
            candidates = [
                p
                for p in target.rglob("*")
                if p.is_file()
                and p.suffix in [".py", ".js", ".ts"]
                and not any(x in p.parts for x in ["node_modules", ".git", "venv"])
            ][:max_files]
            files_to_check.extend(candidates)

        if not files_to_check:
            return create_error_result("⚠️ 找不到可分析的程式碼檔案 (.py, .js, .ts)")

        # Scoring Variables
        base_score = 100
        deductions = 0
        issues_found = []
        doc_missing = 0
        security_issues = []

        # 2. 逐檔分析
        for f in files_to_check:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")

                # A. Code Review (Lint/Quality)
                rev_res = vibe_engine.perform_code_review(str(f), content, focus="all")
                for issue in rev_res.issues:
                    deduction = (
                        5 if issue.severity == "low" else 10 if issue.severity == "medium" else 15
                    )
                    deductions += deduction
                    issues_found.append(f"[{f.name}:{issue.line}] {issue.message}")

                # B. Doc Check
                doc_res = vibe_engine.extract_documentation(str(f), content)
                for item in doc_res.items:
                    if not item.docstring:
                        deductions += 5
                        doc_missing += 1

            except Exception:
                continue

        # 3. Security Scan (Phase 14 Enhancement)
        try:
            scanner = SecurityScanner(project_root)
            sec_report = scanner.scan_for_secrets(target if target.is_dir() else target.parent)
            for sec_issue in sec_report.issues:
                severity_deduction = (
                    20
                    if sec_issue.severity == "CRITICAL"
                    else 15
                    if sec_issue.severity == "HIGH"
                    else 10
                )
                deductions += severity_deduction
                security_issues.append(
                    f"🔒 [{sec_issue.severity}] {sec_issue.description} ({sec_issue.file_path}:{sec_issue.line_number})"
                )
        except Exception:
            pass  # Security scan is optional enhancement

        # 3.5 Memory Injection (Phase 20 Enhancement)
        # Attempt to match error codes with Brain Memory
        brain_advice = []
        try:
            from boring.intelligence.brain_manager import BrainManager

            brain = BrainManager(project_root)

            seen_patterns = set()
            for issue in issues_found:
                # Naive pattern extraction: "[file:line] Message" -> "Message"
                # Better: Extract error code if available (e.g. F401)
                # Here we just take the message part
                msg_part = issue.split("] ", 1)[-1] if "] " in issue else issue

                # Query brain
                patterns = brain.match_error_pattern(msg_part)
                if patterns:
                    best_match = patterns[0]  # Take top match
                    if best_match.pattern_id not in seen_patterns:
                        brain_advice.append(
                            f"🧠 Brain Recall: For '{msg_part}', previously solving by: {best_match.solution}"
                        )
                        seen_patterns.add(best_match.pattern_id)

                        # Apply to fix prompt
                        deductions -= 5  # Bonus for having a known solution!
        except Exception:
            pass

        # 4. 計算分數
        final_score = max(0, base_score - deductions)

        # 5. 評級
        if final_score >= 95:
            tier = "S-Tier (God Like) 🏆"
        elif final_score >= 85:
            tier = "A-Tier (Professional) 🥇"
        elif final_score >= 75:
            tier = "B-Tier (Solid) 🥈"
        elif final_score >= 60:
            tier = "C-Tier (Meh) 🥉"
        else:
            tier = "F-Tier (Spaghetti) 🍝"

        # 6. 生成 One-Click Fix Prompt
        fix_prompt = ""
        if final_score < 100:
            fix_prompt = f"Please act as a Senior Engineer to fix the low Vibe Score ({final_score}) for the following files:\n"
            fix_prompt += f"Target: `{target_path}`\n\n"
            fix_prompt += "Tasks:\n"

            if issues_found:
                fix_prompt += "1. Fix the following code quality issues:\n"
                for i in issues_found[:10]:
                    fix_prompt += f"   - {i}\n"
                if len(issues_found) > 10:
                    fix_prompt += f"   - ... and {len(issues_found) - 10} more issues.\n"

            if doc_missing > 0:
                fix_prompt += f"2. Add missing docstrings/JSDoc to {doc_missing} functions/classes to meet Google Style Guide.\n"

            if security_issues:
                fix_prompt += "3. ⚠️ CRITICAL: Remove or rotate the following exposed secrets:\n"
                for sec in security_issues[:5]:
                    fix_prompt += f"   - {sec}\n"

            fix_prompt += "\nReturn the corrected code directly."
        else:
            fix_prompt = "🎉 Perfect Score! No fixes needed. Maybe go touch some grass? 🌱"

        # 7. V10.21: Storage 歷史追蹤
        score_trend = ""
        previous_score = None
        storage = _get_storage(project_root)
        if storage:
            try:
                # 記錄本次分數
                storage.record_metric(
                    name="vibe_score",
                    value=float(final_score),
                    metadata={
                        "target": target_path,
                        "issues": len(issues_found),
                        "doc_missing": doc_missing,
                        "security_issues": len(security_issues),
                        "tier": tier,
                    },
                )

                # 取得歷史分數
                history = storage.get_metrics("vibe_score", limit=5)
                if len(history) > 1:
                    previous_score = history[1].get("metric_value")
                    if previous_score is not None:
                        diff = final_score - previous_score
                        if diff > 0:
                            score_trend = f"📈 +{diff:.0f} (vs 上次 {previous_score:.0f})"
                        elif diff < 0:
                            score_trend = f"📉 {diff:.0f} (vs 上次 {previous_score:.0f})"
                        else:
                            score_trend = f"➡️ 維持 {previous_score:.0f}"
            except Exception:
                pass  # Storage is optional enhancement

        storage_status = "✅ 分數已記錄" if storage else "⚠️ Storage 未啟用"

        # Import verbosity control
        from boring.mcp.verbosity import Verbosity, get_verbosity

        verb_level = get_verbosity(verbosity)

        # Generate vibe_summary based on verbosity
        if verb_level == Verbosity.MINIMAL:
            # MINIMAL: Only score and tier (~50 tokens)
            vibe_summary = f"📊 Vibe Score: {final_score}/100 | {tier}"
            if score_trend:
                vibe_summary += f"\n{score_trend}"
            vibe_summary += "\n💡 Use verbosity='standard' for details"

        elif verb_level == Verbosity.VERBOSE:
            # VERBOSE: Full detailed report (~800+ tokens)
            summary_lines = [
                f"📊 Vibe Check: `{target_path}`",
                f"Score: {final_score}/100 | {tier}",
                "",
            ]

            if score_trend:
                summary_lines.append(f"{score_trend}\n")

            # Code Quality Issues
            if issues_found:
                summary_lines.append(f"🔍 Code Quality Issues ({len(issues_found)}):")
                for issue in issues_found[:20]:  # Show up to 20
                    summary_lines.append(f"  - {issue}")
                if len(issues_found) > 20:
                    summary_lines.append(f"  ... and {len(issues_found) - 20} more")
                summary_lines.append("")

            # Security Issues
            if security_issues:
                summary_lines.append(f"🔒 Security Issues ({len(security_issues)}):")
                for sec in security_issues[:10]:
                    summary_lines.append(f"  - {sec}")
                if len(security_issues) > 10:
                    summary_lines.append(f"  ... and {len(security_issues) - 10} more")
                summary_lines.append("")

            # Documentation
            if doc_missing > 0:
                summary_lines.append(f"📝 Documentation: {doc_missing} missing docstrings")
                summary_lines.append("")

            summary_lines.append(f"🔗 {storage_status}")
            vibe_summary = "\n".join(summary_lines)

        else:  # STANDARD
            # STANDARD: Score + top issues (~300 tokens)
            summary_lines = [f"📊 Vibe Score: {final_score}/100 | {tier}", ""]

            if score_trend:
                summary_lines.append(f"{score_trend}\n")

            # Top 5 quality issues
            if issues_found:
                summary_lines.append(
                    f"🔍 Top Issues ({min(5, len(issues_found))}/{len(issues_found)}):"
                )
                for issue in issues_found[:5]:
                    summary_lines.append(f"  - {issue}")
                if len(issues_found) > 5:
                    summary_lines.append(f"  ... and {len(issues_found) - 5} more")
                summary_lines.append("")

            # Critical security issues
            if security_issues:
                critical_sec = [s for s in security_issues if "CRITICAL" in s or "HIGH" in s]
                if critical_sec:
                    summary_lines.append(f"🔒 Critical Security ({len(critical_sec)}):")
                    for sec in critical_sec[:3]:
                        summary_lines.append(f"  - {sec}")
                    summary_lines.append("")

            if doc_missing > 0:
                summary_lines.append(f"📝 {doc_missing} missing docstrings\n")

            summary_lines.append(f"🔗 {storage_status}")
            summary_lines.append("\n💡 Use verbosity='verbose' for full report")
            vibe_summary = "\n".join(summary_lines)

        return create_success_result(
            message=vibe_summary,
            data={
                "vibe_score": final_score,
                "tier": tier,
                "vibe_summary": vibe_summary,
            },
        )

    # === boring_impact_check ===
    @mcp.tool(
        description="衝擊分析 (Impact Analysis). "
        "說: 'Check impact of modifying utils.py', '改這隻檔案會影響誰', 'Impact check'. "
        "我會分析反向依賴 (支援多層追蹤)，告訴你修改此檔案會影響哪些模組，並給出驗證 Prompt！ "
        "🆕 V10.21: 整合 RAG 語義分析更精準！",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_impact_check(
        target_path: Annotated[str, Field(description="計畫修改的目標檔案")],
        project_path: Annotated[Optional[str], Field(description="專案根目錄 (自動偵測)")] = None,
        max_depth: Annotated[
            int, Field(description="追蹤深度 (1=直接依賴, 2=間接依賴, 預設 2)")
        ] = 2,
    ) -> BoringResult:
        """
        📡 Impact Analysis - 預判修改帶來的全局衝擊。
        Reverse Dependency Analysis with multi-level tracking (Phase 15 Enhancement).

        V10.21 整合:
        - RAG 語義搜尋: 找出語義相關的檔案（不只是 import）
        - 更精準的衝擊分析
        """
        root_str, error = _get_project_root_or_error(project_path)
        if error:
            return create_error_result(error.get("message", "Unknown error"))

        project_root = Path(root_str)
        # Handle both absolute and relative paths
        if target_path != "." and (
            target_path.startswith("/") or (len(target_path) > 1 and target_path[1] == ":")
        ):
            target = Path(target_path)
        elif target_path == ".":
            target = project_root
        else:
            target = project_root / target_path

        if not target.exists() or not target.is_file():
            return create_error_result(f"❌ 找不到目標檔案: {target_path}")

        # 1. 識別目標特徵 for fuzzy matching
        target_stem = target.stem  # e.g., "utils"
        rel_target = target.relative_to(project_root).as_posix()

        # V10.21: RAG 語義分析 - 找出語義相關的檔案
        semantic_related = []
        rag = _get_rag_retriever(project_root)
        if rag:
            try:
                # 讀取目標檔案內容，提取關鍵詞
                target_content = target.read_text(encoding="utf-8", errors="ignore")[:500]

                # 語義搜尋相關函數/類別
                results = rag.retrieve(
                    query=f"{target_stem} {target_content[:100]}",
                    top_k=5,
                    chunk_types=["function", "class"],
                )
                for r in results:
                    if r.chunk.file_path != str(target):
                        rel_path = Path(r.chunk.file_path).relative_to(project_root).as_posix()
                        if rel_path not in semantic_related:
                            semantic_related.append(rel_path)
            except Exception:
                pass  # RAG is optional enhancement

        # 2. 全專案掃描建立完整依賴圖
        files_to_scan = [
            p
            for p in project_root.rglob("*")
            if p.is_file()
            and p.suffix in [".py", ".js", ".ts", ".jsx", ".tsx"]
            and not any(
                x in p.parts
                for x in ["node_modules", ".git", "venv", "__pycache__", "dist", "build"]
            )
        ]

        # Build dependency graph: { file_rel_path -> [dependencies] }
        dep_graph = {}
        file_stems = {}  # stem -> [rel_paths]

        for f in files_to_scan:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                deps = vibe_engine.extract_dependencies(str(f), content)
                f_rel = f.relative_to(project_root).as_posix()
                dep_graph[f_rel] = deps

                # Index by stem for fuzzy matching
                stem = f.stem
                if stem not in file_stems:
                    file_stems[stem] = []
                file_stems[stem].append(f_rel)
            except Exception:
                continue

        # 3. Fuzzy matching helper
        def matches_target(dep: str, target_stem: str) -> bool:
            if target_stem == dep:
                return True
            if dep.endswith(f".{target_stem}"):
                return True
            if dep.endswith(f"/{target_stem}"):
                return True
            return False

        # 4. Build reverse dependency graph (who imports what)
        # direct_dependents: files that directly import target
        direct_dependents = set()
        for f_rel, deps in dep_graph.items():
            if f_rel == rel_target:
                continue
            for dep in deps:
                if matches_target(dep, target_stem):
                    direct_dependents.add(f_rel)
                    break

        # 5. Multi-level impact tracking (Phase 15 Enhancement)
        all_affected = set(direct_dependents)
        indirect_dependents = set()

        if max_depth >= 2:
            # Level 2: Find files that import direct_dependents
            for direct_dep in direct_dependents:
                direct_stem = Path(direct_dep).stem
                for f_rel, deps in dep_graph.items():
                    if f_rel in all_affected or f_rel == rel_target:
                        continue
                    for dep in deps:
                        if matches_target(dep, direct_stem):
                            indirect_dependents.add(f_rel)
                            all_affected.add(f_rel)
                            break

        # Level 3 (if max_depth >= 3)
        level3_dependents = set()
        if max_depth >= 3:
            for indirect_dep in indirect_dependents:
                indirect_stem = Path(indirect_dep).stem
                for f_rel, deps in dep_graph.items():
                    if f_rel in all_affected or f_rel == rel_target:
                        continue
                    for dep in deps:
                        if matches_target(dep, indirect_stem):
                            level3_dependents.add(f_rel)
                            all_affected.add(f_rel)
                            break

        # 6. 評估衝擊等級
        impact_level = "Low"
        if len(all_affected) > 10:
            impact_level = "Critical"
        elif len(all_affected) > 5:
            impact_level = "High"
        elif len(all_affected) > 0:
            impact_level = "Medium"

        # 7. Mermaid 圖形輸出
        mermaid_lines = ["graph TD", f'    Target["{rel_target}"]:::target']

        # Direct impacts
        for imp in list(direct_dependents)[:15]:
            sanitized_imp = imp.replace("/", "_").replace(".", "_").replace("-", "_")
            mermaid_lines.append(f'    {sanitized_imp}["{imp}"]:::direct -->|L1| Target')

        # Indirect impacts
        for imp in list(indirect_dependents)[:10]:
            sanitized_imp = imp.replace("/", "_").replace(".", "_").replace("-", "_")
            mermaid_lines.append(f'    {sanitized_imp}["{imp}"]:::indirect -->|L2| ...')

        mermaid_lines.append("    classDef target fill:#f96,stroke:#333")
        mermaid_lines.append("    classDef direct fill:#ff9,stroke:#333")
        mermaid_lines.append("    classDef indirect fill:#9ff,stroke:#333")
        mermaid_graph = "\n".join(mermaid_lines)

        # 8. Fix/Verification Prompt
        verify_prompt = ""
        if all_affected:
            verify_prompt = (
                f"⚠️ Impact Warning: Modifying `{rel_target}` affects {len(all_affected)} files.\n\n"
            )

            if direct_dependents:
                verify_prompt += (
                    f"🔴 **Direct Dependents (L1)** - {len(direct_dependents)} files:\n"
                )
                for aff in list(direct_dependents)[:5]:
                    verify_prompt += f"   - `{aff}`\n"
                if len(direct_dependents) > 5:
                    verify_prompt += f"   - ... and {len(direct_dependents) - 5} more.\n"

            if indirect_dependents:
                verify_prompt += (
                    f"\n🟡 **Indirect Dependents (L2)** - {len(indirect_dependents)} files:\n"
                )
                for aff in list(indirect_dependents)[:5]:
                    verify_prompt += f"   - `{aff}`\n"
                if len(indirect_dependents) > 5:
                    verify_prompt += f"   - ... and {len(indirect_dependents) - 5} more.\n"

            # V10.21: 加入 RAG 語義相關檔案
            if semantic_related:
                verify_prompt += (
                    f"\n🧠 **Semantically Related (RAG)** - {len(semantic_related)} files:\n"
                )
                for sem in semantic_related[:3]:
                    verify_prompt += f"   - `{sem}`\n"

            verify_prompt += (
                "\n📋 **Action Required**: Run tests for these files after your changes."
            )
        else:
            verify_prompt = f"✅ Low Impact: `{rel_target}` appears to have no internal dependents."

        rag_status = (
            f"✅ RAG 語義分析 ({len(semantic_related)} 相關)"
            if semantic_related
            else "⚠️ RAG 未啟用"
        )

        return create_success_result(
            message=f"📡 Impact Analysis: {rel_target}\nImpact Level: {impact_level}\nDirect Dependent Count: {len(direct_dependents)}\nIndirect Dependent Count: {len(indirect_dependents)}\n{rag_status}\n\n{verify_prompt}",
            data={
                "impact_level": impact_level,
                "affected_count": len(all_affected),
                "direct_count": len(direct_dependents),
                "indirect_count": len(indirect_dependents),
                "semantic_related_count": len(semantic_related),
                "rag_enhanced": bool(semantic_related),
                "affected_files": list(all_affected),
                "direct_dependents": list(direct_dependents),
                "indirect_dependents": list(indirect_dependents),
                "semantic_related": semantic_related,
                "mermaid": mermaid_graph,
                "vibe_summary": f"📡 **Impact Analysis**: `{rel_target}`\n"
                f"⚠️ **Impact Level**: {impact_level}\n"
                f"🔗 **Direct (L1)**: {len(direct_dependents)}\n"
                f"🔗 **Indirect (L2+)**: {len(indirect_dependents)}\n"
                f"🧠 **Semantic (RAG)**: {len(semantic_related)}\n"
                f"🔗 {rag_status}",
                "suggested_fix_prompt": verify_prompt,
            },
        )

    # =========================================================================
    # V10.22: Intelligence Tools
    # =========================================================================

    @mcp.tool(
        description="🔮 預測可能的錯誤 (Predict likely errors before running). "
        "說: '預測這個檔案會有什麼錯誤', 'predict errors for auth.py'. "
        "我會分析歷史模式，預測最可能發生的錯誤並提供預防建議！",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_predict_errors(
        file_path: Annotated[str, Field(description="要預測錯誤的檔案路徑")],
        limit: Annotated[int, Field(description="最多返回幾個預測")] = 5,
        project_path: Annotated[Optional[str], Field(description="專案根目錄")] = None,
    ) -> BoringResult:
        """
        🔮 預測錯誤 - 根據歷史模式預測可能發生的錯誤。

        V10.22 Intelligence:
        - 分析檔案類型與過去錯誤的關聯
        - 提供信心分數和預防建議
        - 學習專案特定的錯誤模式
        """
        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return create_error_result(error.get("message", "Unknown error"))

        # Try to use PredictiveAnalyzer
        predictions = []
        try:
            from ..intelligence import PredictiveAnalyzer

            analyzer = PredictiveAnalyzer(project_root)
            predictions = analyzer.predict_errors(file_path, limit)
        except ImportError:
            pass

        # Fallback to storage-based prediction
        if not predictions:
            storage = _get_storage(project_root)
            if storage:
                predictions_data = storage.get_error_predictions(file_path, limit)
                for p in predictions_data:
                    predictions.append(type("Prediction", (), p)())

        if not predictions:
            return create_error_result(
                f"📊 尚無足夠歷史資料進行預測。繼續使用系統累積資料！\n檔案: {file_path}",
                error_details="NO_DATA",
            )

        # Format results
        result_items = []
        for p in predictions:
            result_items.append(
                {
                    "error_type": p.error_type
                    if hasattr(p, "error_type")
                    else p.get("error_type", "Unknown"),
                    "confidence": getattr(p, "confidence", p.get("confidence", 0.5)),
                    "message": getattr(p, "predicted_message", p.get("message", "")),
                    "prevention_tip": getattr(p, "prevention_tip", p.get("prevention_tip", "")),
                    "frequency": getattr(p, "historical_frequency", p.get("frequency", 0)),
                }
            )

        # Build summary
        top = result_items[0] if result_items else None
        summary = f"🔮 **Error Predictions for** `{file_path}`\n\n"
        for i, item in enumerate(result_items[:5], 1):
            conf_bar = (
                "🟢" if item["confidence"] >= 0.7 else "🟡" if item["confidence"] >= 0.4 else "⚪"
            )
            summary += f"{i}. {conf_bar} **{item['error_type']}** ({item['confidence'] * 100:.0f}% confidence)\n"
            summary += f"   💡 {item['prevention_tip']}\n"

        return create_success_result(
            message=summary,
            data={
                "predictions": result_items,
                "top_prediction": top,
                "file_path": file_path,
                "vibe_summary": summary,
            },
        )

    @mcp.tool(
        description="📊 專案健康評分 (Project health score). "
        "說: '專案健康狀況', '給我健康報告', 'project health score'. "
        "我會分析成功率、錯誤趨勢、解決率，給出綜合健康評分！",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_health_score(
        project_path: Annotated[Optional[str], Field(description="專案根目錄")] = None,
    ) -> BoringResult:
        """
        📊 專案健康評分 - 綜合分析專案狀態。

        V10.22 Intelligence:
        - 成功率分析 (40% 權重)
        - 錯誤解決率 (30% 權重)
        - 執行效率 (30% 權重)
        - 趨勢分析和建議
        """
        root_str, error = _get_project_root_or_error(project_path)
        if error:
            return create_error_result(error.get("message", "Unknown error"))
        project_root = Path(root_str)

        storage = _get_storage(project_root)
        if not storage:
            return create_error_result("Storage 未初始化")

        # Get health score
        health = storage.get_health_score()

        # Get error trend
        trend = storage.get_error_trend(days=7)

        # Build detailed report
        score = health["score"]
        grade = health["grade"]

        # Emoji for grade
        grade_emoji = {
            "A+": "🏆",
            "A": "🌟",
            "B": "✅",
            "C": "👍",
            "D": "⚠️",
            "F": "🚨",
            "N/A": "📊",
        }.get(grade, "📊")

        breakdown = health.get("breakdown", {})

        summary = f"""# {grade_emoji} 專案健康報告

## 綜合評分: **{score}/100** (等級: {grade})

{health["message"]}

## 📈 指標分解
- 成功率: **{breakdown.get("success_rate", "N/A")}%**
- 錯誤解決率: **{breakdown.get("resolution_rate", "N/A")}%**
- 平均執行時間: **{breakdown.get("avg_loop_duration", "N/A")}s**

## 📊 錯誤趨勢 (7天)
- 趨勢方向: {trend.get("emoji", "➡️")} {trend.get("trend", "N/A")}
- 變化幅度: {trend.get("change_percent", 0)}%
- {trend.get("recommendation", "")}
"""

        return create_success_result(
            message=summary,
            data={
                "score": score,
                "grade": grade,
                "breakdown": breakdown,
                "trend": trend,
                "vibe_summary": summary,
            },
        )

    @mcp.tool(
        description="🧠 優化上下文 (Optimize context for LLM). "
        "說: '幫我壓縮這些程式碼', 'optimize context'. "
        "我會智能壓縮程式碼上下文，減少 token 使用同時保留關鍵資訊！",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_optimize_context(
        file_paths: Annotated[list[str], Field(description="要優化的檔案路徑列表")],
        max_tokens: Annotated[int, Field(description="最大 token 限制")] = 8000,
        error_message: Annotated[
            Optional[str], Field(description="相關錯誤訊息 (最高優先級)")
        ] = None,
        project_path: Annotated[Optional[str], Field(description="專案根目錄")] = None,
    ) -> BoringResult:
        """
        🧠 上下文優化 - 智能壓縮程式碼以減少 token 使用。

        V10.22 Intelligence:
        - 去重複內容
        - 優先保留關鍵程式碼
        - 壓縮文檔和註釋
        - 保持語義完整性
        """
        root_str, error = _get_project_root_or_error(project_path)
        if error:
            return create_error_result(error.get("message", "Unknown error"))
        project_root = Path(root_str)

        try:
            from ..intelligence import SmartContextBuilder

            builder = SmartContextBuilder(max_tokens=max_tokens, project_root=project_root)
        except ImportError:
            return create_error_result("Intelligence 模組未安裝")

        # Add error context (highest priority)
        if error_message:
            builder.with_error(error_message, priority=1.0)

        # Add code files
        for fp in file_paths:
            try:
                path = Path(project_root) / fp if not Path(fp).is_absolute() else Path(fp)
                if path.exists():
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    rel_path = (
                        str(path.relative_to(project_root))
                        if path.is_relative_to(project_root)
                        else str(path)
                    )
                    builder.with_code_file(rel_path, content, priority=0.8)
            except Exception:
                continue

        # Build optimized context
        optimized = builder.build()
        report = builder.get_compression_report()
        stats = builder.stats

        return create_success_result(
            message=report,
            data={
                "optimized_context": optimized,
                "stats": {
                    "original_tokens": stats.original_tokens if stats else 0,
                    "optimized_tokens": stats.optimized_tokens if stats else 0,
                    "compression_ratio": stats.compression_ratio if stats else 1.0,
                    "sections_removed": stats.sections_removed if stats else 0,
                    "duplicates_merged": stats.duplicates_merged if stats else 0,
                },
                "vibe_summary": report,
            },
        )

    return {
        "boring_test_gen": boring_test_gen,
        "boring_code_review": boring_code_review,
        "boring_perf_tips": boring_perf_tips,
        "boring_arch_check": boring_arch_check,
        "boring_doc_gen": boring_doc_gen,
        "boring_vibe_check": boring_vibe_check,
        "boring_impact_check": boring_impact_check,
        # V10.22 Intelligence Tools
        "boring_predict_errors": boring_predict_errors,
        "boring_health_score": boring_health_score,
        "boring_optimize_context": boring_optimize_context,
    }
