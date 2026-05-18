"""Unit tests for resume schema normalization."""

from app.schemas.models import ResumeData


def test_resume_data_maps_top_level_skills_to_additional_technical_skills() -> None:
    """LLM parse output may put technical skills at the top level."""
    parsed = ResumeData.model_validate(
        {
            "personalInfo": {"name": "Test Candidate"},
            "skills": ["Python", "FastAPI", "Docker"],
        }
    )

    assert parsed.additional.technicalSkills == ["Python", "FastAPI", "Docker"]


def test_resume_data_maps_additional_skills_alias_to_technical_skills() -> None:
    """LLM parse output may use additional.skills instead of technicalSkills."""
    parsed = ResumeData.model_validate(
        {
            "personalInfo": {"name": "Test Candidate"},
            "additional": {"skills": ["React", "TypeScript"]},
        }
    )

    assert parsed.additional.technicalSkills == ["React", "TypeScript"]
