import logging
import aiohttp
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re
from pathlib import Path
import json
import uuid
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Lesson:
    time: str
    name: str
    professor: str
    place: str
    subgroup: Optional[str] = None

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

class SourceType(Enum):
    PROXY = "PROXY" # From filesystem cache
    RAW = "RAW"     # From network request

@dataclass
class Schedule:
    group_name: str
    semester: str
    weeks: List[WeekSchedule] = field(default_factory=list)
    session: Optional[SessionSchedule] = None
    source: SourceType = field(default=SourceType.RAW)

async def _parse_schedule(html_content: str) -> Schedule:
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract group name and semester info
    title_element = soup.find('h3', class_='text-center bold')
    if not title_element:
        raise ValueError("Could not find title element")

    title_text = title_element.get_text(strip=True)
    parts = title_text.split('"')
    if len(parts) != 3:
        raise ValueError(f"Unexpected title format: {title_text}")

    group_name = parts[1]
    semester = parts[2].strip()
    semester = re.sub(r'г\.', '', semester).strip()

    schedule = Schedule(group_name=group_name, semester=semester)

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
                    professor_link = discipline_div.find('a')
                    professor = professor_link.text.strip() if professor_link else 'N/A'

                    place_link = discipline_div.find('a', title=True)
                    place_separator = " / "
                    if place_link:
                        place_title = place_link['title']
                        place_text = place_link.text
                        place = f"{place_title}{place_separator}{place_text}"
                    else:
                        place = 'N/A'

                    subgroup_element = discipline_div.find('li', class_='bold num_pdgrp')
                    subgroup = subgroup_element.text.strip() if subgroup_element else None

                    lesson = Lesson(time=time, name=name, professor=professor, place=place, subgroup=subgroup)
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
                professor_link = discipline_div.find('a')
                professor = professor_link.text.strip() if professor_link else 'N/A'

                place_link = discipline_div.find('a', title=True)
                place_separator = " / "
                if place_link:
                    place_title = place_link['title']
                    place_text = place_link.text
                    place = f"{place_title}{place_separator}{place_text}"
                else:
                    place = 'N/A'

                subgroup_element = discipline_div.find('li', class_='bold num_pdgrp')
                subgroup = subgroup_element.text.strip() if subgroup_element else None
                lesson = Lesson(time=time, name=name, professor=professor, place=place, subgroup=subgroup)
                day_schedule.lessons.append(lesson)
            session_schedule.days.append(day_schedule)
        schedule.session = session_schedule

    return schedule

def _parse_schedule_sync(html_content: str) -> Schedule:
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract group name and semester info
    title_element = soup.find('h3', class_='text-center bold')
    if not title_element:
        raise ValueError("Could not find title element")

    title_text = title_element.get_text(strip=True)
    parts = title_text.split('"')
    if len(parts) != 3:
        raise ValueError(f"Unexpected title format: {title_text}")

    group_name = parts[1]
    semester = parts[2].strip()
    semester = re.sub(r'г\.', '', semester).strip()

    schedule = Schedule(group_name=group_name, semester=semester)

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
                    professor_link = discipline_div.find('a')
                    professor = professor_link.text.strip() if professor_link else 'N/A'

                    place_link = discipline_div.find('a', title=True)
                    place_separator = " / "
                    if place_link:
                        place_title = place_link['title']
                        place_text = place_link.text
                        place = f"{place_title}{place_separator}{place_text}"
                    else:
                        place = 'N/A'

                    subgroup_element = discipline_div.find('li', class_='bold num_pdgrp')
                    subgroup = subgroup_element.text.strip() if subgroup_element else None

                    lesson = Lesson(time=time, name=name, professor=professor, place=place, subgroup=subgroup)
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
                professor_link = discipline_div.find('a')
                professor = professor_link.text.strip() if professor_link else 'N/A'

                place_link = discipline_div.find('a', title=True)
                place_separator = " / "
                if place_link:
                    place_title = place_link['title']
                    place_text = place_link.text
                    place = f"{place_title}{place_separator}{place_text}"
                else:
                    place = 'N/A'

                subgroup_element = discipline_div.find('li', class_='bold num_pdgrp')
                subgroup = subgroup_element.text.strip() if subgroup_element else None
                lesson = Lesson(time=time, name=name, professor=professor, place=place, subgroup=subgroup)
                day_schedule.lessons.append(lesson)
            session_schedule.days.append(day_schedule)
        schedule.session = session_schedule

    return schedule

