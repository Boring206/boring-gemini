"""
Boring-Gemini Custom Theme (Rich Aesthetics).
Defines the color palette and styles for the CLI.
"""

from rich.theme import Theme

# Modern, Premium Color Palette
BORING_THEME = Theme(
    {
        # Core Status
        "success": "bold #48BB78",  # Green 400
        "error": "bold #F56565",  # Red 400
        "warning": "bold #ED8936",  # Orange 400
        "info": "#4299E1",  # Blue 400
        # UI Elements
        "header": "bold #9F7AEA",  # Purple 400
        "panel.border": "#667EEA",  # Indigo 400
        "title": "bold #F687B3",  # Pink 400
        # Code / Data
        "key": "#A0AEC0",  # Gray 400
        "value": "bold #E2E8F0",  # Gray 200
        "command": "bold #D53F8C",  # Pink 500
        "path": "underline #63B3ED",  # Blue 300
        # Branding
        "boring.brand": "bold #805AD5",  # Purple 500
    }
)
