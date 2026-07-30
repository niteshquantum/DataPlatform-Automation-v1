import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path


def get_execution_file(database, action, build_number):
    return (
        Path("logs")
        / database.lower()
        / action.lower()
        / f"build_{build_number}"
        / "execution.json"
    )


def get_history_directory():
    return Path("reports") / "history"


def get_history_json_file():
    return get_history_directory() / "execution_history.json"


def get_history_html_file():
    return get_history_directory() / "execution_history.html"


def load_json_file(file_path):
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        print(f"ERROR: Invalid JSON file: {error}")
        sys.exit(1)

    except OSError as error:
        print(f"ERROR: Unable to read file: {error}")
        sys.exit(1)


def load_history():
    history_file = get_history_json_file()

    if not history_file.exists():
        return {
            "generated_at": None,
            "total_executions": 0,
            "executions": []
        }

    try:
        with history_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("History root must be a JSON object.")

        if "executions" not in data:
            data["executions"] = []

        if not isinstance(data["executions"], list):
            raise ValueError(
                "History executions must be a JSON list."
            )

        return data

    except (json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: Invalid execution history: {error}")
        sys.exit(1)

    except OSError as error:
        print(f"ERROR: Unable to read execution history: {error}")
        sys.exit(1)


def save_history(history):
    history_file = get_history_json_file()

    try:
        history_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with history_file.open("w", encoding="utf-8") as file:
            json.dump(
                history,
                file,
                indent=4
            )

    except OSError as error:
        print(f"ERROR: Unable to save execution history: {error}")
        sys.exit(1)


def safe_value(value):
    if value is None:
        return "N/A"

    return html.escape(str(value))


def format_duration(duration):
    if duration is None:
        return "N/A"

    try:
        duration = float(duration)

    except (TypeError, ValueError):
        return safe_value(duration)

    if duration < 60:
        return f"{duration:.2f} seconds"

    minutes, seconds = divmod(duration, 60)

    if minutes < 60:
        return f"{int(minutes)} min {seconds:.2f} sec"

    hours, minutes = divmod(minutes, 60)

    return (
        f"{int(hours)} hr "
        f"{int(minutes)} min "
        f"{seconds:.2f} sec"
    )


def get_status_class(status):
    status = str(status).upper()

    if status == "SUCCESS":
        return "status-success"

    if status == "FAILURE":
        return "status-failure"

    if status == "ABORTED":
        return "status-aborted"

    if status == "UNSTABLE":
        return "status-unstable"

    if status == "RUNNING":
        return "status-running"

    return "status-default"


def create_execution_record(execution_data):
    pipeline = execution_data.get("pipeline", {})
    execution = execution_data.get("execution", {})
    error = execution_data.get("error")

    failed_stage = None
    error_message = None

    if isinstance(error, dict):
        failed_stage = error.get("failed_stage")
        error_message = error.get("message")

    return {
        "database": pipeline.get("database"),
        "action": pipeline.get("action"),
        "operating_system": pipeline.get("operating_system"),
        "build_number": pipeline.get("build_number"),
        "job_name": pipeline.get("job_name"),
        "build_url": pipeline.get("build_url"),
        "start_time": execution.get("start_time"),
        "end_time": execution.get("end_time"),
        "duration_seconds": execution.get("duration_seconds"),
        "final_status": execution.get("final_status"),
        "failed_stage": failed_stage,
        "error_message": error_message
    }


def get_record_identity(record):
    return (
        str(record.get("database", "")).lower(),
        str(record.get("action", "")).lower(),
        str(record.get("operating_system", "")).lower(),
        str(record.get("job_name", "")),
        str(record.get("build_number", ""))
    )


def update_history(history, new_record):
    new_identity = get_record_identity(new_record)

    existing_index = None

    for index, record in enumerate(history["executions"]):
        if get_record_identity(record) == new_identity:
            existing_index = index
            break

    if existing_index is None:
        history["executions"].append(new_record)
        operation = "added"

    else:
        history["executions"][existing_index] = new_record
        operation = "updated"

    history["generated_at"] = (
        datetime.now()
        .astimezone()
        .isoformat(timespec="seconds")
    )

    history["total_executions"] = len(
        history["executions"]
    )

    return operation


def generate_history_rows(executions):
    if not executions:
        return """
        <tr>
            <td colspan="10">
                No pipeline execution history available.
            </td>
        </tr>
        """

    rows = []

    for record in reversed(executions):
        status = record.get("final_status", "UNKNOWN")
        status_class = get_status_class(status)

        rows.append(
            f"""
            <tr>
                <td>
                    {safe_value(record.get("build_number"))}
                </td>

                <td>
                    {safe_value(record.get("database"))}
                </td>

                <td>
                    {safe_value(record.get("action"))}
                </td>

                <td>
                    {
                        safe_value(
                            record.get("operating_system")
                        )
                    }
                </td>

                <td>
                    {safe_value(record.get("job_name"))}
                </td>

                <td>
                    {safe_value(record.get("start_time"))}
                </td>

                <td>
                    {
                        format_duration(
                            record.get("duration_seconds")
                        )
                    }
                </td>

                <td>
                    <span class="{status_class}">
                        {safe_value(status)}
                    </span>
                </td>

                <td>
                    {safe_value(record.get("failed_stage"))}
                </td>

                <td>
                    {safe_value(record.get("error_message"))}
                </td>
            </tr>
            """
        )

    return "\n".join(rows)


def generate_html_history(history):
    history_file = get_history_html_file()

    rows = generate_history_rows(
        history.get("executions", [])
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Pipeline Execution History</title>

    <style>

        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 30px;
            background: #f4f6f8;
            color: #222;
        }}

        .container {{
            max-width: 1600px;
            margin: auto;
        }}

        .header {{
            background: #ffffff;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            border: 1px solid #dddddd;
        }}

        .card {{
            background: #ffffff;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #dddddd;
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th,
        td {{
            padding: 10px;
            border: 1px solid #dddddd;
            text-align: left;
            vertical-align: top;
        }}

        th {{
            background: #f0f2f5;
        }}

        .status-success {{
            color: #157347;
            font-weight: bold;
        }}

        .status-failure {{
            color: #b02a37;
            font-weight: bold;
        }}

        .status-aborted {{
            color: #664d03;
            font-weight: bold;
        }}

        .status-unstable {{
            color: #997404;
            font-weight: bold;
        }}

        .status-running {{
            color: #0a58ca;
            font-weight: bold;
        }}

        .status-default {{
            font-weight: bold;
        }}

        .footer {{
            margin-top: 25px;
            text-align: center;
            color: #666666;
        }}

    </style>

</head>


<body>

<div class="container">

    <div class="header">

        <h1>
            Data Platform Automation Execution History
        </h1>

        <p>
            Total Executions:
            <strong>
                {
                    safe_value(
                        history.get(
                            "total_executions",
                            0
                        )
                    )
                }
            </strong>
        </p>

        <p>
            Last Updated:
            {
                safe_value(
                    history.get("generated_at")
                )
            }
        </p>

    </div>


    <section class="card">

        <table>

            <thead>

                <tr>
                    <th>Build</th>
                    <th>Database</th>
                    <th>Action</th>
                    <th>OS</th>
                    <th>Job Name</th>
                    <th>Start Time</th>
                    <th>Duration</th>
                    <th>Status</th>
                    <th>Failed Stage</th>
                    <th>Error Message</th>
                </tr>

            </thead>

            <tbody>
                {rows}
            </tbody>

        </table>

    </section>


    <div class="footer">
        Generated by Data Platform Automation Reporting Framework
    </div>

</div>

</body>

</html>
"""

    try:
        history_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with history_file.open(
            "w",
            encoding="utf-8"
        ) as file:
            file.write(html_content)

    except OSError as error:
        print(
            f"ERROR: Unable to generate "
            f"execution history HTML: {error}"
        )
        sys.exit(1)


def generate_history(args):
    execution_file = get_execution_file(
        args.database,
        args.action,
        args.build_number
    )

    execution_data = load_json_file(
        execution_file
    )

    history = load_history()

    new_record = create_execution_record(
        execution_data
    )

    operation = update_history(
        history,
        new_record
    )

    save_history(history)

    generate_html_history(history)

    print("Execution history generated successfully.")

    print(
        f"History Record: {operation.upper()}"
    )

    print(
        f"Total Executions: "
        f"{history['total_executions']}"
    )

    print(
        f"JSON History: "
        f"{get_history_json_file()}"
    )

    print(
        f"HTML History: "
        f"{get_history_html_file()}"
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Common pipeline execution "
            "history generator"
        )
    )

    parser.add_argument(
        "--database",
        required=True
    )

    parser.add_argument(
        "--action",
        required=True
    )

    parser.add_argument(
        "--build-number",
        required=True
    )

    args = parser.parse_args()

    generate_history(args)


if __name__ == "__main__":
    main()