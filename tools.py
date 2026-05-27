from datetime import datetime, timedelta
from typing import Any

from public_data import get_nws_forecast


# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_ZONE_FORECASTS = {
    "west slopes north": {
        "danger": {"above_treeline": 3, "near_treeline": 3, "below_treeline": 2},
        "problems": [
            {
                "type": "Wind Slab",
                "aspects": ["N", "NE", "E"],
                "elevation": "above_treeline",
                "likelihood": "Likely",
                "size": "Large",
                "description": (
                    "Recent loading on N-NE-E aspects above treeline from sustained SW winds. "
                    "Shooting cracks reported by several parties. Avoid lee terrain and cross-loaded "
                    "rolls. Slabs up to 18\" thick in exposed areas."
                ),
            },
            {
                "type": "Persistent Slab",
                "aspects": ["N", "NE", "NW", "E"],
                "elevation": "near_treeline",
                "likelihood": "Possible",
                "size": "Very Large",
                "description": (
                    "Buried weak layer from mid-season faceting event remains reactive on shaded aspects "
                    "40-70cm down. Human triggering possible from steep convexities and rolls. "
                    "Long runouts — consequential terrain management essential."
                ),
            },
        ],
        "confidence": "Moderate",
        "forecaster_summary": (
            "A persistent weak layer buried 60-90cm down is the primary concern. Recent wind loading "
            "has stacked a new wind slab problem on top. The combination — newer slab sitting above a "
            "buried weak layer — is the classic setup for large human-triggered avalanches. "
            "Cautious route-finding on shaded aspects. Cornices on Baker's summit ridges are large "
            "and can remotely trigger the persistent layer on slopes below."
        ),
    },
    "west slopes central": {
        "danger": {"above_treeline": 2, "near_treeline": 2, "below_treeline": 1},
        "problems": [
            {
                "type": "Storm Slab",
                "aspects": ["all"],
                "elevation": "above_treeline",
                "likelihood": "Possible",
                "size": "Medium",
                "description": (
                    "12\" of new snow from last week's storm is settling and bonding. Steep, "
                    "unsupported terrain and convexities still capable of producing natural storm slab "
                    "activity. Watch for hollow, drum-like sounds underfoot."
                ),
            },
            {
                "type": "Wind Slab",
                "aspects": ["N", "NE", "E", "SE"],
                "elevation": "above_treeline",
                "likelihood": "Unlikely",
                "size": "Medium",
                "description": (
                    "Isolated wind slabs on lee aspects from post-storm ridgeline winds. Generally thin "
                    "— a few inches — but reactive in isolated spots. Easy to identify by chalky, "
                    "hollow feel underfoot."
                ),
            },
        ],
        "confidence": "High",
        "forecaster_summary": (
            "Snowpack is in reasonable shape for this time of year. Last week's storm snow has mostly "
            "settled and bonded. Primary concern is terrain management on steep aspects above treeline. "
            "Low-angle and forested terrain is low-risk. Good day for moderate objectives with "
            "conservative terrain choices above treeline."
        ),
    },
    "west slopes south": {
        "danger": {"above_treeline": 4, "near_treeline": 3, "below_treeline": 2},
        "problems": [
            {
                "type": "Persistent Slab",
                "aspects": ["N", "NE", "NW", "E"],
                "elevation": "above_treeline",
                "likelihood": "Likely",
                "size": "Very Large",
                "description": (
                    "Deeply buried weak layer (1.2m) from a November faceting event remains a sleeper. "
                    "Multiple natural cycle events observed this week on N and NE aspects. Long runouts "
                    "into terrain traps below. This layer is not going away — it's been reactive for "
                    "three weeks."
                ),
            },
            {
                "type": "Wind Slab",
                "aspects": ["N", "NE", "E"],
                "elevation": "above_treeline",
                "likelihood": "Likely",
                "size": "Large",
                "description": (
                    "Strong SW winds have aggressively loaded N-NE-E aspects. Whumpfing reported by "
                    "multiple parties near Crystal and Snoqualmie Pass. Avoid cross-loading on ridgelines."
                ),
            },
            {
                "type": "Cornice",
                "aspects": ["N", "NE", "E", "SE"],
                "elevation": "above_treeline",
                "likelihood": "Possible",
                "size": "Very Large",
                "description": (
                    "Large cornices on summit ridges. Cornice fall can remotely trigger slabs on "
                    "slopes below. Assess cornice size before committing to lines under ridgelines."
                ),
            },
        ],
        "confidence": "High",
        "forecaster_summary": (
            "High danger above treeline — this is a serious day in the mountains. A deeply buried "
            "persistent weak layer combined with fresh wind loading creates the worst-case combination. "
            "If you're going out, low-angle terrain with clean runouts only. This is not a day for "
            "exposed lines above treeline regardless of experience level."
        ),
    },
    "mt. rainier": {
        "danger": {"above_treeline": 3, "near_treeline": 2, "below_treeline": 1},
        "problems": [
            {
                "type": "Wind Slab",
                "aspects": ["N", "NE", "NW"],
                "elevation": "above_treeline",
                "likelihood": "Likely",
                "size": "Large",
                "description": (
                    "Orographic winds have hammered the upper mountain. Aggressive wind loading on "
                    "N through NW aspects above 10,000'. Slabs up to 18\" thick on lee aspects of the "
                    "summit ice cap. Shooting cracks observed near Crater Rim."
                ),
            },
            {
                "type": "Persistent Slab",
                "aspects": ["N", "NE", "E"],
                "elevation": "near_treeline",
                "likelihood": "Possible",
                "size": "Large",
                "description": (
                    "Faceted snow from a dry cold spell is present 40-60cm down on shaded aspects "
                    "in the 6,000-9,000' band. Has been quiet but not to be trusted on steep terrain. "
                    "Snowpit observations from Muir show concerning structure."
                ),
            },
        ],
        "confidence": "Low",
        "forecaster_summary": (
            "Upper Rainier is operating under a separate weather regime from the rest of the range. "
            "Summit winds sustained 40-60mph with gusts higher. Snowpack at elevation is complex and "
            "incompletely observed — confidence is lower than usual. The objective hazards "
            "(seracs, crevasses, weather) may be more limiting than the avalanche hazard on most "
            "standard routes. Check with RMI guides and the Paradise ranger station for upper-mountain "
            "conditions before committing."
        ),
    },
    "mt. hood": {
        "danger": {"above_treeline": 2, "near_treeline": 2, "below_treeline": 1},
        "problems": [
            {
                "type": "Wind Slab",
                "aspects": ["NE", "E", "SE"],
                "elevation": "above_treeline",
                "likelihood": "Possible",
                "size": "Medium",
                "description": (
                    "Moderate wind loading on NE-E-SE aspects from recent SW flow. Wind slabs are "
                    "generally thin but reactive on the Hogsback approaches and near the Pearly Gates. "
                    "Cracking observed by parties in the couloir."
                ),
            },
            {
                "type": "Wet Avalanche",
                "aspects": ["S", "SE", "SW"],
                "elevation": "near_treeline",
                "likelihood": "Possible",
                "size": "Medium",
                "description": (
                    "South-facing aspects warming quickly on sunny days. Wet loose activity possible "
                    "by midday on S-SW aspects below 7,000'. Alpine start strongly recommended. "
                    "Surface crust in the morning protects against wet activity — plan to be "
                    "descending by 10am."
                ),
            },
        ],
        "confidence": "High",
        "forecaster_summary": (
            "Hood is in relatively stable shape. The main concern is timing on south-facing routes — "
            "get up and off the Hogsback before solar heating destabilizes the surface. Wind slabs "
            "on the northeast aspects near the summit are the secondary concern. "
            "Standard early-start strategy manages most of the risk on the standard South Side route."
        ),
    },
    "east slopes north": {
        "danger": {"above_treeline": 2, "near_treeline": 1, "below_treeline": 1},
        "problems": [
            {
                "type": "Wind Slab",
                "aspects": ["NE", "E"],
                "elevation": "above_treeline",
                "likelihood": "Possible",
                "size": "Small",
                "description": (
                    "Drier snowpack on the east side limits wind slab development, but isolated "
                    "reactive pockets exist on NE and E aspects above treeline. Generally thin "
                    "and manageable with conservative terrain choices."
                ),
            },
        ],
        "confidence": "High",
        "forecaster_summary": (
            "East slopes are in better shape than the west side. Drier, thinner snowpack means less "
            "slab development but also lower snow quality. Primary concern is wind effect on exposed "
            "ridgelines. Good conditions for mellow ridge tours."
        ),
    },
}

