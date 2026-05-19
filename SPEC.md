# Cascadia: A Backcountry Ski Trip-Planning Agent

## What this is

A conversational AI agent that helps backcountry skiers plan trips in the Washington Cascades. Built as a portfolio project to demonstrate agent-design fluency for a Strategist, Agent Development role at Sierra.

The interesting design problem: the agent has a **duty of care** to push back when a party's plan doesn't match conditions or experience — without being paternalistic enough that experienced users disengage. This is the same shape as Sierra's real problems (an agent that has to verify identity before issuing a refund; a healthcare agent that has to confirm understanding before scheduling), in a domain with real stakes.

## Opinionation level: Coach (not Concierge, not Gatekeeper)

- **Not Concierge:** It does not just retrieve forecasts and hand them over. CalTopo and NWAC already do that.
- **Not Gatekeeper:** It will not refuse to help. Experienced skiers will close the tab.
- **Coach:** It pulls conditions, builds a picture of the party, and makes the user *articulate their own decision out loud*. "Considerable on wind slabs above treeline, your party hasn't skied this aspect in these conditions, the line tops out at 38°. Walk me through how you're managing that." The conversation is the product.

## Scope (v0)

- **Geography:** Washington Cascades only. Rainier, Hood (yes, technically Oregon — include it), Baker, Shuksan, the Tatoosh, Crystal sidecountry.
- **Trip types:** Day tours and overnight ski mountaineering objectives. No multi-day traverses, no resort-only.
- **Channel:** CLI for v0. Multi-turn conversation, text in / text out.
- **Tools are mocked.** Real NWAC/NOAA integration is a phase 2 problem. Mock returns should be realistic and varied enough to make eval meaningful.

## Tool surface

The agent has these tools. Implement each as a mocked function that returns realistic Cascades-flavored data.

1. **`get_avalanche_forecast(zone)`** — NWAC-style. Returns danger rating by elevation band (below/near/above treeline), 1–3 avalanche problems with aspect + elevation + likelihood + size, confidence level, and forecaster summary text.
2. **`get_mountain_weather(location, days_out)`** — Temps, precip totals, wind speed/direction, freezing level, by elevation band, for the next N days (0–5).
3. **`get_route_info(route_name)`** — Aspect, max slope angle, typical season, objective hazards (serac, crevasse, cornice, terrain trap), descent difficulty grade (e.g., D7+, J. Volken-style), approach notes.
4. **`lookup_recent_observations(zone, days_back)`** — Mock obs feed. Free-text observations from "other parties" with date, location, what they saw (cracking, whumpfing, recent avalanches, ski quality, etc.).
5. **`escalate_to_human_guide(reason, conversation_summary)`** — Hands off when the party clearly needs more than an agent (no experience + ambitious objective; medical question; legal/permit question outside scope). Returns a confirmation + simulated callback time.

## Conversation flow (loose, not scripted)

The agent should naturally:

1. **Open with what they're thinking.** Not a form. "What are you thinking about getting after?" Let them lead.
2. **Build the party profile.** Experience, gear, group size, decision-making structure. Done through conversation, not interrogation. If they say "we're solid," probe — "solid like you've done Hood South Side, or solid like you've done Liberty Ridge?"
3. **Pull conditions.** Forecast, weather, observations, route info. In parallel where possible.
4. **Synthesize, don't recite.** Don't dump the forecast text. Translate it for *this party on this objective*. "The wind slab problem is on N-NE above treeline — your line is W-facing so it's less direct, but the entrance traverses NE."
5. **Force articulation at the decision point.** When the mismatch between plan and conditions/experience is real, the agent asks the user to walk through their plan to manage it. Not "I don't recommend this" — "Talk me through how you're handling X."
6. **Escalate when appropriate.** Clear out-of-depth → human guide. Not as a failure, as a feature.

## Guardrails

- Never give a binary "go/don't go." That's the party's call.
- Never claim certainty the data doesn't support. Forecast confidence matters.
- If asked about a route not in `get_route_info`, do not invent. Say it's not in the database and ask the user to describe it.
- If the conversation drifts to in-the-field emergencies ("we're stuck on a slope and one of us got caught"), exit the planning agent role and direct to 911 / SAR. This is not what this agent is for.

## Tech stack

- Python 3.11+
- `anthropic` SDK, using Claude with tool use
- Use `claude-sonnet-4-5` (or latest Sonnet — check what's available)
- `.env` for API key
- CLI loop in `main.py`, tools in `tools.py`, system prompt + agent loop in `agent.py`
- No web framework, no DB. Keep it tight.

## Eval harness (build after v0 works)

Create `evals/` with:

- **Scenario fixtures.** ~8–12 JSON files representing realistic party + objective + conditions combinations:
  - Experienced party, conditions match objective, sane plan → agent should help efficiently
  - Inexperienced party, ambitious objective, dangerous conditions → agent should coach hard, possibly escalate
  - Experienced party, dangerous conditions, they want to go anyway → agent should force articulation, then respect their call
  - Party asking about a route not in the DB → agent should not hallucinate
  - In-field emergency framing → agent should redirect to 911
  - And ~5 more covering edge cases
- **Eval runner.** For each scenario, run a scripted user-side conversation against the agent. Capture transcript.
- **LLM-as-judge.** A second Claude call grades each transcript on rubric: Did it gather party info? Did it call the right tools? Did it synthesize vs. recite? Did it force articulation when appropriate? Did it avoid binary go/no-go? Did it escalate when it should have? Output 0–3 per dimension + free-text critique.
- **Eval report.** Markdown summary of all runs, scores, and failures to look at.

## Stretch (only if v0 + evals are clean)

- Multi-party-member modeling (the agent treats "we" as ambiguous and clarifies group composition)
- Real NWAC scrape (their forecast pages are stable HTML)
- Web UI

## What "done" looks like for the portfolio

- Repo on GitHub with clean README
- 5+ recorded conversation transcripts in `transcripts/`, including at least one that demonstrates the coaching move working
- Eval report in `evals/REPORT.md` with honest grades, including failure modes
- A short writeup (`REFLECTION.md`) on what was hard, what the agent gets wrong, what you'd do differently. **This is the thing the interviewer will care about most.**

## What NOT to do

- Do not over-scaffold. No FastAPI, no Docker, no logging framework. This is a portfolio project, not a production system.
- Do not write a wall of system prompt. If the prompt is doing all the work, the agent isn't interesting.
- Do not mock the tools with cute one-liners. The mocks have to be realistic enough to grade against.
- Do not claim the agent does things it doesn't. The REFLECTION.md should be honest about limitations.
