from datetime import datetime, timedelta


def get_longest_run_streak(habits):
    """
    Calculates the longest streak for each habit in a list of habits.

    Args:
        habits (list[Habit]): A list of Habit objects.

    Returns:
        list[tuple[Habit, int]]: A list of tuples, containing the habit and its
                                  longest streak.
    """
    results = []
    now = datetime.now()  # Current time
    for habit in habits:
        # Consider only completions up to the current time
        relevant_completions = [c for c in habit.completions if c <= now]
        if not relevant_completions:
            results.append((habit, 0))
            continue

        longest_streak = 0
        # Ensure the list is still sorted after filtering
        sorted_completions = sorted(relevant_completions)

        for i in range(len(sorted_completions)):
            current_streak = 1  # Starts the streak with the current completion
            for j in range(i + 1, len(sorted_completions)):
                # Check if the next completion follows the periodicity pattern
                if habit.periodicity == "daily":
                    expected_next_date = sorted_completions[j - 1].date() + timedelta(days=1)
                    if sorted_completions[j].date() == expected_next_date:
                        current_streak += 1
                    else:
                        break  # Streak broken
                elif habit.periodicity == "weekly":
                    # Check if the next completion is in the directly following week
                    # Assumption: Weeks start on Monday (weekday 0)
                    current_iso_week = sorted_completions[j - 1].isocalendar()
                    next_iso_week = sorted_completions[j].isocalendar()

                    # Check if the next completion is in the directly following week,
                    # considering year changes.
                    if (next_iso_week[0] == current_iso_week[0] and next_iso_week[1] == current_iso_week[1] + 1) or \
                            (next_iso_week[0] == current_iso_week[0] + 1 and next_iso_week[1] == 1 and current_iso_week[
                                1] in [52, 53]):  # Handle 52 or 53 weeks in a year
                        current_streak += 1
                    else:
                        break
            longest_streak = max(longest_streak, current_streak)
        results.append((habit, longest_streak))
    return results


def get_current_streak(habit, today):
    """
    Calculates the current streak for a single habit.

    Args:
        habit (Habit): The Habit object.
        today (datetime): The current time up to which the streak should be calculated.

    Returns:
        int: The current streak.
    """
    if not habit.completions:
        return 0

    # Filter out future completions for the current streak calculation
    relevant_completions = [c for c in habit.completions if c.date() <= today.date()]
    if not relevant_completions:
        return 0  # No relevant completions

    # Sort completions in descending order by date to check the current streak
    sorted_relevant_completions = sorted(relevant_completions, reverse=True)

    if habit.periodicity == "daily":
        # If the most recent completion is not today, the current streak is 0
        if sorted_relevant_completions[0].date() != today.date():
            return 0

        current_streak = 1  # Reaches here ONLY if sorted_relevant_completions[0].date() == today.date()
        expected_date = today.date() - timedelta(days=1)

        for i in range(1, len(sorted_relevant_completions)):
            if sorted_relevant_completions[i].date() == expected_date:
                current_streak += 1
                expected_date -= timedelta(days=1)
            elif sorted_relevant_completions[i].date() < expected_date:
                break  # Gap found
        return current_streak

    elif habit.periodicity == "weekly":
        current_year, current_week_num, _ = today.isocalendar()

        # Check if the habit was completed in the current calendar week
        completed_this_week = False
        for c in sorted_relevant_completions:
            c_year, c_week_num, _ = c.isocalendar()
            if c_year == current_year and c_week_num == current_week_num:
                completed_this_week = True
                break

        # If the habit was not completed this week, the current streak is 0
        if not completed_this_week:
            return 0

        # If the habit was completed this week
        current_streak = 1
        expected_week_year = current_year
        expected_week_num = current_week_num - 1
        if expected_week_num < 1:  # Year change
            expected_week_num = 52  # assuming 52 weeks in a year for simplicity
            expected_week_year -= 1

        for c in sorted_relevant_completions:
            c_year, c_week_num, _ = c.isocalendar()
            if c_year == expected_week_year and c_week_num == expected_week_num:
                current_streak += 1
                expected_week_num -= 1
                if expected_week_num < 1:  # Year change
                    expected_week_num = 52
                    expected_week_year -= 1
            elif c_year < expected_week_year or (c_year == expected_week_year and c_week_num < expected_week_num):
                break  # Gap found
        return current_streak
    return 0


def get_struggling_habits(habits, period_days):
    """
    Determines the habits that were most frequently missed in the specified period.

    Args:
        habits (list[Habit]): A list of Habit objects.
        period_days (int): The period in days (e.g., 30 for the last month).

    Returns:
        list[str]: A list of the names of habits, sorted in descending order by the number of missed periods.
                   Habits with 0 missed periods are not returned.
    """
    struggling = []
    end_date = datetime.now()
    # The period includes exactly 'period_days' days up to and including today.
    # If period_days=30, the period starts 29 days ago and ends today (total 30 days).
    start_date_period = end_date - timedelta(days=period_days - 1) if period_days > 0 else end_date

    for habit in habits:
        missed_count = 0
        # Relevant completions only within the strictly defined period
        completions_in_period = [c for c in habit.completions if
                                 start_date_period.date() <= c.date() <= end_date.date()]

        if habit.periodicity == "daily":
            current_date_iter = start_date_period.date()
            while current_date_iter <= end_date.date():
                if not any(c.date() == current_date_iter for c in completions_in_period):
                    missed_count += 1
                current_date_iter += timedelta(days=1)
        elif habit.periodicity == "weekly":
            # Determine the start week of the checking period (Monday)
            first_week_in_period_start = start_date_period - timedelta(days=start_date_period.weekday())

            current_week_iter_start = first_week_in_period_start

            # Loop through each week that overlaps with the 'period_days' window
            while current_week_iter_start <= end_date:
                current_week_iter_end = current_week_iter_start + timedelta(days=6)

                # Check if this calendar week is even relevant
                # A week is relevant if at least one day of the week falls within the 'period_days' window
                # i.e., the start of the week (Monday) must be BEFORE the end of the period
                # AND the end of the week (Sunday) must be AFTER the beginning of the period.
                if current_week_iter_start > end_date or current_week_iter_end < start_date_period:
                    current_week_iter_start += timedelta(weeks=1)
                    continue

                week_completed = False
                for c in completions_in_period:
                    if current_week_iter_start.date() <= c.date() <= current_week_iter_end.date():
                        week_completed = True
                        break

                if not week_completed:
                    missed_count += 1

                current_week_iter_start += timedelta(weeks=1)

        if missed_count > 0:  # Only add habits that were actually missed
            struggling.append((habit, missed_count))

    # Sort in descending order by the number of missed periods
    struggling.sort(key=lambda x: x[1], reverse=True)

    # Return only the names of the habits
    return [h.name for h, count in struggling]

