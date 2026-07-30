import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def current_time():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def get_log_file(database, action, build_number):
    return (
        Path("logs")
        / database.lower()
        / action.lower()
        / f"build_{build_number}"
        / "execution.json"
    )


def load_log_data(log_file):
    if not log_file.exists():
        print(f"ERROR: Execution log not found: {log_file}")
        sys.exit(1)

    try:
        with log_file.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        print(f"ERROR: Invalid execution log JSON: {error}")
        sys.exit(1)

    except OSError as error:
        print(f"ERROR: Unable to read execution log: {error}")
        sys.exit(1)


def save_log_data(log_file, data):
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with log_file.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    except OSError as error:
        print(f"ERROR: Unable to save execution log: {error}")
        sys.exit(1)


def initialize_log(args):
    log_file = get_log_file(
        args.database,
        args.action,
        args.build_number
    )

    data = {
        "pipeline": {
            "database": args.database.lower(),
            "action": args.action.lower(),
            "operating_system": args.os.lower(),
            "build_number": args.build_number,
            "job_name": args.job_name,
            "build_url": args.build_url,
        },
        "execution": {
            "start_time": current_time(),
            "end_time": None,
            "duration_seconds": None,
            "final_status": "RUNNING",
        },
        "environment": {},
        "stages": [],
        "error": None,
    }

    save_log_data(log_file, data)

    print(f"Execution log initialized: {log_file}")


def set_environment(args):
    log_file = get_log_file(
        args.database,
        args.action,
        args.build_number
    )

    data = load_log_data(log_file)

    administrator_privileges = (
        args.administrator_privileges.lower() == "true"
    )

    if administrator_privileges:
        execution_mode = "windows_service"
    else:
        execution_mode = "project_local"

    data["environment"]["administrator_privileges"] = (
        administrator_privileges
    )

    data["environment"]["execution_mode"] = execution_mode

    save_log_data(log_file, data)

    print(f"Environment information updated: {log_file}")
    print(f"Administrator Privileges: {administrator_privileges}")
    print(f"Execution Mode: {execution_mode}")


def stage_start(args):
    log_file = get_log_file(
        args.database,
        args.action,
        args.build_number
    )

    data = load_log_data(log_file)

    for stage in data["stages"]:
        if (
            stage["name"] == args.stage_name
            and stage["status"] == "RUNNING"
        ):
            print(f"ERROR: Stage is already running: {args.stage_name}")
            sys.exit(1)

    stage_data = {
        "name": args.stage_name,
        "start_time": current_time(),
        "end_time": None,
        "duration_seconds": None,
        "status": "RUNNING",
    }

    data["stages"].append(stage_data)

    save_log_data(log_file, data)

    print(f"Stage started: {args.stage_name}")


def stage_end(args):
    log_file = get_log_file(
        args.database,
        args.action,
        args.build_number
    )

    data = load_log_data(log_file)

    target_stage = None

    for stage in reversed(data["stages"]):
        if (
            stage["name"] == args.stage_name
            and stage["status"] == "RUNNING"
        ):
            target_stage = stage
            break

    if target_stage is None:
        print(f"ERROR: Running stage not found: {args.stage_name}")
        sys.exit(1)

    try:
        start_time = datetime.fromisoformat(
            target_stage["start_time"]
        )

    except (KeyError, TypeError, ValueError) as error:
        print(f"ERROR: Invalid stage start time: {error}")
        sys.exit(1)

    end_time = datetime.now().astimezone()

    duration = (end_time - start_time).total_seconds()

    target_stage["end_time"] = end_time.isoformat(
        timespec="seconds"
    )

    target_stage["duration_seconds"] = round(duration, 2)

    target_stage["status"] = args.status.upper()

    save_log_data(log_file, data)

    print(f"Stage completed: {args.stage_name}")
    print(f"Stage Status: {args.status.upper()}")
    print(f"Stage Duration: {round(duration, 2)} seconds")


