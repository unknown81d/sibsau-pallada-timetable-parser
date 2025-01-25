import logging
import asyncio
import aiohttp
from typing import Optional, List, Dict, TypedDict
from rapidfuzz import fuzz

import group_parser
import professor_parser

logger = logging.getLogger(__name__)

# Constants for ID ranges
PROFESSOR_ID_START = 13500
PROFESSOR_ID_END = 13508
GROUP_ID_START = 3099
GROUP_ID_END = 3110

# Minimum similarity percentage (0-100) required for a match to be considered valid
MINIMUM_SIMILARITY_PERCENTAGE: int = 30

class SearchResultDict(TypedDict):
    name: str
    type: str
    id: int
    url: str

class SearchResult:
    def __init__(self, name: str, type: str, id: int, url: str):
        self.name = name
        self.type = type
        self.id = id
        self.url = url

    def __repr__(self) -> str:
        return f"SearchResult(name='{self.name}', type='{self.type}', id={self.id}, url='{self.url}')"

    def to_dict(self) -> SearchResultDict:
        """Convert SearchResult to dictionary format"""
        return {
            "name": self.name,
            "type": self.type,
            "id": self.id,
            "url": self.url
        }

async def fetch_database() -> List[SearchResultDict]:
    """
    Asynchronously creates and returns a database of groups and professors.
    """
    data: List[SearchResultDict] = []

    async def fetch_group(id: int):
        url = f"https://timetable.pallada.sibsau.ru/timetable/group/{id}"
        try:
            schedule = await group_parser.get_schedule_from_url(url)
            return SearchResultDict(
                name=schedule.group_name,
                type="group",
                id=id,
                url=url
            )
        except Exception as e:
            logger.warning(f"Error fetching group {id}: {str(e)}")
            return None

    async def fetch_professor(id: int):
        url = f"https://timetable.pallada.sibsau.ru/timetable/professor/{id}"
        try:
            schedule = await professor_parser.get_schedule_from_url(url)
            return SearchResultDict(
                name=schedule.person_name,
                type="professor",
                id=id,
                url=url
            )
        except Exception as e:
            logger.warning(f"Error fetching professor {id}: {str(e)}")
            return None

    # Create tasks for all fetches
    tasks = []
    for id in range(PROFESSOR_ID_START, PROFESSOR_ID_END):
        tasks.append(fetch_group(id))
    for id in range(GROUP_ID_START, GROUP_ID_END):
        tasks.append(fetch_professor(id))

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out None results and exceptions
    data = [r for r in results if isinstance(r, dict)]

    return data

# Keep the synchronous version for compatibility
def fetch_database_sync() -> List[SearchResultDict]:
    """
    Synchronously creates and returns a database of groups and professors.
    """
    data: List[SearchResultDict] = []

    for id in range(PROFESSOR_ID_START, PROFESSOR_ID_END):
        url = f"https://timetable.pallada.sibsau.ru/timetable/group/{id}"
        try:
            schedule = group_parser.get_schedule_from_url_sync(url)
            data.append(SearchResultDict(
                name=schedule.group_name,
                type="group",
                id=id,
                url=url
            ))
        except Exception as e:
            logger.warning(f"Error fetching group {id}: {str(e)}")
            continue

    for id in range(GROUP_ID_START, GROUP_ID_END):
        url = f"https://timetable.pallada.sibsau.ru/timetable/professor/{id}"
        try:
            schedule = professor_parser.get_schedule_from_url_sync(url)
            data.append(SearchResultDict(
                name=schedule.person_name,
                type="professor",
                id=id,
                url=url
            ))
        except Exception as e:
            logger.warning(f"Error fetching professor {id}: {str(e)}")
            continue

    return data

# Mapping for transliteration
CYRILLIC_TO_LATIN: Dict[str, str] = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

def transliterate(text: str) -> str:
    """
    Transliterate text from Cyrillic to Latin characters.
    """
    return ''.join(CYRILLIC_TO_LATIN.get(char, char) for char in text.lower())

def get_by_search_query(data: List[SearchResultDict], query: str) -> Optional[SearchResult]:
    """
    Search for data in the list using fuzzy string matching.
    """
    if not query or not data:
        return None

    best_match_score = 0
    best_match_record = None
    query_lower = query.lower()
    latin_query = transliterate(query_lower)

    for record in data:
        name = record['name'].lower()

        # Check for exact match first
        if query_lower == name:
            return SearchResult(**record)

        # Apply fuzzy matching
        latin_name = transliterate(name)
        score = max(
            fuzz.ratio(query_lower, name),
            fuzz.ratio(latin_query, latin_name)
        )

        if score > best_match_score:
            best_match_score = score
            best_match_record = record

    if best_match_record and best_match_score > MINIMUM_SIMILARITY_PERCENTAGE:
        return SearchResult(**best_match_record)

    return None
