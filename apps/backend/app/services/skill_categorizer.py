"""AI-assisted skill categorization for resume presentation."""

import copy
import json
import logging
import re
from typing import Any

from app.llm import complete_json
from app.prompts import CATEGORIZE_SKILLS_PROMPT, get_language_name

logger = logging.getLogger(__name__)

FALLBACK_CATEGORY_NAME = "Technical Skills"
MISSING_SKILLS_CATEGORY_NAME = "Other Skills"


def _normalize_skill_key(skill: str) -> str:
    """Normalize a skill for matching while preserving stored display text."""
    return re.sub(r"\s+", " ", skill.strip()).casefold()


def _coerce_skill_list(value: Any) -> list[str]:
    """Return clean string skills from loosely structured input."""
    if not isinstance(value, list):
        return []
    skills: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        skill = item.strip()
        if skill:
            skills.append(skill)
    return skills


def _extract_flat_skills(resume_data: dict[str, Any]) -> list[str]:
    """Extract canonical flat technical skills from resume data."""
    additional = resume_data.get("additional", {})
    if not isinstance(additional, dict):
        return _coerce_skill_list(resume_data.get("technicalSkills", []))
    skills = _coerce_skill_list(additional.get("technicalSkills", []))
    return skills or _coerce_skill_list(resume_data.get("technicalSkills", []))


def _fallback_categories(
    skills: list[str],
    category_name: str = FALLBACK_CATEGORY_NAME,
) -> list[dict[str, Any]]:
    """Build a deterministic one-category fallback."""
    if not skills:
        return []
    return [{"name": category_name, "skills": list(skills)}]


def _build_resume_context(resume_data: dict[str, Any]) -> dict[str, Any]:
    """Build limited context that helps the LLM choose category names."""
    personal_info = resume_data.get("personalInfo", {})
    if not isinstance(personal_info, dict):
        personal_info = {}

    work_titles: list[str] = []
    for entry in resume_data.get("workExperience", []):
        if not isinstance(entry, dict):
            continue
        title = entry.get("title")
        if isinstance(title, str) and title.strip():
            work_titles.append(title.strip())

    project_names: list[str] = []
    for entry in resume_data.get("personalProjects", []):
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if isinstance(name, str) and name.strip():
            project_names.append(name.strip())

    return {
        "title": str(personal_info.get("title", "")).strip(),
        "summary": str(resume_data.get("summary", "")).strip(),
        "work_titles": work_titles[:5],
        "project_names": project_names[:5],
    }


def validate_skill_categories(
    raw_categories: Any,
    original_skills: list[str],
    missing_category_name: str = MISSING_SKILLS_CATEGORY_NAME,
) -> tuple[list[dict[str, Any]], bool]:
    """Validate category data against the canonical flat skill list.

    Returns:
        A tuple of ``(categories, is_exact)``. ``is_exact`` is true only when
        the input categories already used every original skill exactly once and
        did not include unsupported skills.
    """
    skills = _coerce_skill_list(original_skills)
    if not skills:
        return [], True
    if not isinstance(raw_categories, list):
        return _fallback_categories(skills, missing_category_name), False

    entries: list[dict[str, Any]] = [
        {"key": _normalize_skill_key(skill), "skill": skill, "used": False}
        for skill in skills
    ]
    categories: list[dict[str, Any]] = []
    dropped_unsupported = False

    for raw_category in raw_categories:
        if not isinstance(raw_category, dict):
            dropped_unsupported = True
            continue

        name = str(raw_category.get("name", "")).strip() or missing_category_name
        category_skills: list[str] = []

        for raw_skill in _coerce_skill_list(raw_category.get("skills", [])):
            key = _normalize_skill_key(raw_skill)
            matched_entry = next(
                (
                    entry
                    for entry in entries
                    if entry["key"] == key and not bool(entry["used"])
                ),
                None,
            )
            if matched_entry is None:
                dropped_unsupported = True
                continue
            matched_entry["used"] = True
            category_skills.append(str(matched_entry["skill"]))

        if category_skills:
            categories.append({"name": name, "skills": category_skills})

    missing_skills = [str(entry["skill"]) for entry in entries if not bool(entry["used"])]
    if missing_skills:
        categories.append({"name": missing_category_name, "skills": missing_skills})

    if not categories:
        return _fallback_categories(skills), False

    return categories, not dropped_unsupported and not missing_skills


async def categorize_resume_skills(
    resume_data: dict[str, Any],
    language: str = "en",
) -> dict[str, Any]:
    """Return resume data with derived skill categories.

    Categorization is best-effort. Failures fall back to a deterministic single
    category and never fail the parent resume operation.
    """
    result = copy.deepcopy(resume_data)
    additional = result.get("additional")
    if not isinstance(additional, dict):
        additional = {}
        result["additional"] = additional

    skills = _extract_flat_skills(result)
    if not skills:
        additional["skillCategories"] = []
        return result

    existing_categories, existing_is_current = validate_skill_categories(
        additional.get("skillCategories"),
        skills,
    )
    if existing_is_current and existing_categories:
        additional["skillCategories"] = existing_categories
        return result

    output_language = get_language_name(language)
    prompt = CATEGORIZE_SKILLS_PROMPT.format(
        output_language=output_language,
        skills=json.dumps(skills, ensure_ascii=False),
        resume_context=json.dumps(_build_resume_context(result), ensure_ascii=False),
    )

    try:
        response = await complete_json(
            prompt=prompt,
            system_prompt=(
                "You categorize resume skills for presentation. Output only valid "
                "JSON and preserve input skill text exactly."
            ),
            max_tokens=1536,
            retries=2,
            schema_type="diff",
        )
        categories, _ = validate_skill_categories(response.get("categories"), skills)
    except Exception as e:
        logger.warning("Skill categorization failed; using fallback categories: %s", e)
        categories = _fallback_categories(skills)

    additional["skillCategories"] = categories or _fallback_categories(skills)
    return result
