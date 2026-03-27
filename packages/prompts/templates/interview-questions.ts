// Prompt template: Generate tailored interview questions for a candidate

import type { CandidateScore, Role } from '@rolefitai/types';

export interface InterviewQuestionsInput {
  candidateName: string;
  candidateResumeText: string;
  role: Pick<Role, 'title' | 'description' | 'requirements'>;
  score?: CandidateScore;
  questionCount?: number; // default 8
  categories?: InterviewCategory[];
}

export type InterviewCategory =
  | 'technical'
  | 'behavioural'
  | 'situational'
  | 'culture-fit'
  | 'gap-probe';

export interface InterviewQuestion {
  category: InterviewCategory;
  question: string;
  rationale: string; // why this question for this candidate
}

/**
 * Builds a prompt that asks the LLM to generate tailored interview questions
 * based on the candidate's background and identified gaps.
 */
export function buildInterviewQuestionsPrompt(
  input: InterviewQuestionsInput,
): string {
  const {
    candidateName,
    candidateResumeText,
    role,
    score,
    questionCount = 8,
    categories = ['technical', 'behavioural', 'situational', 'gap-probe'],
  } = input;

  const scoreContext = score
    ? `\nScoring highlights:
- Overall: ${score.overall}/100
- Strengths: ${score.strengths.join('; ')}
- Risks: ${score.risks.join('; ')}
- Missing evidence: ${score.missingEvidence.join('; ')}`
    : '';

  return `You are an experienced technical interviewer preparing for an interview with ${candidateName} for the role of "${role.title}".

Role description:
${role.description}

Key requirements:
${role.requirements.map((r, i) => `${i + 1}. ${r}`).join('\n')}
${scoreContext}

Candidate resume:
---
${candidateResumeText}
---

Generate exactly ${questionCount} interview questions tailored to this specific candidate.
Focus on these categories: ${categories.join(', ')}.

Return ONLY valid JSON as an array matching this schema:
[
  {
    "category": "technical" | "behavioural" | "situational" | "culture-fit" | "gap-probe",
    "question": "...",
    "rationale": "..."  // one sentence: why this question for this candidate
  }
]

Prioritise gap-probe questions for any missing evidence or weak signals in the candidate's background.
Do not include generic questions that could apply to any candidate.

JSON output:`;
}
