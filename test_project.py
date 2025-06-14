import unittest
import os
from datetime import datetime, timedelta
from habit_tracker import Habit, HabitTracker
from db import DB
import analytics


class TestHabitTracker(unittest.TestCase):
    """
    Testklasse für die Funktionen des Habit Trackers.
    """

    def setUp(self):
        """
        Setzt die Testumgebung für jeden Test auf.
        Erstellt eine temporäre Datenbankdatei.
        """
        self.test_db_file = "test_habits.json"
        # Stelle sicher, dass die Testdatei vor jedem Test leer ist
        if os.path.exists(self.test_db_file):
            os.remove(self.test_db_file)
        self.db_manager = DB(self.test_db_file)
        self.tracker = HabitTracker(self.db_manager)

    def tearDown(self):
        """
        Räumt die Testumgebung nach jedem Test auf.
        Löscht die temporäre Datenbankdatei.
        """
        if os.path.exists(self.test_db_file):
            os.remove(self.test_db_file)

    def test_add_habit(self):
        """
        Testet das Hinzufügen eines Habits.
        """
        self.tracker.add_habit("Lesen", "Jeden Tag 30 Minuten lesen", "daily")
        self.assertEqual(len(self.tracker.habits), 1)
        self.assertEqual(self.tracker.habits[0].name, "Lesen")

        with self.assertRaises(ValueError):
            self.tracker.add_habit("Lesen", "Nochmal lesen", "daily")  # Darf nicht doppelt sein

    def test_delete_habit(self):
        """
        Testet das Löschen eines Habits.
        """
        self.tracker.add_habit("Lesen", "Jeden Tag 30 Minuten lesen", "daily")
        self.tracker.add_habit("Joggen", "Dreimal pro Woche joggen", "weekly")
        self.assertTrue(self.tracker.delete_habit("Lesen"))
        self.assertEqual(len(self.tracker.habits), 1)
        self.assertEqual(self.tracker.habits[0].name, "Joggen")
        self.assertFalse(self.tracker.delete_habit("Nicht Existiert"))

    def test_complete_habit_daily(self):
        """
        Testet das Abschließen eines täglichen Habits.
        """
        self.tracker.add_habit("Lesen", "Jeden Tag 30 Minuten lesen", "daily")
        habit = self.tracker.get_habit_by_name("Lesen")

        # Abschluss für gestern
        yesterday = datetime.now() - timedelta(days=1)
        self.tracker.complete_habit("Lesen", date=yesterday)
        self.assertEqual(len(habit.completions), 1)
        self.assertEqual(habit.completions[0].date(), yesterday.date())
        # Aktuelle Streak ist 0, da heute nicht abgeschlossen wurde (wenn gestern letzter Abschluss war)
        self.assertEqual(habit.get_current_streak(), 0)

        # Abschluss für heute
        today = datetime.now()
        self.tracker.complete_habit("Lesen", date=today)
        self.assertEqual(len(habit.completions), 2)
        self.assertEqual(habit.get_current_streak(), 2)  # Gestern und heute abgeschlossen

        # Versuch, heute nochmal abzuschließen
        with self.assertRaises(ValueError):
            self.tracker.complete_habit("Lesen", date=today)
        self.assertEqual(len(habit.completions), 2)  # Anzahl der Abschlüsse sollte gleich bleiben

    def test_complete_habit_weekly(self):
        """
        Testet das Abschließen eines wöchentlichen Habits.
        """
        self.tracker.add_habit("Wöchentliche Meditation", "Einmal pro Woche meditieren", "weekly")
        habit = self.tracker.get_habit_by_name("Wöchentliche Meditation")

        # Abschluss für letzte Woche
        last_week_completion_date = datetime.now() - timedelta(weeks=1, days=3)  # Mittwoch letzte Woche
        self.tracker.complete_habit("Wöchentliche Meditation", date=last_week_completion_date)
        self.assertEqual(len(habit.completions), 1)
        # Erwartet 0, da der letzte Abschluss in der VORHERIGEN Woche war und die aktuelle Woche nicht abgeschlossen ist.
        self.assertEqual(habit.get_current_streak(), 0)

        # Abschluss für diese Woche
        this_week_completion_date = datetime.now() - timedelta(days=1)  # Gestern
        self.tracker.complete_habit("Wöchentliche Meditation", date=this_week_completion_date)
        self.assertEqual(len(habit.completions), 2)
        self.assertEqual(habit.get_current_streak(), 2)  # Letzte und diese Woche abgeschlossen

        # Versuch, diese Woche nochmal abzuschließen
        with self.assertRaises(ValueError):
            self.tracker.complete_habit("Wöchentliche Meditation", date=datetime.now())
        self.assertEqual(len(habit.completions), 2)  # Anzahl der Abschlüsse sollte gleich bleiben

    def test_get_all_habits(self):
        """
        Testet das Abrufen aller Habits.
        """
        self.tracker.add_habit("Lesen", "...", "daily")
        self.tracker.add_habit("Joggen", "...", "weekly")
        habits = self.tracker.get_all_habits()
        self.assertEqual(len(habits), 2)
        self.assertIn("Lesen", [h.name for h in habits])
        self.assertIn("Joggen", [h.name for h in habits])

    def test_get_habits_by_period(self):
        """
        Testet das Abrufen von Habits nach Periodizität.
        """
        self.tracker.add_habit("Lesen", "...", "daily")
        self.tracker.add_habit("Joggen", "...", "weekly")
        self.tracker.add_habit("Spazieren", "...", "daily")

        daily_habits = self.tracker.get_habits_by_period("daily")
        self.assertEqual(len(daily_habits), 2)
        self.assertIn("Lesen", [h.name for h in daily_habits])
        self.assertIn("Spazieren", [h.name for h in daily_habits])

        weekly_habits = self.tracker.get_habits_by_period("weekly")
        self.assertEqual(len(weekly_habits), 1)
        self.assertIn("Joggen", [h.name for h in weekly_habits])

    def test_save_and_load_data(self):
        """
        Testet das Speichern und Laden von Daten.
        """
        self.tracker.add_habit("Schreiben", "Täglich schreiben", "daily")
        self.tracker.add_habit("Kochen", "Wöchentlich kochen", "weekly")
        self.tracker.complete_habit("Schreiben", date=datetime.now() - timedelta(days=2))
        self.tracker.complete_habit("Schreiben", date=datetime.now() - timedelta(days=1))
        self.tracker.complete_habit("Schreiben", date=datetime.now())
        self.tracker.complete_habit("Kochen", date=datetime.now() - timedelta(weeks=1))

        # Erstelle einen neuen Tracker und lade die Daten
        new_db_manager = DB(self.test_db_file)
        new_tracker = HabitTracker(new_db_manager)
        new_tracker.load_from_file()

        self.assertEqual(len(new_tracker.habits), 2)
        schreiben_habit = new_tracker.get_habit_by_name("Schreiben")
        self.assertIsNotNone(schreiben_habit)
        self.assertEqual(schreiben_habit.get_current_streak(), 3)
        self.assertEqual(schreiben_habit.periodicity, "daily")
        self.assertEqual(len(schreiben_habit.completions), 3)

        kochen_habit = new_tracker.get_habit_by_name("Kochen")
        self.assertIsNotNone(kochen_habit)
        self.assertEqual(kochen_habit.periodicity, "weekly")
        self.assertEqual(len(kochen_habit.completions), 1)

    def test_longest_streak_daily(self):
        """
        Testet die längste Streak für einen täglichen Habit.
        """
        self.tracker.add_habit("Tägliche Übung", "...", "daily")
        habit = self.tracker.get_habit_by_name("Tägliche Übung")

        # Simuliere eine Streak von 3 Tagen (z.B. vor 3, 2, 1 Tagen)
        for i in range(3):
            self.tracker.complete_habit("Tägliche Übung", date=datetime.now() - timedelta(days=2 - i))
        self.assertEqual(habit.get_longest_streak(), 3)

        # Simuliere eine Unterbrechung und eine neue, kürzere Streak
        # (WICHTIG: Verwende hier keine zukünftigen Daten, um die längste Streak nicht zu verfälschen)
        # Setze die Abschlüsse zurück und füge eine längere Streak hinzu
        habit.completions = []
        for i in range(5):  # Eine Streak von 5 Tagen
            self.tracker.complete_habit("Tägliche Übung", date=datetime.now() - timedelta(days=4 - i))
        self.assertEqual(habit.get_longest_streak(), 5)  # Erwartet 5 für die neue längste Streak

        # Füge eine Lücke und dann eine kürzere, neue Streak hinzu, um zu prüfen, ob die längste erhalten bleibt
        # Beispiel: Eine 2-Tages-Streak nach einer Lücke von 3 Tagen
        gap_start_date = datetime.now() - timedelta(days=8)
        self.tracker.complete_habit("Tägliche Übung", date=gap_start_date)
        self.tracker.complete_habit("Tägliche Übung", date=gap_start_date + timedelta(days=1))

        # Die längste Streak sollte immer noch 5 sein, von der vorherigen längeren Streak
        self.assertEqual(habit.get_longest_streak(), 5)

    def test_longest_streak_weekly(self):
        """
        Testet die längste Streak für einen wöchentlichen Habit.
        """
        self.tracker.add_habit("Wöchentlicher Rückblick", "...", "weekly")
        habit = self.tracker.get_habit_by_name("Wöchentlicher Rückblick")

        # Simuliere eine Streak von 2 Wochen
        today = datetime.now()
        last_week = today - timedelta(weeks=1)
        two_weeks_ago = today - timedelta(weeks=2)

        self.tracker.complete_habit("Wöchentlicher Rückblick", date=two_weeks_ago)
        self.tracker.complete_habit("Wöchentlicher Rückblick", date=last_week)
        self.assertEqual(habit.get_longest_streak(), 2)

        # Simuliere eine längere Streak
        habit.completions = []  # Reset completions
        for i in range(4):
            self.tracker.complete_habit("Wöchentlicher Rückblick", date=today - timedelta(weeks=3 - i, days=2))
        self.assertEqual(habit.get_longest_streak(), 4)

    def test_struggling_habits(self):
        """
        Testet die Funktion zur Ermittlung von "struggling habits".
        """
        self.tracker.add_habit("Yoga", "Täglich", "daily")
        self.tracker.add_habit("Sprache lernen", "Täglich", "daily")
        self.tracker.add_habit("Projektarbeit", "Wöchentlich", "weekly")

        # Yoga für die letzten 30 Tage abgeschlossen (um sicherzustellen, dass es NICHT struggling ist)
        # Die range muss 30 Tage vorwärts gehen, da timedelta(days=i) rückwärts zählt.
        # Start ist (heute - 29 Tage) bis (heute - 0 Tage).
        for i in range(30):
            self.tracker.complete_habit("Yoga", date=datetime.now() - timedelta(days=29 - i))

        # Sprache lernen nur einmal abgeschlossen (sollte struggling sein)
        self.tracker.complete_habit("Sprache lernen", date=datetime.now() - timedelta(days=25))

        # Projektarbeit nur einmal letzte Woche abgeschlossen (sollte struggling sein, da viele Wochen verpasst wurden)
        self.tracker.complete_habit("Projektarbeit", date=datetime.now() - timedelta(weeks=1, days=2))

        struggling = self.tracker.get_struggling_habits(period_days=30)
        # self.tracker.get_struggling_habits() gibt bereits eine Liste von Namen zurück
        struggling_names = struggling

        # Erwartung: "Sprache lernen" und "Projektarbeit" sollten auftauchen
        # "Yoga" sollte NICHT auftauchen, da es regelmäßig gemacht wurde

        self.assertIn("Sprache lernen", struggling_names)
        self.assertIn("Projektarbeit", struggling_names)
        self.assertNotIn("Yoga", struggling_names)

        # Optional: Test with no struggling habits
        self.tracker.habits = []  # Clear existing habits for new test
        self.tracker.add_habit("Super Habit", "Daily", "daily")
        for i in range(30):
            self.tracker.complete_habit("Super Habit", date=datetime.now() - timedelta(days=29 - i))  # 30 Tage am Stück
        no_struggling = self.tracker.get_struggling_habits(period_days=30)
        self.assertEqual(len(no_struggling), 0)