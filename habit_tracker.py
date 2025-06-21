import json
from datetime import datetime, timedelta
import analytics

class Habit:
    """
    Represents a single habit with its properties and methods.
    """
    def __init__(self, name, description, periodicity, creation_date=None, last_completed=None, completions=None):
        """
        Initializes a Habit.

        Args:
            name (str): The name of the habit.
            description (str): A description of the habit.
            periodicity (str): The periodicity of the habit ('daily' or 'weekly').
            creation_date (datetime, optional): The creation date of the habit.
                                                 Defaults to now.
            last_completed (datetime, optional): The date of the last completion.
                                                  Defaults to None.
            completions (list[datetime], optional): A list of timestamps
                                                     when the habit was completed.
                                                     Defaults to empty.
        """
        self.name = name
        self.description = description
        self.periodicity = periodicity
        self.creation_date = creation_date if creation_date else datetime.now()
        self.last_completed = last_completed
        self.completions = sorted(completions) if completions else []

    def mark_completed(self, date=None):
        """
        Marks the habit as completed for the specified date.
        If no date is specified, the current time is used.

        Args:
            date (datetime, optional): The date the habit was completed.
                                       Defaults to None (current time).
        """
        completion_date = date if date else datetime.now()
        # Prevent duplicate entries for the same day/week
        if self.periodicity == "daily":
            if self.completions and self.completions[-1].date() == completion_date.date():
                raise ValueError("Habit has already been completed today.")
        elif self.periodicity == "weekly":
            # Check if the habit has already been completed in the current calendar week
            # Calendar week starts on Monday (isocalendar().week)
            if self.completions and self.completions[-1].isocalendar().week == completion_date.isocalendar().week \
                                and self.completions[-1].year == completion_date.year:
                raise ValueError("Habit has already been completed this week.")
        self.completions.append(completion_date)
        self.completions.sort() # Ensure the list is always sorted
        self.last_completed = completion_date

    def get_current_streak(self):
        """
        Calculates the current streak (number of consecutive completions).

        Returns:
            int: The current streak.
        """
        if not self.completions:
            return 0

        # Calculates the current streak based on periodicity
        return analytics.get_current_streak(self, datetime.now())

    def get_longest_streak(self):
        """
        Calculates the longest streak (number of consecutive completions)
        in the history of the habit.

        Returns:
            int: The longest streak.
        """
        if not self.completions:
            return 0
        return analytics.get_longest_run_streak([self])[0][1] # Pass habit as a list to analytics function

    def was_broken(self, period_start, period_end):
        """
        Checks if the habit was broken in a specific period (defined by period_start and period_end).

        Args:
            period_start (datetime): The start of the period.
            period_end (datetime): The end of the period.

        Returns:
            bool: True if the habit was broken, False otherwise.
        """
        # Get all completion dates within the specified period
        completions_in_period = [
            c for c in self.completions if period_start <= c <= period_end
        ]

        if self.periodicity == "daily":
            # Check each day in the period
            current_date = period_start
            while current_date <= period_end:
                if not any(c.date() == current_date.date() for c in completions_in_period):
                    # If no completion was found on a day in the period
                    return True
                current_date += timedelta(days=1)
            return False
        elif self.periodicity == "weekly":
            # Check each week in the period
            # Find the first week
            first_week_start = period_start - timedelta(days=period_start.weekday()) # Monday of the week
            current_week_start = first_week_start
            while current_week_start <= period_end:
                # Find the end of the current week
                current_week_end = current_week_start + timedelta(days=6)
                # Check if there was a completion in this week
                if not any(c for c in completions_in_period if current_week_start.date() <= c.date() <= current_week_end.date()):
                    return True # Habit broken this week
                current_week_start += timedelta(weeks=1)
            return False
        return True # Invalid periodicity

    def to_dict(self):
        """
        Converts the Habit object to a dictionary for JSON serialization.
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
        Creates a Habit object from a dictionary.
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
    Manages a collection of Habit objects and their persistence.
    """
    def __init__(self, db_manager):
        """
        Initializes the HabitTracker.

        Args:
            db_manager (DB): An instance of the DB manager for saving/loading.
        """
        self.habits = []
        self.db_manager = db_manager

    def add_habit(self, name, description, periodicity):
        """
        Adds a new habit to the tracker.

        Args:
            name (str): The name of the habit.
            description (str): The description of the habit.
            periodicity (str): The periodicity of the habit ('daily' or 'weekly').
        """
        if self.get_habit_by_name(name):
            raise ValueError(f"Habit with the name '{name}' already exists.")
        habit = Habit(name, description, periodicity)
        self.habits.append(habit)
        self.save_to_file()

    def delete_habit(self, name):
        """
        Deletes a habit by its name.

        Args:
            name (str): The name of the habit to delete.

        Returns:
            bool: True if the habit was deleted, False otherwise.
        """
        initial_len = len(self.habits)
        self.habits = [h for h in self.habits if h.name != name]
        if len(self.habits) < initial_len:
            self.save_to_file()
            return True
        return False

    def complete_habit(self, name, date=None):
        """
        Marks a habit as completed.

        Args:
            name (str): The name of the habit.
            date (datetime, optional): The date of completion. Defaults to now.

        Raises:
            ValueError: If the habit is not found or has already been completed.
        """
        habit = self.get_habit_by_name(name)
        if habit:
            habit.mark_completed(date)
            self.save_to_file()
        else:
            raise ValueError(f"Habit '{name}' not found.")

    def get_habit_by_name(self, name):
        """
        Searches for a habit by its name.

        Args:
            name (str): The name of the habit to search for.

        Returns:
            Habit or None: The Habit object if found, None otherwise.
        """
        for habit in self.habits:
            if habit.name == name:
                return habit
        return None

    def get_all_habits(self):
        """
        Returns a list of all habits.
        """
        return self.habits

    def get_habits_by_period(self, periodicity):
        """
        Returns a list of habits with a specific periodicity.

        Args:
            periodicity (str): The desired periodicity ('daily' or 'weekly').

        Returns:
            list[Habit]: A list of Habit objects.
        """
        return [h for h in self.habits if h.periodicity == periodicity]

    def get_longest_streak_for_habit(self, habit_name):
        """
        Returns the longest streak for a specific habit.

        Args:
            habit_name (str): The name of the habit.

        Returns:
            int: The longest streak.
        """
        habit = self.get_habit_by_name(habit_name)
        if habit:
            return habit.get_longest_streak()
        return 0 # Or raise an error, depending on desired behavior

    def get_struggling_habits(self, period_days=30):
        """
        Returns a list of habits most frequently missed in the last month.
        This function uses the Analytics function.

        Args:
            period_days (int): Number of days for which "struggling habits" should be determined.

        Returns:
            list[str]: A list of the names of "struggling habits".
        """
        # Correction: analytics.get_struggling_habits now returns a list of names directly
        return analytics.get_struggling_habits(self.habits, period_days)


    def save_to_file(self):
        """
        Saves all habits to the configured JSON file.
        """
        data = [habit.to_dict() for habit in self.habits]
        self.db_manager.save_data(data)

    def load_from_file(self):
        """
        Loads habits from the configured JSON file.
        """
        data = self.db_manager.load_data()
        self.habits = [Habit.from_dict(d) for d in data]