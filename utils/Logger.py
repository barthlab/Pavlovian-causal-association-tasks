import csv
from typing import List


class CSVFile:
    """CSV file writer for data logging.

    Provides methods to write data to CSV files with headers, supporting both
    list-based and dictionary-based data formats.
    """

    def __init__(self, file_dir: str, headers: List[str]):
        """Initialize CSV file with headers.

        Args:
            file_dir: Path to the CSV file to create/write to.
            headers: List of column headers for the CSV file.
        """
        self.file_dir = file_dir
        self.headers = headers
        with open(file_dir, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def addrow(self, data: List):
        """Add a single row of data to the CSV file.

        Args:
            data: List of values to write as a row.
        """
        with open(self.file_dir, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data)

    def addrows(self, data_list: List[List]):
        """Add multiple rows of data to the CSV file.

        Args:
            data_list: List of lists, where each inner list represents a row.
        """
        with open(self.file_dir, 'a', newline='') as f:
            writer = csv.writer(f)
            for tmp_data in data_list:
                writer.writerow(tmp_data)

    def write(self, **kwargs):
        """Write a single row using keyword arguments.

        Args:
            **kwargs: Key-value pairs where keys match the CSV headers.
        """
        with open(self.file_dir, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writerow(kwargs)

    def write_multiple(self, dict_list: List[dict]):
        """Write multiple rows using a list of dictionaries.

        Args:
            dict_list: List of dictionaries where keys match the CSV headers.
        """
        with open(self.file_dir, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            for tmp_dict in dict_list:
                writer.writerow(tmp_dict)
