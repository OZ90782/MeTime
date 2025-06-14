import json
from datetime import datetime, timedelta
import analytics

class Habit:
    """
    Repräsentiert einen einzelnen Habit mit seinen Eigenschaften und Methoden.
    """
    def __init__(self, name, description, periodicity, creation_date=None, last_completed=None, completions=None):
        """
        Initialisiert einen Habit.

        Args:
            name (str): Der Name des Habits.
            description (str): Eine Beschreibung des Habits.
            periodicity (str): Die Periodizität des Habits ('daily' oder 'weekly').
            creation_date (datetime, optional): Das Erstellungsdatum des Habits.
                                                 Standardmäßig jetzt.
            last_completed (datetime, optional): Das Datum des letzten Abschlusses.
                                                  Standardmäßig None.
            completions (list[datetime], optional): Eine Liste von Zeitstempeln,
                                                     wann der Habit abgeschlossen wurde.
                                                     Standardmäßig leer.
        """
        self.name = name
        self.description = description
        self.periodicity = periodicity
        self.creation_date = creation_date if creation_date else datetime.now()
        self.last_completed = last_completed
        self.completions = sorted(completions) if completions else []

    def mark_completed(self, date=None):
        """
        Markiert den Habit als abgeschlossen für das angegebene Datum.
        Wenn kein Datum angegeben ist, wird der aktuelle Zeitpunkt verwendet.

        Args:
            date (datetime, optional): Das Datum, an dem der Habit abgeschlossen wurde.
                                       Standardmäßig None (aktueller Zeitpunkt).
        """
        completion_date = date if date else datetime.now()
        # Verhindere doppelte Einträge für den gleichen Tag/Woche
        if self.periodicity == "daily":
            if self.completions and self.completions[-1].date() == completion_date.date():
                raise ValueError("Habit wurde heute bereits abgeschlossen.")
        elif self.periodicity == "weekly":
            # Prüfen, ob der Habit in der aktuellen Kalenderwoche bereits abgeschlossen wurde
            # Kalenderwoche beginnt mit Montag (isocalendar().week)
            if self.completions and self.completions[-1].isocalendar().week == completion_date.isocalendar().week \
                                and self.completions[-1].year == completion_date.year:
                raise ValueError("Habit wurde diese Woche bereits abgeschlossen.")
        self.completions.append(completion_date)
        self.completions.sort() # Sicherstellen, dass die Liste immer sortiert ist
        self.last_completed = completion_date

    def get_current_streak(self):
        """
        Berechnet die aktuelle Streak (Anzahl der aufeinanderfolgenden Abschlüsse).

        Returns:
            int: Die aktuelle Streak.
        """
        if not self.completions:
            return 0

        # Berechnet die aktuelle Streak basierend auf der Periodizität
        return analytics.get_current_streak(self, datetime.now())

    def get_longest_streak(self):
        """
        Berechnet die längste Streak (Anzahl der aufeinanderfolgenden Abschlüsse)
        in der Geschichte des Habits.

        Returns:
            int: Die längste Streak.
        """
        if not self.completions:
            return 0
        return analytics.get_longest_run_streak([self])[0][1] # Pass habit as a list to analytics function

    def was_broken(self, period_start, period_end):
        """
        Überprüft, ob der Habit in einem bestimmten Zeitraum (definiert durch period_start und period_end)
        gebrochen wurde.

        Args:
            period_start (datetime): Der Start des Zeitraums.
            period_end (datetime): Das Ende des Zeitraums.

        Returns:
            bool: True, wenn der Habit gebrochen wurde, False sonst.
        """
        # Holen Sie sich alle Abschlussdaten innerhalb des angegebenen Zeitraums
        completions_in_period = [
            c for c in self.completions if period_start <= c <= period_end
        ]

        if self.periodicity == "daily":
            # Prüfe jeden Tag im Zeitraum
            current_date = period_start
            while current_date <= period_end:
                if not any(c.date() == current_date.date() for c in completions_in_period):
                    # Wenn an einem Tag im Zeitraum keine Abschluss gefunden wurde
                    return True
                current_date += timedelta(days=1)
            return False
        elif self.periodicity == "weekly":
            # Prüfe jede Woche im Zeitraum
            # Finde die erste Woche
            first_week_start = period_start - timedelta(days=period_start.weekday()) # Montag der Woche
            current_week_start = first_week_start
            while current_week_start <= period_end:
                # Finde das Ende der aktuellen Woche
                current_week_end = current_week_start + timedelta(days=6)
                # Prüfe, ob es eine Abschluss in dieser Woche gab
                if not any(c for c in completions_in_period if current_week_start.date() <= c.date() <= current_week_end.date()):
                    return True # Habit in dieser Woche gebrochen
                current_week_start += timedelta(weeks=1)
            return False
        return True # Ungültige Periodizität

    def to_dict(self):
        """
        Konvertiert das Habit-Objekt in ein Wörterbuch für die JSON-Serialisierung.
        """
        return {
            "name": self.name,
            "description": self.description,
            "periodicity": self.periodicity,
            "creation_date": self.creation_date.isoformat(),
            "last_completed": self.last_completed.isoformat() if self.last_completed else None,
            "completions": [c.isoformat() for c in self.completions]
        }

    @classmethod
    def from_dict(cls, data):
        """
        Erstellt ein Habit-Objekt aus einem Wörterbuch.
        """
        creation_date = datetime.fromisoformat(data["creation_date"])
        last_completed = datetime.fromisoformat(data["last_completed"]) if data["last_completed"] else None
        completions = [datetime.fromisoformat(c) for c in data["completions"]]
        return cls(
            data["name"],
            data["description"],
            data["periodicity"],
            creation_date,
            last_completed,
            completions
        )