def _generate_cache_filename(url: str) -> str:
    """Generate a unique filename for caching"""
    unique_id = str(uuid.uuid4())[:8]
    return f"group_{unique_id}.json"

def _save_schedule_to_cache(schedule: Schedule, directory: Path, filename: str):
    """Save schedule to cache file"""
    cache_path = directory / filename
    with open(cache_path, 'w', encoding='utf-8') as f:
        # Convert schedule to dict for JSON serialization
        data = {
            'group_name': schedule.group_name,
            'semester': schedule.semester,
            'weeks': [{'week_number': w.week_number,
                      'days': [{'day_name': d.day_name,
                               'lessons': [vars(l) for l in d.lessons]}
                              for d in w.days]}
                     for w in schedule.weeks],
            'session': {'days': [{'day_name': d.day_name,
                                'lessons': [vars(l) for l in d.lessons]}
                               for d in schedule.session.days]} if schedule.session else None,
            'source': schedule.source.value
        }
        json.dump(data, f, ensure_ascii=False, indent=2)

def _load_schedule_from_cache(cache_path: Path) -> Schedule:
    """Load schedule from cache file"""
    with open(cache_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        schedule = Schedule(
            group_name=data['group_name'],
            semester=data['semester'],
            source=SourceType.PROXY
        )

        # Reconstruct weeks
        for week_data in data['weeks']:
            week = WeekSchedule(week_number=week_data['week_number'])
            for day_data in week_data['days']:
                day = DaySchedule(day_name=day_data['day_name'])
                for lesson_data in day_data['lessons']:
                    lesson = Lesson(**lesson_data)
                    day.lessons.append(lesson)
                week.days.append(day)
            schedule.weeks.append(week)

        # Reconstruct session if exists
        if data['session']:
            session = SessionSchedule()
            for day_data in data['session']['days']:
                day = DaySchedule(day_name=day_data['day_name'])
                for lesson_data in day_data['lessons']:
                    lesson = Lesson(**lesson_data)
                    day.lessons.append(lesson)
                session.days.append(day)
            schedule.session = session

        return schedule

async def get_schedule_from_url(url: str, directory: Optional[str] = None) -> Schedule:
    """
    Fetches schedule from URL or loads from cache if available.
    If directory is provided, will try to load from cache first, otherwise fetch from network.
    Returns Schedule object with source indicating whether it came from cache (PROXY) or network (RAW).
    """
    if directory:
        cache_dir = Path(directory)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_files = list(cache_dir.glob("group_*.json"))

        if cache_files:
            # Load from cache if available
            return _load_schedule_from_cache(cache_files[0])

    # Fetch from network
    conn = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                html_content = await response.text()
                schedule = await _parse_schedule(html_content)
                schedule.source = SourceType.RAW

                # Save to cache if directory provided
                if directory:
                    filename = _generate_cache_filename(url)
                    _save_schedule_to_cache(schedule, Path(directory), filename)

                return schedule
        except aiohttp.ClientError as e:
            raise Exception(f"Failed to fetch URL: {e}")

def get_schedule_from_url_sync(url: str, directory: Optional[str] = None) -> Schedule:
    """
    Synchronous version of get_schedule_from_url.
    """
    import requests

    if directory:
        cache_dir = Path(directory)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_files = list(cache_dir.glob("group_*.json"))

        if cache_files:
            return _load_schedule_from_cache(cache_files[0])

    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        schedule = _parse_schedule_sync(response.text)
        schedule.source = SourceType.RAW

        if directory:
            filename = _generate_cache_filename(url)
            _save_schedule_to_cache(schedule, Path(directory), filename)

        return schedule
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch URL: {e}")

