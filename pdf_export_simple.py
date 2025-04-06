import os
import datetime

def create_history_pdf(history, user_variables, filename=None):
    if filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluate_expressions_history_{timestamp}.txt"

    output_dir = os.path.join(os.getcwd(), "static", "exports")
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, filename)

    with open(file_path, "w") as f:
        f.write("ExprEval - Expression History\n")
        f.write("=" * 40 + "\n\n")

        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"Generated on: {date_str}\n\n")

        f.write("Variables:\n")
        f.write("-" * 20 + "\n")

        for name, value in user_variables.items():
            if name == name.upper() and name.startswith("NUM"):
                f.write(f"{name} = {value}\n")

        f.write("\n")

        f.write("Expression History:\n")
        f.write("-" * 40 + "\n")

        if history:
            for idx, entry in enumerate(history):
                f.write(f"{idx + 1}. {entry}\n")
        else:
            f.write("No history entries.\n")

    return file_path, f"/static/exports/{filename}"


def clean_old_pdfs(max_age_hours=24):
    export_dir = os.path.join(os.getcwd(), "static", "exports")
    if not os.path.exists(export_dir):
        return

    now = datetime.datetime.now()

    for filename in os.listdir(export_dir):
        if filename.endswith(".txt") or filename.endswith(".pdf"):
            file_path = os.path.join(export_dir, filename)

            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

            age = now - file_time

            if age.total_seconds() > max_age_hours * 3600:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Failed to remove old file {filename}: {e}")
