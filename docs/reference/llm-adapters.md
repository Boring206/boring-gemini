# LLM 適配器開發指南 (LLM Adapter Development Guide)

> **解決風險**: 對特定技術棧 (Gemini) 的強依賴

本指南說明如何為 Boring-Gemini 添加新的 LLM Provider，實現技術棧多元化。

---

## 🎯 概述

Boring-Gemini 使用抽象的 `LLMProvider` 介面來支持多種語言模型後端：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LLM Provider 架構                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                        ┌─────────────────┐                                  │
│                        │   LLMProvider   │                                  │
│                        │    (Abstract)   │                                  │
│                        └────────┬────────┘                                  │
│                                 │                                            │
│     ┌───────────────┬───────────┼───────────┬───────────────┐               │
│     ▼               ▼           ▼           ▼               ▼               │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐      │
│ │  Gemini   │ │  Ollama   │ │  OpenAI   │ │  Claude   │ │   你的    │      │
│ │  Provider │ │  Provider │ │  Compat   │ │  Adapter  │ │  Provider │      │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 核心介面

### LLMProvider (抽象基類)

位置: `src/boring/llm/provider.py`

```python
from abc import abstractmethod
from boring.interfaces import LLMClient, LLMResponse


class LLMProvider(LLMClient):
    """
    Extended LLM Client interface that allows for more flexible configuration
    and swapping of backends (Gemini, Ollama, LMStudio, etc.)
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the specific model being used"""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider/CLI is available and configured"""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        timeout_seconds: int = 600,
    ) -> tuple[str, bool]:
        """
        Generate text from prompt and context.
        
        Returns:
            tuple[str, bool]: (generated_text, success)
        """
        pass

    @abstractmethod
    def generate_with_tools(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        timeout_seconds: int = 600,
    ) -> LLMResponse:
        """
        Generate text and/or function calls.
        
        Returns:
            LLMResponse with text and function_calls
        """
        pass

    def get_token_usage(self) -> dict[str, int]:
        """Return token usage statistics if available"""
        return {}
```

### LLMResponse (數據模型)

位置: `src/boring/interfaces.py`

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    text: str = ""
    function_calls: list[dict[str, Any]] = field(default_factory=list)
    success: bool = True
    error: str = ""
    raw_response: Any = None
```

---

## 🚀 實現新的 Provider

### 步驟 1: 創建 Provider 文件

在 `src/boring/llm/` 創建新文件，例如 `my_provider.py`:

```python
"""
My Custom LLM Provider Implementation
"""

from pathlib import Path
from typing import Optional

from ..logger import get_logger
from .provider import LLMProvider, LLMResponse

_logger = get_logger("my_provider")


class MyProvider(LLMProvider):
    """
    Provider for My Custom LLM Service.
    """

    def __init__(
        self,
        model_name: str = "my-model-v1",
        api_key: Optional[str] = None,
        base_url: str = "https://api.my-llm.com",
        log_dir: Optional[Path] = None,
    ):
        self._model_name = model_name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.log_dir = log_dir or Path("logs")
        
        # Initialize your client here
        self._client = None
        if self.api_key:
            self._client = self._initialize_client()

    def _initialize_client(self):
        """Initialize the API client"""
        # Your initialization logic
        pass

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider_name(self) -> str:
        """Optional: Provider identifier"""
        return "my_provider"

    @property
    def is_available(self) -> bool:
        """Check if the provider is available and configured"""
        if not self.api_key:
            return False
        try:
            # Perform a health check
            # e.g., ping the API
            return True
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        timeout_seconds: int = 600,
    ) -> tuple[str, bool]:
        """
        Generate text using the LLM.
        
        Args:
            prompt: The user's prompt
            context: Additional context (code, documentation, etc.)
            system_instruction: System-level instructions
            timeout_seconds: Request timeout
            
        Returns:
            tuple[str, bool]: (generated_text, success)
        """
        if not self.is_available:
            return "Error: Provider not available", False

        try:
            # Build the full prompt
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            
            # Make the API call
            response = self._call_api(full_prompt, system_instruction, timeout_seconds)
            
            return response, True

        except Exception as e:
            _logger.error(f"Generation failed: {e}")
            return str(e), False

    def generate_with_tools(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        timeout_seconds: int = 600,
    ) -> LLMResponse:
        """
        Generate text with function calling support.
        
        If your provider doesn't support native function calling,
        you can parse tool calls from the text response.
        """
        text, success = self.generate(prompt, context, system_instruction, timeout_seconds)
        
        # If your provider supports function calling natively:
        # function_calls = self._extract_function_calls(raw_response)
        
        return LLMResponse(
            text=text,
            function_calls=[],  # Populate if supported
            success=success,
        )

    def _call_api(
        self, prompt: str, system_instruction: str, timeout: int
    ) -> str:
        """Make the actual API call"""
        import requests
        
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def get_token_usage(self) -> dict[str, int]:
        """Return token usage if tracked"""
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
```

### 步驟 2: 註冊 Provider

在 `src/boring/llm/__init__.py` 中導出:

```python
from .my_provider import MyProvider

