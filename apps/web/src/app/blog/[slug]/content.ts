/**
 * Blog post content — HTML strings for each slug.
 * Structured for SEO with proper headings (h2, h3), internal links, and keyword density.
 */

export const BLOG_CONTENT: Record<string, string> = {

"ai-resume-screening-guide": `
<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">What is AI Resume Screening?</h2>
<p>AI resume screening uses machine learning and natural language processing to read, parse, and evaluate resumes against job requirements. Unlike keyword matching, modern AI screening understands context &mdash; it knows that "React" and "React.js" are the same thing, and that "led a team of 5 engineers" implies leadership experience.</p>
<p>The best AI screening tools go beyond simple parsing. They extract structured data from any resume format (PDF, DOCX, even images), map candidate qualifications against specific job requirements, and produce evidence-backed scores that explain <em>why</em> a candidate matches or doesn&rsquo;t.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">How AI Resume Screening Works: The 5-Step Process</h2>
<h3 style="color: var(--text-heading); font-size: 16px; font-weight: 600; margin-top: 20px;">1. Document Parsing</h3>
<p>The AI reads the resume file and extracts raw text, handling different formats, layouts, and even multi-column designs. Modern parsers can handle PDFs with complex formatting that would break older keyword scanners.</p>

<h3 style="color: var(--text-heading); font-size: 16px; font-weight: 600; margin-top: 20px;">2. Structured Data Extraction</h3>
<p>The AI identifies key fields: name, contact details, work history, education, skills, certifications. It understands that "2019 &ndash; Present" means current employment and calculates years of experience automatically.</p>

<h3 style="color: var(--text-heading); font-size: 16px; font-weight: 600; margin-top: 20px;">3. Job Description Analysis</h3>
<p>Simultaneously, the AI parses the job description to extract requirements: required skills, experience level, domain knowledge, qualifications, and nice-to-haves. This creates a structured rubric for evaluation.</p>

<h3 style="color: var(--text-heading); font-size: 16px; font-weight: 600; margin-top: 20px;">4. Evidence-Based Scoring</h3>
<p>Each candidate is scored against every requirement, with evidence cited from their resume. A score of 85% on "Technical Skills" doesn&rsquo;t just mean "good" &mdash; it means "the candidate has TypeScript, React, and PostgreSQL (matched) but is missing Terraform (gap)."</p>

<h3 style="color: var(--text-heading); font-size: 16px; font-weight: 600; margin-top: 20px;">5. Ranking and Shortlisting</h3>
<p>Candidates are ranked by overall fit, with clear evidence for each position. The recruiter sees a shortlist with scores, strengths, risks, and missing evidence &mdash; not a black-box number.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">What to Look for in an AI Screening Tool</h2>
<p><strong>Transparency:</strong> Can you see <em>why</em> a candidate scored high or low? Black-box scores are useless for client conversations.</p>
<p><strong>Evidence, not opinions:</strong> The tool should cite specific resume text, not generate vague summaries.</p>
<p><strong>Speed:</strong> Processing 10 resumes should take seconds, not minutes. If you&rsquo;re waiting longer than a minute, the tool isn&rsquo;t production-ready.</p>
<p><strong>Format flexibility:</strong> PDFs, DOCX, even scanned documents. Recruiters can&rsquo;t control what candidates submit.</p>
<p><strong>No hallucinations:</strong> The AI should never invent qualifications that aren&rsquo;t in the resume. Every claim must be traceable.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">The ROI of AI Resume Screening</h2>
<p>The average recruiter spends 23 hours per hire on resume screening alone. With AI screening, that drops to under 5 minutes per role &mdash; including reviewing the ranked shortlist. For an agency handling 20 roles per month, that&rsquo;s 460 hours saved annually.</p>
<p>More importantly, structured scoring reduces mis-hires. When every shortlist decision is backed by evidence, you can defend your recommendations to clients and hiring managers with data, not gut feel.</p>
`,

"reduce-time-to-shortlist": `
<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">The Shortlisting Bottleneck</h2>
<p>A single job posting on a major job board receives an average of 250 applications. For a recruiter managing 10-15 active roles, that&rsquo;s 2,500+ resumes to process at any given time. The math doesn&rsquo;t work with manual screening.</p>
<p>Most recruiters develop shortcuts: scan for keywords, check the current employer, look at years of experience, move on. This takes 7-10 seconds per resume but misses nuance. The candidate who used "React" in a side project gets the same treatment as the one who led a React migration at a Fortune 500.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Why Manual Screening Fails at Scale</h2>
<p><strong>Inconsistency:</strong> The first 20 resumes get careful attention. By resume 80, you&rsquo;re skimming. Research shows screening accuracy drops by 30% after the first hour.</p>
<p><strong>Format blindness:</strong> A beautifully designed resume gets more attention than a plain-text one, regardless of qualifications. Studies show visual formatting bias affects up to 40% of screening decisions.</p>
<p><strong>Keyword tunnel vision:</strong> Searching for "Python" misses the candidate who listed "Django, Flask, FastAPI" without explicitly stating "Python." Context matters more than keywords.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">The Evidence-Based Alternative</h2>
<p>Evidence-based screening replaces gut-feel with structured evaluation. Instead of asking "does this look good?", you ask "does this candidate have evidence of meeting each specific requirement?"</p>
<p>Here&rsquo;s how it works in practice:</p>
<p><strong>Step 1:</strong> Paste your job description. The AI extracts 6-10 specific requirements (technical skills, experience level, domain knowledge, etc.).</p>
<p><strong>Step 2:</strong> Upload all resumes at once. The AI reads every line of every CV in seconds.</p>
<p><strong>Step 3:</strong> Review the ranked shortlist. Each candidate has a score with evidence: what matched, what&rsquo;s missing, and what&rsquo;s uncertain.</p>
<p>Total time: 30-60 seconds for the AI, plus 2-3 minutes for the recruiter to review the top 5. Compare that to 4-6 hours of manual screening for the same role.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Real Impact: Agency Case Study</h2>
<p>A mid-sized recruitment agency handling 25 roles per month switched from manual screening to evidence-based AI scoring. Results after 3 months:</p>
<p>&bull; <strong>Time to shortlist:</strong> Reduced from 4.2 hours to 12 minutes per role</p>
<p>&bull; <strong>Client satisfaction:</strong> Shortlist acceptance rate increased from 60% to 85%</p>
<p>&bull; <strong>Candidate quality:</strong> 40% fewer interviews needed to fill each role</p>
<p>The key insight: faster screening didn&rsquo;t mean lower quality. It meant <em>higher</em> quality, because the AI reads every line of every resume &mdash; something no human can sustain across 250 applications.</p>
`,

"bias-in-resume-screening": `
<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">The 7.4-Second Problem</h2>
<p>Research from Ladders Inc. found that recruiters spend an average of 7.4 seconds on an initial resume screen. In that time, unconscious biases activate based on name, university, employer brand, and visual formatting &mdash; before the recruiter has actually evaluated qualifications.</p>
<p>This isn&rsquo;t a character flaw. It&rsquo;s how human cognition works under time pressure. When you&rsquo;re processing hundreds of resumes, your brain creates shortcuts. The problem is that those shortcuts correlate with demographic factors, not job performance.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Common Biases in Resume Screening</h2>
<p><strong>Name bias:</strong> Identical resumes with Anglo-Saxon names receive 50% more interview callbacks than those with ethnic names (Bertrand &amp; Mullainathan, 2004).</p>
<p><strong>Prestige bias:</strong> Candidates from well-known companies or universities are rated higher regardless of actual qualifications. A mid-level developer from Google gets more attention than a senior architect from a lesser-known firm.</p>
<p><strong>Recency bias:</strong> The last few resumes reviewed are disproportionately favoured or rejected compared to those reviewed earlier in the session.</p>
<p><strong>Confirmation bias:</strong> Once a recruiter forms an initial impression (positive or negative), they selectively read the rest of the resume to confirm it.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">How Structured Scoring Reduces Bias</h2>
<p>Structured scoring evaluates every candidate against the same criteria, in the same order, with the same weights. It doesn&rsquo;t know the candidate&rsquo;s name, university prestige, or resume design. It only knows:</p>
<p>&bull; Does the candidate have evidence of the required technical skills?</p>
<p>&bull; Do they meet the experience level requirement?</p>
<p>&bull; Is there evidence of relevant domain knowledge?</p>
<p>&bull; What&rsquo;s their cloud/infrastructure experience?</p>
<p>&bull; Is there evidence of leadership and mentoring?</p>
<p>Each factor is scored independently with cited evidence. The final ranking is a weighted combination &mdash; transparent, auditable, and defensible.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">The Human-AI Partnership</h2>
<p>The goal isn&rsquo;t to remove humans from hiring. It&rsquo;s to give humans better information. AI screening surfaces the evidence; the recruiter makes the decision. The AI might rank a candidate #3, but the recruiter notices they&rsquo;re relocating to the right city &mdash; context the AI can&rsquo;t capture.</p>
<p>The best outcomes come from structured AI scoring <em>plus</em> informed human judgment. The AI handles the parts humans are bad at (consistency, exhaustive reading, avoiding bias). Humans handle the parts AI is bad at (cultural fit assessment, reading between the lines, client relationships).</p>
`,

"recruitment-agency-ai-tools": `
<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Speed Is the New Differentiator</h2>
<p>In agency recruitment, the first shortlist wins. Clients work with multiple agencies simultaneously, and the agency that delivers qualified candidates fastest gets the placement. AI-powered screening turns days of manual work into minutes.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">1. Instant Shortlisting for New Briefs</h2>
<p>When a client sends a new job brief, the clock starts. Traditional process: read the JD, search the ATS, review 30-50 profiles, build a shortlist. That&rsquo;s half a day minimum.</p>
<p>With AI scoring: paste the JD, upload candidate resumes from your database, get a ranked shortlist with evidence in under a minute. Send the shortlist to the client while competitors are still reading CVs.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">2. Evidence-Backed Client Presentations</h2>
<p>Clients are tired of "trust me, they&rsquo;re great." AI scoring gives you structured evidence for every recommendation: "Sarah scored 92% &mdash; she has 7 years of TypeScript/React experience, direct Stripe integration at PayRight, and has mentored 3 junior engineers."</p>
<p>This transforms the client conversation from subjective opinion to data-driven recommendation. Shortlist acceptance rates increase because clients can see the reasoning.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">3. Skills Gap Analysis for Candidate Coaching</h2>
<p>When a candidate doesn&rsquo;t make the shortlist, the AI tells you exactly why: "Missing Terraform experience, only 3 years (JD requires 5+), no fintech domain evidence." Use this to coach candidates on upskilling or to reposition them for better-fit roles.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">4. Consistent Quality Across Consultants</h2>
<p>Every agency has senior consultants who screen brilliantly and juniors who miss things. AI scoring creates a quality baseline &mdash; every shortlist meets minimum evidence standards regardless of who prepared it.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">5. Competitive Pitches and Business Development</h2>
<p>Show prospective clients how your AI-powered process works. Run a live demo: "Give us a JD, we&rsquo;ll show you a scored shortlist in 60 seconds." It&rsquo;s a powerful differentiator in agency pitches where everyone claims to have "the best network."</p>
`,

"job-description-matching-explained": `
<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">The Problem with Keyword Matching</h2>
<p>Traditional ATS systems match resumes to job descriptions using keywords. If the JD says "Python" and the resume says "Python," it&rsquo;s a match. But this approach fails in three critical ways:</p>
<p><strong>Synonyms:</strong> A candidate who writes "machine learning" won&rsquo;t match a JD that says "ML." A developer who lists "React.js" won&rsquo;t match "ReactJS."</p>
<p><strong>Context:</strong> "Python" in "Completed a Python course on Udemy" is very different from "Built a Python-based trading platform processing $2B in transactions."</p>
<p><strong>Implicit skills:</strong> A candidate who lists "Django" and "FastAPI" clearly knows Python, but keyword matching won&rsquo;t infer that.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Evidence-Based JD Matching: A Better Approach</h2>
<p>Evidence-based matching goes beyond keywords. It extracts structured requirements from the JD, then evaluates each candidate against those requirements using contextual understanding.</p>
<p>A job description for "Senior Full Stack Engineer" might produce these requirements:</p>
<p>&bull; <strong>Technical Skills (25%):</strong> TypeScript, React/Next.js, Node.js, PostgreSQL</p>
<p>&bull; <strong>Experience Level (20%):</strong> 5+ years professional development</p>
<p>&bull; <strong>Domain Knowledge (15%):</strong> Payment systems, fintech, regulated industries</p>
<p>&bull; <strong>Cloud &amp; Infrastructure (10%):</strong> AWS or GCP, CI/CD, Docker</p>
<p>&bull; <strong>Leadership (10%):</strong> Mentoring, technical direction, cross-functional work</p>
<p>Each requirement has a weight reflecting its importance. The AI then evaluates every candidate against every requirement, citing specific evidence from their resume.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">The 8-Factor Scoring Model</h2>
<p>The most effective JD matching uses multiple evaluation factors, not a single score. An 8-factor model typically includes: technical skills, experience level, domain knowledge, cloud/infrastructure, leadership, testing/CI-CD, communication, and culture fit.</p>
<p>Each factor gets its own score with a verdict (strong/partial/weak/missing) and evidence. This creates a rich, explainable evaluation that recruiters can use in client conversations.</p>
<p>The key difference: instead of "Match: 78%", you get "Technical Skills: 95% (strong) &mdash; has TypeScript, React, Next.js, Node.js, PostgreSQL. Domain Knowledge: 45% (weak) &mdash; e-commerce checkout experience but no direct payments/fintech."</p>
`,

"screen-tech-resumes-faster": `
<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Why Tech Resume Screening Is Uniquely Difficult</h2>
<p>Technical hiring has challenges that other domains don&rsquo;t:</p>
<p><strong>Framework sprawl:</strong> React, Angular, Vue, Svelte, Next.js, Nuxt, Remix &mdash; the JavaScript ecosystem alone has dozens of frameworks. A JD asking for "React experience" might miss candidates with extensive Next.js experience (which is built on React).</p>
<p><strong>Title inconsistency:</strong> "Full Stack Developer," "Software Engineer," "Frontend Developer," "Web Developer" can all describe the same role depending on the company. A "Platform Engineer" at one startup does the same work as a "DevOps Engineer" at another.</p>
<p><strong>Resume format chaos:</strong> Developers often use custom-designed resumes, LaTeX templates, or even GitHub profiles as CVs. Parsing these reliably requires sophisticated document understanding.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">The AI Approach to Tech Screening</h2>
<p>Modern AI screening handles these challenges by understanding technology context:</p>
<p><strong>Technology graph:</strong> The AI knows that Next.js implies React, that Django implies Python, that Kubernetes implies Docker. It builds a complete picture of the candidate&rsquo;s technical profile, not just what&rsquo;s explicitly listed.</p>
<p><strong>Experience depth:</strong> "Used React for a side project" is different from "Led React migration serving 2M users." The AI evaluates context and scale, not just presence.</p>
<p><strong>Stack matching:</strong> A JD requiring "TypeScript, React, Node.js, PostgreSQL" gets evaluated as a complete stack. The AI identifies candidates who match the full stack vs. those who only match individual pieces.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Practical Workflow for Tech Recruiters</h2>
<p><strong>Step 1:</strong> Get the JD from the hiring manager. Paste it into the screening tool. The AI extracts the technical requirements and weights them.</p>
<p><strong>Step 2:</strong> Batch-upload all 50 resumes. The AI processes them in parallel &mdash; typically 30-60 seconds for 50 CVs.</p>
<p><strong>Step 3:</strong> Review the top 5-8 candidates. Expand each card to see factor-by-factor scoring with evidence. "Technical Skills: 95% &mdash; has TypeScript (5 years), React/Next.js (3 years at Canva), Node.js, PostgreSQL."</p>
<p><strong>Step 4:</strong> Use the skills gap analysis to prepare interview questions. If the top candidate is missing Terraform experience, flag it for the technical interview.</p>
<p>Total time: under 5 minutes for what used to take 4-6 hours.</p>
`,

"candidate-comparison-side-by-side": `
<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">The Spreadsheet Problem</h2>
<p>Most recruiters compare candidates using spreadsheets, sticky notes, or memory. "I think Candidate A was stronger on technical skills, but Candidate B had better leadership experience..." This approach is error-prone, inconsistent, and impossible to explain to clients.</p>
<p>When a hiring manager asks "Why did you recommend Candidate A over Candidate B?", you need more than "they felt like a better fit."</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Evidence-Based Comparison</h2>
<p>Side-by-side comparison with structured scoring solves this. Select any two (or more) candidates and see their scores aligned factor-by-factor:</p>
<p>Take two candidates for a Senior Full Stack Engineer role:</p>
<p><strong>Sarah Chen (92%):</strong> Technical Skills 95%, Experience 90%, Domain 95%, Cloud 90%, Leadership 88%</p>
<p><strong>Marcus Wright (78%):</strong> Technical Skills 88%, Experience 75%, Domain 45%, Cloud 85%, Leadership 60%</p>
<p>The comparison instantly reveals: both are strong technically, but Sarah has deep fintech domain knowledge (Stripe integration, PCI compliance) while Marcus has e-commerce experience that doesn&rsquo;t transfer directly. Sarah also has clear leadership evidence (mentoring 3 juniors) that Marcus lacks.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">How to Use Comparison in Client Conversations</h2>
<p>When presenting a shortlist to a client, comparison data is powerful:</p>
<p>"We&rsquo;re recommending Sarah as the top candidate. She scores 95% on domain knowledge because she built Stripe Connect integration processing $800M annually at PayRight. Marcus is our #2 &mdash; equally strong technically, but he&rsquo;d need to ramp up on payment systems. He&rsquo;s a great option if the client is willing to invest in that development."</p>
<p>This is a fundamentally different conversation than "We think Sarah is better." It&rsquo;s evidence-based, specific, and gives the client information to make their own decision.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Comparison for Interview Planning</h2>
<p>Side-by-side comparison also helps design interview processes. If your top 3 candidates all score weak on "Leadership," you know to include a leadership assessment. If they all score strong on technical skills, you can skip the coding test and focus on cultural fit and communication.</p>
`,

"skills-gap-analysis-hiring": `
<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Every Candidate Has Gaps</h2>
<p>The perfect candidate doesn&rsquo;t exist. Even your top-scoring applicant will have gaps &mdash; a missing certification, limited experience with a specific tool, or no evidence of a particular skill. The question isn&rsquo;t whether gaps exist, but which gaps matter.</p>
<p>Skills gap analysis maps every candidate&rsquo;s evidence against every job requirement, identifying exactly what&rsquo;s present, what&rsquo;s missing, and what&rsquo;s uncertain. This transforms vague concerns into specific, actionable insights.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Three Types of Gaps</h2>
<p><strong>Hard gaps:</strong> The JD requires Kubernetes experience; the candidate has never used it. This is a training investment or a deal-breaker depending on the role.</p>
<p><strong>Soft gaps:</strong> The JD requires "5+ years experience"; the candidate has 4 years. Close enough? Depends on the depth of those 4 years.</p>
<p><strong>Evidence gaps:</strong> The candidate probably has the skill but their resume doesn&rsquo;t explicitly mention it. A developer who lists "Docker, AWS ECS, Terraform" likely understands CI/CD, but there&rsquo;s no direct evidence. Worth exploring in an interview.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Using Gap Analysis for Better Hiring Decisions</h2>
<p><strong>Shortlist refinement:</strong> When two candidates score similarly overall, gap analysis reveals who has critical gaps vs. nice-to-have gaps. A candidate missing "Terraform" (learnable in weeks) is different from one missing "5 years of React" (not learnable quickly).</p>
<p><strong>Interview design:</strong> Focus interview questions on the gaps. If the AI flags "no evidence of leadership experience," design a behavioral interview around team collaboration and mentoring scenarios.</p>
<p><strong>Offer negotiation:</strong> If a candidate has a skills gap that requires training, factor that into the compensation discussion. "We&rsquo;re offering a slightly lower starting salary with a 6-month review, plus budget for AWS certification."</p>
<p><strong>Onboarding planning:</strong> Before the candidate starts, you already know their gaps. Build an onboarding plan that addresses them: pair them with a mentor who has the missing expertise, schedule relevant training, set 90-day milestones.</p>
`,

"ai-recruitment-tools-australia": `
<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">The AI Recruitment Landscape in Australia</h2>
<p>Australian recruitment agencies are increasingly adopting AI tools, but the market is fragmented. Some tools focus on sourcing, others on screening, others on scheduling. Here&rsquo;s a practical breakdown of what&rsquo;s available and what actually helps.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Categories of AI Recruitment Tools</h2>
<h3 style="color: var(--text-heading); font-size: 16px; font-weight: 600; margin-top: 20px;">1. Resume Screening &amp; Candidate Ranking</h3>
<p>These tools evaluate resumes against job descriptions and produce ranked shortlists. The best ones provide evidence-based scoring (not just a number) so you can explain recommendations to clients.</p>
<p>Key features to look for: multi-factor scoring, evidence citations, skills gap analysis, side-by-side comparison, batch processing (10+ resumes at once).</p>

<h3 style="color: var(--text-heading); font-size: 16px; font-weight: 600; margin-top: 20px;">2. Sourcing &amp; Candidate Discovery</h3>
<p>Tools like LinkedIn Recruiter, Seek Talent Search, and various AI-powered sourcing platforms help find candidates. These are complementary to screening tools &mdash; they find candidates, but still leave you with the screening problem.</p>

<h3 style="color: var(--text-heading); font-size: 16px; font-weight: 600; margin-top: 20px;">3. Interview Scheduling &amp; Coordination</h3>
<p>Calendly, Paradox (Olivia), and similar tools automate interview scheduling. Useful but not transformative &mdash; they save administrative time, not decision-making time.</p>

<h3 style="color: var(--text-heading); font-size: 16px; font-weight: 600; margin-top: 20px;">4. ATS with AI Features</h3>
<p>Modern ATS platforms (Jobadder, Bullhorn, JobAdder) are adding AI features, but they&rsquo;re typically basic keyword matching, not deep evidence-based analysis. They&rsquo;re good for tracking but not for screening.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">What Australian Agencies Should Prioritise</h2>
<p>For most Australian agencies, the biggest ROI comes from AI <strong>screening</strong>, not AI sourcing. Why? Because sourcing is already semi-automated (Seek, LinkedIn), but screening is still almost entirely manual. The 4-6 hours per role spent reading resumes is the bottleneck.</p>
<p>Look for tools that:</p>
<p>&bull; Work with Australian resume formats and terminology</p>
<p>&bull; Handle AU-specific qualifications (CPA, AHPRA, state-based licensing)</p>
<p>&bull; Provide evidence that&rsquo;s useful in client conversations</p>
<p>&bull; Don&rsquo;t require lengthy onboarding or ATS integration to start</p>
<p>&bull; Offer transparent pricing in AUD</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Getting Started</h2>
<p>The best approach is to try a screening tool on a real role. Take a current job brief, upload the resumes you&rsquo;ve already received, and compare the AI&rsquo;s ranking with your own. If it surfaces candidates you would have shortlisted (and explains why), it&rsquo;s worth adopting.</p>
`,

"evidence-based-hiring-decisions": `
<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">The Gut-Feel Problem</h2>
<p>A 2023 survey by the Society for Human Resource Management found that 68% of hiring managers admit to making "gut feel" decisions when shortlisting candidates. They scan the resume, get a general impression, and make a quick call. This works sometimes. But at scale, it fails.</p>
<p>Gut-feel hiring has three fundamental problems:</p>
<p><strong>It&rsquo;s inconsistent:</strong> The same hiring manager evaluates candidates differently on Monday morning vs. Friday afternoon.</p>
<p><strong>It&rsquo;s indefensible:</strong> When a hiring decision is challenged &mdash; by the candidate, by HR, by a client &mdash; "I just felt they were the right fit" doesn&rsquo;t hold up.</p>
<p><strong>It&rsquo;s biased:</strong> Gut feel correlates with familiarity, not capability. We favour candidates who remind us of ourselves or our previous successful hires.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">What Evidence-Based Hiring Looks Like</h2>
<p>Evidence-based hiring replaces intuition with structured evaluation. Every decision is backed by specific, citable evidence from the candidate&rsquo;s resume, work history, or assessment results.</p>
<p>Instead of: "Sarah seems like a strong candidate."</p>
<p>You get: "Sarah scores 92% against the JD. She has 7 years of TypeScript/React experience (matches 5+ year requirement), built Stripe Connect integration at PayRight processing $800M annually (matches payment systems requirement), and mentored 3 junior engineers (matches leadership requirement). Gaps: none identified."</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">The Four Pillars of Evidence-Based Hiring</h2>
<p><strong>1. Structured requirements:</strong> Before evaluating any candidate, define exactly what the role requires. Not "we need a good developer" but "we need TypeScript + React + 5 years + payment systems experience."</p>
<p><strong>2. Consistent evaluation:</strong> Every candidate is assessed against the same criteria with the same weights. No shortcuts, no favourites, no order effects.</p>
<p><strong>3. Cited evidence:</strong> Every score and recommendation points to specific evidence. "Leadership: 88% &mdash; evidence: mentored 3 juniors at PayRight, led API versioning strategy adopted by 4 teams."</p>
<p><strong>4. Documented decisions:</strong> The shortlist rationale is recorded and shareable. Clients, hiring managers, and compliance teams can all see why each candidate was recommended or rejected.</p>

<h2 style="color: var(--text-heading); font-size: 20px; font-weight: 600; margin-top: 32px;">Making the Shift</h2>
<p>You don&rsquo;t need to overhaul your entire process. Start with one change: for your next role, use structured scoring alongside your normal process. Compare the results. You&rsquo;ll likely find that the AI surfaces candidates you would have missed, and flags risks you would have overlooked.</p>
<p>The goal isn&rsquo;t to replace human judgment. It&rsquo;s to give humans better information so their judgment is more accurate, more consistent, and more defensible.</p>
`,

};
