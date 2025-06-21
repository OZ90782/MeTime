# MeTime
A simple yet functional habit tracker developed in Python, focusing on promoting regular breaks and relaxation exercises to support mental well-being and mindfulness in daily life.

## What it is

MeTime is a command-line interface (CLI) application designed to help users track habits that support mental health, such as taking screen breaks, guided meditations, short breathing exercises, or movement/stretching breaks.

Key features include:

* **Habit Management:** Create, delete, and mark habits as completed.

* **Periodicity:** Supports both daily and weekly habits.

* **Tracking:** Automatically tracks habit creation dates and completion timestamps.

* **Streaks:** Calculates current and longest run streaks for habits.

* **Analytics:** Provides insights into habit performance, including habits with the same periodicity, longest streaks, and identifying "struggling habits" (most frequently missed).

* **Data Persistence:** All habit data is stored locally in JSON files between user sessions, ensuring your data remains private and accessible.

## Installation

MeTime is built using **Python 3.7 or later**. It relies solely on Python's built-in standard libraries, so there are no external dependencies to install.

To set up the project:

1.  **Clone or download** the project files to your local machine.

2.  **Navigate** to the project directory in your terminal.

## Usage

To start the MeTime application, run the main.py script from your terminal:

python main.py

Upon launching, the application will load any existing habit data and present you with an interactive command-line menu. You can then choose from options like:

* Create a new habit

* Delete an existing habit

* Mark a habit as completed

* View current habits

* Analyze habit performance

* Exit the application

Predefined Habits and Example Data:
The system is designed to load existing data. For testing and verification, the unit tests programmatically generate sample habit data, including "Yoga", "Breathing Exercise", and "Screen Break", covering periods of four weeks or more to test streak calculations and struggling habit identification. When you first run main.py, it will start with an empty state and save your new habits to habits.json.

## Test
To run the unit tests and verify the functionality of the habit tracker, use the following command in your terminal from the project root directory:

python -m unittest test_project.py

