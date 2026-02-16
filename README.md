# Agent-OS Swarm (Local)

## Overview
Production-ready local autonomous swarm with Telegram entrypoint, persistent memory, self-healing loop, and autonomous operator mode.

## Folder Tree
```
agent_os/
  core/
  agents/
  memory/
  tools/
  interfaces/
  swarm/
  config/
```

## Run Instructions
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Export required environment variables:
   ```
   export TELEGRAM_BOT_TOKEN="your-telegram-token"
   export AGENT_OS_BASE_URL="http://127.0.0.1:1234/v1"
   export AGENT_OS_API_KEY="local"
   export AGENT_OS_MODEL="local-model"
   ```
3. Start the swarm:
   ```
   python -m agent_os.swarm
   ```

### Autonomous Operator Mode
```
python -m agent_os.swarm --operator
```

## Dependencies
- aiohttp

## Example Autonomous Task
Schedule a goal in operator mode:
```
python -m agent_os.swarm --operator
```
The operator seeds a goal to review and continue unfinished tasks.
