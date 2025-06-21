import os
from habit_tracker import HabitTracker
from db import DB
from datetime import datetime

class CLI:
    """
    Class for the Command Line Interface (CLI) of the Habit Tracker.
    Manages interaction with the user and calls HabitTracker functions.
    """
    def __init__(self, habit_tracker):
        """
        Initializes the CLI with an instance of HabitTracker.
        Args:
            habit_tracker (HabitTracker): The HabitTracker instance.
        """
        self.habit_tracker = habit_tracker

    def run(self):
        """
        Starts the main CLI loop and displays the menu.
        """
        print("Welcome to the Habit Tracker – \"MeTime\"")
        while True:
            self._display_menu()
            choice = input("Select an option: ")
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
                print("Goodbye!")
                break
            else:
                print("Invalid input. Please try again.")

    def _display_menu(self):
        """
        Displays the main CLI menu.
        """
        print("\n--- Menu ---")
        print("1. Create a new habit")
        print("2. Delete an existing habit")
        print("3. Mark a habit as completed")
        print("4. View current habits")
        print("5. Analyze habit performance")
        print("6. Exit")

    def prompt_create_habit(self):
        """
        Prompts the user for information to create a new habit
        and creates it.
        """
        name = input("Habit Name: ").strip()
        if not name:
            print("Habit name cannot be empty.")
            return
        description = input("Habit Description: ").strip()
        periodicity = input("Periodicity (daily/weekly): ").strip().lower()
        if periodicity not in ["daily", "weekly"]:
            print("Invalid periodicity. Please enter 'daily' or 'weekly'.")
            return
        self.habit_tracker.add_habit(name, description, periodicity)
        print(f"Habit '{name}' successfully created.")

    def prompt_delete_habit(self):
        """
        Prompts the user for the name of a habit to delete
        and deletes it.
        """
        name = input("Name of the habit to delete: ").strip()
        if not name:
            print("Habit name cannot be empty.")
            return
        if self.habit_tracker.delete_habit(name):
            print(f"Habit '{name}' successfully deleted.")
        else:
            print(f"Habit '{name}' not found.")

    def prompt_mark_completed(self):
        """
        Prompts the user for the name of a habit to mark as completed
        and marks it as completed.
        """
        name = input("Name of the habit to mark as completed: ").strip()
        if not name:
            print("Habit name cannot be empty.")
            return
        try:
            self.habit_tracker.complete_habit(name)
            print(f"Habit '{name}' marked as completed.")
        except ValueError as e:
            print(f"Error: {e}")

    def prompt_view_current_habits(self):
        """
        Displays all current habits of the user.
        """
        habits = self.habit_tracker.get_all_habits()
        if not habits:
            print("No habits found.")
            return
        print("\n--- Current Habits ---")
        for habit in habits:
            print(f"Name: {habit.name}")
            print(f"  Description: {habit.description}")
            print(f"  Periodicity: {habit.periodicity}")
            print(f"  Current Streak: {habit.get_current_streak()}")
            print(f"  Longest Streak: {habit.get_longest_streak()}")
            if habit.completions:
                print(f"  Last Completion Time: {habit.completions[-1].strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("  Not completed yet.")
            print("-" * 20)

    def prompt_analysis(self):
        """
        Offers various analysis options for habit performance.
        """
        print("\n--- Habit Analysis ---")
        print("1. Show habits by periodicity")
        print("2. Show longest streak of a habit")
        print("3. Show habits most frequently missed in the last month")
        analysis_choice = input("Select an analysis option: ")

        if analysis_choice == '1':
            period = input("Periodicity (daily/weekly): ").strip().lower()
            if period not in ["daily", "weekly"]:
                print("Invalid periodicity. Please enter 'daily' or 'weekly'.")
                return
            habits_by_period = self.habit_tracker.get_habits_by_period(period)
            if habits_by_period:
                print(f"\n--- Habits with Periodicity '{period}' ---")
                for habit in habits_by_period:
                    print(f"- {habit.name} (Streak: {habit.get_current_streak()})")
            else:
                print(f"No habits with periodicity '{period}' found.")
        elif analysis_choice == '2':
            name = input("Name of the habit for the longest streak: ").strip()
            if not name:
                print("Habit name cannot be empty.")
                return
            habit = self.habit_tracker.get_habit_by_name(name)
            if habit:
                longest_streak = habit.get_longest_streak()
                print(f"The longest streak for '{name}' is: {longest_streak} days.")
            else:
                print(f"Habit '{name}' not found.")
        elif analysis_choice == '3':
            struggling_habits = self.habit_tracker.get_struggling_habits()
            if struggling_habits:
                print("\n--- Habits Most Frequently Missed in the Last Month ---")
                for habit_name in struggling_habits:
                    print(f"- {habit_name}")
            else:
                print("No habits were missed in the last month or no data available.")
        else:
            print("Invalid selection for analysis option.")


if __name__ == "__main__":
    # Path to the JSON file where habits will be stored
    DATA_FILE = "habits.json"
    db_manager = DB(DATA_FILE)
    habit_tracker_instance = HabitTracker(db_manager)

    # Load existing data on startup
    habit_tracker_instance.load_from_file()

    cli = CLI(habit_tracker_instance)
    cli.run()


