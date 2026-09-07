class DataProcessor:
    """
    A class to process a list of dictionaries with methods to filter, group, and summarize the data.
    """

    def __init__(self, data: list[dict]):
        """
        Initialize the DataProcessor with a list of dictionaries.

        :param data: List of dictionaries to process.
        """
        self.data = data

    def filter_by(self, key: str, value: any) -> list[dict]:
        """
        Filter the data by a specific key-value pair.

        :param key: The key to filter by.
        :param value: The value to match.
        :return: A list of dictionaries that match the key-value pair.
        """
        return [item for item in self.data if item.get(key) == value]

    def group_by(self, key: str) -> dict:
        """
        Group the data by a specific key.

        :param key: The key to group by.
        :return: A dictionary where each key is a unique value from the specified key in the data,
                 and each value is a list of dictionaries that have that key value.
        """
        grouped_data = {}
        for item in self.data:
            group_key = item.get(key)
            if group_key not in grouped_data:
                grouped_data[group_key] = []
            grouped_data[group_key].append(item)
        return grouped_data

    def summarize(self) -> dict:
        """
        Summarize the data by providing the count of items, keys present, and a sample row.

        :return: A dictionary containing the count of items, keys present, and a sample row.
        """
        if not self.data:
            return {'count': 0, 'keys': [], 'sample_row': None}

        count = len(self.data)
        keys = list(self.data[0].keys())
        sample_row = self.data[0]

        return {
            'count': count,
            'keys': keys,
            'sample_row': sample_row
        }
