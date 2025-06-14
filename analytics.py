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
    now = datetime.now()  # Aktueller Zeitpunkt
    for habit in habits:
        # Nur Abschlüsse bis zum aktuellen Zeitpunkt berücksichtigen
        relevant_completions = [c for c in habit.completions if c <= now]
        if not relevant_completions:
            results.append((habit, 0))
            continue

        longest_streak = 0
        # Sicherstellen, dass die Liste nach dem Filtern immer noch sortiert ist
        sorted_completions = sorted(relevant_completions)

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
                    current_iso_week = sorted_completions[j - 1].isocalendar()
                    next_iso_week = sorted_completions[j].isocalendar()

                    # Prüfen, ob die nächste Abschluss in der direkt folgenden Woche ist,
                    # unter Berücksichtigung des Jahreswechsels.
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
    Berechnet die aktuelle Streak für einen einzelnen Habit.

    Args:
        habit (Habit): Das Habit-Objekt.
        today (datetime): Der aktuelle Zeitpunkt, bis zu dem die Streak berechnet werden soll.

    Returns:
        int: Die aktuelle Streak.
    """
    if not habit.completions:
        return 0

    # Filtert zukünftige Abschlüsse für die aktuelle Streak-Berechnung
    relevant_completions = [c for c in habit.completions if c.date() <= today.date()]
    if not relevant_completions:
        return 0  # Keine relevanten Abschlüsse

    # Sortiere Abschlüsse absteigend nach Datum, um die aktuelle Streak zu prüfen
    sorted_relevant_completions = sorted(relevant_completions, reverse=True)

    if habit.periodicity == "daily":
        # Wenn der neueste Abschluss nicht heute ist, ist die aktuelle Streak 0
        if sorted_relevant_completions[0].date() != today.date():
            return 0

        current_streak = 1  # Reaches here ONLY if sorted_relevant_completions[0].date() == today.date()
        expected_date = today.date() - timedelta(days=1)

        for i in range(1, len(sorted_relevant_completions)):
            if sorted_relevant_completions[i].date() == expected_date:
                current_streak += 1
                expected_date -= timedelta(days=1)
            elif sorted_relevant_completions[i].date() < expected_date:
                break  # Lücke gefunden
        return current_streak

    elif habit.periodicity == "weekly":
        current_year, current_week_num, _ = today.isocalendar()

        # Prüfe, ob der Habit in der aktuellen Kalenderwoche abgeschlossen wurde
        completed_this_week = False
        for c in sorted_relevant_completions:
            c_year, c_week_num, _ = c.isocalendar()
            if c_year == current_year and c_week_num == current_week_num:
                completed_this_week = True
                break

        # Wenn der Habit diese Woche nicht abgeschlossen wurde, ist die aktuelle Streak 0
        if not completed_this_week:
            return 0

        # Wenn der Habit in der aktuellen Woche abgeschlossen wurde
        current_streak = 1
        expected_week_year = current_year
        expected_week_num = current_week_num - 1
        if expected_week_num < 1:  # Jahreswechsel
            expected_week_num = 52  # assuming 52 weeks in a year for simplicity
            expected_week_year -= 1

        for c in sorted_relevant_completions:
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
    return 0


def get_struggling_habits(habits, period_days):
    """
    Ermittelt die Habits, die im angegebenen Zeitraum am häufigsten verpasst wurden.

    Args:
        habits (list[Habit]): Eine Liste von Habit-Objekten.
        period_days (int): Der Zeitraum in Tagen (z.B. 30 für den letzten Monat).

    Returns:
        list[str]: Eine Liste der Namen der Habits, absteigend sortiert nach der Anzahl der verpassten Perioden.
                   Habits mit 0 verpassten Perioden werden nicht zurückgegeben.
    """
    struggling = []
    end_date = datetime.now()
    # Der Zeitraum umfasst genau 'period_days' Tage bis einschließlich heute.
    # Wenn period_days=30, beginnt der Zeitraum vor 29 Tagen und endet heute (insgesamt 30 Tage).
    start_date_period = end_date - timedelta(days=period_days - 1) if period_days > 0 else end_date

    for habit in habits:
        missed_count = 0
        # Relevante Abschlüsse nur innerhalb des genau definierten Zeitraums
        completions_in_period = [c for c in habit.completions if
                                 start_date_period.date() <= c.date() <= end_date.date()]

        if habit.periodicity == "daily":
            current_date_iter = start_date_period.date()
            while current_date_iter <= end_date.date():
                if not any(c.date() == current_date_iter for c in completions_in_period):
                    missed_count += 1
                current_date_iter += timedelta(days=1)
        elif habit.periodicity == "weekly":
            # Bestimme die Startwoche des Prüfzeitraums (Montag)
            first_week_in_period_start = start_date_period - timedelta(days=start_date_period.weekday())

            current_week_iter_start = first_week_in_period_start

            # Schleife durch jede Woche, die sich mit dem 'period_days'-Fenster überschneidet
            while current_week_iter_start <= end_date:
                current_week_iter_end = current_week_iter_start + timedelta(days=6)

                # Überprüfen, ob diese Kalenderwoche überhaupt relevant ist
                # Eine Woche ist relevant, wenn mindestens ein Tag der Woche im 'period_days'-Fenster liegt
                # D.h., der Wochenanfang (Montag) muss VOR dem Ende des Zeitraums liegen
                # UND das Wochenende (Sonntag) muss NACH dem Beginn des Zeitraums liegen.
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

        if missed_count > 0:  # Nur Habits hinzufügen, die tatsächlich verpasst wurden
            struggling.append((habit, missed_count))

    # Sortiere absteigend nach der Anzahl der verpassten Perioden
    struggling.sort(key=lambda x: x[1], reverse=True)

    # Rückgabe nur der Namen der Habits
    return [h.name for h, count in struggling]
