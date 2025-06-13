from datetime import datetime, timedelta


def get_longest_run_streak(habits):
    """
    Berechnet die längste Streak für jeden Habit in einer Liste von Habits.

    Args:
        habits (list[Habit]): Eine Liste von Habit-Objekten.

    Returns:
        list[tuple[Habit, int]]: Eine Liste von Tupeln, die den Habit und seine
                                  längste Streak enthalten.
    """
    results = []
    for habit in habits:
        if not habit.completions:
            results.append((habit, 0))
            continue

        longest_streak = 0
        current_streak = 0
        # Sortiere Abschlussdaten, um sicherzustellen, dass sie chronologisch sind
        sorted_completions = sorted(habit.completions)

        for i in range(len(sorted_completions)):
            current_streak = 1  # Startet die Streak mit der aktuellen Abschluss
            for j in range(i + 1, len(sorted_completions)):
                # Prüfe, ob die nächste Abschluss dem Periodizitätsmuster folgt
                if habit.periodicity == "daily":
                    expected_next_date = sorted_completions[j - 1].date() + timedelta(days=1)
                    if sorted_completions[j].date() == expected_next_date:
                        current_streak += 1
                    else:
                        break  # Streak unterbrochen
                elif habit.periodicity == "weekly":
                    # Prüfe, ob die nächste Abschluss in der direkt folgenden Woche ist
                    # Annahme: Wochen beginnen am Montag (weekday 0)
                    current_week_num = sorted_completions[j - 1].isocalendar()[1]
                    next_completion_week_num = sorted_completions[j].isocalendar()[1]
                    # Berücksichtige Jahreswechsel
                    if (next_completion_week_num == (current_week_num % 52) + 1 and
                        sorted_completions[j].year == sorted_completions[j - 1].year) or \
                            (next_completion_week_num == 1 and current_week_num == 52 and
                             sorted_completions[j].year == sorted_completions[j - 1].year + 1):
                        current_streak += 1
                    else:
                        break
            longest_streak = max(longest_streak, current_streak)
        results.append((habit, longest_streak))
    return results


