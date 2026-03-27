// Prompt template: Explain candidate fit for a given role

import type { CandidateScore, Role } from '@rolefitai/types';

export interface ExplainCandidateInput {
  candidateName: string;
  candidateResumeText: string;
  role: Pick<Role, 'title' | 'description' | 'requirements'>;
  score?: CandidateScore;
}

/**
 * Builds a prompt that asks the LLM for a concise narrative explanation of
 * why a candidate is or is not a good fit for the role, suitable for display
 * in the reviewer UI.
 */
export function buildExplainCandidatePrompt(
  input: ExplainCandidateInput,
): string {
  const { candidateName, candidateResumeText, role, score } = input;

  const scoreContext = score
    ? `\nPre-computed score summary:
- Overall score: ${score.overall}/100
- Strengths: ${score.strengths.join('; ')}
- Risks: ${score.risks.join('; ')}
- Missing evidence: ${score.missingEvidence.join('; ')}`
    : '';

  return `You are a senior technical recruiter reviewing candidates for the role of "${role.title}".

Role description:
${role.description}

Key requirements:
${role.requirements.map((r, i) => `${i + 1}. ${r}`).join('\n')}
${scoreContext}

Candidate: ${candidateName}
Resume / CV:
---
${candidateResumeText}
---

Write a concise (3–5 sentences) narrative that explains this candidate's fit for the role. Cover:
1. Their strongest relevant qualifications
2. Any notable gaps or risks
3. An overall hiring recommendation (Strong Yes / Yes / Maybe / No)

Be specific and reference details from the resume. Do not repeat the job requirements verbatim.`;
}
