import argparse
import html
import json
import shutil
import sys
from pathlib import Path


def get_execution_file(database, action, build_number):
    return (
        Path("logs")
        / database.lower()
        / action.lower()
        / f"build_{build_number}"
        / "execution.json"
    )


def get_report_directory(database, action, build_number):
    return (
        Path("reports")
        / database.lower()
        / action.lower()
        / f"build_{build_number}"
    )


def load_execution_data(execution_file):
    if not execution_file.exists():
        print(f"ERROR: Execution file not found: {execution_file}")
        sys.exit(1)

    try:
        with execution_file.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        print(f"ERROR: Invalid execution JSON: {error}")
        sys.exit(1)

    except OSError as error:
        print(f"ERROR: Unable to read execution file: {error}")
        sys.exit(1)


def write_json_report(execution_file, report_file):
    try:
        report_file.parent.mkdir(parents=True, exist_ok=True)

        shutil.copyfile(execution_file, report_file)

    except OSError as error:
        print(f"ERROR: Unable to generate JSON report: {error}")
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

    if status == "RUNNING":
        return "status-running"

    if status == "SKIPPED":
        return "status-skipped"

    if status == "ABORTED":
        return "status-aborted"

    if status == "UNSTABLE":
        return "status-unstable"

    return "status-default"


def generate_stage_rows(stages):
    if not stages:
        return """
            <tr>
                <td colspan="5">No stage information available.</td>
            </tr>
        """

    rows = []

    for stage in stages:
        stage_name = safe_value(stage.get("name"))
        start_time = safe_value(stage.get("start_time"))
        end_time = safe_value(stage.get("end_time"))
        duration = format_duration(stage.get("duration_seconds"))
        status = safe_value(stage.get("status"))
        status_class = get_status_class(stage.get("status"))

        rows.append(
            f"""
            <tr>
                <td>{stage_name}</td>
                <td>{start_time}</td>
                <td>{end_time}</td>
                <td>{duration}</td>
                <td>
                    <span class="{status_class}">
                        {status}
                    </span>
                </td>
            </tr>
            """
        )

    return "\n".join(rows)


def generate_environment_rows(environment):
    if not environment:
        return """
            <tr>
                <td colspan="2">
                    No environment information available.
                </td>
            </tr>
        """

    rows = []

    for key, value in environment.items():
        display_key = key.replace("_", " ").title()

        rows.append(
            f"""
            <tr>
                <th>{safe_value(display_key)}</th>
                <td>{safe_value(value)}</td>
            </tr>
            """
        )

    return "\n".join(rows)


def generate_error_section(error):
    if not error:
        return """
        <section class="card">
            <h2>Error Information</h2>
            <p class="no-error">
                No pipeline errors were recorded.
            </p>
        </section>
        """

    return f"""
    <section class="card error-card">
        <h2>Error Information</h2>

        <table>
            <tr>
                <th>Failed Stage</th>
                <td>{safe_value(error.get("failed_stage"))}</td>
            </tr>

            <tr>
                <th>Error Message</th>
                <td>{safe_value(error.get("message"))}</td>
            </tr>

            <tr>
                <th>Recorded At</th>
                <td>{safe_value(error.get("recorded_at"))}</td>
            </tr>
        </table>
    </section>
    """


def generate_html_report(data, report_file):
    pipeline = data.get("pipeline", {})
    execution = data.get("execution", {})
    environment = data.get("environment", {})
    stages = data.get("stages", [])
    error = data.get("error")

    final_status = execution.get("final_status", "UNKNOWN")
    final_status_class = get_status_class(final_status)

    stage_rows = generate_stage_rows(stages)
    environment_rows = generate_environment_rows(environment)
    error_section = generate_error_section(error)

    html_content = f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Pipeline Execution Report</title>

    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 30px;
            background: #f4f6f8;
            color: #222;
        }}

        .container {{
            max-width: 1200px;
            margin: auto;
        }}

        .header {{
            background: #ffffff;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            border: 1px solid #dddddd;
        }}

        .header h1 {{
            margin-top: 0;
        }}

        .card {{
            background: #ffffff;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            border: 1px solid #dddddd;
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
            font-weight: bold;
            color: #157347;
        }}

        .status-failure {{
            font-weight: bold;
            color: #b02a37;
        }}

        .status-running {{
            font-weight: bold;
            color: #0a58ca;
        }}

        .status-skipped {{
            font-weight: bold;
            color: #6c757d;
        }}

        .status-aborted {{
            font-weight: bold;
            color: #664d03;
        }}

        .status-unstable {{
            font-weight: bold;
            color: #997404;
        }}

        .status-default {{
            font-weight: bold;
        }}

        .error-card {{
            border: 1px solid #b02a37;
        }}

        .no-error {{
            color: #157347;
            font-weight: bold;
        }}

        .footer {{
            text-align: center;
            color: #666666;
            margin-top: 25px;
        }}
    </style>

