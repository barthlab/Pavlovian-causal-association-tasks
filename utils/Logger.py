import csv
from typing import List


class CSVFile:
    def __init__(self, file_dir, headers):
        self.file_dir = file_dir
        self.headers = headers
        with open(file_dir, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def addrow(self, data):
        with open(self.file_dir, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data)

    def addrows(self, data_list: list):
        with open(self.file_dir, 'a', newline='') as f:
            writer = csv.writer(f)
            for tmp_data in data_list:
                writer.writerow(tmp_data)

    def write(self, **kwargs):
        with open(self.file_dir, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writerow(kwargs)

    def write_multiple(self, dict_list: List[dict]):
        with open(self.file_dir, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            for tmp_dict in dict_list:
                writer.writerow(tmp_dict)
