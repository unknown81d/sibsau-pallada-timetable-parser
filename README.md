# SibSAU Pallada Timetable Parser

A Python library for parsing and retrieving timetables from the SibSAU Pallada system. This tool allows you to fetch and parse schedules for both students and professors.

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
poetry run python3 src/__init__.py
```

## Usage

### Basic Example

```python
from search_results import get_by_search_query, fetch_database
import group_parser
import professor_parser
```

Fetch the database
```python
database = fetch_database_sync()
# ... proxy & process database
```

Search for a group
```python
search_result = get_by_search_query(database, "группа")
if search_result:
    schedule = group_parser.get_schedule_from_url_sync(search_result.url)
        print(f"Group: {schedule.group_name}")
        print(f"Semester: {schedule.semester}")
# ... process schedule data
```

Search for a professor
```python
search_result = get_by_search_query(database, "фамилия")
if search_result:
    schedule = professor_parser.get_schedule_from_url_sync(search_result.url)
        print(f"Professor: {schedule.person_name}")
        print(f"Academic Year: {schedule.academic_year}")
# ... process schedule data
```

### Async Usage Example

```python
import asyncio
from search_results import get_by_search_query, fetch_database
import group_parser

async def main():
    database = await fetch_database()

    search_result = get_by_search_query(database, "группа")
    if search_result:
        schedule = await group_parser.get_schedule_from_url(search_result.url)
        print(f"Group: {schedule.group_name}")
        print(f"Semester: {schedule.semester}")

# Run the async code
asyncio.run(main())
```

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

## Acknowledgments

- SibSAU Pallada system
- Contributors and maintainers
