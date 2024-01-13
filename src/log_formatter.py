"""
This module contains the LogAligner class for aligning log lines in a log file.
"""

import asyncio
import logging
import os
import re
from datetime import datetime
from pathlib import Path

import aiofiles


class LogAligner:
    """
    Aligns log lines in a log file.

    Attributes:
        file_path (Path): Path to the log file.
        delete_original (bool): Whether to delete the original file after alignment.
    """

    LOG_LINE_PATTERN = re.compile(r" - ")

    def __init__(self, file_path="app.log", delete_original=False):
        self.file_path = Path(file_path)
        self.delete_original = delete_original
        self.logger = logging.getLogger(self.__class__.__name__)

    async def align_log_entries(self):
        """
        Aligns the log lines in the file asynchronously.
        """
        lines = await self._read_logs()
        if not lines:
            return

        max_name_length, max_level_length = self._analyze_log_lines(lines)
        output_file = Path(f"stripalerts_{datetime.now().strftime('%Y%m%d')}.log")
        await self._write_aligned_logs(lines, max_name_length, max_level_length, output_file)

        if self.delete_original:
            self._delete_file(self.file_path)

    async def _read_logs(self):
        self.logger.debug(f"Reading logs from '{self.file_path}' and aligning them.")
        try:
            async with aiofiles.open(self.file_path, mode="r", encoding="utf-8") as file:
                return await file.readlines()
        except IOError as e:
            raise IOError(f"Error reading file {self.file_path}: {e}") from e

    def _analyze_log_lines(self, lines):
        max_name_length, max_level_length = 0, 0
        for line in lines:
            parts = self.LOG_LINE_PATTERN.split(line)
            if len(parts) >= 4:
                max_name_length, max_level_length = (
                    max(max_name_length, len(parts[1])),
                    max(max_level_length, len(parts[2])),
                )
        return max_name_length, max_level_length

    async def _write_aligned_logs(self, lines, max_name_length, max_level_length, output_file):
        try:
            async with aiofiles.open(output_file, mode="w", encoding="utf-8") as file:
                for line in lines:
                    parts = self.LOG_LINE_PATTERN.split(line, maxsplit=3)
                    if len(parts) >= 4:
                        aligned_line = f"{parts[0]} - {parts[1]:<{max_name_length}} - {parts[2]:<{max_level_length}} - {parts[3]}"
                        await file.write(aligned_line)
        except IOError as e:
            raise IOError(f"Error writing to file {output_file}: {e}") from e

    def _delete_file(self, file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            raise OSError(f"Error deleting file {file_path}: {e}") from e


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(LogAligner("app.log").align_log_entries())
