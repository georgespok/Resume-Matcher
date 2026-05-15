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

_PROSE_SKILL_PREFIX_RE = re.compile(
    r"^(?:.+?\b(?:with|using|including|such as|through)\b|[^:]{1,80}:)\s+",
    re.IGNORECASE,
)
_LEADING_CONJUNCTION_RE = re.compile(r"^(?:and|or)\s+", re.IGNORECASE)
_SKILL_AND_SPLIT_RE = re.compile(r"\s+(?:and|or)\s+", re.IGNORECASE)

_SKILL_CANONICAL_NAMES: dict[str, str] = {
    ".net core": ".NET Core",
    "api management": "API Management",
    "app services": "App Services",
    "application architecture": "Application architecture",
    "application insights": "Application Insights",
    "arm templates": "ARM Templates",
    "asp.net core": "ASP.NET Core",
    "azure ad b2c": "Azure AD B2C",
    "azure boards": "Azure Boards",
    "azure devops pipelines": "Azure DevOps Pipelines",
    "azure functions": "Azure Functions",
    "azure sql": "Azure SQL",
    "bicep": "Bicep",
    "c#": "C#",
    "cosmos db": "Cosmos DB",
    "css": "CSS",
    "docker": "Docker",
    "entity framework": "Entity Framework",
    "git": "Git",
    "html": "HTML",
    "javascript": "JavaScript",
    "jira": "Jira",
    "json": "JSON",
    "key vault": "Key Vault",
    "microservices design": "Microservices design",
    "mongodb": "MongoDB",
    "oauth2": "OAuth2",
    "oracle": "Oracle",
    "react": "React",
    "rest apis": "REST APIs",
    "scrum": "Scrum",
    "service bus": "Service Bus",
    "sql server": "SQL Server",
    "typescript": "TypeScript",
    "vue.js": "Vue.js",
    "web api": "Web API",
}

_CATEGORY_TAXONOMY: list[tuple[str, tuple[str, ...]]] = [
    (
        "Cloud & IaC",
        (
            "azure functions",
            "app services",
            "service bus",
            "api management",
            "key vault",
            "arm templates",
            "bicep",
        ),
    ),
    (
        "Back-end",
        ("c#", ".net core", "asp.net core", "web api", "entity framework"),
    ),
    (
        "Front-end",
        ("vue.js", "angular", "react", "javascript", "typescript", "html", "css"),
    ),
    ("Data", ("oracle", "sql server", "azure sql", "cosmos db", "mongodb")),
    ("DevOps & CI/CD", ("azure devops pipelines", "git", "docker")),
    ("Agile", ("scrum", "jira", "azure boards")),
    (
        "Architecture and Standards",
        (
            "application architecture",
            "n-tier systems",
            "microservices design",
            "sdlc",
            "design patterns",
        ),
    ),
    (
        "Security",
        (
            "oauth2",
            "azure ad b2c",
            "role-based access control",
            "secure api design",
            "managed identity",
        ),
    ),
    ("Integration", ("rest apis", "enterprise system integrations", "json", "xml")),
    (
        "Monitoring and Reliability",
        (
            "application insights",
            "logging",
            "performance tuning",
            "production troubleshooting",
        ),
    ),
]


def _normalize_skill_key(skill: str) -> str:
    """Normalize a skill for matching while preserving stored display text."""
    return re.sub(r"\s+", " ", skill.strip()).casefold()


def _strip_trailing_skill_punctuation(skill: str) -> str:
    """Strip sentence punctuation without damaging leading characters like .NET."""
    return skill.strip().removesuffix(".").strip()


def _canonicalize_skill(skill: str) -> str:
    """Return a stable display name for known skills."""
    cleaned = re.sub(r"\s+", " ", _strip_trailing_skill_punctuation(skill)).strip()
    return _SKILL_CANONICAL_NAMES.get(_normalize_skill_key(cleaned), cleaned)


def _split_skill_phrase(skill: str) -> list[str]:
    """Split prose-like grouped skill text into atomic skill names."""
    phrase = _PROSE_SKILL_PREFIX_RE.sub("", skill.strip()).strip()
    if not phrase:
        return []

    parts: list[str] = []
    for comma_part in re.split(r"[,;]", phrase):
        candidate = _strip_trailing_skill_punctuation(
            _LEADING_CONJUNCTION_RE.sub("", comma_part.strip())
        )
        if not candidate:
            continue

        and_parts = [
            _strip_trailing_skill_punctuation(
                _LEADING_CONJUNCTION_RE.sub("", part.strip())
            )
            for part in _SKILL_AND_SPLIT_RE.split(candidate)
        ]
        parts.extend(part for part in and_parts if part)

    return [_canonicalize_skill(part) for part in parts]


def normalize_technical_skills(skills: list[str]) -> list[str]:
    """Normalize technical skills to concise atomic skill names."""
    normalized: list[str] = []
    seen: set[str] = set()

    for skill in skills:
        split_skills = _split_skill_phrase(skill)
        if not split_skills:
            split_skills = [_canonicalize_skill(skill)]

        for split_skill in split_skills:
            key = _normalize_skill_key(split_skill)
            if key and key not in seen:
                seen.add(key)
                normalized.append(split_skill)

    return normalized


def _known_skill_categories(skills: list[str]) -> list[dict[str, Any]]:
    """Build deterministic categories for known resume technology terms."""
    if not skills:
        return []

    skill_by_key = {_normalize_skill_key(skill): skill for skill in skills}
    used: set[str] = set()
    categories: list[dict[str, Any]] = []

    for category_name, category_keys in _CATEGORY_TAXONOMY:
        category_skills: list[str] = []
        for key in category_keys:
            if key in skill_by_key and key not in used:
                used.add(key)
                category_skills.append(skill_by_key[key])
        if category_skills:
            categories.append({"name": category_name, "skills": category_skills})

    missing_skills = [
        skill for skill in skills if _normalize_skill_key(skill) not in used
    ]
    if missing_skills:
        categories.append({"name": MISSING_SKILLS_CATEGORY_NAME, "skills": missing_skills})

    categorized_count = len(skills) - len(missing_skills)
    if categorized_count < max(3, len(skills) // 2):
        return []

    return categories


def normalize_resume_skill_data(resume_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize skill list and deterministic categories without calling the LLM."""
    result = copy.deepcopy(resume_data)
    additional = result.get("additional")
    if not isinstance(additional, dict):
        return result

    skills = normalize_technical_skills(_extract_flat_skills(result))
    additional["technicalSkills"] = skills
    if not skills:
        additional["skillCategories"] = []
        return result

    categories = _known_skill_categories(skills)
    if categories:
        additional["skillCategories"] = categories

    return result


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

    skills = normalize_technical_skills(skills)
    additional["technicalSkills"] = skills

    known_categories = _known_skill_categories(skills)
    if known_categories:
        additional["skillCategories"] = known_categories
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
