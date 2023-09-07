#! /usr/bin/env python3

import csv
import json
from pathlib import Path
import re
import subprocess


def parse_unit(string):
    """Parse strings like '2.2 TiB' and return float."""
    unit_to_exponent = {
        "KiB": 3,  # Kibi (2^10)
        "MiB": 6,  # Mebi (2^20)
        "GiB": 9,  # Gibi (2^30)
        "TiB": 12,  # Tebi (2^40)
        "PiB": 15,  # Peti (2^50)
    }

    value, unit = re.match(r"(\d+\.\d+)\s*([A-Za-z]+)", string).groups()
    parsed_data = float(value) * (10 ** unit_to_exponent[unit])
    return parsed_data


def run_dusage():
    command = ("dusage --csv",)
    completed_process = subprocess.run(
        command,
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
    )
    output = completed_process.stdout.decode()
    return output


def parse_csv(csv_data):
    """
    Parse CSV data and convert it into a list of dictionaries.

    Args:
        csv_data (str): CSV data as a string.

    Returns:
        list: List of dictionaries containing parsed CSV data.
    """
    parsed_data = []
    lines = csv_data.strip().split("\n")
    csv_reader = csv.reader(lines)
    _ = next(csv_reader) # skip header

    for row in csv_reader:
        if len(row) == 6:  # Saga
            path, backup, space_used, space_quota, files, files_quota = row
        elif len(row) == 8:
            # Fram & betzy return soft and hard quota.
            # Soft quota is used for warning
            path, backup, space_used, space_quota, _, files, files_quota, _ = row
        else:
            raise ValueError("Unkown number of fields in dusage csv output")

        parsed_data.append(
            {
                "path": path,
                "backup": backup,
                "space_used": space_used,
                "space_quota": space_quota,
                "files": int(files),
                "files_quota": files_quota if files_quota == "-" else int(files_quota),
            }
        )

    return parsed_data


def load_warning_messages(config_file):
    """
    Load warning messages from a JSON config file.

    Args:
        config_file (str): Path to the JSON config file.

    Returns:
        dict: Dictionary containing warning messages.
    """
    if not Path(config_file).exists():
        raise ValueError("config.json has to be in same folder as script")
    with open(config_file, "r", encoding="utf-8") as file:
        return json.load(file)


def check_space_quota_warnings(data, warning_messages, warning_threshold):
    """
    Check space quota warnings and print messages for exceeded space quotas.

    Args:
        data (list): List of dictionaries containing parsed CSV data.
        warning_messages (dict): Dictionary containing warning messages.
        warning_threshold (float): Threshold for issuing warnings (0 to 1).
    """
    for entry in data:
        if entry["space_quota"] != "-" and entry["space_used"] != "-":
            space_used = parse_unit(entry["space_used"])
            space_quota = parse_unit(entry["space_quota"])
            if space_used >= warning_threshold * space_quota:
                print(
                    warning_messages["space_quota_warning"].format(path=entry["path"])
                )


def check_files_quota_warnings(data, warning_messages, warning_threshold):
    """
    Check files quota warnings and print messages for exceeded files quotas.

    Args:
        data (list): List of dictionaries containing parsed CSV data.
        warning_messages (dict): Dictionary containing warning messages.
        warning_threshold (float): Threshold for issuing warnings (0 to 1).
    """
    for entry in data:
        if entry["files_quota"] != "-" and entry["files"] != "-":
            files_used = int(entry["files"])
            files_quota = int(entry["files_quota"])
            if files_used >= warning_threshold * files_quota:
                print(
                    warning_messages["files_quota_warning"].format(path=entry["path"])
                )


def main():
    """Print warning if users quota is close to quota. Do nothing oherwise.

    Checks quotas for number of files and space used and compares against usage.
    Uses `dusage` to get data.
    """
    config_file = "config.json"
    config_path = Path(__file__).parent / config_file

    dusage_output = run_dusage()  # dusage output is csv formatted
    data = parse_csv(dusage_output)
    warning_messages = load_warning_messages(config_path)

    space_warning_threshold = warning_messages.get("space_warning_threshold", 0.9)
    files_warning_threshold = warning_messages.get("files_warning_threshold", 0.8)

    check_space_quota_warnings(data, warning_messages, space_warning_threshold)
    check_files_quota_warnings(data, warning_messages, files_warning_threshold)


if __name__ == "__main__":
    main()
