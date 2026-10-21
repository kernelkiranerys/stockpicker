def build_lessons_context(limit=10):
    """Build a context string from recent lessons to inject into AI expert prompts."""
    from feedback.weekly_review import get_active_lessons
    lessons = get_active_lessons(limit)
    if not lessons:
        return ""
    lines = ["## Past Lessons (Avoid These Mistakes)"]
    for lesson in lessons:
        lines.append(f"- [{lesson.ticker_symbol}] {lesson.lesson}")
    return "\n".join(lines)