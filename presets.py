from __future__ import annotations

PRESETS = {
    "Arkansas Recruiting": {
        "title_bg": "#9D2235",
        "title_fg": "#FFFFFF",
        "subtitle_bg": "#9D2235",
        "subtitle_fg": "#FFFFFF",
        "header_bg": "#000000",
        "header_fg": "#FFFFFF",
        "body_bg": "#FFFFFF",
        "body_fg": "#000000",
        "font_family": "Chakra Petch",
        "title_size": 18,
        "subtitle_size": 11,
        "header_size": 10,
        "body_size": 10,
        "border_preset": "Dotted Vertical + Solid Horizontal",
        "uppercase_headers": True,
        "freeze_headers": True,
    },
    "Scouting Report": {
        "title_bg": "#000000",
        "title_fg": "#FFFFFF",
        "subtitle_bg": "#FFFFFF",
        "subtitle_fg": "#000000",
        "header_bg": "#D9D9D9",
        "header_fg": "#000000",
        "body_bg": "#FFFFFF",
        "body_fg": "#000000",
        "font_family": "Arial",
        "title_size": 18,
        "subtitle_size": 11,
        "header_size": 10,
        "body_size": 10,
        "border_preset": "Solid Horizontal",
        "uppercase_headers": True,
        "freeze_headers": True,
    },
    "Analytics": {
        "title_bg": "#FFFFFF",
        "title_fg": "#000000",
        "subtitle_bg": "#FFFFFF",
        "subtitle_fg": "#666666",
        "header_bg": "#EEEEEE",
        "header_fg": "#000000",
        "body_bg": "#FFFFFF",
        "body_fg": "#000000",
        "font_family": "Arial",
        "title_size": 20,
        "subtitle_size": 11,
        "header_size": 10,
        "body_size": 10,
        "border_preset": "Solid Gridlines",
        "uppercase_headers": False,
        "freeze_headers": True,
    },
}

TEMPLATE_TYPES = {
    "Blank Custom Template": [],
    "Recruiting Board": [
        "YR", "POS", "#", "FIRST", "LAST", "SCHOOL", "ST",
        "HT", "WT", "OFFERS", "STATUS", "NOTES"
    ],
    "Player Evaluation": [
        "POS", "PLAYER", "SCHOOL", "CLASS", "HT", "WT",
        "FILM TYPE", "GRADE", "STRENGTHS", "CONCERNS", "PROJECTION", "NOTES"
    ],
    "Camp Roster": [
        "YR", "POS", "#", "FIRST", "LAST", "SCHOOL", "ST",
        "HT", "WT", "40 #1", "40 #2", "SHUTTLE #1", "SHUTTLE #2",
        "BROAD #1", "BROAD #2", "OFFERS", "NOTES"
    ],
    "Opponent Scouting": [
        "UNIT", "PERSONNEL", "FORMATION", "CONCEPT", "DOWN", "DIST",
        "FIELD ZONE", "HASH", "TENDENCY", "NOTES"
    ],
    "Analytics Report": [
        "CATEGORY", "METRIC", "TEAM VALUE", "BENCHMARK", "DIFFERENCE", "NOTES"
    ],
    "Portal Board": [
        "POS", "PLAYER", "ORIGIN", "CLASS", "HT", "WT", "SNAPS",
        "STARTS", "GRADE", "FIT", "PRIORITY", "STATUS", "NOTES"
    ],
    "Meeting Sheet": [
        "TOPIC", "OWNER", "STATUS", "DECISION", "NEXT STEP", "DUE DATE", "NOTES"
    ],
}
