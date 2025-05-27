def classify_intent(nl_query: str) -> str:
    nl_query = nl_query.lower()

    if "average" in nl_query and "grade" in nl_query:
        return "average_query"
    elif "performance score" in nl_query:
        return "performance_query"
    elif "bar graph" in nl_query or "bar chart" in nl_query:
        return "plot_bar"
    elif "line graph" in nl_query or "line chart" in nl_query:
        return "plot_line"
    elif "pie chart" in nl_query or "distribution" in nl_query:
        return "plot_pie"
    elif "top" in nl_query:
        return "top_n_query"
    elif "filter" in nl_query or "greater than" in nl_query or "less than" in nl_query:
        return "conditional_query"
    else:
        return "unknown"
