# Release Notes - v11.2.12 (Node.js Autonomy)

## 🚀 Key Features

### Node.js Autonomy & Portable Environment
- **System-First Detection**: Automatically detects existing system Node.js and Gemini CLI.
- **Fallback Download**: If Node.js is missing, Boring now offers to download a portable, high-isolation Node.js environment (v20 LTS).
- **One-Click Wizard**: Integrated into `boring wizard` to ensure a seamless setup experience for newcomers.
- **Optional Consent**: Users are now prompted for consent before any download occurs, ensuring those not using the Gemini CLI can skip the Node.js setup.

## 🛠️ Internal Improvements
- **NodeManager Service**: A new dedicated service (`src/boring/services/nodejs.py`) manages the lifecycle of portable Node.js binaries.
- **Enhanced Health Checks**: `boring health` now accurately reports on both system and portable Gemini CLI installations.
- **Deep Verification**: Comprehensive quality sweep (230+ checks passed) ensuring stability for this release.

## 📝 Documentation
- New dedicated feature guides for Node.js support in both English and Traditional Chinese.
- Updated main index and READMEs to reflect the latest "Cognitive Evolution" pillars.

---
*Built with ❤️ by the Boring for Gemini Team*