class HabitTracker:
    """
    Verwaltet eine Sammlung von Habit-Objekten und deren Persistenz.
    """
    def __init__(self, db_manager):
        """
        Initialisiert den HabitTracker.

        Args:
            db_manager (DB): Eine Instanz des DB-Managers zum Speichern/Laden.
        """
        self.habits = []
        self.db_manager = db_manager

    def add_habit(self, name, description, periodicity):
        """
        Fügt einen neuen Habit zum Tracker hinzu.

        Args:
            name (str): Der Name des Habits.
            description (str): Die Beschreibung des Habits.
            periodicity (str): Die Periodizität des Habits ('daily' oder 'weekly').
        """
        if self.get_habit_by_name(name):
            raise ValueError(f"Habit mit dem Namen '{name}' existiert bereits.")
        habit = Habit(name, description, periodicity)
        self.habits.append(habit)
        self.save_to_file()

    def delete_habit(self, name):
        """
        Löscht einen Habit anhand seines Namens.

        Args:
            name (str): Der Name des zu löschenden Habits.

        Returns:
            bool: True, wenn der Habit gelöscht wurde, False sonst.
        """
        initial_len = len(self.habits)
        self.habits = [h for h in self.habits if h.name != name]
        if len(self.habits) < initial_len:
            self.save_to_file()
            return True
        return False

    def complete_habit(self, name, date=None):
        """
        Markiert einen Habit als abgeschlossen.

        Args:
            name (str): Der Name des Habits.
            date (datetime, optional): Das Datum des Abschlusses. Standardmäßig jetzt.

        Raises:
            ValueError: Wenn der Habit nicht gefunden wird oder bereits abgeschlossen ist.
        """
        habit = self.get_habit_by_name(name)
        if habit:
            habit.mark_completed(date)
            self.save_to_file()
        else:
            raise ValueError(f"Habit '{name}' nicht gefunden.")

    def get_habit_by_name(self, name):
        """
        Sucht einen Habit anhand seines Namens.

        Args:
            name (str): Der Name des zu suchenden Habits.

        Returns:
            Habit or None: Das Habit-Objekt, wenn gefunden, sonst None.
        """
        for habit in self.habits:
            if habit.name == name:
                return habit
        return None

    def get_all_habits(self):
        """
        Gibt eine Liste aller Habits zurück.
        """
        return self.habits

    def get_habits_by_period(self, periodicity):
        """
        Gibt eine Liste von Habits mit einer bestimmten Periodizität zurück.

        Args:
            periodicity (str): Die gewünschte Periodizität ('daily' oder 'weekly').

        Returns:
            list[Habit]: Eine Liste von Habit-Objekten.
        """
        return [h for h in self.habits if h.periodicity == periodicity]

    def get_longest_streak_for_habit(self, habit_name):
        """
        Gibt die längste Streak für einen bestimmten Habit zurück.

        Args:
            habit_name (str): Der Name des Habits.

        Returns:
            int: Die längste Streak.
        """
        habit = self.get_habit_by_name(habit_name)
        if habit:
            return habit.get_longest_streak()
        return 0 # Oder Raise Error, je nach gewünschtem Verhalten

    def get_struggling_habits(self, period_days=30):
        """
        Gibt eine Liste von Habits zurück, die im letzten Monat am häufigsten verpasst wurden.
        Diese Funktion nutzt die Analytics-Funktion.

        Args:
            period_days (int): Anzahl der Tage, für die die "struggling habits" ermittelt werden sollen.

        Returns:
            list[str]: Eine Liste der Namen der "struggling habits".
        """
        # Korrektur: analytics.get_struggling_habits gibt jetzt bereits eine Liste von Namen zurück
        return analytics.get_struggling_habits(self.habits, period_days)


    def save_to_file(self):
        """
        Speichert alle Habits in der konfigurierten JSON-Datei.
        """
        data = [habit.to_dict() for habit in self.habits]
        self.db_manager.save_data(data)

    def load_from_file(self):
        """
        Lädt Habits aus der konfigurierten JSON-Datei.
        """
        data = self.db_manager.load_data()
        self.habits = [Habit.from_dict(d) for d in data]