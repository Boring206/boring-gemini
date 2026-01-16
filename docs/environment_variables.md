# Environment Variables

This document lists the most common environment variables used by Boring-Gemini.
Unless noted, variables use the `BORING_` prefix and are loaded from `.env`.

## Core

| Variable | Description | Default | Example |
| --- | --- | --- | --- |
| `GOOGLE_API_KEY` | Gemini API key (legacy key lookup). | (empty) | `GOOGLE_API_KEY=...` |
| `BORING_GOOGLE_API_KEY` | Gemini API key (preferred). | (empty) | `BORING_GOOGLE_API_KEY=...` |
| `BORING_DEFAULT_MODEL` | Default Gemini model name. | `default` | `BORING_DEFAULT_MODEL=gemini-2.5-flash` |
| `BORING_TIMEOUT_MINUTES` | Request timeout (minutes). | `15` | `BORING_TIMEOUT_MINUTES=20` |
| `BORING_MCP_PROFILE` | MCP tool profile (`lite`, `standard`, `full`). | `lite` | `BORING_MCP_PROFILE=standard` |
| `BORING_LANGUAGE` | UI language (`zh`, `en`). | `zh` | `BORING_LANGUAGE=en` |
| `BORING_LANG` | UI language (legacy alias). | (empty) | `BORING_LANG=zh` |

## LLM Providers

| Variable | Description | Default | Example |
| --- | --- | --- | --- |
| `BORING_LLM_PROVIDER` | LLM provider (`gemini-cli`, `sdk`, `ollama`, `openai_compat`). | `gemini-cli` | `BORING_LLM_PROVIDER=ollama` |
| `BORING_LLM_BASE_URL` | Base URL for local/OpenAI-compatible providers. | (empty) | `BORING_LLM_BASE_URL=http://localhost:11434` |
| `BORING_LLM_MODEL` | Override model name for local providers. | (empty) | `BORING_LLM_MODEL=qwen2.5-coder-1.5b` |
| `BORING_CLAUDE_CLI_PATH` | Path to Claude CLI binary. | (auto) | `BORING_CLAUDE_CLI_PATH=/usr/local/bin/claude` |
| `BORING_GEMINI_CLI_PATH` | Path to Gemini CLI binary. | (auto) | `BORING_GEMINI_CLI_PATH=C:\Program Files\Gemini\gemini.exe` |

## Offline Mode

| Variable | Description | Default | Example |
| --- | --- | --- | --- |
| `BORING_OFFLINE_MODE` | Force offline mode (`true`/`false`). | `false` | `BORING_OFFLINE_MODE=true` |
| `BORING_LOCAL_LLM_MODEL` | Local GGUF model path. | (empty) | `BORING_LOCAL_LLM_MODEL=~/.boring/models/model.gguf` |
| `BORING_LOCAL_LLM_CONTEXT_SIZE` | Context window size for local LLM. | `4096` | `BORING_LOCAL_LLM_CONTEXT_SIZE=8192` |
| `BORING_MODEL_DIR` | Directory for local model downloads. | (auto) | `BORING_MODEL_DIR=~/.boring/models` |

## Verification & Loop

| Variable | Description | Default | Example |
| --- | --- | --- | --- |
| `BORING_MAX_LOOPS` | Max loops for agent runs. | `100` | `BORING_MAX_LOOPS=10` |
| `BORING_MAX_HOURLY_CALLS` | Hourly API call limit. | `50` | `BORING_MAX_HOURLY_CALLS=100` |
| `BORING_USE_FUNCTION_CALLING` | Enable tool/function calling. | `true` | `BORING_USE_FUNCTION_CALLING=false` |
| `BORING_USE_INTERACTIONS_API` | Enable Interactions API (experimental). | `false` | `BORING_USE_INTERACTIONS_API=true` |
| `BORING_USE_DIFF_PATCHING` | Prefer search/replace over full rewrites. | `true` | `BORING_USE_DIFF_PATCHING=false` |

## Performance

| Variable | Description | Default | Example |
| --- | --- | --- | --- |
| `BORING_SEMANTIC_CACHE_ENABLED` | Enable semantic cache. | `true` | `BORING_SEMANTIC_CACHE_ENABLED=false` |
| `BORING_SEMANTIC_CACHE_THRESHOLD` | Similarity threshold for cache hits. | `0.95` | `BORING_SEMANTIC_CACHE_THRESHOLD=0.9` |
| `BORING_STARTUP_PROFILE` | Enable startup profiling. | `false` | `BORING_STARTUP_PROFILE=true` |

## Notifications

| Variable | Description | Default | Example |
| --- | --- | --- | --- |
| `BORING_NOTIFICATIONS_ENABLED` | Enable notifications. | `true` | `BORING_NOTIFICATIONS_ENABLED=false` |
| `BORING_SLACK_WEBHOOK` | Slack webhook URL. | (empty) | `BORING_SLACK_WEBHOOK=https://hooks.slack.com/...` |
| `BORING_DISCORD_WEBHOOK` | Discord webhook URL. | (empty) | `BORING_DISCORD_WEBHOOK=https://discord.com/api/...` |
| `BORING_EMAIL_NOTIFY` | Notification email address. | (empty) | `BORING_EMAIL_NOTIFY=dev@company.com` |
| `BORING_GMAIL_USER` | Gmail sender account. | (empty) | `BORING_GMAIL_USER=dev@gmail.com` |
| `BORING_GMAIL_PASSWORD` | Gmail App Password. | (empty) | `BORING_GMAIL_PASSWORD=...` |
| `BORING_LINE_NOTIFY_TOKEN` | LINE Notify token. | (empty) | `BORING_LINE_NOTIFY_TOKEN=...` |
| `BORING_MESSENGER_ACCESS_TOKEN` | Facebook Messenger access token. | (empty) | `BORING_MESSENGER_ACCESS_TOKEN=...` |
| `BORING_MESSENGER_RECIPIENT_ID` | Facebook Messenger recipient ID. | (empty) | `BORING_MESSENGER_RECIPIENT_ID=...` |
