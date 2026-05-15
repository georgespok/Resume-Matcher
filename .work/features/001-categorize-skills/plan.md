# Feature 001: Categorize Skills

## Goal

Present resume skills grouped by AI-generated categories in resume previews and exported documents, while keeping the existing flat `additional.technicalSkills` list as the canonical data source for matching, diffing, regeneration, and refinement.

## Non-Goals

- No editor UI for manually creating, renaming, or moving skill categories.
- No replacement of `additional.technicalSkills`.
- No change to job matching, diff review, or skill verification logic beyond preserving categorized presentation data.
- No changes to CI, Docker behavior, or GitHub workflow files.

## Data Model Direction

Add derived presentation metadata under `additional`:

```json
{
  "technicalSkills": ["Python", "TypeScript", "AWS", "Docker"],
  "skillCategories": [
    {
      "name": "Programming Languages",
      "skills": ["Python", "TypeScript"]
    },
    {
      "name": "Cloud & DevOps",
      "skills": ["AWS", "Docker"]
    }
  ]
}
```

`technicalSkills` remains the source of truth. `skillCategories` is regenerated from it and can be safely discarded or rebuilt.

## Phase 1: Backend Schema

Add backend schema support for categorized skills without breaking existing resumes.

Deliverables:

- Add a `SkillCategory` Pydantic model.
- Add `skillCategories` to `AdditionalInfo`.
- Normalize category names and skill arrays.
- Ensure old resumes without `skillCategories` still validate.

## Phase 2: AI Categorization Service

Create a backend service that asks the configured LLM to categorize the existing skills list.

Deliverables:

- Add a category prompt in `apps/backend/app/prompts/templates.py`.
- Add `apps/backend/app/services/skill_categorizer.py`.
- Use `complete_json` for structured output.
- Pass only the flat skill list and limited resume context.
- Request concise category names in the configured output language.

## Phase 3: Deterministic Validation And Fallback

Validate AI output before storing or returning it.

Rules:

- Every original skill must appear exactly once across all categories.
- Skill casing and spelling must match `technicalSkills`.
- Hallucinated skills are dropped.
- Duplicate categorized skills are ignored after first use.
- Missing original skills are appended to a fallback category.
- If AI categorization fails, produce one category containing all flat skills.

## Phase 4: Backend Pipeline Integration

Regenerate categories whenever backend code creates or mutates resume skill data.

Integration points:

- Resume upload parse flow after `parse_resume_to_json`.
- Improve preview flow after refinement and safety checks.
- Improve confirm flow before saving tailored resume data.
- Direct resume update endpoint before persisting `processed_data`.
- Regeneration apply flow after replacing `additional.technicalSkills`.

Failure behavior:

- Categorization must not fail the parent operation.
- Log detailed errors server-side.
- Use deterministic fallback categories when categorization cannot complete.

## Phase 5: Frontend Types

Expose the new backend field to TypeScript without changing editor behavior.

Deliverables:

- Add `skillCategories?: SkillCategory[]` to resume API and UI types.
- Keep existing form fields bound to `technicalSkills`.
- Do not add category editing controls.

## Phase 6: Resume Rendering

Update document renderers so Skills are formatted by category when valid categories exist.

Deliverables:

- Add a shared skill rendering helper or component.
- Render categorized skills when `additional.skillCategories` has usable data.
- Fall back to the current flat `technicalSkills` display.
- Update single-column and two-column resume templates.
- Preserve Swiss International Style: hard structure, black text, no decorative cards.

## Phase 7: PDF And Print Verification

Verify that print/PDF output uses the same categorized presentation.

Deliverables:

- Confirm print routes consume the updated resume components.
- Verify categorized resumes render correctly.
- Verify uncategorized legacy resumes still render as flat skills.

## Phase 8: Tests And Quality Gates

Add targeted test coverage around the new derived data and renderer behavior.

Backend checks:

- Unit tests for category validation.
- Unit tests for fallback behavior.
- Mocked service tests for AI categorization.
- Endpoint or service tests proving categories are generated after write flows.

Frontend checks:

- Rendering test for categorized skills.
- Rendering test for flat fallback.
- `npm run lint`.
- `npm run format`.

## Acceptance Criteria

- Tailored resume preview responses include both `additional.technicalSkills` and `additional.skillCategories`.
- Saved tailored resumes persist categorized skills.
- Uploaded and manually updated resumes receive categories when skills exist.
- Resume preview and PDF output display Skills grouped by category when categories exist.
- Legacy resumes without categories still render correctly.
- Existing matching, diffing, refinement, and regeneration behavior continues to use flat `technicalSkills`.
