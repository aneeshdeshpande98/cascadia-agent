import json
import os
from typing import Any

import anthropic

from tools import TOOLS, dispatch

MODEL = "claude-sonnet-4-6"
TOOL_LABELS = {
    "get_avalanche_forecast": "Avalanche forecast",
    "get_nws_forecast": "Live NWS forecast",
    "get_mountain_weather": "Mock mountain weather",
    "get_route_info": "Route info",
    "lookup_recent_observations": "Recent observations",
    "escalate_to_human_guide": "Human guide escalation",
}

SYSTEM_PROMPT = """You are a backcountry ski planning agent for the Washington Cascades (and Mt. Hood in Oregon). Your role is Coach — not Concierge, not Gatekeeper.

**What that means:**
- You do not just fetch forecasts and hand them over. CalTopo and NWAC already do that.
- You do not refuse to help or give binary go/no-go calls. That's the party's decision, not yours.
- You pull conditions, build a picture of the party, and make them articulate their own decision out loud.

**How to run a conversation:**

1. Open with curiosity. "What are you thinking about getting after?" Let them lead. Don't start with a form.

2. Build the party profile through conversation — experience, gear, group size, decision-making structure. If they say "we're solid," probe: "Solid like you've done Hood South Side, or solid like you've done Liberty Ridge?" Push gently until you have a real picture.

3. Pull conditions using your tools. When a specific objective comes up, call get_avalanche_forecast, get_route_info, and lookup_recent_observations. Use get_nws_forecast for live public National Weather Service data when the user asks about current weather, timing, wind, precipitation, or alerts. Use get_mountain_weather only when you need the mocked mountain-specific forecast. Do this before synthesizing.

4. Synthesize, don't recite. Translate the forecast for *this party on this objective*. Don't dump raw data. "The wind slab problem is on N-NE above treeline — your line tops out on the W aspect so it's less direct, but the entrance traverses NE at 38°."

5. Force articulation at the decision point. When the mismatch between the plan and conditions or experience is real, ask the party to walk through how they're managing it. Not "I don't recommend this" — "Talk me through how you're handling the wind slab on the approach." The conversation is the product.

6. Escalate when it's the right call. Use escalate_to_human_guide when: the party clearly lacks the experience their objective demands, there's a medical or permit question you can't answer, or the situation requires professional judgment. Frame it as a feature, not a failure.

**Hard constraints:**
- Never give a binary "go" or "don't go." That's the party's call.
- Never claim certainty the data doesn't support. If forecast confidence is Low, say so and say why it matters.
- When you use live public data from get_nws_forecast, include a short "Sources" line with Markdown hyperlinks to the relevant NWS source_urls, such as [NWS forecast](...) and [NWS alerts](...). Keep citations concise and do not invent source links.
- If asked about a route not in get_route_info, do not invent data. Tell them it's not in the database and ask them to describe the route.
- If the conversation shifts to an active in-field emergency ("we're stuck on a slope", "someone got caught"), immediately exit planning mode and direct them to call 911 and Washington State SAR. This is not what you're for.
- Geography: Washington Cascades and Mt. Hood only. Day tours and overnight ski mountaineering. No resort-only trips, no multi-day traverses.

Be direct. Be specific. Ask one question at a time. The party came here because they want to think clearly about a serious objective — help them do that."""


class Agent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.messages: list[dict] = []

    def chat(self, user_input: str) -> str:
        return self.chat_with_trace(user_input)["reply"]

    def chat_with_trace(self, user_input: str) -> dict[str, Any]:
        self.messages.append({"role": "user", "content": user_input})
        turn = self._run_turn()
        response_text = turn["reply"]
        self.messages.append({"role": "assistant", "content": response_text})
        return turn

    def _run_turn(self) -> dict[str, Any]:
        messages = list(self.messages)
        traces = []

        while True:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                return {"reply": _extract_text(response), "traces": traces}

            if response.stop_reason == "tool_use":
                tool_uses = [b for b in response.content if b.type == "tool_use"]
                tool_results = []

                for tool_use in tool_uses:
                    result = dispatch(tool_use.name, tool_use.input)
                    traces.append(_tool_trace(tool_use.name, tool_use.input, result))
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps(result),
                    })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue

            # Unexpected stop reason — return whatever text we have
            return {"reply": _extract_text(response), "traces": traces}


def _extract_text(response) -> str:
    parts = [b.text for b in response.content if hasattr(b, "text")]
    return "\n".join(parts).strip()


def _tool_trace(tool_name: str, tool_input: dict, result: Any) -> dict[str, Any]:
    status = "ok"
    if isinstance(result, dict) and result.get("error"):
        status = "error"

    return {
        "name": tool_name,
        "label": TOOL_LABELS.get(tool_name, tool_name),
        "input": tool_input,
        "status": status,
        "summary": _summarize_tool_result(tool_name, result),
        "sources": _extract_sources(result),
    }


def _summarize_tool_result(tool_name: str, result: Any) -> str:
    if not isinstance(result, dict):
        return "Tool returned data."

    if result.get("error"):
        return result["error"]

    if tool_name == "get_nws_forecast":
        first_period = _first(result.get("daily_periods", [])) or {}
        location = result.get("resolved_location") or result.get("location")
        forecast = first_period.get("short_forecast", "forecast returned")
        alerts = result.get("active_alert_count", 0)
        return f"{location}: {forecast}; {alerts} active alert(s)."

    if tool_name == "get_avalanche_forecast":
        danger = result.get("danger", {})
        zone = result.get("zone", "zone")
        confidence = result.get("confidence", "unknown confidence")
        above = danger.get("above_treeline", "unknown")
        near = danger.get("near_treeline", "unknown")
        below = danger.get("below_treeline", "unknown")
        return f"{zone}: {above} above, {near} near, {below} below treeline; confidence {confidence}."

    if tool_name == "get_route_info":
        if not result.get("found", True):
            return result.get("message", "Route was not found.")
        route = result.get("route", "Route")
        mountain = result.get("mountain", "unknown mountain")
        grade = result.get("grade", "unknown grade")
        angle = result.get("max_slope_angle", "unknown")
        return f"{route}: {mountain}, grade {grade}, max slope {angle} degrees."

    if tool_name == "lookup_recent_observations":
        zone = result.get("zone", "zone")
        count = result.get("observation_count", 0)
        return f"{count} recent observation(s) for {zone}."

    if tool_name == "get_mountain_weather":
        location = result.get("location", "location")
        date = result.get("forecast_date", "forecast date")
        return f"{location} on {date}: {result.get('summary', 'forecast returned')}"

    if tool_name == "escalate_to_human_guide":
        return result.get("message", "Escalation requested.")

    return "Tool returned data."


def _extract_sources(result: Any) -> list[dict[str, str]]:
    if not isinstance(result, dict):
        return []

    source_urls = result.get("source_urls")
    if not isinstance(source_urls, dict):
        return []

    labels = {
        "point": "NWS grid point",
        "forecast": "NWS forecast",
        "hourly": "NWS hourly",
        "alerts": "NWS alerts",
    }
    return [
        {"label": labels.get(key, key), "url": value}
        for key, value in source_urls.items()
        if isinstance(value, str) and value.startswith("https://")
    ]


def _first(items: Any) -> Any:
    if isinstance(items, list) and items:
        return items[0]
    return None
