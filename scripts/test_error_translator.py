from boring.error_translator import ErrorTranslator

translator = ErrorTranslator()

test_cases = [
    "requests.exceptions.ConnectionError: Max retries exceeded",
    "google.api_core.exceptions.PermissionDenied: 403 The caller does not have permission",
    "Model 'phi-3-mini' not found",
    "pydantic_settings.exceptions.SettingsError: error parsing JSON",
]

print("Running Error Translator Verification...")
for err in test_cases:
    print(f"\n[Original]: {err}")
    explanation = translator.translate(err)
    print(f"[Friendly]: {explanation.friendly_message}")
    if explanation.fix_command:
        print(f"[Fix]: {explanation.fix_command}")

print("\nVerification Complete.")
