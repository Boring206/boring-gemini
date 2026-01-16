import base64
import logging
from pathlib import Path

from boring.llm.sdk import GeminiClient, types

logger = logging.getLogger(__name__)


class VisionManager:
    """
    Handles multi-modal vision tasks for Boring agents.
    Uses Gemini 1.5/2.0 vision capabilities.
    """

    def __init__(self, client: GeminiClient | None = None):
        from boring.llm.sdk import create_gemini_client

        self.client = client or create_gemini_client(
            model_name="gemini-1.5-flash"
        )  # Use flash for speed/vision

    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def analyze_image(self, image_path: str | Path, prompt: str) -> str:
        """
        Analyze an image (screenshot, diagram, etc.) with a prompt.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found at {image_path}")

        logger.info(f"Analyzing image: {path.name}")

        # Read image
        image_bytes = path.read_bytes()

        # Determine mime type
        mime_type = "image/png"
        if path.suffix.lower() in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        elif path.suffix.lower() == ".webp":
            mime_type = "image/webp"

        # Build contents using SDK parts
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(inline_data=types.Blob(mime_type=mime_type, data=image_bytes)),
                    types.Part(text=prompt),
                ],
            )
        ]

        try:
            # We use the raw client.models.generate_content since GeminiClient.generate is currently text-only
            response = self.client.client.models.generate_content(
                model=self.client.model_name,
                contents=contents,
                config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=2048),
            )
            return response.text or "No visual analysis returned."
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return f"ERROR: {e}"

    def audit_ui(self, screenshot_path: str | Path) -> str:
        """Perform a UI/UX audit on a screenshot."""
        prompt = (
            "Analyze this UI screenshot. Identify any visual bugs, "
            "alignment issues, accessibility problems, or design inconsistencies. "
            "Provide actionable feedback for a developer."
        )
        return self.analyze_image(screenshot_path, prompt)


if __name__ == "__main__":
    # Test stub
    import sys

    if len(sys.argv) > 1:
        vm = VisionManager()
        print(vm.audit_ui(sys.argv[1]))
