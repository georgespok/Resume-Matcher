import React from 'react';
import type { SkillCategory } from '@/components/dashboard/resume-component';
import baseStyles from './styles/_base.module.css';

interface SkillCategoryInput {
  technicalSkills?: string[];
  skillCategories?: SkillCategory[];
}

interface SkillCategoryRowsProps extends SkillCategoryInput {
  label?: string;
}

function cleanStringList(values?: string[]): string[] {
  if (!Array.isArray(values)) return [];
  return values.map((value) => value.trim()).filter(Boolean);
}

function normalizeSkill(value: string): string {
  return value.trim().replace(/\s+/g, ' ').toLocaleLowerCase();
}

export function getRenderableSkillCategories({
  technicalSkills,
  skillCategories,
}: SkillCategoryInput): SkillCategory[] {
  if (!Array.isArray(skillCategories) || skillCategories.length === 0) {
    return [];
  }

  const flatSkills = cleanStringList(technicalSkills);
  const skillEntries = flatSkills.map((skill) => ({
    key: normalizeSkill(skill),
    skill,
    used: false,
  }));

  const renderedCategories: SkillCategory[] = [];

  for (const category of skillCategories) {
    if (!category || typeof category.name !== 'string' || !Array.isArray(category.skills)) {
      continue;
    }

    const name = category.name.trim();
    const categorySkills = cleanStringList(category.skills);
    const renderedSkills: string[] = [];

    for (const skill of categorySkills) {
      if (flatSkills.length === 0) {
        renderedSkills.push(skill);
        continue;
      }

      const key = normalizeSkill(skill);
      const matchedEntry = skillEntries.find((entry) => entry.key === key && !entry.used);
      if (!matchedEntry) {
        continue;
      }
      matchedEntry.used = true;
      renderedSkills.push(matchedEntry.skill);
    }

    if (name && renderedSkills.length > 0) {
      renderedCategories.push({ name, skills: renderedSkills });
    }
  }

  if (flatSkills.length > 0 && skillEntries.some((entry) => !entry.used)) {
    return [];
  }

  return renderedCategories;
}

export function hasRenderableSkillContent(input: SkillCategoryInput): boolean {
  return (
    cleanStringList(input.technicalSkills).length > 0 ||
    getRenderableSkillCategories(input).length > 0
  );
}

export const SkillCategoryRows: React.FC<SkillCategoryRowsProps> = ({
  technicalSkills,
  skillCategories,
  label,
}) => {
  const categories = getRenderableSkillCategories({ technicalSkills, skillCategories });
  const flatSkills = cleanStringList(technicalSkills);

  if (categories.length > 0) {
    return (
      <div className="space-y-0.5">
        {label && <div className="font-bold">{label}</div>}
        <div className="min-w-0 space-y-0.5">
          {categories.map((category, categoryIndex) => (
            <div key={`${category.name}-${categoryIndex}`} className="min-w-0">
              <span className="font-bold">{category.name}: </span>
              <span>{category.skills.join(', ')}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (flatSkills.length === 0) return null;

  return (
    <div className="space-y-0.5">
      {label && <div className="font-bold">{label}</div>}
      <span>{flatSkills.join(', ')}</span>
    </div>
  );
};

export const SkillCategoryPillGroups: React.FC<SkillCategoryInput> = ({
  technicalSkills,
  skillCategories,
}) => {
  const categories = getRenderableSkillCategories({ technicalSkills, skillCategories });
  const flatSkills = cleanStringList(technicalSkills);

  if (categories.length > 0) {
    return (
      <div className={baseStyles['resume-stack-tight']}>
        {categories.map((category, categoryIndex) => (
          <div key={`${category.name}-${categoryIndex}`}>
            <p className={`${baseStyles['resume-meta-sm']} font-bold uppercase`}>{category.name}</p>
            <div className="flex flex-wrap gap-1">
              {category.skills.map((skill, skillIndex) => (
                <span
                  key={`${category.name}-${skill}-${skillIndex}`}
                  className={baseStyles['resume-skill-pill']}
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (flatSkills.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1">
      {flatSkills.map((skill) => (
        <span key={skill} className={baseStyles['resume-skill-pill']}>
          {skill}
        </span>
      ))}
    </div>
  );
};
