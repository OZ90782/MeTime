import json
import os

class DB:
    """
    Verwaltet das Laden und Speichern von Daten in einer JSON-Datei.
    """
    def __init__(self, file_path):
        """
        Initialisiert den DB-Manager mit dem Pfad zur JSON-Datei.

        Args:
            file_path (str): Der Pfad zur JSON-Datei.
        """
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """
        Stellt sicher, dass die JSON-Datei existiert. Wenn nicht, wird sie erstellt.
        """
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f) # Erstellt eine leere JSON-Liste

    def load_data(self):
        """
        Lädt Daten aus der JSON-Datei.

        Returns:
            list: Eine Liste der geladenen Daten (Habit-Wörterbücher).
        """
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warnung: Die Datei '{self.file_path}' ist leer oder beschädigt. Starte mit leeren Daten.")
            return []
        except FileNotFoundError:
            self._ensure_file_exists() # Sollte nicht passieren, aber zur Sicherheit
            return []

    def save_data(self, data):
        """
        Speichert Daten in der JSON-Datei.

        Args:
            data (list): Die zu speichernde Liste von Daten (Habit-Wörterbüchern).
        """
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=4)