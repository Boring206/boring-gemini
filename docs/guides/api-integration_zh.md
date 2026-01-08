# API 整合指南

> 將 Boring 的智慧直接嵌入您的 Python 腳本與工作流程中。

---

## 🛠️ 基礎引用 (Imports)

Boring 的所有核心邏輯都可以透過 `boring` 套件存取。

### 核心模組
| 模組路徑 | 用途 | 關鍵類別 (Classes) |
|----------|------|--------------------|
| `boring.rag` | 理解代碼庫內容 | `RAGRetriever`, `IndexManager` |
| `boring.agents` | 自主執行邏輯 | `StatefulAgentLoop`, `CoderAgent` |
| `boring.security` | 安全與攔截 | `ShadowInterceptor` |
| `boring.mcp` | 生態系工具整合 | `SpeckitManager`, `McpServer` |

---

## 🚀 實戰範例：自動化專案摘要生成器

此腳本展示如何使用 RAG API 掃描專案並生成一份高階摘要文件。

### `summarize_project.py`

```python
import os
from boring.rag.retriever import RAGRetriever

def generate_report(project_dir: str):
    # 1. 初始化 RAG（會使用現有索引或自動掃描）
    retriever = RAGRetriever(project_path=project_dir)
    
    print(f"🔍 正在分析專案路徑: {project_dir}...")
    
    # 向 Boring 詢問核心功能
    queries = [
        "這個應用程式的主要入口點在哪裡？",
        "使用了哪些外部套件來處理網路或資料庫？",
        "驗證 (Authentication) 邏輯是如何實作的？"
    ]
    
    report_content = "# Project AI 專案分析報告\n\n"
    
    for q in queries:
        report_content += f"### {q}\n"
        # 這裡就是 API 的威力：語意搜尋
        results = retriever.search(q, max_results=2)
        
        if not results:
            report_content += "_找不到相關代碼。_\n\n"
            continue
            
        for doc in results:
            report_content += f"- **檔案**: `{doc.file_path}`\n"
            # 在實際應用中，您可以將 doc.content 傳送給 LLM 進行總結
            report_content += f"  - 相關內容摘要: {doc.content[:150].strip()}...\n\n"

    # 3. 儲存報告
    with open("PROJECT_SUMMARY.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print("✅ 報告已生成: PROJECT_SUMMARY.md")

if __name__ == "__main__":
    generate_report(".")
```

---

## ⚙️ 進階應用：在 CI 中加入品質閘道 (Quality Gates)

您可以使用 `Verifier` API，在程式碼不符規範時自動讓 CI 失敗。

```python
from boring.core.verifier import ParallelVerifier

verifier = ParallelVerifier(project_path=".")
results = verifier.verify_all()

if not results.passed:
    print(f"❌ 驗證失敗：發現 {len(results.issues)} 個問題。")
    for issue in results.issues:
        print(f"  - [{issue.category}] {issue.message}")
    exit(1)

print("🚀 所有品質檢查均已通過！")
```

---

## 💡 專家建議

1.  **環境變數**：許多 API 會尊重 `BORING_LOG_LEVEL` 或 `SHADOW_MODE_LEVEL` 等環境變數設定。
2.  **單例模式 (Singleton)**：像是 `RAGRetriever` 會在內部處理索引快取，因此您不需要擔心重複掃描造成的效能損失。
3.  **非同步支援**：對於需要高性能的整合，可以查看 `boring.agents` 模組中的 `async` 方法。