def set_error(args):
    log_file = get_log_file(
        args.database,
        args.action,
        args.build_number
    )

    data = load_log_data(log_file)

    data["error"] = {
        "failed_stage": args.failed_stage,
        "message": args.message,
        "recorded_at": current_time(),
    }

    save_log_data(log_file, data)

    print(f"Pipeline error recorded: {log_file}")
    print(f"Failed Stage: {args.failed_stage}")
    print(f"Error Message: {args.message}")


def finalize_log(args):
    log_file = get_log_file(
        args.database,
        args.action,
        args.build_number
    )

    data = load_log_data(log_file)

    try:
        start_time = datetime.fromisoformat(
            data["execution"]["start_time"]
        )

    except (KeyError, TypeError, ValueError) as error:
        print(f"ERROR: Invalid pipeline start time: {error}")
        sys.exit(1)

    end_time = datetime.now().astimezone()

    duration = (end_time - start_time).total_seconds()

    data["execution"]["end_time"] = end_time.isoformat(
        timespec="seconds"
    )

    data["execution"]["duration_seconds"] = round(duration, 2)

    data["execution"]["final_status"] = args.status.upper()

    save_log_data(log_file, data)

    print(f"Execution log finalized: {log_file}")
    print(f"Final Status: {args.status.upper()}")
    print(f"Duration: {round(duration, 2)} seconds")


def main():
    parser = argparse.ArgumentParser(
        description="Common pipeline execution logger"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    init_parser = subparsers.add_parser(
        "init",
        help="Initialize pipeline execution log"
    )

    init_parser.add_argument("--database", required=True)
    init_parser.add_argument("--action", required=True)
    init_parser.add_argument("--os", required=True)
    init_parser.add_argument("--build-number", required=True)
    init_parser.add_argument("--job-name", required=True)
    init_parser.add_argument("--build-url", required=True)

    environment_parser = subparsers.add_parser(
        "set-environment",
        help="Add environment information to execution log"
    )

    environment_parser.add_argument("--database", required=True)
    environment_parser.add_argument("--action", required=True)
    environment_parser.add_argument("--build-number", required=True)

    environment_parser.add_argument(
        "--administrator-privileges",
        required=True,
        choices=["true", "false"]
    )

    stage_start_parser = subparsers.add_parser(
        "stage-start",
        help="Start stage tracking"
    )

    stage_start_parser.add_argument("--database", required=True)
    stage_start_parser.add_argument("--action", required=True)
    stage_start_parser.add_argument("--build-number", required=True)
    stage_start_parser.add_argument("--stage-name", required=True)

    stage_end_parser = subparsers.add_parser(
        "stage-end",
        help="Complete stage tracking"
    )

    stage_end_parser.add_argument("--database", required=True)
    stage_end_parser.add_argument("--action", required=True)
    stage_end_parser.add_argument("--build-number", required=True)
    stage_end_parser.add_argument("--stage-name", required=True)

    stage_end_parser.add_argument(
        "--status",
        required=True,
        choices=[
            "SUCCESS",
            "FAILURE",
            "SKIPPED"
        ]
    )

    error_parser = subparsers.add_parser(
        "set-error",
        help="Record pipeline error information"
    )

    error_parser.add_argument("--database", required=True)
    error_parser.add_argument("--action", required=True)
    error_parser.add_argument("--build-number", required=True)
    error_parser.add_argument("--failed-stage", required=True)
    error_parser.add_argument("--message", required=True)

    finalize_parser = subparsers.add_parser(
        "finalize",
        help="Finalize pipeline execution log"
    )

    finalize_parser.add_argument("--database", required=True)
    finalize_parser.add_argument("--action", required=True)
    finalize_parser.add_argument("--build-number", required=True)

    finalize_parser.add_argument(
        "--status",
        required=True,
        choices=[
            "SUCCESS",
            "FAILURE",
            "ABORTED",
            "UNSTABLE"
        ]
    )

    args = parser.parse_args()

    if args.command == "init":
        initialize_log(args)

    elif args.command == "set-environment":
        set_environment(args)

    elif args.command == "stage-start":
        stage_start(args)

    elif args.command == "stage-end":
        stage_end(args)

    elif args.command == "set-error":
        set_error(args)

    elif args.command == "finalize":
        finalize_log(args)


if __name__ == "__main__":
    main()