</head>

<body>

<div class="container">

    <div class="header">

        <h1>Data Platform Automation Report</h1>

        <p>
            Final Status:
            <span class="{final_status_class}">
                {safe_value(final_status)}
            </span>
        </p>

    </div>


    <section class="card">

        <h2>Pipeline Information</h2>

        <table>

            <tr>
                <th>Database</th>
                <td>{safe_value(pipeline.get("database"))}</td>
            </tr>

            <tr>
                <th>Action</th>
                <td>{safe_value(pipeline.get("action"))}</td>
            </tr>

            <tr>
                <th>Operating System</th>
                <td>{safe_value(pipeline.get("operating_system"))}</td>
            </tr>

            <tr>
                <th>Build Number</th>
                <td>{safe_value(pipeline.get("build_number"))}</td>
            </tr>

            <tr>
                <th>Job Name</th>
                <td>{safe_value(pipeline.get("job_name"))}</td>
            </tr>

            <tr>
                <th>Build URL</th>
                <td>{safe_value(pipeline.get("build_url"))}</td>
            </tr>

        </table>

    </section>


    <section class="card">

        <h2>Execution Information</h2>

        <table>

            <tr>
                <th>Start Time</th>
                <td>{safe_value(execution.get("start_time"))}</td>
            </tr>

            <tr>
                <th>End Time</th>
                <td>{safe_value(execution.get("end_time"))}</td>
            </tr>

            <tr>
                <th>Total Duration</th>
                <td>
                    {
                        format_duration(
                            execution.get("duration_seconds")
                        )
                    }
                </td>
            </tr>

            <tr>
                <th>Final Status</th>
                <td>
                    <span class="{final_status_class}">
                        {safe_value(final_status)}
                    </span>
                </td>
            </tr>

        </table>

    </section>


    <section class="card">

        <h2>Environment Information</h2>

        <table>
            {environment_rows}
        </table>

    </section>


    <section class="card">

        <h2>Stage Execution Details</h2>

        <table>

            <thead>

                <tr>
                    <th>Stage Name</th>
                    <th>Start Time</th>
                    <th>End Time</th>
                    <th>Duration</th>
                    <th>Status</th>
                </tr>

            </thead>

            <tbody>
                {stage_rows}
            </tbody>

        </table>

    </section>


    {error_section}


    <div class="footer">
        Generated by Data Platform Automation Reporting Framework
    </div>

</div>

</body>

</html>
"""

    try:
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with report_file.open("w", encoding="utf-8") as file:
            file.write(html_content)

    except OSError as error:
        print(f"ERROR: Unable to generate HTML report: {error}")
        sys.exit(1)


def generate_reports(args):
    execution_file = get_execution_file(
        args.database,
        args.action,
        args.build_number
    )

    report_directory = get_report_directory(
        args.database,
        args.action,
        args.build_number
    )

    json_report = report_directory / "report.json"
    html_report = report_directory / "report.html"

    data = load_execution_data(execution_file)

    write_json_report(
        execution_file,
        json_report
    )

    generate_html_report(
        data,
        html_report
    )

    print("Reports generated successfully.")
    print(f"JSON Report: {json_report}")
    print(f"HTML Report: {html_report}")


def main():
    parser = argparse.ArgumentParser(
        description="Common pipeline report generator"
    )

    parser.add_argument("--database", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--build-number", required=True)

    args = parser.parse_args()

    generate_reports(args)


if __name__ == "__main__":
    main()