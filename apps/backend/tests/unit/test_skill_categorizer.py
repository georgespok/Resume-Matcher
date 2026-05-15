"""Unit tests for AI-assisted skill categorization."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.skill_categorizer import (
    categorize_resume_skills,
    validate_skill_categories,
)


def test_validate_skill_categories_accepts_exact_categories() -> None:
    categories, is_exact = validate_skill_categories(
        [
            {"name": "Languages", "skills": ["python", "TypeScript"]},
            {"name": "Cloud", "skills": ["AWS"]},
        ],
        ["Python", "TypeScript", "AWS"],
    )

    assert is_exact is True
    assert categories == [
        {"name": "Languages", "skills": ["Python", "TypeScript"]},
        {"name": "Cloud", "skills": ["AWS"]},
    ]


def test_validate_skill_categories_drops_hallucinated_skills() -> None:
    categories, is_exact = validate_skill_categories(
        [{"name": "Backend", "skills": ["Python", "BananaDB"]}],
        ["Python"],
    )

    assert is_exact is False
    assert categories == [{"name": "Backend", "skills": ["Python"]}]


def test_validate_skill_categories_deduplicates_repeated_skills() -> None:
    categories, is_exact = validate_skill_categories(
        [
            {"name": "Backend", "skills": ["Python"]},
            {"name": "Languages", "skills": ["Python", "Python"]},
        ],
        ["Python"],
    )

    assert is_exact is False
    assert categories == [{"name": "Backend", "skills": ["Python"]}]


def test_validate_skill_categories_appends_missing_skills() -> None:
    categories, is_exact = validate_skill_categories(
        [{"name": "Languages", "skills": ["Python"]}],
        ["Python", "Docker"],
    )

    assert is_exact is False
    assert categories == [
        {"name": "Languages", "skills": ["Python"]},
        {"name": "Other Skills", "skills": ["Docker"]},
    ]


@pytest.mark.asyncio
@patch("app.services.skill_categorizer.complete_json", new_callable=AsyncMock)
async def test_categorize_resume_skills_uses_ai_categories(mock_complete_json) -> None:
    mock_complete_json.return_value = {
        "categories": [
            {"name": "Languages", "skills": ["python"]},
            {"name": "Cloud & DevOps", "skills": ["Docker", "AWS"]},
        ]
    }
    resume_data = {
        "personalInfo": {"title": "Backend Engineer"},
        "summary": "Builds APIs.",
        "additional": {"technicalSkills": ["Python", "Docker", "AWS"]},
    }

    result = await categorize_resume_skills(resume_data, language="en")

    assert result["additional"]["skillCategories"] == [
        {"name": "Languages", "skills": ["Python"]},
        {"name": "Cloud & DevOps", "skills": ["Docker", "AWS"]},
    ]
    assert result["additional"]["technicalSkills"] == ["Python", "Docker", "AWS"]
    mock_complete_json.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.skill_categorizer.complete_json", new_callable=AsyncMock)
async def test_categorize_resume_skills_preserves_current_existing_categories(
    mock_complete_json,
) -> None:
    resume_data = {
        "additional": {
            "technicalSkills": ["Python", "Docker"],
            "skillCategories": [
                {"name": "Languages", "skills": ["Python"]},
                {"name": "DevOps", "skills": ["Docker"]},
            ],
        }
    }

    result = await categorize_resume_skills(resume_data, language="en")

    assert result["additional"]["skillCategories"] == [
        {"name": "Languages", "skills": ["Python"]},
        {"name": "DevOps", "skills": ["Docker"]},
    ]
    mock_complete_json.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.skill_categorizer.complete_json", new_callable=AsyncMock)
async def test_categorize_resume_skills_falls_back_when_ai_fails(
    mock_complete_json,
) -> None:
    mock_complete_json.side_effect = RuntimeError("LLM unavailable")
    resume_data = {"additional": {"technicalSkills": ["Python", "Docker"]}}

    result = await categorize_resume_skills(resume_data, language="en")

    assert result["additional"]["skillCategories"] == [
        {"name": "Technical Skills", "skills": ["Python", "Docker"]}
    ]


@pytest.mark.asyncio
@patch("app.services.skill_categorizer.complete_json", new_callable=AsyncMock)
async def test_categorize_resume_skills_splits_sentence_like_skill_groups(
    mock_complete_json,
) -> None:
    resume_data = {
        "additional": {
            "technicalSkills": [
                (
                    "Built backend services with C#, .NET Core, ASP.NET Core, "
                    "Entity Framework, REST APIs, Web API, JSON, and OAuth2"
                ),
                (
                    "Developed frontend applications using JavaScript, TypeScript, "
                    "Angular, React, Vue.js, HTML, and CSS"
                ),
                (
                    "Delivered Azure cloud solutions with Azure Functions, App Services, "
                    "Azure DevOps Pipelines, ARM Templates, Bicep, Key Vault, and Application Insights"
                ),
                (
                    "Designed data and messaging solutions with Service Bus, Cosmos DB, "
                    "MongoDB, SQL Server, Azure SQL, and Oracle"
                ),
                (
                    "Architected scalable application and microservices solutions with "
                    "application architecture and microservices design"
                ),
                (
                    "Secured and managed APIs with Azure AD B2C, API Management, "
                    "OAuth2, and Application Insights"
                ),
                "Streamlined delivery with Git, Docker, Scrum, Jira, and Azure Boards",
            ]
        }
    }

    result = await categorize_resume_skills(resume_data, language="en")

    assert "Designed data and messaging solutions with Service Bus" not in result["additional"][
        "technicalSkills"
    ]
    assert "Service Bus" in result["additional"]["technicalSkills"]
    assert "Cosmos DB" in result["additional"]["technicalSkills"]
    assert "Oracle" in result["additional"]["technicalSkills"]
    assert result["additional"]["skillCategories"] == [
        {
            "name": "Cloud & IaC",
            "skills": [
                "Azure Functions",
                "App Services",
                "Service Bus",
                "API Management",
                "Key Vault",
                "ARM Templates",
                "Bicep",
            ],
        },
        {
            "name": "Back-end",
            "skills": [
                "C#",
                ".NET Core",
                "ASP.NET Core",
                "Web API",
                "Entity Framework",
            ],
        },
        {
            "name": "Front-end",
            "skills": [
                "Vue.js",
                "Angular",
                "React",
                "JavaScript",
                "TypeScript",
                "HTML",
                "CSS",
            ],
        },
        {
            "name": "Data",
            "skills": ["Oracle", "SQL Server", "Azure SQL", "Cosmos DB", "MongoDB"],
        },
        {
            "name": "DevOps & CI/CD",
            "skills": ["Azure DevOps Pipelines", "Git", "Docker"],
        },
        {"name": "Agile", "skills": ["Scrum", "Jira", "Azure Boards"]},
        {
            "name": "Architecture and Standards",
            "skills": ["Application architecture", "Microservices design"],
        },
        {"name": "Security", "skills": ["OAuth2", "Azure AD B2C"]},
        {"name": "Integration", "skills": ["REST APIs", "JSON"]},
        {"name": "Monitoring and Reliability", "skills": ["Application Insights"]},
    ]
    assert all(
        category["name"] != "Data & Messaging"
        for category in result["additional"]["skillCategories"]
    )
    mock_complete_json.assert_not_awaited()
