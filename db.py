import json
import os

class DB:
    """
    Manages loading and saving data to a JSON file.
    """
    def __init__(self, file_path):
        """
        Initializes the DB manager with the path to the JSON file.

        Args:
            file_path (str): The path to the JSON file.
        """
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """
        Ensures that the JSON file exists. If not, it is created.
        """
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f) # Creates an empty JSON list

    def load_data(self):
        """
        Loads data from the JSON file.

        Returns:
            list: A list of the loaded data (habit dictionaries).
        """
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: The file '{self.file_path}' is empty or corrupted. Starting with empty data.")
            return []
        except FileNotFoundError:
            self._ensure_file_exists() # Should not happen, but for safety
            return []

    def save_data(self, data):
        """
        Saves data to JSON file.

        Args:
            data (list): The list of data (habit dictionaries) to save.
        """
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=4)
