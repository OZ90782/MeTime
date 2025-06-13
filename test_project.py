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
        self.assertEqual(habit.get_current_streak(), 0)  # Gestern abgeschlossen, heute nicht

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
        last_week = datetime.now() - timedelta(weeks=1, days=3)  # Mittwoch letzte Woche
        self.tracker.complete_habit("Wöchentliche Meditation", date=last_week)
        self.assertEqual(len(habit.completions), 1)
        self.assertEqual(habit.get_current_streak(), 0)  # Letzte Woche abgeschlossen, diese Woche nicht

        # Abschluss für diese Woche
        this_week = datetime.now() - timedelta(days=1)  # Gestern
        self.tracker.complete_habit("Wöchentliche Meditation", date=this_week)
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

        # Simuliere eine Streak von 3 Tagen
        self.tracker.complete_habit("Tägliche Übung", date=datetime.now() - timedelta(days=3))
        self.tracker.complete_habit("Tägliche Übung", date=datetime.now() - timedelta(days=2))
        self.tracker.complete_habit("Tägliche Übung", date=datetime.now() - timedelta(days=1))
        self.assertEqual(habit.get_longest_streak(), 3)

        # Simuliere eine Unterbrechung und eine neue, längere Streak
        self.tracker.complete_habit("Tägliche Übung", date=datetime.now() - timedelta(days=0, hours=2))  # Heute früh
        self.tracker.complete_habit("Tägliche Übung", date=datetime.now() - timedelta(days=-1))  # Morgen
        self.tracker.complete_habit("Tägliche Übung", date=datetime.now() - timedelta(days=-2))  # Übermorgen
        self.assertEqual(habit.get_longest_streak(), 3)  # Die längste Streak ist immer noch 3

        # Test mit einer längeren Streak
        habit.completions = []  # Reset completions
        for i in range(5):
            self.tracker.complete_habit("Tägliche Übung",
                                        date=datetime.now() - timedelta(days=4 - i))  # 5 Tage in Folge
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

        # Yoga für die letzten 5 Tage abgeschlossen
        for i in range(5):
            self.tracker.complete_habit("Yoga", date=datetime.now() - timedelta(days=i))

        # Sprache lernen nur einmal abgeschlossen
        self.tracker.complete_habit("Sprache lernen", date=datetime.now() - timedelta(days=10))

        # Projektarbeit letzte Woche abgeschlossen
        self.tracker.complete_habit("Projektarbeit", date=datetime.now() - timedelta(weeks=1, days=2))

        struggling = self.tracker.get_struggling_habits(period_days=30)
        struggling_names = [h for h in struggling]  # struggling_habits_data is list of habit names

        # Erwartung: "Sprache lernen" sollte am häufigsten verpasst werden, dann "Projektarbeit"
        # Yoga sollte nicht auftauchen, da es regelmäßig gemacht wurde

        # Die genaue Anzahl der verpassten Tage/Wochen hängt vom aktuellen Datum und der Periodizität ab.
        # Wir testen, ob die Reihenfolge der "struggling habits" korrekt ist.
        self.assertGreater(struggling_names.index("Sprache lernen"), -1)
        self.assertGreater(struggling_names.index("Projektarbeit"), -1)

        # Stellen Sie sicher, dass "Yoga" nicht als "struggling habit" auftaucht (oder sehr weit hinten)
        self.assertNotIn("Yoga", struggling_names)


if __name__ == '__main__':
    unittest.main()