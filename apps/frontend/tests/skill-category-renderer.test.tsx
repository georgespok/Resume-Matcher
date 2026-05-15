import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  SkillCategoryRows,
  getRenderableSkillCategories,
} from '@/components/resume/skill-category-renderer';

describe('skill category rendering', () => {
  it('uses categorized skills when categories match the flat skill list', () => {
    const categories = getRenderableSkillCategories({
      technicalSkills: ['Python', 'Docker', 'AWS'],
      skillCategories: [
        { name: 'Languages', skills: ['python'] },
        { name: 'Cloud & DevOps', skills: ['Docker', 'AWS'] },
      ],
    });

    expect(categories).toEqual([
      { name: 'Languages', skills: ['Python'] },
      { name: 'Cloud & DevOps', skills: ['Docker', 'AWS'] },
    ]);
  });

  it('falls back when categories are stale or incomplete', () => {
    const categories = getRenderableSkillCategories({
      technicalSkills: ['Python', 'Docker'],
      skillCategories: [{ name: 'Languages', skills: ['Python'] }],
    });

    expect(categories).toEqual([]);
  });

  it('renders category labels and grouped skills', () => {
    const { container } = render(
      <SkillCategoryRows
        technicalSkills={['Python', 'Docker']}
        skillCategories={[
          { name: 'Languages', skills: ['Python'] },
          { name: 'DevOps', skills: ['Docker'] },
        ]}
      />
    );

    expect(screen.queryByText('Technical Skills:')).not.toBeInTheDocument();
    expect(screen.getByText('Languages:', { exact: false })).toBeInTheDocument();
    expect(screen.getByText('DevOps:', { exact: false })).toBeInTheDocument();
    expect(container.querySelector('.font-bold.w-32')).not.toBeInTheDocument();
  });

  it('renders the flat skill list when no valid categories exist', () => {
    render(
      <SkillCategoryRows
        technicalSkills={['Python', 'Docker']}
        skillCategories={[{ name: 'Languages', skills: ['Python'] }]}
      />
    );

    expect(screen.getByText('Python, Docker')).toBeInTheDocument();
  });
});
