# SibSAU Pallada Timetable Parser

A Python library for parsing and retrieving timetables from the SibSAU Pallada system. This tool allows you to fetch and parse schedules for both students and professors.

![CleanShot 2025-01-26 at 22.01.35@2x](images/CleanShot%202025-01-26%20at%2022.01.35@2x.png)
![CleanShot 2025-01-26 at 22.01.51@2x](images/CleanShot%202025-01-26%20at%2022.01.51@2x.png)

## Features

- Search for groups and professors
- Parse group schedules including:
  - Regular weekly schedule
  - Session schedule
- Parse professor schedules including:
  - Regular weekly schedule
  - Session schedule
  - Consultation schedule
- Fuzzy search support for both Cyrillic and Latin characters
- Detailed schedule information (time, location, subject, etc.)

## Installation & Development Setup

Clone the repository
```bash
git clone https://github.com/unknown81d/sibsau-pallada-timetable-parser.git
cd sibsau-pallada-timetable-parser
```

Create and activate virtual environment & Install dependencies
```bash
poetry install
```

Run the script
```bash
poetry run python3 tests/__init__.py
```

## Usage

### Basic Example

```python
import sibsau_pallada_timetable_parser.src
```

Fetch the database
```python
# sync
database = fetch_database_sync()                              # without proxy
database = fetch_database_sync("proxies/search_results.json") # with proxy

print(database, database.source)
# ... process database

# async
database = await fetch_database()                            # without proxy
database = await fetch_database("proxies/search_results.json") # with proxy

print(database, database.source, database.source_date)
# ... process database
```

Search for a group
```python
# sync
search_result = get_by_search_query(database, "группа")
if search_result and search_result.type == "group":
    schedule = group_parser.get_schedule_from_url_sync(search_result.url, "proxies") # with proxy
    # schedule = group_parser.get_schedule_from_url_sync(search_result.url)          # without proxy
    print(schedule.source)
    print(schedule.source_date)
    print(f"Group: {schedule.group_name}")
    print(f"Semester: {schedule.semester}")
# ... process schedule data

# async
search_result = get_by_search_query(database, "группа")
if search_result and search_result.type == "group":
    schedule = await group_parser.get_schedule_from_url(search_result.url, "proxies") # with proxy
    # schedule = await group_parser.get_schedule_from_url(search_result.url)          # without proxy
    print(schedule.source)
    print(schedule.source_date)
    print(f"Group: {schedule.group_name}")
    print(f"Semester: {schedule.semester}")
```

Process changes (New)
```python
if schedule.source == group_parser.SourceType.CHANGED:
    print("Changes detected:")
    for change in schedule.changes:
        if change.week_number:
            print(f"Week {change.week_number}, {change.day_name}, {change.lesson_time}:")
        else:
            print(f"Session schedule, {change.day_name}, {change.lesson_time}:")
        print(f"  {change.field}: {change.old_value} -> {change.new_value}")
elif schedule.source == group_parser.SourceType.PROXY:
    print("Loaded from cache")
else:
    print("Fresh data fetched")
```

Search for a professor
```python
# sync
search_result = get_by_search_query(database, "фамилия")
if search_result and search_result.type == "professor":
    schedule = professor_parser.get_schedule_from_url_sync(search_result.url, "proxies") # with proxy
    # schedule = professor_parser.get_schedule_from_url_sync(search_result.url)          # without proxy
    print(schedule.source)
    print(schedule.source_date)
    print(f"Professor: {schedule.person_name}")
    print(f"Academic Year: {schedule.academic_year}")
# ... process schedule data

# async
search_result = get_by_search_query(database, "фамилия")
if search_result and search_result.type == "professor":
    schedule = await professor_parser.get_schedule_from_url(search_result.url, "proxies") # with proxy
    # schedule = await professor_parser.get_schedule_from_url(search_result.url)          # without proxy
    print(schedule.source)
    print(schedule.source_date)
    print(f"Professor: {schedule.person_name}")
    print(f"Academic Year: {schedule.academic_year}")
```

Process changes (New)
```python
if schedule.source == professor_parser.SourceType.CHANGED:
    print("Changes detected:")
    for change in schedule.changes:
        if change.week_number:
            print(f"Week {change.week_number}, {change.day_name}, {change.lesson_time}:")
        else:
            print(f"Session schedule, {change.day_name}, {change.lesson_time}:")
        print(f"  {change.field}: {change.old_value} -> {change.new_value}")
elif schedule.source == professor_parser.SourceType.PROXY:
    print("Loaded from cache")
else:
    print("Fresh data fetched")
```

Check tests folder for more examples

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

## Acknowledgments

- SibSAU Pallada system
- Contributors and maintainers
