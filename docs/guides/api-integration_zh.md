# Boring Python API 開發與整合指南 (V10.26)

> 將 Boring 的智慧 (Intelligence)、評估 (Judge) 與安全 (Shadow Mode) 直接嵌入您的 Python 應用程式中。

Boring-Gemini 不僅僅是一個 CLI 工具，它也是一個模組化的 Python 庫。您可以將其核心模組導入到您自己的 AI 應用程式或自動化腳本中。

## 📦 安裝

```bash
pip install boring-aicoding
```

## 🧠 Intelligence API (大腦與記憶)

`boring.intelligence` 模組提供了知識管理、模式學習和向量記憶功能。

### 1. 管理知識庫 (BrainManager)

使用 `BrainManager` 來存取或更新 `.boring/brain` 中的長期記憶與學習模式。

```python
from boring.intelligence.brain_manager import BrainManager, LearnedPattern

# 初始化 (自動載入 .boring/brain)
brain = BrainManager(project_path="./my_project")

# 1. 查詢已學習的模式 (Pattern Mining)
patterns = brain.get_patterns(category="error_handling")
for p in patterns:
    print(f"Pattern [{p.confidence}]: {p.description}")

# 2. 記錄新學到的知識
new_pattern = LearnedPattern(
    trigger="ConnectionError",
    solution="Implement exponential backoff in retry logic",
    confidence=0.9
)
brain.learn_pattern(new_pattern)
```

### 2. 混合 RAG (RAGRetriever)

使用高階的 `RAGRetriever` 進行語義搜尋與依賴擴展。

```python
from boring.rag.rag_retriever import RAGRetriever

retriever = RAGRetriever(project_path=".")

# 語義搜尋 (RAG)
results = retriever.search("safe file handling", top_k=3)
for res in results:
    print(f"Found in {res['path']}: {res['snippet']}")
```

---

## ⚖️ Judge API (評估與準則)

`boring.judge` 模組提供了結構化的評估框架，適合用於 LLM 輸出的品質控管。

### 定義評估準則 (Rubric)

您可以定義自己的 `Rubric` 並將其應用於評估流程。

```python
from boring.judge.rubrics import Rubric, Criterion

# 1. 定義準則
security_rubric = Rubric(
    name="API Security",
    criteria=[
        Criterion(name="Auth", description="Standard OIDC/OAuth2 usage", weight=1.0),
        Criterion(name="Validation", description="Input sanitization", weight=0.8),
        Criterion(name="Logging", description="No secrets in logs", weight=1.0),
    ]
)

# 2. 導出為 Markdown (供 LLM 使用)
print(security_rubric.to_markdown())

# 3. 程式化評分 (如果已有 Score 物件)
# score = evaluator.evaluate(code, security_rubric)
```

---

## 🛡️ Loop API (工作流與安全)

`boring.loop` 模組提供了安全防護和原子操作，非常適合構建強健的自動化腳本。

### 1. Shadow Mode 保護 (ShadowModeGuard)

將您的腳本包裹在 Shadow Mode 中，防止意外的毀滅性操作。

```python
from boring.loop.shadow_mode import ShadowModeGuard, OperationSeverity, ShadowModeLevel

# 初始化守衛 (嚴格模式)
guard = ShadowModeGuard(level=ShadowModeLevel.STRICT)

# 嘗試執行操作
def delete_database():
    op = guard.create_operation(
        type="delete",
        target="./data.db",
        severity=OperationSeverity.CRITICAL
    )
    
    if guard.allow(op):
        print("Deleting...")
        # os.remove("./data.db")
    else:
        print(f"Operation blocked: {op.reason}")

delete_database()
# Output: Operation blocked: High severity requires approval in STRICT mode
```

### 2. 原子交易 (TransactionManager)

確保一組檔案操作要麼全部成功，要麼全部回滾。

```python
from boring.loop.transactions import TransactionManager

tx = TransactionManager(project_path=".")

with tx.begin() as transaction:
    try:
        # 這些操作會先寫入暫存區
        transaction.write("config.py", "DEBUG = False")
        transaction.write("src/main.py", "import config")
        
        # 提交 (原子寫入)
        transaction.commit()
        print("原子更新成功")
        
    except Exception as e:
        # 自動回滾 (不修改任何檔案)
        transaction.rollback()
        print(f"更新失敗，已回滾: {e}")
```
