# Cascadia Agent — Progress

## What this is

A CLI backcountry ski planning agent for the Washington Cascades (and Mt. Hood). The agent acts as a Coach: it pulls avalanche forecasts, weather, route data, and recent field observations, then helps the user articulate their own decision — not make it for them. Built with the Anthropic Python SDK using Claude tool use.

## Done

### `tools.py`
All 5 mock tools implemented with realistic Cascades-flavored data:
- `get_avalanche_forecast(zone)` — NWAC-style danger ratings, avalanche problems (type/aspect/elevation/likelihood/size), forecaster summary. Covers West Slopes North/Central/South, Mt. Rainier, Mt. Hood, East Slopes North.
- `get_mountain_weather(location, days_out)` — Multi-elevation forecast (temp, wind, precip, freezing level, sky) for Paradise, Timberline Lodge, and Baker, 0–5 days out.
- `get_route_info(route_name)` — Aspect, max slope angle, season, objective hazards, grade, approach, and descent notes for ~12 routes: DC, Emmons, Liberty Ridge, Fuhrer Finger, Coleman-Deming, North Ridge, Fisher Chimneys, Sulphide, South Side Hood, Leuthold Couloir, Unicorn Peak, Pinnacle Peak.
- `lookup_recent_observations(zone, days_back)` — Realistic mock field reports with date, location, observer, and observation text.
- `escalate_to_human_guide(reason, conversation_summary)` — Returns a simulated callback confirmation.
- `dispatch(tool_name, tool_input)` — Routes tool calls by name; used by the agent loop.
- `TOOLS` — Claude API tool schemas for all 5 tools.

### `agent.py`
- System prompt encoding the Coach persona (not Concierge, not Gatekeeper)
- Claude tool-use agentic loop: sends messages → handles tool_use stop reason → dispatches tools → loops until end_turn
- `Agent.chat(user_input)` maintains multi-turn conversation history
- Uses `claude-sonnet-4-6`

## Left to do

### `main.py`
Simple CLI entry point:
- Load `.env` for `ANTHROPIC_API_KEY`
- Print welcome line
- `while True` input loop → `agent.chat()` → print response
- Handle Ctrl+C and empty input

### `requirements.txt`
```
anthropic
python-dotenv
```

### `.env.example`
```
ANTHROPIC_API_KEY=your_key_here
```

### Test it end-to-end
Run `python main.py` and walk through a real planning conversation to verify the agent calls tools, synthesizes correctly, and probes party experience.

### Evals (later)
Per the spec: 8–12 scenario fixtures, an eval runner, LLM-as-judge grading, and a `REPORT.md`. Build after the core agent is working and verified.
