import unittest
import os
from datetime import datetime, timedelta
from habit_tracker import Habit, HabitTracker
from db import DB
import analytics


class TestHabitTracker(unittest.TestCase):
    """
    Test class for the Habit Tracker functions.
    """

    def setUp(self):
        """
        Sets up the test environment for each test.
        Creates a temporary database file.
        """
        self.test_db_file = "test_habits.json"
        # Ensure the test file is empty before each test
        if os.path.exists(self.test_db_file):
            os.remove(self.test_db_file)
        self.db_manager = DB(self.test_db_file)
        self.tracker = HabitTracker(self.db_manager)

    def tearDown(self):
        """
        Cleans up the test environment after each test.
        Deletes the temporary database file.
        """
        if os.path.exists(self.test_db_file):
            os.remove(self.test_db_file)

    def test_add_habit(self):
        """
        Tests adding a habit.
        """
        self.tracker.add_habit("Read", "Read 30 minutes every day", "daily")
        self.assertEqual(len(self.tracker.habits), 1)
        self.assertEqual(self.tracker.habits[0].name, "Read")

        with self.assertRaises(ValueError):
            self.tracker.add_habit("Read", "Read again", "daily")

    def test_delete_habit(self):
        """
        Tests deleting a habit.
        """
        self.tracker.add_habit("Read", "Read 30 minutes every day", "daily")
        self.tracker.add_habit("Jog", "Jog three times a week", "weekly")
        self.assertTrue(self.tracker.delete_habit("Read"))
        self.assertEqual(len(self.tracker.habits), 1)
        self.assertEqual(self.tracker.habits[0].name, "Jog")
        self.assertFalse(self.tracker.delete_habit("Does Not Exist"))

    def test_complete_habit_daily(self):
        """
        Tests completing a daily habit.
        """
        self.tracker.add_habit("Read", "Read 30 minutes every day", "daily")
        habit = self.tracker.get_habit_by_name("Read")

        # Completion for yesterday
        yesterday = datetime.now() - timedelta(days=1)
        self.tracker.complete_habit("Read", date=yesterday)
        self.assertEqual(len(habit.completions), 1)
        self.assertEqual(habit.completions[0].date(), yesterday.date())
        # Current streak is 0 because it was not completed today (if yesterday was the last completion)
        self.assertEqual(habit.get_current_streak(), 0)

        # Completion for today
        today = datetime.now()
        self.tracker.complete_habit("Read", date=today)
        self.assertEqual(len(habit.completions), 2)
        self.assertEqual(habit.get_current_streak(), 2)  # Completed yesterday and today

        # Attempt to complete again today
        with self.assertRaises(ValueError):
            self.tracker.complete_habit("Read", date=today)
        self.assertEqual(len(habit.completions), 2)  # Number of completions should remain the same

    def test_complete_habit_weekly(self):
        """
        Tests completing a weekly habit.
        """
        self.tracker.add_habit("Weekly Meditation", "Meditate once a week", "weekly")
        habit = self.tracker.get_habit_by_name("Weekly Meditation")

        # Completion for last week
        last_week_completion_date = datetime.now() - timedelta(weeks=1, days=3)  # Wednesday last week
        self.tracker.complete_habit("Weekly Meditation", date=last_week_completion_date)
        self.assertEqual(len(habit.completions), 1)
        # Expected 0, because the last completion was in the PREVIOUS week and the current week is not completed.
        self.assertEqual(habit.get_current_streak(), 0)

        # Completion for this week
        this_week_completion_date = datetime.now() - timedelta(days=1)  # Yesterday
        self.tracker.complete_habit("Weekly Meditation", date=this_week_completion_date)
        self.assertEqual(len(habit.completions), 2)
        self.assertEqual(habit.get_current_streak(), 2)  # Completed last week and this week

        # Attempt to complete again this week
        with self.assertRaises(ValueError):
            self.tracker.complete_habit("Weekly Meditation", date=datetime.now())
        self.assertEqual(len(habit.completions), 2)  # Number of completions should remain the same

    def test_get_all_habits(self):
        """
        Tests retrieving all habits.
        """
        self.tracker.add_habit("Read", "...", "daily")
        self.tracker.add_habit("Jog", "...", "weekly")
        habits = self.tracker.get_all_habits()
        self.assertEqual(len(habits), 2)
        self.assertIn("Read", [h.name for h in habits])
        self.assertIn("Jog", [h.name for h in habits])

    def test_get_habits_by_period(self):
        """
        Tests retrieving habits by periodicity.
        """
        self.tracker.add_habit("Read", "...", "daily")
        self.tracker.add_habit("Jog", "...", "weekly")
        self.tracker.add_habit("Walk", "...", "daily")

        daily_habits = self.tracker.get_habits_by_period("daily")
        self.assertEqual(len(daily_habits), 2)
        self.assertIn("Read", [h.name for h in daily_habits])
        self.assertIn("Walk", [h.name for h in daily_habits])

        weekly_habits = self.tracker.get_habits_by_period("weekly")
        self.assertEqual(len(weekly_habits), 1)
        self.assertIn("Jog", [h.name for h in weekly_habits])

    def test_save_and_load_data(self):
        """
        Tests saving and loading data.
        """
        self.tracker.add_habit("Write", "Write daily", "daily")
        self.tracker.add_habit("Cook", "Cook weekly", "weekly")
        self.tracker.complete_habit("Write", date=datetime.now() - timedelta(days=2))
        self.tracker.complete_habit("Write", date=datetime.now() - timedelta(days=1))
        self.tracker.complete_habit("Write", date=datetime.now())
        self.tracker.complete_habit("Cook", date=datetime.now() - timedelta(weeks=1))

        # Create a new tracker and load data
        new_db_manager = DB(self.test_db_file)
        new_tracker = HabitTracker(new_db_manager)
        new_tracker.load_from_file()

        self.assertEqual(len(new_tracker.habits), 2)
        write_habit = new_tracker.get_habit_by_name("Write")
        self.assertIsNotNone(write_habit)
        self.assertEqual(write_habit.get_current_streak(), 3)
        self.assertEqual(write_habit.periodicity, "daily")
        self.assertEqual(len(write_habit.completions), 3)

        cook_habit = new_tracker.get_habit_by_name("Cook")
        self.assertIsNotNone(cook_habit)
        self.assertEqual(cook_habit.periodicity, "weekly")
        self.assertEqual(len(cook_habit.completions), 1)

    def test_longest_streak_daily(self):
        """
        Tests the longest streak for a daily habit.
        """
        self.tracker.add_habit("Daily Exercise", "...", "daily")
        habit = self.tracker.get_habit_by_name("Daily Exercise")

        # Simulate a streak of 3 days (e.g., 3, 2, 1 days ago)
        for i in range(3):
            self.tracker.complete_habit("Daily Exercise", date=datetime.now() - timedelta(days=2 - i))
        self.assertEqual(habit.get_longest_streak(), 3)

        # Simulate a break and a new, shorter streak
        # (IMPORTANT: Do not use future dates here, so as not to falsify the longest streak)
        # Reset completions and add a longer streak
        habit.completions = []
        for i in range(5):  # A streak of 5 days
            self.tracker.complete_habit("Daily Exercise", date=datetime.now() - timedelta(days=4 - i))
        self.assertEqual(habit.get_longest_streak(), 5)  # Expected 5 for the new longest streak

        # Add a gap and then a shorter, new streak to check if the longest is retained
        # Example: A 2-day streak after a 3-day gap
        gap_start_date = datetime.now() - timedelta(days=8)
        self.tracker.complete_habit("Daily Exercise", date=gap_start_date)
        self.tracker.complete_habit("Daily Exercise", date=gap_start_date + timedelta(days=1))

        # The longest streak should still be 5, from the previous longer streak
        self.assertEqual(habit.get_longest_streak(), 5)

    def test_longest_streak_weekly(self):
        """
        Tests the longest streak for a weekly habit.
        """
        self.tracker.add_habit("Weekly Review", "...", "weekly")
        habit = self.tracker.get_habit_by_name("Weekly Review")

        # Simulate a streak of 2 weeks
        today = datetime.now()
        last_week = today - timedelta(weeks=1)
        two_weeks_ago = today - timedelta(weeks=2)

        self.tracker.complete_habit("Weekly Review", date=two_weeks_ago)
        self.tracker.complete_habit("Weekly Review", date=last_week)
        self.assertEqual(habit.get_longest_streak(), 2)

        # Simulate a longer streak
        habit.completions = []  # Reset completions
        for i in range(4):
            self.tracker.complete_habit("Weekly Review", date=today - timedelta(weeks=3 - i, days=2))
        self.assertEqual(habit.get_longest_streak(), 4)

    def test_struggling_habits(self):
        """
        Tests the function for identifying "struggling habits".
        """
        self.tracker.add_habit("Yoga", "Daily", "daily")
        self.tracker.add_habit("Breathing Exercise", "Daily", "daily")  # Changed from "Learn Language"
        self.tracker.add_habit("Screen Break", "Weekly", "weekly")  # Changed from "Project Work"

        # Yoga completed for the last 30 days (to ensure it is NOT struggling)
        # The range must go forward 30 days, as timedelta(days=i) counts backwards.
        # Start is (today - 29 days) to (today - 0 days).
        for i in range(30):
            self.tracker.complete_habit("Yoga", date=datetime.now() - timedelta(days=29 - i))

        # Breathing Exercise completed only once (should be struggling)
        self.tracker.complete_habit("Breathing Exercise", date=datetime.now() - timedelta(days=25))

        # Screen Break completed only once last week (should be struggling, as many weeks were missed)
        self.tracker.complete_habit("Screen Break", date=datetime.now() - timedelta(weeks=1, days=2))

        struggling = self.tracker.get_struggling_habits(period_days=30)
        # self.tracker.get_struggling_habits() already returns a list of names
        struggling_names = struggling

        # Expected: "Breathing Exercise" and "Screen Break" should appear
        # "Yoga" should NOT appear, as it was done regularly

        self.assertIn("Breathing Exercise", struggling_names)
        self.assertIn("Screen Break", struggling_names)
        self.assertNotIn("Yoga", struggling_names)

        # Optional: Test with no struggling habits
        self.tracker.habits = []  # Clear existing habits for new test
        self.tracker.add_habit("Super Habit", "Daily", "daily")
        for i in range(30):
            self.tracker.complete_habit("Super Habit",
                                        date=datetime.now() - timedelta(days=29 - i))  # 30 consecutive days
        no_struggling = self.tracker.get_struggling_habits(period_days=30)
        self.assertEqual(len(no_struggling), 0)

