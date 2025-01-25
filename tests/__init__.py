import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from search_results import get_by_search_query, fetch_database
import group_parser
import professor_parser

import asyncio

async def main():
    database = await fetch_database()
    print(database)

    search_result = get_by_search_query(database, "бпи23-01")
    if search_result:
        url = search_result.url
        schedule = await group_parser.get_schedule_from_url(url)
        print(f"Group: {schedule.group_name}")
        print(f"Semester: {schedule.semester}")
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
    else:
        print("No search result found")


    search_result = get_by_search_query(database, "проскурин")
    if search_result:
        url = search_result.url
        schedule = await professor_parser.get_schedule_from_url(url)
        print(f"Professor: {schedule.person_name}")
        print(f"Academic Year: {schedule.academic_year}")
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
    else:
        print("No search result found")

if __name__ == '__main__':
    asyncio.run(main())