_WEATHER_DATA = {
    "paradise": {
        0: {
            "summary": "Clear and cold. Excellent visibility. Light winds at ridgeline.",
            "high_elevation": {"temp_f": 22, "wind_mph": 18, "wind_dir": "W", "precip_in": 0.0, "freezing_level_ft": 6800},
            "mid_elevation": {"temp_f": 28, "wind_mph": 10, "wind_dir": "W", "precip_in": 0.0},
            "sky": "Clear",
        },
        1: {
            "summary": "High pressure holding. Light wind, sunny skies. Prime day.",
            "high_elevation": {"temp_f": 24, "wind_mph": 14, "wind_dir": "NW", "precip_in": 0.0, "freezing_level_ft": 7200},
            "mid_elevation": {"temp_f": 30, "wind_mph": 8, "wind_dir": "NW", "precip_in": 0.0},
            "sky": "Clear",
        },
        2: {
            "summary": "System approaching from the southwest. Increasing clouds by afternoon.",
            "high_elevation": {"temp_f": 26, "wind_mph": 28, "wind_dir": "SW", "precip_in": 0.1, "freezing_level_ft": 6400},
            "mid_elevation": {"temp_f": 32, "wind_mph": 16, "wind_dir": "SW", "precip_in": 0.05},
            "sky": "Mostly Cloudy",
        },
        3: {
            "summary": "Active weather. 8-14\" snow above 7,000'. High winds on the upper mountain.",
            "high_elevation": {"temp_f": 18, "wind_mph": 52, "wind_dir": "SW", "precip_in": 1.2, "freezing_level_ft": 5200},
            "mid_elevation": {"temp_f": 28, "wind_mph": 30, "wind_dir": "SW", "precip_in": 0.8},
            "sky": "Overcast / Whiteout above 8,000'",
        },
        4: {
            "summary": "Storm clearing. Unsettled. Wind loading on lee aspects.",
            "high_elevation": {"temp_f": 16, "wind_mph": 38, "wind_dir": "NW", "precip_in": 0.2, "freezing_level_ft": 5600},
            "mid_elevation": {"temp_f": 24, "wind_mph": 20, "wind_dir": "NW", "precip_in": 0.1},
            "sky": "Partly Cloudy",
        },
        5: {
            "summary": "High pressure rebuilding. Cold and clear. Good consolidation window.",
            "high_elevation": {"temp_f": 20, "wind_mph": 16, "wind_dir": "NW", "precip_in": 0.0, "freezing_level_ft": 6600},
            "mid_elevation": {"temp_f": 26, "wind_mph": 8, "wind_dir": "NW", "precip_in": 0.0},
            "sky": "Clear",
        },
    },
    "timberline lodge": {
        0: {
            "summary": "Sunny and mild for the time of year. Light wind. Corn snow developing by 10am on S aspects.",
            "high_elevation": {"temp_f": 28, "wind_mph": 12, "wind_dir": "W", "precip_in": 0.0, "freezing_level_ft": 8500},
            "mid_elevation": {"temp_f": 34, "wind_mph": 6, "wind_dir": "W", "precip_in": 0.0},
            "sky": "Clear",
        },
        1: {
            "summary": "Warming trend. Freezing level rising to 9,500'. Wet conditions on south aspects by midday.",
            "high_elevation": {"temp_f": 32, "wind_mph": 10, "wind_dir": "SW", "precip_in": 0.0, "freezing_level_ft": 9500},
            "mid_elevation": {"temp_f": 38, "wind_mph": 5, "wind_dir": "SW", "precip_in": 0.0},
            "sky": "Clear to Partly Cloudy",
        },
        2: {
            "summary": "Marine push incoming. Rain below 7,000', snow above. Timing uncertain.",
            "high_elevation": {"temp_f": 34, "wind_mph": 24, "wind_dir": "S", "precip_in": 0.6, "freezing_level_ft": 7000},
            "mid_elevation": {"temp_f": 40, "wind_mph": 14, "wind_dir": "S", "precip_in": 0.4},
            "sky": "Overcast",
        },
    },
    "baker": {
        0: {
            "summary": "Partly cloudy. Moderate SW winds on the upper mountain. Snow quality excellent.",
            "high_elevation": {"temp_f": 18, "wind_mph": 28, "wind_dir": "SW", "precip_in": 0.0, "freezing_level_ft": 5800},
            "mid_elevation": {"temp_f": 24, "wind_mph": 14, "wind_dir": "SW", "precip_in": 0.0},
            "sky": "Partly Cloudy",
        },
        1: {
            "summary": "Storm approaching. Heavy snow likely by evening. 16-24\" over 48 hours.",
            "high_elevation": {"temp_f": 16, "wind_mph": 46, "wind_dir": "S", "precip_in": 2.1, "freezing_level_ft": 4200},
            "mid_elevation": {"temp_f": 22, "wind_mph": 28, "wind_dir": "S", "precip_in": 1.4},
            "sky": "Overcast / Whiteout",
        },
        2: {
            "summary": "Storm continues. Not a summit day. Visibility near zero above 5,000'.",
            "high_elevation": {"temp_f": 14, "wind_mph": 58, "wind_dir": "SW", "precip_in": 1.8, "freezing_level_ft": 3800},
            "mid_elevation": {"temp_f": 20, "wind_mph": 32, "wind_dir": "SW", "precip_in": 1.2},
            "sky": "Whiteout",
        },
        3: {
            "summary": "Clearing from the north. Cold shot following the storm. Wind-loaded aspects dangerous.",
            "high_elevation": {"temp_f": 8, "wind_mph": 42, "wind_dir": "NW", "precip_in": 0.1, "freezing_level_ft": 4000},
            "mid_elevation": {"temp_f": 16, "wind_mph": 24, "wind_dir": "NW", "precip_in": 0.0},
            "sky": "Clearing",
        },
        4: {
            "summary": "Cold and clear. Post-storm high pressure. Wind slabs consolidating.",
            "high_elevation": {"temp_f": 10, "wind_mph": 18, "wind_dir": "NW", "precip_in": 0.0, "freezing_level_ft": 5000},
            "mid_elevation": {"temp_f": 18, "wind_mph": 8, "wind_dir": "NW", "precip_in": 0.0},
            "sky": "Clear",
        },
    },
}

