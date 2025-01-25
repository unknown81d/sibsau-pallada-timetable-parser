import logging
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)


@dataclass
class Lesson:
    time: str
    name: str
    place: str
    groups: List[str] = field(default_factory=list)
    subgroup: Optional[str] = None
    type: Optional[str] = None


@dataclass
class DaySchedule:
    day_name: str
    lessons: List[Lesson] = field(default_factory=list)


@dataclass
class WeekSchedule:
    week_number: int
    days: List[DaySchedule] = field(default_factory=list)


@dataclass
class SessionSchedule:
    days: List[DaySchedule] = field(default_factory=list)

@dataclass
class ConsultationSchedule:
    days: List[DaySchedule] = field(default_factory=list)


@dataclass
class Schedule:
    person_name: str
    academic_year: str
    weeks: List[WeekSchedule] = field(default_factory=list)
    session: Optional[SessionSchedule] = None
    consultations: Optional[ConsultationSchedule] = None


def _parse_schedule(html_content: str) -> Schedule:
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract professor name and academic year
    title_element = soup.find('h3', class_='text-center bold')
    if not title_element:
        raise ValueError("Could not find title element")

    title_text = title_element.get_text(strip=True)
    parts = title_text.split('-')
    if len(parts) != 2:
        raise ValueError(f"Unexpected title format: {title_text}")

    person_name = parts[0].strip()
    academic_year = parts[1].strip()

    schedule = Schedule(person_name=person_name, academic_year=academic_year)

    # Find all week tabs
    week_tabs = soup.select('ul.nav.nav-pills.navbar-right.n_week li a')

    for week_tab in week_tabs:
        week_number = int(week_tab.text.split()[0])
        week_id = week_tab['href'].replace('#', '')
        week_schedule = WeekSchedule(week_number=week_number)

        # Find the corresponding week content
        week_content = soup.find('div', id=week_id)
        if week_content:
            # Find all days within the week
            day_divs = week_content.find_all('div', class_=lambda x: x and 'day' in x)
            for day_div in day_divs:
                day_name = day_div.find('div', class_='name text-center').text.strip().split()[0]
                day_schedule = DaySchedule(day_name=day_name)

                # Find all lessons within the day
                lesson_lines = day_div.find('div', class_='body').find_all('div', class_='line')
                for lesson_line in lesson_lines:
                    time_div = lesson_line.find('div', class_='time text-center')
                    time = time_div.find(class_="hidden-xs").text.strip().replace("\n", "") if time_div.find(
                        class_="hidden-xs") else time_div.find(class_="visible-xs").text.strip().replace("\n",
                                                                                                         "").replace(
                        "<br>", "-")

                    discipline_div = lesson_line.find('div', class_='discipline')
                    name = discipline_div.find('span', class_='name').text.strip() if discipline_div.find('span',
                                                                                                          class_='name') else 'N/A'
                    place_link = discipline_div.find('a', title=True)
                    place_separator = " / "
                    if place_link:
                        place_title = place_link['title']
                        place_text = place_link.text
                        place = f"{place_title}{place_separator}{place_text}"
                    else:
                        place = 'N/A'

                    group_links = discipline_div.find_all('a', href=re.compile(r'/timetable/group/\d+'))
                    groups = [link.text.strip() for link in group_links]

                    subgroup_element = discipline_div.find('li', class_='bold num_pdgrp')
                    subgroup = subgroup_element.text.strip() if subgroup_element else None
                    lesson_type_element = discipline_div.find('li')
                    lesson_type = lesson_type_element.text.strip().split('(')[1].replace(')', '') if lesson_type_element and '(' in lesson_type_element.text else None


                    lesson = Lesson(time=time, name=name, place=place, groups=groups, subgroup=subgroup, type=lesson_type)
                    day_schedule.lessons.append(lesson)

                week_schedule.days.append(day_schedule)

        schedule.weeks.append(week_schedule)

    # Parse session schedule
    session_tab = soup.find('div', id='session_tab')
    if session_tab:
        session_schedule = SessionSchedule()
        day_divs = session_tab.find_all('div', class_='day')
        for day_div in day_divs:
            day_name = day_div.find('div', class_='name text-center').text.strip().split()[0]
            day_schedule = DaySchedule(day_name=day_name)

            lesson_lines = day_div.find('div', class_='body').find_all('div', class_='line')
            for lesson_line in lesson_lines:
                time_div = lesson_line.find('div', class_='time text-center')
                if time_div:
                    time_text_element = time_div.find('div')
                    if time_text_element:
                        time = time_text_element.get_text(strip=True).strip()
                        time = time.split(' ')[-1]
                    else:
                        time = ""
                else:
                    time = ""
                # 9.01.2025 11:15 fix for single time

                discipline_div = lesson_line.find('div', class_='discipline')
                name = discipline_div.find('span', class_='name').text.strip() if discipline_div.find('span',
                                                                                                      class_='name') else 'N/A'
                place_link = discipline_div.find('a', title=True)
                place_separator = " / "
                if place_link:
                    place_title = place_link['title']
                    place_text = place_link.text
                    place = f"{place_title}{place_separator}{place_text}"
                else:
                    place = 'N/A'

                group_links = discipline_div.find_all('a', href=re.compile(r'/timetable/group/\d+'))
                groups = [link.text.strip() for link in group_links]

                lesson_type_element = discipline_div.find('li')
                lesson_type = lesson_type_element.text.strip().split('(')[1].replace(')', '') if lesson_type_element and '(' in lesson_type_element.text else None


                lesson = Lesson(time=time, name=name, place=place, groups=groups, type = lesson_type)
                day_schedule.lessons.append(lesson)
            session_schedule.days.append(day_schedule)
        schedule.session = session_schedule


    # Parse consultation schedule
    consultation_tab = soup.find('div', id='consultation_tab')
    if consultation_tab:
        consultation_schedule = ConsultationSchedule()
        day_divs = consultation_tab.find_all('div', class_='day')
        for day_div in day_divs:
            day_name = day_div.find('div', class_='name text-center').text.strip().split()[0]
            day_schedule = DaySchedule(day_name=day_name)

            lesson_lines = day_div.find('div', class_='body').find_all('div', class_='line')
            for lesson_line in lesson_lines:
                time_div = lesson_line.find('div', class_='time text-center')
                time = time_div.find(class_="hidden-xs").text.strip().replace("\n", "") if time_div.find(
                    class_="hidden-xs") else time_div.find(class_="visible-xs").text.strip().replace("\n", "").replace(
                    "<br>", "-")
                discipline_div = lesson_line.find('div', class_='discipline')

                place_link = discipline_div.find('a', title=True)
                place_separator = " / "
                if place_link:
                    place_title = place_link['title']
                    place_text = place_link.text
                    place = f"{place_title}{place_separator}{place_text}"
                else:
                    place = 'N/A'

                name = 'Консультация'

                lesson = Lesson(time=time, name=name, place=place)
                day_schedule.lessons.append(lesson)

            consultation_schedule.days.append(day_schedule)
        schedule.consultations = consultation_schedule

    return schedule


def get_schedule_from_url(url: str) -> Schedule:
    """
    Fetches HTML content from a URL and parses it to extract schedule data.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return _parse_schedule(response.text)
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch URL: {e}")