__all__ = [
    "LLMProvider",
    "GeminiProvider",
    "OllamaProvider",
    "MyProvider",  # 新增
]
```

### 步驟 3: 添加配置支持

在 `src/boring/config.py` 添加配置:

```python
# 新 Provider 設置
MY_PROVIDER_API_KEY: Optional[str] = os.getenv("MY_PROVIDER_API_KEY")
MY_PROVIDER_MODEL: str = os.getenv("MY_PROVIDER_MODEL", "my-model-v1")
MY_PROVIDER_BASE_URL: str = os.getenv(
    "MY_PROVIDER_BASE_URL", "https://api.my-llm.com"
)
```

### 步驟 4: 添加 Provider 選擇邏輯

在需要使用 LLM 的地方添加選擇邏輯:

```python
from boring.config import settings
from boring.llm import GeminiProvider, OllamaProvider, MyProvider


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider with fallback chain"""
    
    # Priority: Gemini > MyProvider > Ollama (local)
    providers = [
        lambda: GeminiProvider() if settings.GOOGLE_API_KEY else None,
        lambda: MyProvider() if settings.MY_PROVIDER_API_KEY else None,
        lambda: OllamaProvider("llama3.2") if OllamaProvider("llama3.2").is_available else None,
    ]
    
    for get_provider in providers:
        provider = get_provider()
        if provider and provider.is_available:
            return provider
    
    raise RuntimeError("No LLM provider available")
```

---

## 🧪 測試你的 Provider

### 單元測試

創建 `tests/unit/llm/test_my_provider.py`:

```python
import pytest
from unittest.mock import Mock, patch

from boring.llm.my_provider import MyProvider


class TestMyProvider:
    """Tests for MyProvider"""

    def test_initialization(self):
        """Test provider initialization"""
        provider = MyProvider(
            model_name="test-model",
            api_key="test-key",
        )
        assert provider.model_name == "test-model"
        assert provider.api_key == "test-key"

    def test_is_available_without_key(self):
        """Test availability check without API key"""
        provider = MyProvider(api_key=None)
        assert provider.is_available is False

    @patch("boring.llm.my_provider.requests.post")
    def test_generate_success(self, mock_post):
        """Test successful generation"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Hello, World!"}}]
        }

        provider = MyProvider(api_key="test-key")
        text, success = provider.generate("Say hello")

        assert success is True
        assert "Hello" in text

    @patch("boring.llm.my_provider.requests.post")
    def test_generate_failure(self, mock_post):
        """Test generation failure handling"""
        mock_post.side_effect = Exception("API Error")

        provider = MyProvider(api_key="test-key")
        text, success = provider.generate("Say hello")

        assert success is False
        assert "Error" in text or "API Error" in text
```

### 整合測試

創建 `tests/integration/test_my_provider_integration.py`:

```python
import os
import pytest

from boring.llm.my_provider import MyProvider


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("MY_PROVIDER_API_KEY"),
    reason="MY_PROVIDER_API_KEY not set"
)
class TestMyProviderIntegration:
    """Integration tests for MyProvider (requires real API key)"""

    def test_real_generation(self):
        """Test real API call"""
        provider = MyProvider(api_key=os.getenv("MY_PROVIDER_API_KEY"))
        
        text, success = provider.generate("What is 2+2? Reply with just the number.")
        
        assert success is True
        assert "4" in text
```

---

## 📋 實現檢查清單

在提交 PR 前確認:

- [ ] 實現了 `LLMProvider` 的所有抽象方法
- [ ] 處理了 API 錯誤和超時
- [ ] 添加了適當的日誌記錄
- [ ] 配置通過環境變量讀取
- [ ] 有 `is_available` 健康檢查
- [ ] 編寫了單元測試 (≥80% 覆蓋)
- [ ] 編寫了整合測試 (可選，需真實 API)
- [ ] 更新了 `docs/reference/feature-matrix.md`
- [ ] 更新了 `pyproject.toml` 添加可選依賴 (如需)
- [ ] 更新了 README 說明新 Provider

---

## 🔄 功能降級策略

### 降級鏈

```
Gemini (雲端) → Ollama (本地) → 功能禁用
     │              │              │
     ▼              ▼              ▼
  API Key       本地運行        錯誤提示
```

### 實現降級

```python
def generate_with_fallback(prompt: str) -> tuple[str, bool]:
    """Generate with automatic fallback to available providers"""
    
    providers = [
        ("gemini", lambda: GeminiProvider()),
        ("ollama", lambda: OllamaProvider("llama3.2")),
    ]
    
    for name, get_provider in providers:
        try:
            provider = get_provider()
            if provider.is_available:
                return provider.generate(prompt)
        except Exception as e:
            _logger.warning(f"Provider {name} failed: {e}")
            continue
    
    return "Error: All LLM providers unavailable", False
```

---

## 🏷️ 現有 Provider 參考

| Provider | 文件 | 特點 |
|----------|------|------|
| `GeminiProvider` | `gemini.py` | SDK + CLI 雙模式 |
| `OllamaProvider` | `ollama.py` | 本地運行，無需 API Key |
| `OpenAICompatProvider` | `openai_compat.py` | 通用 OpenAI 兼容 API |
| `ClaudeAdapter` | `claude_adapter.py` | Anthropic Claude |

---

## 🤝 貢獻

如果你實現了新的 Provider，歡迎提交 PR！

請確保:
1. 遵循本指南的規範
2. 通過所有測試
3. 更新文檔

詳見- [Contributing Guide](./contributing.md)

---

*最後更新: 2026-01-12 | 版本: 1.0.0*
