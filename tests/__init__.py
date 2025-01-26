import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
# It's bad

from search_results import fetch_database, SearchResultList
import group_parser
import professor_parser

async def main():
    database = await fetch_database("tests/proxies/search_results.json")

    print()
    print(database.source)
    print(database.source_date)
    print()
    print(database)
    print()


    search_result = database.get_by_search_query("бпи23-01")
    if search_result and search_result.type == "group":
        url = search_result.url
        schedule = await group_parser.get_schedule_from_url(url, "tests/proxies")

        print()
        print(schedule.source)
        print(schedule.source_date)
        print()
        print(f"Group: {schedule.group_name}")
        print(f"Semester: {schedule.semester}")
        print()
        for week in schedule.weeks:
            print(f"  Week {week.week_number}:")
            for day in week.days:
                print(f"    {day.day_name}:")
                for lesson in day.lessons:
                    print(f"      - Time: {lesson.time}, Name: {lesson.name}, Professor: {lesson.professor}, Place: {lesson.place}, Subgroup: {lesson.subgroup}")
        if schedule.session:
            print("  Session Schedule:")
            for day in schedule.session.days:
                print(f"   {day.day_name}")
                for lesson in day.lessons:
                    print(f"      - Time: {lesson.time}, Name: {lesson.name}, Professor: {lesson.professor}, Place: {lesson.place}, Subgroup: {lesson.subgroup}")

        print()
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

    else:
        print("No search result found")


    search_result = database.get_by_search_query("проскурин")
    if search_result and search_result.type == "professor":
        url = search_result.url
        schedule = await professor_parser.get_schedule_from_url(url, "tests/proxies")

        print()
        print(schedule.source)
        print(schedule.source_date)
        print()
        print(f"Professor: {schedule.person_name}")
        print(f"Academic Year: {schedule.academic_year}")
        print()
        for week in schedule.weeks:
            print(f"  Week {week.week_number}:")
            for day in week.days:
                print(f"    {day.day_name}:")
                for lesson in day.lessons:
                    print(f"      - Time: {lesson.time}, Name: {lesson.name}, Place: {lesson.place}, Groups: {lesson.groups}, Subgroup: {lesson.subgroup}, Type: {lesson.type}")
        if schedule.session:
            print("  Session Schedule:")
            for day in schedule.session.days:
                print(f"   {day.day_name}")
                for lesson in day.lessons:
                    print(f"      - Time: {lesson.time}, Name: {lesson.name}, Place: {lesson.place}, Groups: {lesson.groups}, Type: {lesson.type}")
        if schedule.consultations:
            print("  Consultation Schedule:")
            for day in schedule.consultations.days:
                print(f"   {day.day_name}")
                for lesson in day.lessons:
                    print(f"      - Time: {lesson.time}, Name: {lesson.name}, Place: {lesson.place}")

        print()
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

    else:
        print("No search result found")

if __name__ == '__main__':
    asyncio.run(main())
