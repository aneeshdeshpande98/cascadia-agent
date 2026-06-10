# Cascadia Agent

Cascadia Agent is a portfolio backcountry ski planning agent for the Washington Cascades and Mt. Hood. It is designed as a coach: it gathers conditions, builds a picture of the party, and asks users to articulate their own decision instead of giving a binary go/no-go answer.

The project currently has both a CLI and a browser chat interface. Most external data tools are mocked with realistic Cascades-flavored avalanche forecasts, mountain weather, route information, recent observations, and a simulated human-guide escalation. The first real public-data integration uses the National Weather Service API for live forecasts and active alerts.

## How It Works

```text
Browser UI or CLI
  -> Agent.chat()
  -> Anthropic Messages API
  -> Claude may request tools
  -> tools.py dispatches mocked condition/route data or live public NWS data
  -> Claude synthesizes a coaching response
```

Key files:

- `agent.py` contains the system prompt, Claude client, conversation memory, and tool-use loop.
- `tools.py` contains mocked forecast, weather, route, observation, and escalation tools plus Claude tool schemas.
- `public_data.py` contains live public-data clients, starting with the National Weather Service API.
- `main.py` runs the terminal chat loop.
- `web.py` runs the local browser UI server.
- `web/` contains the static chat interface.
- `SPEC.md` describes the intended product and portfolio direction.

## Setup

Use Python 3.11 or newer if possible.

```bash
cd /Users/aneeshdeshpande/Desktop/cascadia-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env` and set:

```bash
ANTHROPIC_API_KEY=your_key_here
```

Do not commit `.env`; it is ignored by Git.

## Run The CLI

```bash
python main.py
```

## Run The Browser UI

```bash
python web.py
```

Then open:

```text
http://127.0.0.1:8000
```

The browser UI keeps a separate agent session per browser cookie and includes a reset button to start a fresh conversation.

## Optional PostHog Analytics

Set these environment variables in `.env` to test PostHog locally:

```bash
POSTHOG_PROJECT_KEY=phc_your_project_key
POSTHOG_HOST=https://us.i.posthog.com
```

When configured, the browser UI loads PostHog and captures product events such as:

- `app_loaded`
- `chat_message_sent`
- `agent_reply_received`
- `chat_error`
- `conversation_reset`
- `example_prompt_selected`
- `trace_opened`

The app does not send raw chat text to PostHog by default. It sends metadata such as message length, response time, trace count, and tool names.

## GitHub Workflow

This project is local until you connect it to GitHub. A normal first push looks like:

```bash
git status
git add .gitignore README.md SPEC.md PROGRESS.md agent.py main.py tools.py requirements.txt web.py web transcripts .env.example
git commit -m "Add Cascadia agent chat interface"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/cascadia-agent.git
git push -u origin main
```

Before committing, confirm that `.env` and `.env.en` are not staged:

```bash
git status --short
```

## Next Technical Steps

- Add tests for `tools.py` and the web API.
- Add visible tool-call traces in the UI so users can see when the agent fetched route, avalanche, weather, or observation data.
- Add more public-data connectors, such as Recreation.gov/RIDB or USGS water data.
- Add scenario-based evals for coaching behavior, route hallucination, escalation, and emergency handling.
- Add GitHub Actions to run tests on every push.

## Safety Note

This is a portfolio and learning project. Forecast, route, and observation data are mocked. It should not be used for real backcountry decisions.
