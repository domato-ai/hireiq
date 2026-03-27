// Prompt template: Compare multiple candidates for the same role

import type { CandidateScore, Role } from '@rolefitai/types';

export interface CandidateSummary {
  name: string;
  resumeText: string;
  score?: CandidateScore;
}

export interface CompareCandidatesInput {
  role: Pick<Role, 'title' | 'description' | 'requirements'>;
  candidates: CandidateSummary[];
}

/**
 * Builds a prompt that asks the LLM to rank and compare a shortlist of
 * candidates against each other for the same role.
 */
export function buildCompareCandidatesPrompt(
  input: CompareCandidatesInput,
): string {
  const { role, candidates } = input;

  if (candidates.length < 2) {
    throw new Error('At least 2 candidates are required for a comparison.');
  }

  const candidateBlocks = candidates
    .map((c, i) => {
      const scoreLines = c.score
        ? `Score: ${c.score.overall}/100 | Strengths: ${c.score.strengths.join(', ')} | Risks: ${c.score.risks.join(', ')}`
        : 'Score: not yet computed';
      return `Candidate ${i + 1}: ${c.name}
${scoreLines}
Resume excerpt:
${c.resumeText.slice(0, 800)}${c.resumeText.length > 800 ? '…' : ''}`;
    })
    .join('\n\n');

  return `You are a senior hiring manager comparing a shortlist of candidates for the role of "${role.title}".

Role description:
${role.description}

Key requirements:
${role.requirements.map((r, i) => `${i + 1}. ${r}`).join('\n')}

Candidates:
---
${candidateBlocks}
---

Provide a structured comparison:
1. Rank the candidates from best to weakest fit for this role.
2. For each candidate, give one sentence on their key advantage and one sentence on their main concern.
3. Recommend which candidate to advance to the next interview stage and why.

Be concise, objective, and use specific evidence from the resumes.`;
}
