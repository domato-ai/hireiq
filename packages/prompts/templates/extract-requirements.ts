// Prompt template: Extract structured role requirements from a job description

export interface ExtractRequirementsInput {
  jobDescriptionText: string;
  roleTitle?: string;
}

export interface ExtractRequirementsOutput {
  mustHave: string[];
  niceToHave: string[];
  yearsOfExperience: string | null;
  educationRequirements: string[];
  skills: string[];
  responsibilities: string[];
  locationRequirement: string | null;
  remotePolicy: 'remote' | 'hybrid' | 'onsite' | 'unknown';
}

/**
 * Builds a prompt that instructs the LLM to extract structured requirements
 * from a raw job description.
 */
export function buildExtractRequirementsPrompt(
  input: ExtractRequirementsInput,
): string {
  const { jobDescriptionText, roleTitle } = input;

  return `You are an expert technical recruiter. Your task is to extract structured hiring requirements from the following job description${roleTitle ? ` for the role of "${roleTitle}"` : ''}.

Return ONLY valid JSON matching the schema below. Do not include any explanation or markdown.

Schema:
{
  "mustHave": string[],           // Non-negotiable requirements explicitly stated
  "niceToHave": string[],         // Preferred but not required qualifications
  "yearsOfExperience": string | null,  // e.g. "3-5 years", "5+ years", or null
  "educationRequirements": string[],   // e.g. ["Bachelor's in Computer Science"]
  "skills": string[],             // Technical and soft skills mentioned
  "responsibilities": string[],   // Key duties and responsibilities
  "locationRequirement": string | null, // City/country or null
  "remotePolicy": "remote" | "hybrid" | "onsite" | "unknown"
}

Job Description:
---
${jobDescriptionText}
---

JSON output:`;
}
