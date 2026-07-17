# People Context OpenClaw Plugin

An OpenClaw tool plugin that connects your agent to
[`people-context-mcp`](https://github.com/JinyangWang27/people-context-mcp),
a local-first store for knowledge about the people in your life.

## What it adds

- `people_resolve` — resolve a name, nickname, or partial reference to known people
- `people_context` — get a minimal-disclosure context bundle for a person
- `people_communication_guidance` — get traits, friction notes, reminders, and your communication philosophy
- `people_remember` — create or update a person record

## Setup

### 1. Start the people-context MCP HTTP server

From the `people-context-mcp` checkout, run:

```bash
uv run python -m people_context --http --db people_context.db --port 8765
```

This starts the Streamable HTTP transport on `http://127.0.0.1:8765/mcp`.

### 2. Install the plugin in OpenClaw

```bash
openclaw plugins install ./openclaw-plugin
```

Restart the OpenClaw gateway.

### 3. Configure (optional)

In your OpenClaw gateway config:

```json
{
  "plugins": {
    "people-context": {
      "baseUrl": "http://127.0.0.1:8765",
      "path": "/mcp"
    }
  }
}
```

Defaults to `http://127.0.0.1:8765/mcp`.

## Development

```bash
cd openclaw-plugin
npm install
npm run build
npm run plugin:validate
npm test
```

## Publishing to ClawHub

```bash
clawhub login
clawhub package validate ./openclaw-plugin
clawhub package publish ./openclaw-plugin --owner jinyangwang27
```

After the first publish, set up trusted publishing from GitHub Actions:

```bash
clawhub package trusted-publisher set @jinyangwang27/people-context \
  --repository JinyangWang27/people-context-mcp \
  --workflow-filename package-publish.yml
```
