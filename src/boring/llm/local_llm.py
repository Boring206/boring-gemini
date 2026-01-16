"""
Local LLM Integration for Boring V13.2

Provides local LLM inference using llama-cpp-python for offline operation.
Supports GGUF models (Phi-3, Qwen, Llama, Mistral, etc.)

Features:
- Zero-network operation after setup
- Automatic model download helpers
- Smart routing between local and API models
- Memory-efficient inference
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default model recommendations (sorted by size, smallest first)
# Default model recommendations (sorted by size, smallest first)
RECOMMENDED_MODELS = {
    "qwen2.5-coder-1.5b": {
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q8_0.gguf",
        "size_mb": 1800,
        "context": 32768,
        "description": "Best lightweight coding model (Ultra-fast)",
    },
    "deepseek-coder-v2-lite": {
        "url": "https://huggingface.co/bartowski/DeepSeek-Coder-V2-Lite-Instruct-GGUF/resolve/main/DeepSeek-Coder-V2-Lite-Instruct-Q4_K_M.gguf",
        "size_mb": 8900,
        "context": 65536,
        "description": "SOTA open source coding model (Requires 16GB+ RAM)",
    },
    "qwen2.5-coder-7b": {
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "size_mb": 5600,
        "context": 32768,
        "description": "Balanced performance and speed (Recommended for 8GB+ RAM)",
    },
    "llama-3.2-3b": {
        "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "size_mb": 2400,
        "context": 131072,
        "description": "Great general purpose reasoning",
    },
}


class LocalLLM:
    """
    Local LLM inference wrapper using llama-cpp-python.

    Usage:
        llm = LocalLLM.from_settings()
        if llm.is_available:
            response = llm.complete("Write a Python function to...")
    """

    _instance: Optional["LocalLLM"] = None

    def __init__(
        self,
        model_path: str | None = None,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,  # Auto-detect
        verbose: bool = False,
    ):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.verbose = verbose
        self._llm: Any = None
        self._available: bool | None = None

    @classmethod
    def from_settings(cls) -> "LocalLLM":
        """Create LocalLLM from Boring settings.

        Checks BORING_OFFLINE_MODE environment variable and settings.OFFLINE_MODE
        to determine if local LLM should be prioritized.
        """
        if cls._instance is not None:
            return cls._instance

        try:
            from ..core.config import settings

            model_path = settings.LOCAL_LLM_MODEL
            n_ctx = settings.LOCAL_LLM_CONTEXT_SIZE

            # V14.0: Enhanced OFFLINE_MODE support
            offline_mode = (
                settings.OFFLINE_MODE or os.environ.get("BORING_OFFLINE_MODE", "").lower() == "true"
            )

            # If offline mode is enabled and no model configured, try to find one
            if offline_mode and not model_path:
                available = list_available_models()
                if available:
                    model_path = available[0]["path"]
                    logger.info(f"OFFLINE_MODE: Auto-selected local model: {model_path}")

        except (ImportError, AttributeError):
            model_path = os.environ.get("BORING_LOCAL_LLM_MODEL")
            n_ctx = int(os.environ.get("BORING_LOCAL_LLM_CONTEXT_SIZE", "4096"))

        cls._instance = cls(model_path=model_path, n_ctx=n_ctx)
        return cls._instance

    @property
    def is_available(self) -> bool:
        """Check if local LLM is available and configured."""
        if self._available is not None:
            return self._available

        # Check if llama-cpp-python is installed
        try:
            import llama_cpp  # noqa: F401
        except ImportError:
            self._available = False
            return False

        # Check if model is configured and exists
        if not self.model_path:
            self._available = False
            return False

        model_file = Path(self.model_path)
        if not model_file.exists():
            logger.warning(f"Local LLM model not found: {self.model_path}")
            self._available = False
            return False

        self._available = True
        return True

    def _ensure_loaded(self) -> bool:
        """Ensure the model is loaded."""
        if self._llm is not None:
            return True

        if not self.is_available:
            return False

        try:
            from llama_cpp import Llama

            logger.info(f"Loading local LLM from {self.model_path}...")
            self._llm = Llama(
                model_path=str(self.model_path),
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                verbose=self.verbose,
            )
            logger.info("Local LLM loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load local LLM: {e}")
            self._available = False
            return False

    def complete(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stop: list[str] | None = None,
    ) -> str | None:
        """
        Generate text completion.

        Args:
            prompt: The prompt to complete
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop: Stop sequences

        Returns:
            Generated text or None if unavailable
        """
        if not self._ensure_loaded():
            return None

        try:
            output = self._llm(
                prompt, max_tokens=max_tokens, temperature=temperature, stop=stop or [], echo=False
            )
            return output["choices"][0]["text"]
        except Exception as e:
            logger.error(f"Local LLM completion failed: {e}")
            return None

    def chat(
        self, messages: list[dict[str, str]], max_tokens: int = 1024, temperature: float = 0.7
    ) -> str | None:
        """
        Generate chat completion.

        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Assistant response or None if unavailable
        """
        if not self._ensure_loaded():
            return None

        try:
            output = self._llm.create_chat_completion(
                messages=messages, max_tokens=max_tokens, temperature=temperature
            )
            return output["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Local LLM chat failed: {e}")
            return None

    def generate_with_tools(self, prompt: str, context: str, tools: list[dict]) -> Any:
        """
        Generate response compatible with GeminiCLIAdapter interface.
        Returns LLMResponse object.
        """
        # Import dynamically to avoid circular imports if any
        from ..interfaces import LLMResponse

        full_prompt = f"{context}\n\n{prompt}"
        messages = [{"role": "user", "content": full_prompt}]
        response = self.chat(messages)
        if response:
            return LLMResponse(text=response, function_calls=[], success=True)
        return LLMResponse(text="", function_calls=[], success=False, error="Local LLM failed")

    def unload(self) -> None:
        """Unload the model to free memory."""
        if self._llm is not None:
            del self._llm
            self._llm = None
            logger.info("Local LLM unloaded")


def get_model_dir() -> Path:
    """Get the directory for storing local models."""
    from pathlib import Path

    # Check environment variable
    model_dir = os.environ.get("BORING_MODEL_DIR")
    if model_dir:
        return Path(model_dir)

    # Default to ~/.boring/models
    return Path.home() / ".boring" / "models"


def download_model(model_name: str = "qwen2.5-1.5b", progress: bool = True) -> Path | None:
    """
    Download a recommended model.

    Args:
        model_name: Name from RECOMMENDED_MODELS
        progress: Show download progress

    Returns:
        Path to downloaded model or None on failure
    """
    if model_name not in RECOMMENDED_MODELS:
        logger.error(f"Unknown model: {model_name}. Available: {list(RECOMMENDED_MODELS.keys())}")
        return None

    model_info = RECOMMENDED_MODELS[model_name]
    model_dir = get_model_dir()
    model_dir.mkdir(parents=True, exist_ok=True)

    filename = model_info["url"].split("/")[-1]
    model_path = model_dir / filename

    if model_path.exists():
        logger.info(f"Model already exists: {model_path}")
        return model_path

    try:
        import urllib.request

        logger.info(f"Downloading {model_name} ({model_info['size_mb']}MB)...")

        if progress:
            from rich.progress import (
                BarColumn,
                DownloadColumn,
                Progress,
                SpinnerColumn,
                TextColumn,
                TransferSpeedColumn,
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                DownloadColumn(),
                "•",
                TransferSpeedColumn(),
            ) as p:
                task_id = p.add_task("download", filename=filename, start=False)

                def reporthook(count, block_size, total_size):
                    p.update(task_id, total=total_size)
                    p.start_task(task_id)
                    p.update(task_id, advance=block_size)

                urllib.request.urlretrieve(model_info["url"], model_path, reporthook)  # nosec B310
        else:
            urllib.request.urlretrieve(model_info["url"], model_path)  # nosec B310

        logger.info(f"Model downloaded to: {model_path}")
        return model_path

    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        if model_path.exists():
            model_path.unlink()  # Clean up partial download
        return None


def list_available_models() -> list[dict]:
    """List all available local models."""
    model_dir = get_model_dir()
    if not model_dir.exists():
        return []

    models = []
    for f in model_dir.glob("*.gguf"):
        models.append({"name": f.stem, "path": str(f), "size_mb": f.stat().st_size / (1024 * 1024)})
    return models
