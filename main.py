import os
from habit_tracker import HabitTracker
from db import DB
from datetime import datetime

class CLI:
    """
    Klasse für die Kommandozeilen-Benutzeroberfläche (CLI) des Habit Trackers.
    Verwaltet die Interaktion mit dem Benutzer und ruft die Funktionen des HabitTrackers auf.
    """
    def __init__(self, habit_tracker):
        """
        Initialisiert die CLI mit einer Instanz des HabitTrackers.
        Args:
            habit_tracker (HabitTracker): Die Instanz des HabitTrackers.
        """
        self.habit_tracker = habit_tracker

    def run(self):
        """
        Startet die Hauptschleife der CLI und zeigt das Menü an.
        """
        print("Willkommen beim Habit Tracker – „MeTime“")
        while True:
            self._display_menu()
            choice = input("Wählen Sie eine Option: ")
            if choice == '1':
                self.prompt_create_habit()
            elif choice == '2':
                self.prompt_delete_habit()
            elif choice == '3':
                self.prompt_mark_completed()
            elif choice == '4':
                self.prompt_view_current_habits()
            elif choice == '5':
                self.prompt_analysis()
            elif choice == '6':
                print("Auf Wiedersehen!")
                break
            else:
                print("Ungültige Eingabe. Bitte versuchen Sie es erneut.")

    def _display_menu(self):
        """
        Zeigt das Hauptmenü der CLI an.
        """
        print("\n--- Menü ---")
        print("1. Neuen Habit erstellen")
        print("2. Bestehenden Habit löschen")
        print("3. Habit als abgeschlossen markieren")
        print("4. Aktuelle Habits anzeigen")
        print("5. Habit-Performance analysieren")
        print("6. Beenden")

    def prompt_create_habit(self):
        """
        Fordert den Benutzer zur Eingabe von Informationen für einen neuen Habit auf
        und erstellt diesen.
        """
        name = input("Name des Habits: ").strip()
        if not name:
            print("Habit-Name darf nicht leer sein.")
            return
        description = input("Beschreibung des Habits: ").strip()
        periodicity = input("Periodizität (daily/weekly): ").strip().lower()
        if periodicity not in ["daily", "weekly"]:
            print("Ungültige Periodizität. Bitte 'daily' oder 'weekly' eingeben.")
            return
        self.habit_tracker.add_habit(name, description, periodicity)
        print(f"Habit '{name}' erfolgreich erstellt.")

    def prompt_delete_habit(self):
        """
        Fordert den Benutzer zur Eingabe des Namens eines zu löschenden Habits auf
        und löscht diesen.
        """
        name = input("Name des zu löschenden Habits: ").strip()
        if not name:
            print("Habit-Name darf nicht leer sein.")
            return
        if self.habit_tracker.delete_habit(name):
            print(f"Habit '{name}' erfolgreich gelöscht.")
        else:
            print(f"Habit '{name}' nicht gefunden.")

    def prompt_mark_completed(self):
        """
        Fordert den Benutzer zur Eingabe des Namens eines abzuschließenden Habits auf
        und markiert diesen als abgeschlossen.
        """
        name = input("Name des als abgeschlossen zu markierenden Habits: ").strip()
        if not name:
            print("Habit-Name darf nicht leer sein.")
            return
        try:
            self.habit_tracker.complete_habit(name)
            print(f"Habit '{name}' als abgeschlossen markiert.")
        except ValueError as e:
            print(f"Fehler: {e}")

    def prompt_view_current_habits(self):
        """
        Zeigt alle aktuellen Habits des Benutzers an.
        """
        habits = self.habit_tracker.get_all_habits()
        if not habits:
            print("Keine Habits vorhanden.")
            return
        print("\n--- Aktuelle Habits ---")
        for habit in habits:
            print(f"Name: {habit.name}")
            print(f"  Beschreibung: {habit.description}")
            print(f"  Periodizität: {habit.periodicity}")
            print(f"  Aktuelle Streak: {habit.get_current_streak()}")
            print(f"  Längste Streak: {habit.get_longest_streak()}")
            if habit.completions:
                print(f"  Letzte Abschlusszeit: {habit.completions[-1].strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("  Noch nicht abgeschlossen.")
            print("-" * 20)

    def prompt_analysis(self):
        """
        Bietet verschiedene Analyseoptionen für die Habit-Performance an.
        """
        print("\n--- Habit-Analyse ---")
        print("1. Habits nach Periodizität anzeigen")
        print("2. Längste Streak eines Habits anzeigen")
        print("3. Habits anzeigen, die im letzten Monat am häufigsten verpasst wurden")
        analysis_choice = input("Wählen Sie eine Analyse-Option: ")

        if analysis_choice == '1':
            period = input("Periodizität (daily/weekly): ").strip().lower()
            if period not in ["daily", "weekly"]:
                print("Ungültige Periodizität. Bitte 'daily' oder 'weekly' eingeben.")
                return
            habits_by_period = self.habit_tracker.get_habits_by_period(period)
            if habits_by_period:
                print(f"\n--- Habits mit Periodizität '{period}' ---")
                for habit in habits_by_period:
                    print(f"- {habit.name} (Streak: {habit.get_current_streak()})")
            else:
                print(f"Keine Habits mit Periodizität '{period}' gefunden.")
        elif analysis_choice == '2':
            name = input("Name des Habits für die längste Streak: ").strip()
            if not name:
                print("Habit-Name darf nicht leer sein.")
                return
            habit = self.habit_tracker.get_habit_by_name(name)
            if habit:
                longest_streak = habit.get_longest_streak()
                print(f"Die längste Streak für '{name}' ist: {longest_streak} Tage.")
            else:
                print(f"Habit '{name}' nicht gefunden.")
        elif analysis_choice == '3':
            struggling_habits = self.habit_tracker.get_struggling_habits()
            if struggling_habits:
                print("\n--- Habits, die im letzten Monat am häufigsten verpasst wurden ---")
                for habit_name in struggling_habits:
                    print(f"- {habit_name}")
            else:
                print("Keine Habits wurden im letzten Monat verpasst oder es sind keine Daten vorhanden.")
        else:
            print("Ungültige Auswahl für Analyse-Option.")


if __name__ == "__main__":
    # Pfad zur JSON-Datei, in der die Habits gespeichert werden
    DATA_FILE = "habits.json"
    db_manager = DB(DATA_FILE)
    habit_tracker_instance = HabitTracker(db_manager)

    # Lade vorhandene Daten beim Start
    habit_tracker_instance.load_from_file()

    cli = CLI(habit_tracker_instance)
    cli.run()


