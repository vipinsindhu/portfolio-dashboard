"""
Educational content engine for Learn tab
Provides interactive lessons on common investing pitfalls
Loads lessons from lessons.json for easy updates without code changes
"""

import json
import os

def load_lessons():
    """Load lessons from JSON file"""
    lessons_file = os.path.join(os.path.dirname(__file__), 'lessons.json')
    try:
        with open(lessons_file, 'r') as f:
            data = json.load(f)
            return data.get('lessons', [])
    except Exception as e:
        print(f"Error loading lessons from {lessons_file}: {e}")
        return []

LESSONS = load_lessons()


def get_all_lessons():
    """Return all lessons"""
    return LESSONS


def get_lesson_by_id(lesson_id: str):
    """Get single lesson by ID"""
    for lesson in LESSONS:
        if lesson["id"] == lesson_id:
            return lesson
    return None


def get_lessons_by_category(category: str):
    """Get all lessons in a category"""
    return [l for l in LESSONS if l["category"] == category]


def get_lesson_categories():
    """Get unique categories"""
    return sorted(set(l["category"] for l in LESSONS))


def get_difficulty_levels():
    """Get unique difficulty levels"""
    return sorted(set(l["difficulty"] for l in LESSONS))
