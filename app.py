from flask import Flask, render_template, request, jsonify
import pandas as pd
from edsql_compiler import parser
from convert_to_edsql import convert_entities_to_edsql
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend suitable for web apps

import matplotlib.pyplot as plt
import io
import base64

# Initialize Flask app
app = Flask(__name__)

# Load dataset
df = pd.read_csv("students.csv")

def execute_query(parsed_query):
    """Execute the parsed EDSQL query."""
    _, select_list, table, where_clause, group_by_clause, plot_clause, order_clause, limit_clause, _ = parsed_query
    result = df.copy()

    # Apply WHERE clause
    if where_clause:
        column, op, value = where_clause[1][1:]
        if op == '>':
            result = result[result[column] > value]
        elif op == '<':
            result = result[result[column] < value]
        elif op == '=':
            result = result[result[column] == value]

    # Apply GROUP BY and Aggregation
    if group_by_clause:
        group_col = group_by_clause[1]
        if isinstance(select_list[0], tuple) and select_list[0][0] == 'AVG':
            result = result.groupby(group_col)[select_list[0][1]].mean().reset_index()

    # Apply ORDER BY
    if order_clause:
        _, order_col, order_dir = order_clause
        result = result.sort_values(by=order_col, ascending=(order_dir.upper() == 'ASC'))

    # Apply LIMIT
    if limit_clause:
        _, limit_val = limit_clause
        result = result.head(int(limit_val))

    # Select specified columns
    columns = [sel if isinstance(sel, str) else sel[1] for sel in select_list]
    result = result[columns]

    return result

@app.route("/", methods=["GET", "POST"])
def index():
    query = ""
    sql_query = ""
    output = None
    graph = None

    if request.method == "POST":
        query = request.form.get("query").strip()  # Get the query and strip whitespace
        
        # Check if it's NLP or SQL
        if query:  # Ensure the query is not empty
            if "select" not in query.lower():
                sql_query = convert_entities_to_edsql(query)  # Convert NLP to SQL
                if not sql_query:  # If conversion fails
                    output = "Sorry, couldn't understand the NLP."
                    return render_template("index.html", query=query, sql_query=sql_query, output=output, graph=graph)
            else:
                sql_query = query

            # Parse and execute query
            parsed = parser.parse(sql_query)
            if parsed:
                result = execute_query(parsed)

                # Check for plot
                plot_clause = parsed[5]
                if plot_clause:
                    plot_type = plot_clause[1]
                    fig, ax = plt.subplots()
                    if plot_type == "BAR":
                        result.plot(kind="bar", x=result.columns[0], y=result.columns[1], ax=ax)
                    elif plot_type == "LINE":
                        result.plot(kind="line", x=result.columns[0], y=result.columns[1], ax=ax)
                    elif plot_type == "PIE":
                        if result.shape[1] >= 2:
                            data = result.set_index(result.columns[0])[result.columns[1]]
                        else:
                            data = result[result.columns[0]].value_counts()
                        data.plot(kind="pie", ax=ax, autopct='%1.1f%%')
                        ax.set_ylabel("")

                    # Convert plot to base64
                    buf = io.BytesIO()
                    plt.savefig(buf, format="png")
                    buf.seek(0)
                    graph = base64.b64encode(buf.getvalue()).decode()
                    buf.close()
                    plt.close(fig)
                else:
                    output = result.to_html(classes="table table-bordered")
            else:
                output = "Error parsing query."
        else:
            output = "Please enter a valid query."

    return render_template("index.html", query=query, sql_query=sql_query, output=output, graph=graph)

if __name__ == "__main__":
    app.run(debug=True)