def get_current_streak(habit, today):
    """
    Berechnet die aktuelle Streak für einen einzelnen Habit.

    Args:
        habit (Habit): Das Habit-Objekt.
        today (datetime): Der aktuelle Zeitpunkt, bis zu dem die Streak berechnet werden soll.

    Returns:
        int: Die aktuelle Streak.
    """
    if not habit.completions:
        return 0

    current_streak = 0
    # Gehe die Abschlüsse rückwärts durch
    sorted_completions = sorted(habit.completions, reverse=True)

    # Startpunkt für die Prüfung (gestern für täglich, letzte Woche für wöchentlich)
    if habit.periodicity == "daily":
        expected_date = today.date()
        # Prüfe, ob der Habit heute abgeschlossen wurde
        if sorted_completions[0].date() == expected_date:
            current_streak = 1
            expected_date -= timedelta(days=1)
        elif sorted_completions[0].date() == expected_date - timedelta(days=1):
            # Wenn der letzte Abschluss gestern war, aber nicht heute
            current_streak = 0
            expected_date = sorted_completions[0].date() - timedelta(days=1)
        else:
            return 0  # Habit wurde nicht heute oder gestern abgeschlossen, Streak ist 0

        for i in range(len(sorted_completions)):
            if sorted_completions[i].date() == expected_date:
                current_streak += 1
                expected_date -= timedelta(days=1)
            elif sorted_completions[i].date() < expected_date:
                break  # Lücke gefunden
            # Wenn der Abschluss für ein zukünftiges Datum ist oder bereits geprüft wurde, überspringen
            # else: continue
        return current_streak

    elif habit.periodicity == "weekly":
        # Eine Woche ist abgeschlossen, wenn ein Eintrag in dieser Woche existiert
        # und die vorherige Woche ebenfalls einen Eintrag hatte.
        # Prüfe die letzte volle Woche bis zur aktuellen Woche

        # Aktuelle Kalenderwoche
        current_year, current_week_num, _ = today.isocalendar()

        # Finde den letzten Abschluss in der aktuellen Woche (oder in der letzten Woche, wenn heute Montag ist und noch kein Abschluss für diese Woche)
        last_completion_this_week = None
        for c in sorted_completions:
            c_year, c_week_num, _ = c.isocalendar()
            if c_year == current_year and c_week_num == current_week_num:
                last_completion_this_week = c
                break

        # Wenn der Habit in der aktuellen Woche abgeschlossen wurde
        if last_completion_this_week:
            current_streak = 1
            expected_week_year = current_year
            expected_week_num = current_week_num - 1 if current_week_num > 1 else 52  # Vorherige Woche
            if current_week_num == 1:  # Jahreswechsel
                expected_week_year -= 1

            for c in sorted_completions:
                c_year, c_week_num, _ = c.isocalendar()
                if c_year == expected_week_year and c_week_num == expected_week_num:
                    current_streak += 1
                    expected_week_num -= 1
                    if expected_week_num < 1:  # Jahreswechsel
                        expected_week_num = 52
                        expected_week_year -= 1
                elif c_year < expected_week_year or (c_year == expected_week_year and c_week_num < expected_week_num):
                    break  # Lücke gefunden
            return current_streak
        else:  # Habit wurde diese Woche noch nicht abgeschlossen
            # Prüfe, ob der letzte Abschluss in der *letzten* Woche war
            last_week_year = current_year
            last_week_num = current_week_num - 1
            if last_week_num < 1:
                last_week_num = 52
                last_week_year -= 1

            last_completion_last_week = None
            for c in sorted_completions:
                c_year, c_week_num, _ = c.isocalendar()
                if c_year == last_week_year and c_week_num == last_week_num:
                    last_completion_last_week = c
                    break

            if last_completion_last_week:
                # Streak beginnt von der letzten abgeschlossenen Woche
                current_streak = 1
                expected_week_year = last_week_year
                expected_week_num = last_week_num - 1
                if expected_week_num < 1:
                    expected_week_num = 52
                    expected_week_year -= 1

                for c in sorted_completions:
                    c_year, c_week_num, _ = c.isocalendar()
                    if c_year == expected_week_year and c_week_num == expected_week_num:
                        current_streak += 1
                        expected_week_num -= 1
                        if expected_week_num < 1:
                            expected_week_num = 52
                            expected_week_year -= 1
                    elif c_year < expected_week_year or (
                            c_year == expected_week_year and c_week_num < expected_week_num):
                        break
                return current_streak
            else:
                return 0  # Keine Abschlüsse in der aktuellen oder letzten Woche
    return 0


def get_struggling_habits(habits, period_days):
    """
    Ermittelt die Habits, die im angegebenen Zeitraum am häufigsten verpasst wurden.

    Args:
        habits (list[Habit]): Eine Liste von Habit-Objekten.
        period_days (int): Der Zeitraum in Tagen (z.B. 30 für den letzten Monat).

    Returns:
        list[tuple[Habit, int]]: Eine Liste von Tupeln (Habit-Objekt, Anzahl der verpassten Perioden),
                                  absteigend sortiert nach der Anzahl der verpassten Perioden.
    """
    struggling = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)

    for habit in habits:
        missed_count = 0
        if habit.periodicity == "daily":
            current_date = start_date.date()
            while current_date <= end_date.date():
                if not any(c.date() == current_date for c in habit.completions):
                    missed_count += 1
                current_date += timedelta(days=1)
        elif habit.periodicity == "weekly":
            # Start der ersten relevanten Woche
            current_week_start = start_date - timedelta(days=start_date.weekday())  # Montag der Startwoche

            while current_week_start <= end_date:
                current_week_end = current_week_start + timedelta(days=6)
                # Prüfe, ob in dieser Woche eine Abschluss existiert
                if not any(c for c in habit.completions if
                           current_week_start.date() <= c.date() <= current_week_end.date()):
                    missed_count += 1
                current_week_start += timedelta(weeks=1)
        struggling.append((habit, missed_count))

    # Sortiere absteigend nach der Anzahl der verpassten Perioden
    struggling.sort(key=lambda x: x[1], reverse=True)
    return struggling


def get_all_habits_by_period(habits, period):
    """
    Gibt eine Liste von Habits mit einer bestimmten Periodizität zurück.

    Args:
        habits (list[Habit]): Eine Liste von Habit-Objekten.
        period (str): Die gewünschte Periodizität ('daily' oder 'weekly').

    Returns:
        list[Habit]: Eine Liste von Habit-Objekten.
    """
    return [h for h in habits if h.periodicity == period]