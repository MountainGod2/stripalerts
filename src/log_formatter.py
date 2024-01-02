"""
This module contains functions related to log file formatting and manipulation.
It includes functionality to align logs and handle file operations.
"""

import logging
import os
import re
from datetime import datetime

# Setting up basic logging
logging.basicConfig(level=logging.INFO)


def read_logs(file_path):
    """
    Read logs from a file.

    Args:
        file_path (str): Path of the log file.

    Returns:
        list: List of log lines.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.readlines()
    except IOError as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return []


def write_aligned_logs(lines, max_name_length, max_level_length, output_file):
    """
    Write aligned logs to a new file.

    Args:
        lines (list): List of log lines.
        max_name_length (int): Maximum length of the name field.
        max_level_length (int): Maximum length of the level field.
        output_file (str): Path for the output file.
    """
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            for line in lines:
                parts = re.split(r" - ", line, maxsplit=3)
                if len(parts) >= 4:
                    aligned_line = f"{parts[0]} - {parts[1]:<{max_name_length}} - {parts[2]:<{max_level_length}} - {parts[3]}"
                    file.write(aligned_line)
    except IOError as e:
        logging.error(f"Error writing to file {output_file}: {e}")


def analyze_log_lines(lines):
    """
    Analyze log lines to find the maximum length of name and level fields.

    Args:
        lines (list): List of log lines.

    Returns:
        tuple: Maximum lengths of name and level fields.
    """
    max_name_length = 0
    max_level_length = 0
    for line in lines:
        parts = re.split(r" - ", line)
        if len(parts) >= 4:
            max_name_length = max(max_name_length, len(parts[1]))
            max_level_length = max(max_level_length, len(parts[2]))
    return max_name_length, max_level_length


def align_logs(file_path="app.log", delete_original=False):
    """
    Aligns the logs in the log file and writes them to a new file with the date appended to the file name.
    Then it deletes the original log file.

    Args:
        file_path (str, optional): The path of the log file. Defaults to "app.log".
        delete_original (bool, optional): Whether to delete the original log file. Defaults to False.
    """
    lines = read_logs(file_path)
    max_name_length, max_level_length = analyze_log_lines(lines)

    output_file = f"stripalerts_{datetime.now().strftime('%Y%m%d')}.log"
    write_aligned_logs(lines, max_name_length, max_level_length, output_file)

    if delete_original:
        delete_file(file_path)


def delete_file(file_path):
    """
    Deletes the specified file.

    Args:
        file_path (str): Path of the file to delete.
    """
    try:
        os.remove(file_path)
    except OSError as e:
        logging.error(f"Error deleting file {file_path}: {e}")


if __name__ == "__main__":
    align_logs("app.log")
