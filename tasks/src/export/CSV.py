from export import Writer
import csv


class CSV(Writer):
    def __init__(self):
        self.__headers = None
        self.__rows = []

    @property
    def headers(self):
        return self.__headers

    @headers.setter
    def headers(self, headers):
        self.__headers = headers

    def add_row(self, data):
        self.__rows.append(data)

    @property
    def rows(self):
        return self.__rows

    def save(self, filename):
        with open(filename, "wb") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(self.headers)
            for row in self.rows:
                writer.writerow(row)
