import csv
import json
import subprocess


def run_dusage():
    command = ("dusage --csv",)
    try:
        completed_process = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Capture output as text
        )

        if completed_process.returncode == 0:
            output = completed_process.stdout
        else:
            print(
                f"Error: Dusage command failed with return code {completed_process.returncode}"
            )
            print(completed_process.stderr)
    except Exception as e:
        print(f"Error: {e}")
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
    header = next(csv_reader)

    for row in csv_reader:
        path, backup, space_used, space_quota, files, files_quota = row
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
    with open(config_file, "r") as f:
        return json.load(f)


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
            space_used = float(entry["space_used"].split()[0])
            space_quota = float(entry["space_quota"].split()[0])
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


def main(config_file="config.json"):
    """Print warning if users quota is close to quota. Do nothing oherwise.

    Checks quotas for number of files and space used and compares against usage.
    Uses `dusage` to get data.
    """
    dusage_output = run_dusage()  # dusage output is csv formatted
    data = parse_csv(dusage_output)
    warning_messages = load_warning_messages(config_file)

    space_warning_threshold = warning_messages.get("space_warning_threshold", 0.9)
    files_warning_threshold = warning_messages.get("files_warning_threshold", 0.8)

    check_space_quota_warnings(data, warning_messages, space_warning_threshold)
    check_files_quota_warnings(data, warning_messages, files_warning_threshold)


if __name__ == "__main__":
    main()