_DEFAULT_WEATHER = {
    "summary": "Typical Cascades spring conditions. Check mountain-forecast.com for current updates.",
    "high_elevation": {"temp_f": 22, "wind_mph": 20, "wind_dir": "W", "precip_in": 0.0, "freezing_level_ft": 7000},
    "mid_elevation": {"temp_f": 30, "wind_mph": 10, "wind_dir": "W", "precip_in": 0.0},
    "sky": "Variable",
}

_ROUTE_DATABASE = {
    "disappointment cleaver": {
        "mountain": "Mt. Rainier",
        "also_known_as": "DC Route",
        "aspect": "S-SW lower, W upper cleaver",
        "max_slope_angle": 45,
        "typical_season": "April–July",
        "grade": "D4",
        "objective_hazards": ["crevasse", "serac", "rockfall on cleaver"],
        "approach": "Paradise TH (5,400'). Skin or bootpack to Camp Muir (10,188') via Muir Snowfield. Route follows Cowlitz Glacier, Cathedral Gap, Ingraham Glacier, DC to summit (14,411').",
        "descent": "Ski the DC in reverse. Upper slopes 35-42°. High crevasse hazard on Ingraham below the flats — stay on established route. Camp Muir to Paradise is continuous skiing.",
        "notes": "Most-traveled Rainier route. Ranger station at Muir. Climbing permit required for summit attempts ($59/person). Rope up at the top of the Muir Snowfield.",
    },
    "emmons-winthrop glacier": {
        "mountain": "Mt. Rainier",
        "also_known_as": "Emmons Route",
        "aspect": "NE-E",
        "max_slope_angle": 48,
        "typical_season": "May–July",
        "grade": "D5",
        "objective_hazards": ["crevasse", "serac (upper Emmons icefall)", "weather exposure"],
        "approach": "White River CG (4,300'). Skin to Camp Schurman (9,500') on the Emmons moraine. Long approach — plan 2 days minimum.",
        "descent": "Ski the Emmons — sustained 35-45° with excellent snow quality when conditions are right. One of the great ski descents in the range. Route-finding through crevasses is the crux.",
        "notes": "Largest glacier by area in the lower 48. Less crowded than DC. Climbing permit required. Camp Schurman has a toilet and emergency shelter.",
    },
    "liberty ridge": {
        "mountain": "Mt. Rainier",
        "aspect": "NW-N",
        "max_slope_angle": 55,
        "typical_season": "April–June",
        "grade": "D7+",
        "objective_hazards": ["serac (Liberty Cap glacier)", "cornice", "crevasse", "rockfall (Carbon Glacier approach)", "high avalanche exposure on ridge flanks", "no safe retreat once established"],
        "approach": "Carbon River or Mowich Lake TH. Carbon Glacier approach to Liberty Ridge toe (~7,000'). Long approach through crevassed terrain.",
        "descent": "Not commonly skied as a descent. Most parties descend DC route. Some ski the upper ridge in exceptional conditions.",
        "notes": (
            "One of the most serious routes on Rainier with a documented fatality history. "
            "Liberty Cap serac is the primary objective hazard and cannot be fully avoided — "
            "timing and speed are the only mitigations. Not appropriate for parties without "
            "extensive crevassed glacier and mixed climbing experience. The route requires "
            "prior experience on serious Cascades routes (Coleman-Deming, DC multiple times, etc.)."
        ),
    },
    "fuhrer finger": {
        "mountain": "Mt. Rainier",
        "aspect": "S-SW",
        "max_slope_angle": 50,
        "typical_season": "May–June",
        "grade": "D6",
        "objective_hazards": ["serac (Wilson Glacier)", "bergschrund", "rockfall (upper couloir)", "limited descent window before softening"],
        "approach": "Paradise TH. Skin across Nisqually Glacier to base of the Finger. Wilson Glacier serac exposure on the approach — move efficiently.",
        "descent": "The Finger is one of the finest ski descents on Rainier — a 50° couloir opening to sustained 40-45° below. Requires solid snow conditions and a clean bergschrund crossing.",
        "notes": "Window is narrow — too early and the 'schrund is ugly; too late and it softens by noon. Best in May in a good snow year. 3am start from Paradise is standard.",
    },
    "coleman-deming glacier": {
        "mountain": "Mt. Baker",
        "also_known_as": "Coleman-Deming",
        "aspect": "W-NW",
        "max_slope_angle": 45,
        "typical_season": "April–June",
        "grade": "D4",
        "objective_hazards": ["crevasse", "serac (Roman Wall)", "cornice (summit)"],
        "approach": "Heliotrope Ridge TH (3,700'). Skin to Coleman-Deming junction (~7,500'). Roman Wall at 45° is the crux. Summit at 10,781'.",
        "descent": "Ski the Roman Wall — steep and sustained. Route-finding through Coleman Glacier crevasses on the way down. Heavily crevassed — roped travel essential throughout.",
        "notes": "Most popular Baker route. Overnight permit required. Seracs on the Roman Wall are active — move efficiently through exposure zones.",
    },
    "north ridge": {
        "mountain": "Mt. Baker",
        "aspect": "N",
        "max_slope_angle": 52,
        "typical_season": "April–June",
        "grade": "D6",
        "objective_hazards": ["serac", "crevasse", "cornices on upper ridge"],
        "approach": "Park Butte or Schreibers Meadow TH. Long glacier approach to the ridge toe. Committed route with limited retreat options.",
        "descent": "Not commonly skied. Technical mixed terrain on the upper ridge precludes clean ski descent for most parties.",
        "notes": "Excellent mountaineering objective. Serious crevasse terrain throughout. Less frequently done than Coleman-Deming.",
    },
    "fisher chimneys": {
        "mountain": "Mt. Shuksan",
        "aspect": "N-NE approach, W summit pyramid",
        "max_slope_angle": 50,
        "typical_season": "May–July",
        "grade": "D5",
        "objective_hazards": ["rockfall (chimneys)", "cornice (summit pyramid)", "crevasse (Price Lake area)"],
        "approach": "Artist Point TH (when accessible) or White Salmon Lodge. Skin/ski to base of the Chimneys. Short technical rock section requiring crampons and tools — 4th class minimum.",
        "descent": "Summit pyramid skiable at 45-50° in good conditions. Chimneys require rappel or careful downclimbing. Lower glaciers offer excellent moderate ski terrain.",
        "notes": "Summit pyramid is one of the great ski objectives in the North Cascades. Artist Point road typically opens late May — call Glacier Ranger District for current status.",
    },
    "sulphide glacier": {
        "mountain": "Mt. Shuksan",
        "aspect": "SE",
        "max_slope_angle": 42,
        "typical_season": "April–June",
        "grade": "D4",
        "objective_hazards": ["crevasse", "cornice"],
        "approach": "Shannon Ridge TH. Long approach across Shannon Ridge. Camp on the glacier at ~7,000'.",
        "descent": "Excellent ski descent on the Sulphide — moderate angle with good snow quality. More forgiving than Fisher Chimneys.",
        "notes": "Less committing than Fisher Chimneys. Good objective for parties building toward harder Shuksan objectives.",
    },
    "south side": {
        "mountain": "Mt. Hood",
        "also_known_as": "Hogsback Route, South Side Hood",
        "aspect": "S-SE",
        "max_slope_angle": 40,
        "typical_season": "March–June",
        "grade": "D3",
        "objective_hazards": ["serac (Pearly Gates)", "bergschrund", "rockfall (summit crags)", "wet avalanche afternoon"],
        "approach": "Timberline Lodge (6,000'). Skin up Palmer snowfield to Hogsback (10,700'). Pearly Gates couloir to summit (11,249').",
        "descent": "Ski from summit through Pearly Gates, down the Hogsback, and out Palmer snowfield. 35-38° at steepest. Corn snow in May is excellent.",
        "notes": (
            "Most popular Hood route. Critical timing — Pearly Gates serac is active. "
            "Must be through the Gates by 9am in warm weather. Notorious for accidents from "
            "slow-moving parties caught under the serac. If you're not at the Hogsback by 6am, "
            "consider turning around."
        ),
    },
    "leuthold couloir": {
        "mountain": "Mt. Hood",
        "aspect": "W",
        "max_slope_angle": 47,
        "typical_season": "April–June",
        "grade": "D5",
        "objective_hazards": ["bergschrund", "serac (Reid headwall above)", "rockfall"],
        "approach": "Timberline Lodge. Skin to ~8,000', traverse west under the Reid Glacier, gain the base of the couloir.",
        "descent": "Classic ski descent — 47° at steepest, sustained. Bergschrund crossing at the bottom is the crux on descent. Hard-frozen conditions required.",
        "notes": "Less crowded than South Side. Better snow quality on the west aspect. Needs to be frozen for the steep sections — soft snow here is dangerous.",
    },
    "unicorn peak": {
        "mountain": "Tatoosh Range",
        "aspect": "N-NE",
        "max_slope_angle": 40,
        "typical_season": "April–May",
        "grade": "D3",
        "objective_hazards": ["cornice", "terrain trap (bowl below)"],
        "approach": "Narada Falls TH or Paradise. Short approach relative to Rainier objectives. Summit at 6,917'.",
        "descent": "North face descent at 35-40°. Short but aesthetic. Watch for terrain traps in the bowl — clean runout is not guaranteed.",
        "notes": "Good objective for acclimatization to the Rainier area before a bigger objective. Fine views of Rainier's south face.",
    },
    "pinnacle peak": {
        "mountain": "Tatoosh Range",
        "aspect": "N",
        "max_slope_angle": 38,
        "typical_season": "April–May",
        "grade": "D2",
        "objective_hazards": ["cornice", "wind exposure on summit ridge"],
        "approach": "Reflection Lakes TH. Short skin to the peak. Summit at 6,562'.",
        "descent": "Mellow north face. Good introductory objective.",
        "notes": "Accessible intro to ski mountaineering in the Rainier area. Often done as a half-day.",
    },
}

