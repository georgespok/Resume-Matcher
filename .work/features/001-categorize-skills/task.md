# Feature 001 Tasks: Categorize Skills

1. Add a `SkillCategory` model in `apps/backend/app/schemas/models.py`.

2. Add `skillCategories: list[SkillCategory] = Field(default_factory=list)` to `AdditionalInfo`.

3. Add schema validators for `skillCategories` so invalid names become empty strings or are filtered, and invalid skill values become clean string lists.

4. Update backend schema examples in `apps/backend/app/prompts/templates.py` to show `additional.skillCategories` as optional derived presentation data.

5. Add `CATEGORIZE_SKILLS_PROMPT` in `apps/backend/app/prompts/templates.py`.

6. Create `apps/backend/app/services/skill_categorizer.py`.

7. Implement a helper that extracts the canonical flat skills from `resume_data["additional"]["technicalSkills"]`.

8. Implement a helper that builds a normalized skill index so AI output can be matched back to original skill casing.

9. Implement AI categorization using `complete_json` with the category prompt.

10. Implement deterministic category validation that drops hallucinated skills.

11. Implement deterministic category validation that deduplicates repeated skills.

12. Implement deterministic category validation that appends missing original skills to an `Other Skills` fallback category.

13. Implement a full fallback that returns one category containing all flat skills when the AI call fails or returns unusable output.

14. Add logging for categorization failures without exposing detailed model errors to API clients.

15. Integrate categorization into `parse_resume_to_json` after `ResumeData` validation or immediately before returning parsed data.

16. Integrate categorization into the improve preview flow after refinement, date restoration, skill preservation, and custom section protection.

17. Integrate categorization into the improve confirm flow before creating the tailored resume record.

18. Integrate categorization into `PATCH /resumes/{resume_id}` before saving updated `processed_data`.

19. Integrate categorization into enrichment apply flow after regenerated skills replace `additional.technicalSkills`.

20. Ensure all new Python functions have type hints.

21. Add backend unit tests for successful AI category validation.

22. Add backend unit tests for hallucinated skill removal.

23. Add backend unit tests for duplicate skill handling.

24. Add backend unit tests for missing skill fallback.

25. Add backend unit tests for complete AI failure fallback.

26. Add or update service tests with mocked `complete_json`.

27. Add or update integration tests for at least one save path that persists `additional.skillCategories`.

28. Update frontend resume API types to include `SkillCategory` and `additional.skillCategories`.

29. Update shared frontend resume data types to include `SkillCategory` and `additional.skillCategories`.

30. Add a shared resume skill rendering helper or component under `apps/frontend/components/resume/`.

31. Make the shared renderer prefer valid categorized skills over flat `technicalSkills`.

32. Make the shared renderer fall back to the current flat skill list when categories are missing, empty, or invalid.

33. Update `apps/frontend/components/resume/resume-single-column.tsx` to render categorized skills.

34. Update `apps/frontend/components/resume/resume-modern.tsx` to render categorized skills.

35. Update `apps/frontend/components/resume/resume-two-column.tsx` to render categorized skills.

36. Update `apps/frontend/components/resume/resume-modern-two-column.tsx` to render categorized skills.

37. Verify the print route uses the updated renderers and does not need a separate categorization implementation.

38. Add frontend rendering coverage for categorized skills.

39. Add frontend rendering coverage for flat skill fallback.

40. Run backend tests relevant to schema, categorization, improve, and enrichment.

41. Run `npm run lint` from `apps/frontend`.

42. Run `npm run format` from `apps/frontend`.

43. Manually verify a categorized tailored resume preview.

44. Manually verify a categorized PDF or print view.

45. Manually verify an old resume without `skillCategories` still displays the Skills section.
