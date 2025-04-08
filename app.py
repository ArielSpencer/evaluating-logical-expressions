import re
import os
import sys
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_file

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from pdf_export import create_history_pdf, clean_old_pdfs

    print("Using full PDF export functionality")
except ImportError:
    try:
        from pdf_export_simple import create_history_pdf, clean_old_pdfs

        print("Using simplified export functionality (text file)")
    except ImportError:
        def create_history_pdf(history, variables, filename=None):
            print(
                "WARNING: PDF export modules not found. Using built-in fallback function."
            )
            if filename is None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"evaluate_expressions_history_{timestamp}.txt"

            output_dir = os.path.join(os.getcwd(), "static", "exports")
            os.makedirs(output_dir, exist_ok=True)

            file_path = os.path.join(output_dir, filename)

            with open(file_path, "w") as f:
                f.write("ExprEval - Expression History\n\n")
                for item in history:
                    f.write(f"{item}\n")

            return file_path, f"/static/exports/{filename}"

        def clean_old_pdfs():
            pass

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "your_default_secret_key_here"
)

MIN_VARIABLES = 1
MAX_VARIABLES = 10

ALLOWED_KEYWORDS = ["and", "or", "not", "True", "False"]

safe_globals = {
    "abs": abs,
}


@app.route("/")
def index():
    session.pop("variables", None)
    session.pop("history", None)
    session.pop("current_expression", None)
    return render_template("index.html")


@app.route("/setup_variables", methods=["POST"])
def setup_variables():
    try:
        var_count = int(request.form.get("var_count", 2))

        if var_count < MIN_VARIABLES or var_count > MAX_VARIABLES:
            return render_template(
                "index.html",
                error=f"Please enter between {MIN_VARIABLES} and {MAX_VARIABLES} variables.",
            )

        return render_template("variables.html", var_count=var_count)
    except ValueError:
        return render_template("index.html", error="Please enter a valid number.")


@app.route("/save_variables", methods=["POST"])
def save_variables():
    variables = {}
    history = []

    for key, value in request.form.items():
        if key.startswith("NUM"):
            try:
                var_name = key
                var_value = float(value)
                variables[var_name] = var_value
                variables[var_name.lower()] = var_value
            except ValueError:
                return render_template(
                    "variables.html",
                    var_count=len([k for k in request.form if k.startswith("NUM")]),
                    error="All variables must be valid numbers.",
                )

    session["variables"] = variables
    session["history"] = history
    session["current_expression"] = ""

    var_summary = "Variables saved: " + ", ".join(
        [
            f"{k} = {v}"
            for k, v in variables.items()
            if not (k.lower().startswith("num") and k != k.upper())
        ]
    )

    return render_template(
        "evaluate.html",
        variables=variables,
        history=[var_summary],
        current_expression="",
    )


@app.route("/export_pdf")
def export_pdf():
    variables = session.get("variables", {})
    history = session.get("history", [])

    if not history:
        return render_template(
            "evaluate.html",
            variables=variables,
            history=history,
            current_expression=session.get("current_expression", ""),
            error="No history to export.",
        )

    try:
        clean_old_pdfs()

        pdf_path, pdf_url = create_history_pdf(history, variables)

        mime_type = "application/pdf" if pdf_path.endswith(".pdf") else "text/plain"

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=os.path.basename(pdf_path),
            mimetype=mime_type,
        )
    except Exception as e:
        import traceback

        traceback.print_exc()

        return render_template(
            "evaluate.html",
            variables=variables,
            history=history,
            current_expression=session.get("current_expression", ""),
            error=f"Error generating export: {str(e)}",
        )


@app.route("/evaluate", methods=["POST"])
def evaluate():
    variables = session.get("variables", {})
    history = session.get("history", [])
    current_expression = session.get("current_expression", "")

    action = request.form.get("action", "")

    if action == "add_token":
        token = request.form.get("token", "")
        current_expression = add_token_to_expression(current_expression, token)
    elif action == "backspace":
        current_expression = handle_backspace(current_expression)
    elif action == "clear":
        current_expression = ""
    elif action == "evaluate_expr":
        expression = current_expression.strip()

        if not expression:
            return render_template(
                "evaluate.html",
                variables=variables,
                history=history,
                current_expression=current_expression,
                error="Please enter an expression.",
            )

        result = ""
        result_class = ""

        try:
            if not is_safe_expression(expression):
                raise ValueError(
                    "Expression contains disallowed characters or functions."
                )

            safe_locals = dict(variables)

            result_value = eval(expression, safe_globals, safe_locals)

            if isinstance(result_value, bool):
                result = "True" if result_value else "False"
                result_class = "true" if result_value else "false"
            else:
                result = str(result_value)
                result_class = ""

            history_entry = f"Expression: {expression} → {result}"

        except Exception as e:
            result = f"Error: {str(e)}"
            result_class = "error"
            history_entry = f"Expression: {expression} → {result}"

        history.insert(0, history_entry)
        session["history"] = history

        return render_template(
            "evaluate.html",
            variables=variables,
            history=history,
            current_expression="",
            expression=expression,
            result=result,
            result_class=result_class,
        )

    session["current_expression"] = current_expression

    return render_template(
        "evaluate.html",
        variables=variables,
        history=history,
        current_expression=current_expression,
    )


def add_token_to_expression(current_expr, token):
    current_tokens = current_expr.split()

    if (
        token.replace(".", "", 1).isdigit()
        and current_tokens
        and current_tokens[-1].replace(".", "", 1).isdigit()
    ):
        current_tokens[-1] += token
    else:
        if token.endswith("(") and current_tokens:
            current_tokens.append(token)
        elif (token == ")" or token == ",") and current_tokens:
            current_tokens.append(token)
        elif current_tokens:
            current_tokens.append(token)
        else:
            current_tokens = [token]

    rebuilt_expr = ""
    for i, t in enumerate(current_tokens):
        is_number = is_numeric(t)
        prev_is_number = i > 0 and is_numeric(current_tokens[i - 1])

        if is_number and prev_is_number:
            rebuilt_expr += t
        else:
            if i > 0:
                rebuilt_expr += " "
            rebuilt_expr += t

    return rebuilt_expr


def handle_backspace(current_expr):
    if not current_expr:
        return ""

    tokens = current_expr.split()

    if not tokens:
        return ""

    last_token = tokens[-1]

    if is_numeric(last_token) and len(last_token) > 1:
        tokens[-1] = last_token[:-1]
    else:
        tokens.pop()

    return " ".join(tokens)


def is_numeric(token):
    try:
        float(token)
        return True
    except ValueError:
        return False


def is_safe_expression(expr):
    allowed_pattern = r"^[a-zA-Z0-9_\s\.\+\-\*\/\%\(\)\<\>\=\!\,\&\|]*$"
    if not bool(re.match(allowed_pattern, expr)):
        return False

    import keyword

    for word in keyword.kwlist:
        if word not in ALLOWED_KEYWORDS and re.search(r"\b" + word + r"\b", expr):
            return False

    return True


if __name__ == "__main__":
    export_dir = os.path.join(os.getcwd(), "static", "exports")
    os.makedirs(export_dir, exist_ok=True)

    app.run(debug=True)
else:
    export_dir = os.path.join(os.getcwd(), "static", "exports")
    os.makedirs(export_dir, exist_ok=True)

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)