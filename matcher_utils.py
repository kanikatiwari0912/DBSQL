import spacy
from spacy.matcher import Matcher
import re

nlp = spacy.load("en_core_web_sm")

matcher = Matcher(nlp.vocab)

# Patterns
matcher.add("GRADE_COLUMN", [[{"LOWER": "grades"}]])
matcher.add("ATTENDANCE_COLUMN", [[{"LOWER": "attendance"}]])
matcher.add("CLASS_COLUMN", [[{"LOWER": "class"}]])

matcher.add("GREATER_THAN", [[{"LOWER": {"in": ["greater", "more"]}}, {"LOWER": "than"}]])
matcher.add("LESS_THAN", [[{"LOWER": {"in": ["less", "fewer"]}}, {"LOWER": "than"}]])
matcher.add("EQUAL_TO", [[{"LOWER": "equal"}, {"LOWER": "to"}]])

matcher.add("NUMERIC_VALUE", [[{"LIKE_NUM": True}]])

# Extract fields
def extract_entities(nl_query):
    query = nl_query.lower()
    entities = {
        "column": None,
        "operator": None,
        "value": None,
        "aggregation": None,
        "group_by": None,
        "plot": None,
        "x": None,
        "y": None,
        "custom_metric": None,
        "order": None,
        "limit": None
    }

    for col in ["grades", "attendance", "name", "class", "section"]:
        if col in query:
            entities["column"] = col
            break

    if "performance score" in query:
        entities["custom_metric"] = "PERFORMANCE_SCORE"
        entities["column"] = "PERFORMANCE_SCORE"

    # Operator & value
    for phrase, symbol in [("greater than", ">"), ("more than", ">"), ("less than", "<"), ("fewer than", "<"), ("equal to", "=")]:
        if phrase in query:
            entities["operator"] = symbol
            match = re.search(rf"{phrase} (\d+)", query)
            if match:
                entities["value"] = int(match.group(1))
            break

    # Aggregation
    for agg in ["average", "avg", "sum", "total", "max", "maximum", "min", "minimum"]:
        if agg in query:
            if "average" in query or "avg" in query:
                entities["aggregation"] = "AVG"
            elif "sum" in query or "total" in query:
                entities["aggregation"] = "SUM"
            elif "max" in query or "maximum" in query:
                entities["aggregation"] = "MAX"
            elif "min" in query or "minimum" in query:
                entities["aggregation"] = "MIN"
            break

    # Group by
    for group_col in ["class", "section"]:
        if f"group by {group_col}" in query or f"by {group_col}" in query:
            entities["group_by"] = group_col
            break
        
    # Top/Highest
    match = re.search(r"(top|highest) (\d+)", query)
    if match:
        entities["order"] = "DESC"
        entities["limit"] = int(match.group(2))

    # Bottom/Lowest
    match = re.search(r"(bottom|lowest) (\d+)", query)
    if match:
        entities["order"] = "ASC"
        entities["limit"] = int(match.group(2))

    # Fallback: If order is given but no limit
    if ("top" in query or "highest" in query) and entities["limit"] is None:
        entities["order"] = "DESC"
        entities["limit"] = 1
    elif ("bottom" in query or "lowest" in query) and entities["limit"] is None:
        entities["order"] = "ASC"
        entities["limit"] = 1

    # Plot type
    for kind, code in [("bar graph", "BAR"), ("bar", "BAR"), ("line chart", "LINE"), ("line", "LINE"), ("pie chart", "PIE"), ("pie", "PIE")]:
        if kind in query:
            entities["plot"] = code
            break

    # X and Y columns for plotting
    if "by" in query:
        parts = query.split("by")
        if len(parts) == 2:
            entities["y"] = parts[0].strip().split()[-1]
            entities["x"] = parts[1].strip().split()[0]
    else:
        # fallback to use "name" as x and column as y
        entities["x"] = "name"
        entities["y"] = entities["column"]

    return entities



