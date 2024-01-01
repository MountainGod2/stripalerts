"""
This module contains a function that aligns the logs in the log file and
writes them to a new file with the date appended to the file name.
Then it deletes the original log file.
"""
import os
import re
from datetime import datetime


def align_logs(file_path="app.log"):
    """
    This function aligns the logs in the log file and
    writes them to a new file with the date appended to the file name.
    Then it deletes the original log file.

    Args:
        file_path (str, optional): The path of the log file.
        Defaults to "app.log".
    """
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    max_name_length = 0
    max_level_length = 0

    # Analyzing the log to find the maximum length of name and level fields
    for line in lines:
        parts = re.split(r" - ", line)
        if len(parts) >= 4:
            max_name_length = max(max_name_length, len(parts[1]))
            max_level_length = max(max_level_length, len(parts[2]))

    # Writing the logs to a new file and apending the date to the file name
    with open(
        f"stripalerts_{datetime.now().strftime('%Y%m%d')}.log", "w", encoding="utf-8"
    ) as file:
        for line in lines:
            parts = re.split(r" - ", line, maxsplit=3)
            if len(parts) >= 4:
                file.write(
                    f"{parts[0]} - {parts[1]:<{max_name_length}} - "
                    f"{parts[2]:<{max_level_length}} - {parts[3]}"
                )

    # Comment this line if you don't want to delete the original log file
    delete_file(file_path)


# Deleting the original log file
def delete_file(file_path):
    """
    This function deletes the original log file.

    Args:
        file_path (str): The path of the log file.
    """
    os.remove(file_path)


if __name__ == "__main__":
    align_logs("app.log")