_OBSERVATIONS = {
    "west slopes north": [
        {
            "date": (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "location": "Coleman Glacier, ~7,200'",
            "observer": "Party of 3, guided",
            "observation": (
                "Observed shooting cracks propagating 20-30m on the NE aspects approaching the Roman Wall. "
                "Turned around at 7,500'. Wind loading was obvious — obvious wind slab formation on all "
                "N-NE-E aspects. Did not observe any natural activity but the structure was there."
            ),
        },
        {
            "date": (datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "location": "Heliotrope Ridge, ~6,000'",
            "observer": "Solo skier",
            "observation": (
                "Great ski descent on the lower Coleman below the crevasse zone. Avoided upper mountain "
                "due to wind. Surface was a bit chalky up high but lower down was excellent transformed snow. "
                "No signs of instability below treeline."
            ),
        },
        {
            "date": (datetime.today() - timedelta(days=3)).strftime("%Y-%m-%d"),
            "location": "Table Mountain, Artist Ridge",
            "observer": "Party of 4",
            "observation": (
                "Whumpfing on the upper Table Mountain slopes — definitely a buried weak layer present. "
                "Kept to low-angle terrain. No cracking or propagation in the areas we traveled but the "
                "sounds were unsettling. Did not push into steeper terrain."
            ),
        },
    ],
    "west slopes central": [
        {
            "date": (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "location": "Stevens Pass backcountry, Mill Valley",
            "observer": "Party of 2",
            "observation": (
                "Good day in the trees. Stayed below 4,500'. New snow quality was excellent — 10\" "
                "of low-density pow from last week's storm. No signs of instability in the lower-angle "
                "terrain we traveled. Could hear wind loading happening above treeline but didn't go up."
            ),
        },
        {
            "date": (datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "location": "Cowboy Mountain, above treeline",
            "observer": "Party of 3, all with avy certs",
            "observation": (
                "Dug a pit on a NE aspect at 5,200'. ECTP18 on the new snow/old snow interface — "
                "moderate results. Didn't push into anything steeper than 30°. Conditions felt manageable "
                "but the results suggest caution on steeper terrain above treeline."
            ),
        },
    ],
    "mt. rainier": [
        {
            "date": (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "location": "Camp Muir, 10,188'",
            "observer": "Guided party, RMI",
            "observation": (
                "Turned around at the top of the cleaver. Winds were 55+ mph with gusts. Surface conditions "
                "on the upper DC were breakable crust over wind slab — not skiable. Muir itself was fine. "
                "Cowlitz Glacier is in good shape below 9,500'."
            ),
        },
        {
            "date": (datetime.today() - timedelta(days=3)).strftime("%Y-%m-%d"),
            "location": "Emmons Glacier, ~9,000'",
            "observer": "Party of 4",
            "observation": (
                "Made it to about 11,000' on the Emmons before weather shut us down. Snow quality was "
                "excellent on the way up — hard frozen, crampons in beautifully. Crevasse route was "
                "straightforward. Wind picked up dramatically above 10,500'. Would go back in a "
                "calmer weather window."
            ),
        },
        {
            "date": (datetime.today() - timedelta(days=4)).strftime("%Y-%m-%d"),
            "location": "Muir Snowfield",
            "observer": "Party of 2",
            "observation": (
                "Day trip to Muir and back. Snowfield is in great shape — continuous coverage to "
                "Paradise. Hard-booted the morning, skied down in soft afternoon corn. No signs of "
                "instability on the snowfield itself. Nice day."
            ),
        },
    ],
    "mt. hood": [
        {
            "date": (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "location": "Hogsback, ~10,500'",
            "observer": "Party of 5",
            "observation": (
                "Summit day — started at 2am from Timberline. Conditions were perfect through the "
                "Pearly Gates — frozen solid, minimal rockfall. Summit by 6:30am. Corn was developing "
                "on the Palmer by the time we were back down, which was 10am. Perfect timing. "
                "Cracking in the wind slab near the Gates but nothing dramatic."
            ),
        },
        {
            "date": (datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "location": "Leuthold Couloir",
            "observer": "Party of 2",
            "observation": (
                "Skied the Leuthold — excellent conditions. Hard frozen at 4am, perfect corn by "
                "the time we were on the bottom half. 'Schrund crossing was clean. Would go again. "
                "Wind slab on the NE aspects of the summit was obvious but we stayed on the W face."
            ),
        },
    ],
    "west slopes south": [
        {
            "date": (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "location": "Crystal Mountain backcountry",
            "observer": "Ski patrol",
            "observation": (
                "Natural cycle on the North Peak headwall — D3 avalanche on a N aspect at 6,800'. "
                "Crown was 2.5' deep. Debris ran 800' into the basin below. This confirmed the "
                "persistent slab problem is still active. Closed the headwall to backcountry travel."
            ),
        },
        {
            "date": (datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "location": "Snoqualmie Pass area, Kendall Ridge",
            "observer": "Party of 3",
            "observation": (
                "Whumpfing every 50 meters on the approach to Kendall. Turned around immediately — "
                "didn't go above 4,000'. The sounds were alarming. Signs of a recent natural slide "
                "visible on the E aspect of Red Mountain. This snowpack is not trustworthy."
            ),
        },
    ],
}


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def get_avalanche_forecast(zone: str) -> dict[str, Any]:
    """Return NWAC-style avalanche forecast for the given zone."""
    key = zone.lower().strip()
    forecast = _ZONE_FORECASTS.get(key)
    if not forecast:
        # Try partial match
        for k, v in _ZONE_FORECASTS.items():
            if key in k or k in key:
                forecast = v
                key = k
                break

    if not forecast:
        return {
            "zone": zone,
            "date": datetime.today().strftime("%Y-%m-%d"),
            "error": f"Zone '{zone}' not found. Available zones: {', '.join(_ZONE_FORECASTS.keys())}",
        }

    danger_labels = {1: "Low", 2: "Moderate", 3: "Considerable", 4: "High", 5: "Extreme"}
    danger = forecast["danger"]

    return {
        "zone": zone,
        "date": datetime.today().strftime("%Y-%m-%d"),
        "danger": {
            "above_treeline": danger_labels[danger["above_treeline"]],
            "near_treeline": danger_labels[danger["near_treeline"]],
            "below_treeline": danger_labels[danger["below_treeline"]],
        },
        "avalanche_problems": forecast["problems"],
        "confidence": forecast["confidence"],
        "forecaster_summary": forecast["forecaster_summary"],
        "source": "NWAC (mocked)",
    }


def get_mountain_weather(location: str, days_out: int) -> dict[str, Any]:
    """Return weather forecast for the given location N days out (0 = today, max 5)."""
    days_out = max(0, min(5, days_out))
    key = location.lower().strip()

    location_data = None
    for k, v in _WEATHER_DATA.items():
        if key in k or k in key:
            location_data = v
            break

    if location_data and days_out in location_data:
        day_data = location_data[days_out]
    else:
        day_data = _DEFAULT_WEATHER

    target_date = (datetime.today() + timedelta(days=days_out)).strftime("%Y-%m-%d")

    return {
        "location": location,
        "forecast_date": target_date,
        "days_out": days_out,
        "summary": day_data["summary"],
        "sky": day_data.get("sky", "Variable"),
        "high_elevation": day_data["high_elevation"],
        "mid_elevation": day_data["mid_elevation"],
        "source": "NOAA/NWS (mocked)",
    }


def get_route_info(route_name: str) -> dict[str, Any]:
    """Return technical information about a named backcountry ski route."""
    key = route_name.lower().strip()
    route = _ROUTE_DATABASE.get(key)

    if not route:
        for k, v in _ROUTE_DATABASE.items():
            if key in k or k in key:
                route = v
                key = k
                break

    if not route:
        return {
            "route": route_name,
            "found": False,
            "message": (
                f"Route '{route_name}' is not in the database. "
                f"Known routes: {', '.join(_ROUTE_DATABASE.keys())}. "
                "If you're planning an unlisted route, describe it and I'll work with what you give me."
            ),
        }

    return {"route": route_name, "found": True, **route}


def lookup_recent_observations(zone: str, days_back: int) -> dict[str, Any]:
    """Return recent field observations for the given zone over the past N days."""
    days_back = max(1, min(14, days_back))
    key = zone.lower().strip()

    obs_list = None
    for k, v in _OBSERVATIONS.items():
        if key in k or k in key:
            obs_list = v
            break

    if not obs_list:
        obs_list = [
            {
                "date": (datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d"),
                "location": f"{zone}, general area",
                "observer": "Anonymous",
                "observation": "No recent observations on file for this zone. Check NWAC website for field reports.",
            }
        ]

    cutoff = datetime.today() - timedelta(days=days_back)
    filtered = [
        o for o in obs_list
        if datetime.strptime(o["date"], "%Y-%m-%d") >= cutoff
    ]

    return {
        "zone": zone,
        "days_back": days_back,
        "observation_count": len(filtered),
        "observations": filtered,
        "source": "NWAC field observations (mocked)",
    }


def escalate_to_human_guide(reason: str, conversation_summary: str) -> dict[str, Any]:
    """Hand off to a human guide when the situation exceeds what the agent should handle."""
    return {
        "escalated": True,
        "reason": reason,
        "summary_received": True,
        "message": (
            "Your request has been flagged for a certified guide. A guide from Cascadia Mountain Guides "
            "will follow up within 2-4 hours during business hours (8am-6pm PT). "
            "For immediate safety concerns, call 911 or Washington State SAR: 1-800-SAR-HELP."
        ),
        "callback_window": "2-4 hours",
        "contact": "Cascadia Mountain Guides (mocked)",
    }


# ---------------------------------------------------------------------------
# Tool dispatch (used by agent.py)
# ---------------------------------------------------------------------------

def dispatch(tool_name: str, tool_input: dict) -> Any:
    handlers = {
        "get_avalanche_forecast": lambda i: get_avalanche_forecast(i["zone"]),
        "get_nws_forecast": lambda i: get_nws_forecast(i["location"]),
        "get_mountain_weather": lambda i: get_mountain_weather(i["location"], i["days_out"]),
        "get_route_info": lambda i: get_route_info(i["route_name"]),
        "lookup_recent_observations": lambda i: lookup_recent_observations(i["zone"], i["days_back"]),
        "escalate_to_human_guide": lambda i: escalate_to_human_guide(i["reason"], i["conversation_summary"]),
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return handler(tool_input)


# ---------------------------------------------------------------------------
# Tool schemas for Claude API
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_avalanche_forecast",
        "description": (
            "Fetch the current NWAC-style avalanche forecast for a Washington Cascades zone. "
            "Returns danger rating by elevation band, avalanche problems with aspect/elevation/likelihood/size, "
            "forecaster confidence, and a summary. Call this early when any backcountry objective is discussed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "zone": {
                    "type": "string",
                    "description": (
                        "The forecast zone. Options: 'west slopes north', 'west slopes central', "
                        "'west slopes south', 'mt. rainier', 'mt. hood', 'east slopes north'."
                    ),
                }
            },
            "required": ["zone"],
        },
    },
    {
        "name": "get_nws_forecast",
        "description": (
            "Fetch live public National Weather Service forecast and active weather alerts for a known "
            "Cascades or Mt. Hood location. Use this when the user asks for current weather, wants "
            "a real public-data check, or is planning around timing, wind, precipitation, heat, or alerts. "
            "This is real public NWS data, not mocked data. Results include source_urls; cite the relevant "
            "NWS links in the final answer using Markdown links."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": (
                        "Known location such as 'paradise', 'camp muir', 'mt. rainier', "
                        "'timberline lodge', 'mt. hood', 'mt. baker', 'snoqualmie pass', "
                        "'stevens pass', 'crystal mountain', or 'artist point'."
                    ),
                }
            },
            "required": ["location"],
        },
    },
    {
        "name": "get_mountain_weather",
        "description": (
            "Fetch a multi-elevation weather forecast for a specific mountain location. "
            "Returns temperature, wind speed/direction, precipitation, freezing level, and sky conditions "
            "for high and mid elevation bands. Use days_out=0 for today."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Mountain location name, e.g. 'paradise', 'timberline lodge', 'baker'.",
                },
                "days_out": {
                    "type": "integer",
                    "description": "Days from today (0 = today, max 5).",
                    "minimum": 0,
                    "maximum": 5,
                },
            },
            "required": ["location", "days_out"],
        },
    },
    {
        "name": "get_route_info",
        "description": (
            "Look up technical information about a named backcountry ski or ski mountaineering route. "
            "Returns aspect, max slope angle, typical season, objective hazards, grade, approach notes, "
            "and descent description. If a route is not found, do not invent data — tell the user."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "route_name": {
                    "type": "string",
                    "description": (
                        "Route name, e.g. 'disappointment cleaver', 'coleman-deming glacier', "
                        "'fisher chimneys', 'south side', 'leuthold couloir', 'fuhrer finger'."
                    ),
                }
            },
            "required": ["route_name"],
        },
    },
    {
        "name": "lookup_recent_observations",
        "description": (
            "Fetch recent field observations from other parties in a given zone. "
            "Returns free-text reports with date, location, and what observers saw "
            "(cracking, whumpfing, recent avalanche activity, snow quality, etc.)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "zone": {
                    "type": "string",
                    "description": "The zone to look up, e.g. 'west slopes north', 'mt. rainier', 'mt. hood'.",
                },
                "days_back": {
                    "type": "integer",
                    "description": "How many days back to look for observations (1-14).",
                    "minimum": 1,
                    "maximum": 14,
                },
            },
            "required": ["zone", "days_back"],
        },
    },
    {
        "name": "escalate_to_human_guide",
        "description": (
            "Hand off to a human guide when the situation exceeds what this agent should handle. "
            "Use when: the party clearly lacks experience for their objective, there's a medical or "
            "legal question, the party is in an active emergency (→ tell them to call 911 first), "
            "or the conversation reveals something requiring professional judgment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Brief reason for escalation.",
                },
                "conversation_summary": {
                    "type": "string",
                    "description": "Summary of the party, objective, and conversation so far for the guide.",
                },
            },
            "required": ["reason", "conversation_summary"],
        },
    },
]
