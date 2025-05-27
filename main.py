from edsql_compiler import parser
import pandas as pd
import matplotlib.pyplot as plt
import spacy
from intent_classifier import classify_intent
from matcher_utils import extract_entities
from convert_to_edsql import convert_entities_to_edsql


# Load NLP model and dataset
nlp = spacy.load("en_core_web_sm")
df = pd.read_csv("students.csv")

import google.generativeai as genai

# Setup Gemini with your API key
genai.configure(api_key="AIzaSyC_i39OYSR86yUNuGq3WxebgRiMad5vXw0")

model = genai.GenerativeModel("gemini-2.0-flash")

def ask_gemini(nl_query):
    prompt = f"""
You are an expert in converting natural language to a custom SQL-like language called EDSQL.
EDSQL has these rules:

- SELECT ... FROM students;
- SELECT name, grades FROM students WHERE grades > 80;
- SELECT AVG(grades) FROM students GROUP BY class;
- SELECT name, grades FROM students ORDER BY grades DESC LIMIT 5;
- SELECT class FROM students PLOT PIE CHART;
- SELECT name, grades FROM students PLOT BAR GRAPH;
- SELECT PERFORMANCE_SCORE(grades, attendance) FROM students;

Now convert the following natural language query to EDSQL:

"{nl_query}"

Only return the EDSQL code. No explanation.
Only return valid EDSQL syntax without using '*'. List all columns explicitly. No explanation.

"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("Gemini fallback failed:", e)
        return None


def compute_custom_metric(df, metric_name):
    if metric_name == 'PERFORMANCE_SCORE':
        if 'grades' in df.columns and 'attendance' in df.columns:
            return 0.6 * df['grades'] + 0.4 * df['attendance']
        else:
            raise KeyError("Missing 'grades' or 'attendance' for PERFORMANCE_SCORE")
    raise KeyError(f"Unknown custom metric: {metric_name}")

def convert_to_edsql(nl_query):
    intent = classify_intent(nl_query)

    if intent == "average_query":
        return 'SELECT AVG(grades) FROM students GROUP BY class;'
    elif intent == "performance_query":
        return 'SELECT PERFORMANCE_SCORE(grades, attendance) FROM students;'
    elif intent == "plot_bar":
        return 'SELECT name, grades FROM students PLOT BAR GRAPH;'
    elif intent == "plot_line":
        return 'SELECT name, grades FROM students PLOT LINE GRAPH;'
    elif intent == "plot_pie":
        return 'SELECT class FROM students PLOT PIE CHART;'
    elif intent == "top_n_query":
        return 'SELECT name, grades FROM students ORDER BY grades DESC LIMIT 5;'
    elif intent == "conditional_query":
        return 'SELECT name, grades FROM students WHERE grades > 80;'
    else:
        return ask_gemini(nl_query)

def execute_query(parsed_query):
    _, select_list, table, where_clause, group_by_clause, plot_clause, order_clause, limit_clause, _ = parsed_query
    result = df.copy()

    # Step 1: Compute custom metrics if any
    custom_metric_names = []
    for sel in select_list:
        if isinstance(sel, tuple) and sel[0] == 'CUSTOM_METRIC':
            _, metric_name, col1, col2 = sel
            result[metric_name] = compute_custom_metric(result, metric_name)
            custom_metric_names.append(metric_name)

    # Step 2: Check if WHERE clause depends on a custom metric
    if where_clause:
        column, op, value = where_clause[1][1:]
        if column not in result.columns and column in custom_metric_names:
            result[column] = compute_custom_metric(result, column)

        if op == '>':
            result = result[result[column] > value]
        elif op == '<':
            result = result[result[column] < value]
        elif op == '=':
            result = result[result[column] == value]

    # Step 3: GROUP BY
    if group_by_clause:
        group_col = group_by_clause[1]
        if isinstance(select_list[0], tuple) and select_list[0][0] == 'AVG':
            result = result.groupby(group_col)[select_list[0][1]].mean().reset_index()

    # Step 4: ORDER BY
    if order_clause:
        _, order_col, order_dir = order_clause
        if order_col not in result.columns and order_col in custom_metric_names:
            result[order_col] = compute_custom_metric(result, order_col)
        result = result.sort_values(by=order_col, ascending=(order_dir.upper() == 'ASC'))

    # Step 5: LIMIT
    if limit_clause:
        _, limit_val = limit_clause
        result = result.head(int(limit_val))

    # Step 6: Build final select column list
    select_columns = []
    for sel in select_list:
        if isinstance(sel, tuple):
            if sel[0] == 'CUSTOM_METRIC':
                select_columns.append(sel[1])  # metric_name
            else:
                select_columns.append(sel[1])
        else:
            select_columns.append(sel)

    # If 'name' not selected but exists in df and metric used, add it
    if 'name' in df.columns and any(col in custom_metric_names for col in select_columns):
        if 'name' not in select_columns:
            select_columns.insert(0, 'name')

    # Step 7: Select only required columns
    try:
        result = result[select_columns]
    except KeyError as e:
        print(f"Error selecting columns: {e}")
        print(f"Available columns: {result.columns.tolist()}")
        return

    # Step 8: Plot if needed
    if plot_clause:
        plot_type = plot_clause[1]
        if plot_type == 'BAR':
            result.plot(kind='bar', x=select_columns[0], y=select_columns[1])
        elif plot_type == 'LINE':
            result.plot(kind='line', x=select_columns[0], y=select_columns[1])
        elif plot_type == 'PIE':
            result[select_columns[0]].value_counts().plot(kind='pie', autopct='%1.1f%%')
        plt.title(f"{plot_type.title()} Chart")
        plt.tight_layout()
        plt.show()

    # Step 9: Show final result
    print("Result:")
    print(result)


def main():
    user_input = input("Enter EDSQL or NL query:\n")
    if "select" not in user_input.lower():
        user_input = convert_to_edsql(user_input)
        if not user_input:
            print("Sorry, couldn't understand your natural language query.")
            return
        print("Converted to EDSQL:", user_input)

    parsed = parser.parse(user_input)
    if parsed:
        execute_query(parsed)
    else:
        print("Parsing failed.")

if __name__ == "__main__":
    main()
