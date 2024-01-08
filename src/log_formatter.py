"""
This module contains the LogFormatter class which is used to align log lines in a log file.
"""

import asyncio
import logging
import os
import re
from datetime import datetime

import aiofiles

# Setting up basic logging
logging.basicConfig(level=logging.INFO)


class LogFormatter:
    """
    Class to align log lines in a log file.

    Attributes:
        file_path (str): The path to the log file.
        delete_original (bool): Whether to delete the original file after alignment.
        logger (logging.Logger): Logger instance.
    """

    def __init__(self, file_path="app.log", delete_original=False):
        self.file_path = file_path
        self.delete_original = delete_original
        self.logger = logging.getLogger(self.__class__.__name__)

    async def read_logs(self):
        """
        Reads the log lines from the given file asynchronously.

        Returns:
            list: A list of log lines.
        """
        self.logger.debug(f"Reading logs from '{self.file_path}' and aligning them.")
        try:
            async with aiofiles.open(self.file_path, "r", encoding="utf-8") as file:
                return await file.readlines()
        except IOError as e:
            self.logger.error(f"Error reading file {self.file_path}: {e}")
            return []

    async def analyze_log_lines(self, lines):
        """
        Analyzes the log lines and returns the maximum length of the name and level parts.

        Args:
            lines (list): A list of log lines.

        Returns:
            tuple: A tuple containing the maximum length of the name and level parts.
        """
        max_name_length = 0
        max_level_length = 0
        for line in lines:
            parts = re.split(r" - ", line)
            if len(parts) >= 4:
                max_name_length = max(max_name_length, len(parts[1]))
                max_level_length = max(max_level_length, len(parts[2]))
        return max_name_length, max_level_length

    async def align_logs(self):
        """
        Aligns the log lines in the given file asynchronously.
        """
        lines = await self.read_logs()
        if not lines:
            return  # Don't proceed if there are no log lines.

        max_name_length, max_level_length = await self.analyze_log_lines(lines)

        output_file = f"stripalerts_{datetime.now().strftime('%Y%m%d')}.log"
        await self.write_aligned_logs(
            lines, max_name_length, max_level_length, output_file
        )

        if self.delete_original:
            self.delete_file(self.file_path)

    async def write_aligned_logs(
        self, lines, max_name_length, max_level_length, output_file
    ):
        """
        Writes the aligned log lines to a new file asynchronously.

        Args:
            lines (list): A list of log lines.
            max_name_length (int): The maximum length of the name part.
            max_level_length (int): The maximum length of the level part.
            output_file (str): The path to the output file.
        """
        try:
            async with aiofiles.open(output_file, "w", encoding="utf-8") as file:
                for line in lines:
                    parts = re.split(r" - ", line, maxsplit=3)
                    if len(parts) >= 4:
                        aligned_line = f"{parts[0]} - {parts[1]:<{max_name_length}} - {parts[2]:<{max_level_length}} - {parts[3]}"
                        await file.write(aligned_line)
        except IOError as e:
            raise IOError(f"Error writing to file {output_file}: {e}")

    def delete_file(self, file_path):
        """
        Deletes the given file.

        Args:
            file_path (str): The path to the file to delete.
        """
        try:
            os.remove(file_path)
        except OSError as e:
            raise OSError(f"Error deleting file {file_path}: {e}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(LogFormatter("app.log").align_logs())
    loop.close()
