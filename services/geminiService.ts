import { GoogleGenAI, GenerateContentResponse, Part } from "@google/genai";
import { GEMINI_MODEL_TEXT, CACHE_EXPIRY_MS } from '../constants';
import { 
    GeminiAnalysisResponse, Language, GroundingMetadata, ScoreComponent, 
    CachedAnalysisItem, MatchResult, AppSettings, AssessmentDimensionSetting,
    StructuredCV, StructuredJD, WorkExperienceEntry, EducationEntry, SkillEntry, ProjectEntry,
    QualificationEntry, ResponsibilityEntry, PersonalInformation
} from '../types';

// Use Vite prefixed environment variable
const API_KEY = typeof import.meta !== 'undefined' ? import.meta.env?.VITE_GOOGLE_GENAI_API_KEY : undefined;

if (!API_KEY) {
  console.error("API_KEY environment variable not set. Gemini API calls will fail.");
}

const ai = new GoogleGenAI({ apiKey: API_KEY || "MISSING_API_KEY" });

// SHA-256 Hashing function for cache keys
async function sha256(message: string): Promise<string> {
  try {
    const msgBuffer = new TextEncoder().encode(message); // encode as UTF-8
    const hashBuffer = await globalThis.crypto.subtle.digest('SHA-256', msgBuffer); // hash the message
    const hashArray = Array.from(new Uint8Array(hashBuffer)); // convert buffer to byte array
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join(''); // convert bytes to hex string
    return hashHex;
  } catch (e) {
    console.error("SHA-256 hashing failed, falling back to plain key (less safe for complex data):", e);
    return `fallback_${message.substring(0,50)}_${message.length}_${message.slice(-50)}`;
  }
}

export const parseGeminiResponse = (
    responseText: string, 
    fallbackCvName: string, 
    fallbackJdTitle: string,
    activeDimensions: AssessmentDimensionSetting[] 
): GeminiAnalysisResponse => {
  let jsonStr = responseText.trim();
  const fenceRegex = /^```(\w*)?\s*\n?(.*?)\n?\s*```$/s;
  const match = jsonStr.match(fenceRegex);
  if (match && match[2]) {
    jsonStr = match[2].trim();
  }

  jsonStr = jsonStr.replace(/\\(?![\\/"bfnrt]|u[0-9a-fA-F]{4})/g, '');

  let jsonStrAfterFenceRemoval = jsonStr; 
  let modifiedJsonByHeuristic = false;

  try {
    const lines = jsonStr.split('\n');
    for (let i = 0; i < lines.length; i++) {
        const currentLineTrimmed = lines[i].trim();

        if (currentLineTrimmed.endsWith("}") && i + 1 < lines.length) {
            let nextNonEmptyLineIndex = -1;
            for (let j = i + 1; j < lines.length; j++) {
                if (lines[j].trim() !== "") {
                    nextNonEmptyLineIndex = j;
                    break;
                }
            }
            if (nextNonEmptyLineIndex !== -1) {
                const nextLineTrimmed = lines[nextNonEmptyLineIndex].trim();
                if (nextLineTrimmed.startsWith('"') && nextLineTrimmed.includes('":')) {
                    if (!currentLineTrimmed.endsWith("},")) {
                         lines[i] = lines[i].trimRight().replace(/}$/, '},');
                         modifiedJsonByHeuristic = true;
                    }
                }
            }
        }
        
        if (currentLineTrimmed.endsWith("}") && i + 1 < lines.length) {
            let nextLineContent = "";
            for (let k = i + 1; k < lines.length; k++) {
                if (lines[k].trim() !== "") {
                    nextLineContent = lines[k].trim();
                    break;
                }
            }
            if (nextLineContent.startsWith('"') && nextLineContent.includes('":')) {
                 if (!lines[i].trimRight().endsWith(',')) {
                     lines[i] = lines[i].trimRight().replace(/}$/, '},');
                     modifiedJsonByHeuristic = true;
                 }
            }
        }

        if (currentLineTrimmed === '",') {
            let prevLineContent = "";
            let prevLineActualIdx = -1;
            for (let j = i - 1; j >= 0; j--) {
                if (lines[j].trim() !== "") {
                    prevLineContent = lines[j].trim();
                    prevLineActualIdx = j;
                    break;
                }
            }
            let nextLineContent = "";
            for (let k = i + 1; k < lines.length; k++) {
                if (lines[k].trim() !== "") {
                    nextLineContent = lines[k].trim();
                    break;
                }
            }
            if (prevLineActualIdx !== -1 && prevLineContent.endsWith('"') && !prevLineContent.endsWith('\\"')) {
                const nextLineIsNewKey = nextLineContent.match(/^"\s*[^"]+\s*"\s*:/);
                if (nextLineIsNewKey) {
                    lines[i] = lines[i].replace('",', '],');
                    modifiedJsonByHeuristic = true;
                } else {
                    if (!lines[prevLineActualIdx].trimRight().endsWith(',')) {
                        lines[prevLineActualIdx] = lines[prevLineActualIdx].trimRight() + ',';
                    }
                    lines.splice(i, 1); 
                    i--; 
                    modifiedJsonByHeuristic = true;
                }
            }
        }
    }

    if (modifiedJsonByHeuristic) {
        jsonStr = lines.join('\n');
    }

    const rawParsedData = JSON.parse(jsonStr);
    let dataToValidate: any = null;

    if (Array.isArray(rawParsedData) && rawParsedData.length > 0) {
      dataToValidate = rawParsedData[0];
    } else if (typeof rawParsedData === 'object' && rawParsedData !== null && !Array.isArray(rawParsedData)) {
      dataToValidate = rawParsedData;
    }

    if (!dataToValidate) {
      console.error("Parsed JSON was empty or not an object/array:", rawParsedData, "Original JSON string:", jsonStrAfterFenceRemoval);
      throw new Error("Parsed JSON was empty or not a processable object/array.");
    }
    
    // Normalize score keys (e.g., "problem-solving-complexity" to "problem_solving_complexity")
    if (dataToValidate.scores && typeof dataToValidate.scores === 'object') {
        const normalizedScores: Record<string, any> = {};
        for (const key in dataToValidate.scores) {
            const normalizedKey = key.replace(/-/g, '_');
            normalizedScores[normalizedKey] = dataToValidate.scores[key];
        }
        dataToValidate.scores = normalizedScores;
    }
    
    let allScoresValid = true;
    if (dataToValidate.scores && typeof dataToValidate.scores === 'object') {
        for (const dim of activeDimensions) {
            if (!dataToValidate.scores[dim.id] || 
                typeof dataToValidate.scores[dim.id].score !== 'number' ||
                typeof dataToValidate.scores[dim.id].explanation !== 'string') {
                allScoresValid = false;
                console.error(`Missing or invalid score component for dimension ID: ${dim.id}`, dataToValidate.scores[dim.id]);
                break;
            }
        }
    } else {
        allScoresValid = false;
        console.error("Scores object is missing or not an object in parsed data.", dataToValidate.scores);
    }

    const isValidStructure =
      dataToValidate &&
      typeof dataToValidate.overallScore === 'number' &&
      allScoresValid && 
      typeof dataToValidate.detailedExplanation === 'string' &&
      (dataToValidate.positivePoints === undefined || Array.isArray(dataToValidate.positivePoints)) &&
      (dataToValidate.painPoints === undefined || Array.isArray(dataToValidate.painPoints)) &&
      (dataToValidate.discussionPoints === undefined || Array.isArray(dataToValidate.discussionPoints));

    if (isValidStructure) {
      const validatedScores: Record<string, ScoreComponent> = {};
      for (const dim of activeDimensions) {
        const sc = dataToValidate.scores[dim.id];
        validatedScores[dim.id] = {
            score: sc.score,
            explanation: sc.explanation,
            details: sc.details 
        };
      }
      
      return {
          overallScore: dataToValidate.overallScore,
          scores: validatedScores,
          detailedExplanation: dataToValidate.detailedExplanation,
          candidateName: dataToValidate.candidateName, 
          jobTitle: dataToValidate.jobTitle,
          positivePoints: Array.isArray(dataToValidate.positivePoints) ? dataToValidate.positivePoints.filter((item:unknown) => typeof item === 'string') : undefined,
          painPoints: Array.isArray(dataToValidate.painPoints) ? dataToValidate.painPoints.filter((item:unknown) => typeof item === 'string') : undefined,
          discussionPoints: Array.isArray(dataToValidate.discussionPoints) ? dataToValidate.discussionPoints.filter((item:unknown) => typeof item === 'string') : undefined,
      } as GeminiAnalysisResponse;
    }
    
    console.error("Parsed JSON object does not match expected GeminiAnalysisResponse structure (dynamic scores & new report fields):", dataToValidate, "Original JSON string after fence removal:", jsonStrAfterFenceRemoval, "Attempted JSON (after potential fix):", jsonStr);
    throw new Error("Parsed JSON object does not match expected structure. Check console for details.");

  } catch (e: any) {
    console.error(
        "Failed to parse JSON response from Gemini (JSON.parse failed or structure validation failed):", e, 
        "\nRaw response text:", responseText, 
        "\nJSON string after fence removal (before heuristic):", jsonStrAfterFenceRemoval,
        modifiedJsonByHeuristic ? "\nJSON string after heuristic fix attempt:" : "\nJSON string (no heuristic applied or fix was not for this error):", jsonStr
    );
    const errorScores: Record<string, ScoreComponent> = {};
    activeDimensions.forEach(dim => {
        errorScores[dim.id] = { score: 0, explanation: `Error: AI response parsing failed for this dimension. Details: ${e.message}` };
    });

    return {
        candidateName: fallbackCvName,
        jobTitle: fallbackJdTitle,
        scores: errorScores,
        overallScore: 0,
        detailedExplanation: `Critical Error: The AI's response could not be reliably parsed into the expected format. Details: ${e.message}. Raw response (first 500 chars): ${responseText.substring(0, 500)}...`,
        positivePoints: [],
        painPoints: [],
        discussionPoints: [],
    };
  }
};


export const analyzeCvJdMatch = async (
  cvContent: string, 
  cvMimeType: string, 
  jdContent: string,  
  jdMimeType: string, 
  cvName: string,
  jdTitle: string,
  currentLanguage: Language,
  appSettings: AppSettings, 
  cvRecruiterNotes?: string,
  jdRecruiterNotes?: string
): Promise<{ analysis: GeminiAnalysisResponse, cacheUsed: boolean, cacheTimestamp?: number }> => {
  if (!API_KEY) {
    console.error("Gemini API key is not configured.");
    const errorScores: Record<string, ScoreComponent> = {};
    appSettings.assessmentDimensions.filter(d => d.isActive).forEach(dim => {
        errorScores[dim.id] = { score: 0, explanation: "API Key not configured." };
    });
    const errorResponse: GeminiAnalysisResponse = {
        candidateName: cvName,
        jobTitle: jdTitle,
        scores: errorScores,
        overallScore: 0,
        detailedExplanation: "Error: The Gemini API key is not configured. Please set the API_KEY environment variable.",
        positivePoints: [],
        painPoints: [],
        discussionPoints: [],
    };
    return { analysis: errorResponse, cacheUsed: false };
  }
  
  const activeDimensions = appSettings.assessmentDimensions.filter(dim => dim.isActive);

  // --- CONCEPTUAL: Agentic RAG Steps (Would happen in a backend) ---
  // 1. Planner Agent: Analyzes CV/JD/Notes, determines information needs (e.g., detailed skill definitions, company culture context, typical career paths related to the role).
  // 2. Query Generation Agent: Creates targeted queries for the RecruitX knowledge base (Vector DB). Example queries: "Define 'Advanced Python proficiency' for a data science role.", "Key cultural values of 'ExampleCorp' impacting software teams.", "Common responsibilities for 'Senior Cloud Architect' with 5 years experience."
  // 3. Retrieval Agent: Fetches relevant documents/chunks from the Vector DB.
  // 4. Re-ranking/Filtering Agent: Prioritizes and selects the most pertinent retrieved information. For instance, if CV mentions "Project X at ExampleCorp", RAG might pull up details about "Project X" or "ExampleCorp's tech stack" if available.
  // 5. Formatting Agent: Prepares a concise `ragSpecificContextString` for the Synthesis Agent (Gemini).
  // For now, we simulate this output with a placeholder:
  const ragSpecificContextString = `CONCEPTUAL_RAG_CONTEXT:
This is placeholder text simulating retrieved information. In a full Agentic RAG system, this section would contain dynamically fetched, highly relevant data from RecruitX's curated knowledge base. Examples:
- Skill Definition for 'Kubernetes': Includes understanding of pods, services, deployments, Helm charts, and basic cluster administration. Proficiency levels: Basic (can deploy existing charts), Intermediate (can create custom charts, troubleshoot common issues), Advanced (can design and manage complex cluster architectures, optimize performance).
- Company Insight for '${jdTitle.includes("Acme") ? "Acme Corp" : "Target Company"}': Known for a fast-paced, innovative environment valuing collaboration and continuous learning. Engineering teams often use agile methodologies.
- Role Benchmark for '${jdTitle}': Similar roles typically require X-Y years of experience in Z technology. Common career progression leads to Lead/Architect positions.
This retrieved context MUST be used to ground your analysis, enhance understanding of specific terms, and provide deeper context.
--- END OF CONCEPTUAL RAG CONTEXT ---
`;
  // --- End of CONCEPTUAL Agentic RAG Steps ---

  const cacheKeyMaterial = [
    cvContent, cvMimeType, jdContent, jdMimeType, 
    cvName, jdTitle, currentLanguage,
    cvRecruiterNotes || "", jdRecruiterNotes || "",
    GEMINI_MODEL_TEXT,
    JSON.stringify({ 
      assessmentDimensions: appSettings.assessmentDimensions,
      nexusRankingScoreThreshold: appSettings.nexusRankingScoreThreshold
    }),
    ragSpecificContextString 
  ].join('||');
  const cacheKey = await sha256(cacheKeyMaterial);
  const cacheStorageKey = `recruitx_analysis_cache_${cacheKey}`;

  try {
    const cachedItemString = localStorage.getItem(cacheStorageKey);
    if (cachedItemString) {
      const cachedItem: CachedAnalysisItem = JSON.parse(cachedItemString);
      const cachedSettingsValid = cachedItem.appSettingsSnapshot && 
                                  cachedItem.appSettingsSnapshot.assessmentDimensions &&
                                  typeof cachedItem.appSettingsSnapshot.nexusRankingScoreThreshold === 'number' &&
                                  !('aiStrictness' in cachedItem.appSettingsSnapshot); // Ensures old cache with aiStrictness is invalid

      if (Date.now() - cachedItem.timestamp < CACHE_EXPIRY_MS && cachedSettingsValid) {
        console.log("Returning analysis from cache:", cacheKey);
        return { analysis: cachedItem.geminiResponse, cacheUsed: true, cacheTimestamp: cachedItem.timestamp };
      } else {
        if (!cachedSettingsValid) console.log("Cached item settings snapshot is invalid, missing properties, or contains outdated properties like aiStrictness:", cacheKey);
        else console.log("Cache expired for:", cacheKey);
        localStorage.removeItem(cacheStorageKey);
      }
    }
  } catch (e) {
    console.error("Error accessing or parsing cache:", e);
  }

  const languageInstruction = currentLanguage === Language.JA ? "Japanese" : "English";
  
  const dynamicScoresSchemaParts = activeDimensions.map(dim => 
    `    "${dim.id}": {
      "score": 0,
      "explanation": "",
      "details": {}
    }`
  ).join(',\n');
  
  const dynamicScoringInstructions = activeDimensions.map(dim => 
    `*   **${dim.label} (ID: ${dim.id}):** ${dim.promptGuidance} **Your explanation for this dimension MUST explicitly state how Recruiter Notes (if any) AND any provided RETRIEVED CONTEXT influenced the score, and what specific evidence (or lack thereof) in the CV/JD led to your assessment.**`
  ).join('\n        ');

  const systemInstruction = `
You are RecruitX, a SOTA (State-of-the-Art) AI Recruitment Assessment System by Shristyverse LLC, enhanced with Agentic RAG (Retrieval Augmented Generation) capabilities. Your primary function is to deliver exceptionally accurate, unbiased, transparent, and deeply insightful comparisons between candidate CVs and Job Descriptions (JDs). You operate through a conceptual multi-agent framework, simulating a high-level human recruitment panel augmented by a knowledge base, to ensure structured and comprehensive evaluation. Your analysis MUST heavily prioritize any Recruiter Notes AND any "RETRIEVED CONTEXT" provided. You must clearly articulate how these inputs, along with textual evidence from the CV and JD, informed your scoring for EACH dimension.

**Core Mandate: Transparency and Evidence-Based Reasoning**
*   **Show Your Work:** For every score, explicitly state *why* it was given. Reference specific phrases, sections, or the absence of information in the CV, JD, AND the "RETRIEVED CONTEXT".
*   **Recruiter Notes & Retrieved Context Impact:** Clearly explain how Recruiter Notes (for CV and/or JD) AND the "RETRIEVED CONTEXT" influenced the scoring of each specific dimension. If no notes or context were provided or relevant for a dimension, state that.
*   **Objectivity:** Base your analysis strictly on the provided textual content and retrieved factual context. Do not infer information not present, especially regarding protected characteristics or subjective qualities not detailed in the documents.

**AI Behavior Configuration:**
*   **Analysis Approach:** Employ a balanced and fair interpretation of matches, justifying scores with clear evidence from the documents and retrieved context. Focus on objective assessment.
*   **Requested Output Language:** All textual output MUST be in ${languageInstruction}.

**Input Document Handling:**
*   CVs and JDs are provided as extracted plain text. Identify candidate name (fallback to '${cvName}') and job title (fallback to '${jdTitle}').
*   The original file type (e.g., PDF, DOCX) is provided for context, but the content itself is already extracted text.
*   **Retrieved Context from Knowledge Base (RAG):** If a section titled "CONCEPTUAL_RAG_CONTEXT" or similar is provided in the input, this contains factual information fetched by specialized agents from RecruitX's knowledge base. This information is highly relevant and MUST be used to ground your analysis, enhance understanding of specific terms (skills, technologies), and provide deeper context for the role or candidate. Explicitly mention if and how this retrieved context influenced your assessment for relevant dimensions.

**Conceptual Multi-Agent AI Framework & Workflow (Enhanced with Agentic RAG):** 

1.  **Data Ingestion Agent:** Receives CV/JD text.
2.  **(RAG) Planner Agent:** Determines information needs beyond CV/JD (e.g., skill definitions, company context).
3.  **(RAG) Query Generation Agent:** Creates targeted queries for the knowledge base.
4.  **(RAG) Retrieval Agent:** Fetches relevant documents/chunks from RecruitX's knowledge base (Vector DB).
5.  **(RAG) Formatting Agent:** Prepares the \`ragSpecificContextString\`.
6.  **Recruiter Insights & Prioritization Agent (CRITICAL):** Identifies and gives highest precedence to Recruiter Notes. Also integrates and prioritizes the \`ragSpecificContextString\`. Ensures these insights directly and heavily influence subsequent analysis. **You must explain this influence in your dimension-specific explanations.**
7.  **Cross-Referencing & Evidence-Gathering Agent:** Meticulously compares CV against JD, weighted by Recruiter Insights AND the \`ragSpecificContextString\`. Gathers specific textual evidence (or notes its absence) relevant to each active Assessment Dimension.
8.  **Multi-Factor Scoring Agent (Dynamic Dimensions):**
    *   Quantifies the match for each active Assessment Dimension based *only* on the gathered evidence, Recruiter Insights, AND \`ragSpecificContextString\`:
        ${dynamicScoringInstructions}
    *   Calculates an **Overall Match Score** (0-100) based on a holistic assessment, transparently influenced by Recruiter Notes, \`ragSpecificContextString\`, and the evidence for sub-scores.
    *   Output: Numerical scores and detailed, evidence-backed explanations.

9.  **Evidence-Based Explanation & Reporting Agent:**
    *   Generates clear, concise, and actionable explanations for each dimension's score, explicitly linking scores to evidence from CV/JD, recruiter notes, AND \`ragSpecificContextString\`.
    *   Synthesizes a **Detailed Overall Analysis** that summarizes the key findings, again emphasizing the evidence and rationale.
    *   **Generate Strategic Insights (Arrays of strings):**
        *   **Key Strengths (positivePoints):** Succinctly list 3-5 key strengths based *on clear evidence from all inputs*.
        *   **Areas for Clarification (painPoints):** Identify 2-4 potential weaknesses or ambiguities *based on missing evidence or unclear statements, considering all inputs*.
        *   **Strategic Discussion Points (discussionPoints):** Formulate 3-5 questions *arising from the evidence analysis of all inputs*.
    *   **Language Mandate:** Ensures the entire output is strictly in ${languageInstruction}.

**Ethical Mandate:**
*   **Bias Mitigation:** Actively strive for objectivity. Focus solely on skills, experience, and qualifications. Do not make assumptions based on protected characteristics.
*   **Transparency:** Your explanations are paramount. They must be clear enough for a human recruiter to understand precisely how scores were derived from the provided texts, notes, and retrieved context.

**Output JSON Structure:**
You MUST return a single JSON object. Ensure ALL string values are properly escaped AND are in ${languageInstruction}.
**Crucial JSON Syntax & Key Naming:**
*   All keys MUST be in English and exactly as specified. Do NOT translate keys. (e.g., use "skill_assessment", not "skill-assessment")
*   Arrays like "positivePoints" MUST contain only strings.
*   Pay meticulous attention to commas between all object properties and array elements.
\`\`\`json
{
  "candidateName": "${cvName}",
  "jobTitle": "${jdTitle}",
  "scores": {
${dynamicScoresSchemaParts}
  },
  "overallScore": 0,
  "detailedExplanation": "",
  "positivePoints": [],
  "painPoints": [],
  "discussionPoints": []
}
\`\`\`
**Final Instruction:** Proceed with the analysis. Generate the perfect JSON output, ensuring all keys are in English. All textual values must be in ${languageInstruction} and fully justified by evidence from the provided documents, notes, and retrieved RAG context. Transparency is key.
`;

  const parts: Part[] = [];
  parts.push({ text: `CV for candidate "${cvName}" (Original file type: ${cvMimeType}):\n---\n${cvContent}\n---\n` });
  
  if (cvRecruiterNotes) {
    parts.push({ text: `Recruiter Notes for CV ("${cvName}") (Highest Priority - MUST explain impact on scores):\n---\n${cvRecruiterNotes}\n---\n` });
  } else {
     parts.push({ text: `Recruiter Notes for CV ("${cvName}"): None provided.\n`});
  }

  parts.push({ text: `Job Description for role "${jdTitle}" (Original file type: ${jdMimeType}):\n---\n${jdContent}\n---\n` });

  if (jdRecruiterNotes) {
    parts.push({ text: `Recruiter Notes for JD ("${jdTitle}") (Highest Priority - MUST explain impact on scores):\n---\n${jdRecruiterNotes}\n---\n` });
  } else {
      parts.push({ text: `Recruiter Notes for JD ("${jdTitle}"): None provided.\n`});
  }
  
  // Add the conceptual RAG context to the prompt
  parts.push({ text: `\n--- START RETRIEVED CONTEXT (Simulated RAG Output) ---\n${ragSpecificContextString}\n--- END RETRIEVED CONTEXT ---\n`});

  parts.push({text: `\nLanguage for Report: ${languageInstruction}\nBegin Analysis. Adhere strictly to the JSON output format, language requirements, transparency mandates, and assessment dimensions specified in the system instructions. Justify all scores with specific evidence and explanation of how recruiter notes AND any retrieved RAG context impacted the assessment for each dimension.`});

  try {
    const response: GenerateContentResponse = await ai.models.generateContent({
      model: GEMINI_MODEL_TEXT,
      contents: [{ role: "user", parts }],
      config: {
        systemInstruction: systemInstruction,
        responseMimeType: "application/json",
        temperature: 0.1, 
        topP: 0.7,
        topK: 30,
      }
    });
    
    const responseText = response.text || "";
    let parsedResult = parseGeminiResponse(responseText, cvName, jdTitle, activeDimensions);
    
    if (!parsedResult.candidateName || parsedResult.candidateName.trim() === "") parsedResult.candidateName = cvName;
    if (!parsedResult.jobTitle || parsedResult.jobTitle.trim() === "") parsedResult.jobTitle = jdTitle;

    try {
      const { ...settingsForCache } = appSettings;
      const itemToCache: CachedAnalysisItem = { 
        timestamp: Date.now(),
        geminiResponse: parsedResult,
        appSettingsSnapshot: JSON.parse(JSON.stringify(settingsForCache)) 
      };
      localStorage.setItem(cacheStorageKey, JSON.stringify(itemToCache));
      console.log("Analysis stored in cache:", cacheKey);
    } catch (e) {
      console.error("Error storing analysis to cache:", e);
    }

    return { analysis: parsedResult, cacheUsed: false };

  } catch (error: any) { 
    console.error('Error calling Gemini API or processing response:', error);
    const errorMessage = error.message || String(error); 
    let detailedExplanationMsg = `The AI analysis could not be completed due to an error: ${errorMessage}. Please check the application logs or try again. If the problem persists, ensure the API key is correctly configured and the Gemini API service is operational.`;

    if (errorMessage.includes("RESOURCE_EXHAUSTED") || (error.code === 429 || (error.error && error.error.code === 429))) {
        detailedExplanationMsg = "Error: You have exceeded your current Gemini API quota. Please check your Google AI Studio plan and billing details, then try again later. For more information, visit https://ai.google.dev/gemini-api/docs/rate-limits.";
    } else if (typeof error === 'object' && error !== null && 'overallScore' in error && 'scores' in error && 'detailedExplanation' in error) {
        const fallbackScores: Record<string, ScoreComponent> = {};
        activeDimensions.forEach(dim => {
            fallbackScores[dim.id] = (error.scores && error.scores[dim.id]) ? error.scores[dim.id] : { score: 0, explanation: `Error processing this dimension: ${errorMessage}` };
        });
        return { analysis: {...error, scores: fallbackScores } as GeminiAnalysisResponse, cacheUsed: false };
    }

    const errorScores: Record<string, ScoreComponent> = {};
    activeDimensions.forEach(dim => {
        errorScores[dim.id] = { score: 0, explanation: `Error during analysis for this dimension: ${errorMessage}` };
    });
    const errorResponse: GeminiAnalysisResponse = {
        candidateName: cvName,
        jobTitle: jdTitle,
        scores: errorScores,
        overallScore: 0,
        detailedExplanation: detailedExplanationMsg,
        positivePoints: [],
        painPoints: [],
        discussionPoints: [],
    };
     return { analysis: errorResponse, cacheUsed: false };
  }
};

export const getStructuredDocumentRepresentation = async (
  documentText: string,
  documentType: 'cv' | 'jd',
  language: Language,
  existingTitleOrName?: string 
): Promise<StructuredCV | StructuredJD | null> => {
  if (!API_KEY) {
    console.error("Gemini API key is not configured for document structuring.");
    return null;
  }
  if (!documentText.trim()) {
    console.warn("Document text is empty for structuring.");
    return null;
  }

  const languageInstruction = language === Language.JA ? "Japanese" : "English";
  
  let systemInstructionPreamble = `
You are an AI assistant tasked with extracting structured data from document text.
Your output MUST be a single JSON object conforming precisely to the schema provided below.
All textual content within the JSON (all string values) MUST be in ${languageInstruction}.
If a section or piece of information is not found in the document or is ambiguous, use an empty string (""), an empty array ([]), or omit the field as appropriate for the schema's definition for that field. Do NOT invent information.
The output JSON MUST include a 'sourceLanguage' field with the value "${language}".
All list items within arrays (e.g., workExperience, education, skills as list of objects) MUST have a unique 'id' string field (e.g., "work-0", "edu-1", "skillcat-0").
Strictly adhere to the JSON syntax, paying close attention to commas and quoting for all elements, especially between objects in an array.
The document context (e.g., name/title) is: "${existingTitleOrName || 'Not Provided'}".
JSON Schema to follow:
`;

  let jsonSchemaExample = "";
  if (documentType === 'cv') {
    jsonSchemaExample = `
\`\`\`json
{
  "personalInfo": {
    "fullName": "",
    "age": "",
    "sexGender": "",
    "phone": "",
    "address": "",
    "email": "",
    "linkedin": "",
    "portfolio": ""
  },
  "summary": "",
  "workExperience": [
    {
      "id": "work-0",
      "title": "",
      "company": "",
      "dates": "",
      "description": "",
      "responsibilities": [],
      "achievements": []
    }
  ],
  "education": [
    {
      "id": "edu-0",
      "degree": "",
      "institution": "",
      "graduationDate": "",
      "details": ""
    }
  ],
  "skills": [
    {
      "id": "skillcat-0",
      "category": "",
      "skills": []
    }
  ],
  "projects": [
    {
      "id": "proj-0",
      "name": "",
      "description": "",
      "technologiesUsed": [],
      "role": "",
      "dates": ""
    }
  ],
  "certifications": [],
  "awards": [],
  "languages": [],
  "otherSections": {
    "selfPR": "",
    "reasonForJobChange": ""
  },
  "sourceLanguage": "${language}"
}
\`\`\`
`;
  } else { // documentType === 'jd'
    jsonSchemaExample = `
\`\`\`json
{
  "jobTitle": "",
  "companyOverview": "",
  "roleSummary": "",
  "keyResponsibilities": [], 
  "requiredQualifications": [], 
  "preferredQualifications": [], 
  "technicalSkillsRequired": [],
  "softSkillsRequired": [],
  "benefits": [], 
  "location": "",
  "salaryRange": "",
  "otherSections": {
    "workStyle": "",
    "teamCulture": ""
  },
  "sourceLanguage": "${language}"
}
\`\`\`
`;
  }
  const systemInstruction = systemInstructionPreamble + jsonSchemaExample;

  let responseText = "";
  let jsonStr = ""; 
  let originalRepairedJsonStr = ""; 
  let prevJsonStr: string = ""; 
  let iterations = 0; 

  try {
    const response: GenerateContentResponse = await ai.models.generateContent({
      model: GEMINI_MODEL_TEXT, 
      contents: [{ role: "user", parts: [{ text: documentText }] }],
      config: {
        systemInstruction: systemInstruction,
        responseMimeType: "application/json",
        temperature: 0.05, 
        topP: 0.8,
        topK: 20,
      }
    });

    responseText = response.text || "";
    jsonStr = responseText.trim();
    const fenceRegex = /^```(\w*)?\s*\n?(.*?)\n?\s*```$/s;
    const match = jsonStr.match(fenceRegex);
    if (match && match[2]) {
      jsonStr = match[2].trim();
    }
    
    jsonStr = jsonStr.replace(/\\(?![\\/"bfnrt]|u[0-9a-fA-F]{4})/g, '');

    originalRepairedJsonStr = jsonStr; 

    iterations = 0; 
    const maxIterations = 10; 

    do {
      prevJsonStr = jsonStr;

      jsonStr = jsonStr.replace(/(\"(?:\\.|[^\"\\])*\")\s*\n(\s*)(\"(?:\\.|[^\"\\])*\")/g,'$1,\n$2$3');
      jsonStr = jsonStr.replace(/(\})\s*\n(\s*)(\{)/g, '$1,\n$2$3');
      jsonStr = jsonStr.replace(/(\"(?:\\.|[^\"\\])*\")\s*\n(\s*)(\{)/g,'$1,\n$2$3');
      jsonStr = jsonStr.replace(/(\})\s*\n(\s*)(\"(?:\\.|[^\"\\])*\")/g,'$1,\n$2$3');
      jsonStr = jsonStr.replace(/((?:true|false|null|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?))\s*\n(\s*)(\"(?:\\.|[^\"\\])*\"|\{|(?:true|false|null|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?))/g,'$1,\n$2$3');
      
      iterations++;
    } while (prevJsonStr !== jsonStr && iterations < maxIterations);

    if (iterations >= maxIterations && prevJsonStr !== jsonStr) { 
        console.warn(`JSON repair loop for ${documentType} reached max iterations. Parsing might still fail. Last state:`, jsonStr);
    } else if (iterations > 1 && originalRepairedJsonStr !== jsonStr) { 
        console.log(`JSON for ${documentType} comma-repaired after ${iterations-1} iteration(s).`);
    }
    
    const structuredData = JSON.parse(jsonStr);
    
    if (!structuredData.sourceLanguage) {
        structuredData.sourceLanguage = language;
    }

    const ensureIds = (arr: any[] | undefined, prefix: string) => {
        if (Array.isArray(arr)) {
            arr.forEach((item, index) => {
                if (typeof item === 'object' && item !== null && !item.id) {
                    item.id = `${prefix}-${index}-${Math.random().toString(36).substring(2, 7)}`;
                }
            });
        }
    };

    if (documentType === 'cv') {
        const cvData = structuredData as StructuredCV;
        ensureIds(cvData.workExperience, 'work');
        ensureIds(cvData.education, 'edu');
        if (cvData.skills && Array.isArray(cvData.skills) && (cvData.skills as any[]).length > 0 && typeof (cvData.skills as any[])[0] === 'object') {
             ensureIds(cvData.skills as SkillEntry[], 'skillcat');
        }
        ensureIds(cvData.projects, 'proj');
    } else { 
        const jdData = structuredData as StructuredJD;
        const ensureTextObjectIds = (arr: any[] | undefined, prefix: string) => {
            if (Array.isArray(arr)) {
                arr.forEach((item, index) => {
                    if (typeof item === 'object' && item !== null && item.text && !item.id) {
                         item.id = `${prefix}-${index}-${Math.random().toString(36).substring(2, 7)}`;
                    }
                });
            }
        };
        // Ensure that even if AI returns string[], we attempt to map to ResponsibilityEntry[] or QualificationEntry[]
        if (Array.isArray(jdData.keyResponsibilities) && jdData.keyResponsibilities.length > 0 && typeof jdData.keyResponsibilities[0] === 'string') {
            jdData.keyResponsibilities = (jdData.keyResponsibilities as string[]).map((text, index) => ({ id: `resp-${index}`, text }));
        }
        ensureTextObjectIds(jdData.keyResponsibilities as ResponsibilityEntry[] | undefined, 'resp');

        if (Array.isArray(jdData.requiredQualifications) && jdData.requiredQualifications.length > 0 && typeof jdData.requiredQualifications[0] === 'string') {
            jdData.requiredQualifications = (jdData.requiredQualifications as string[]).map((text, index) => ({ id: `req-${index}`, text }));
        }
        ensureTextObjectIds(jdData.requiredQualifications as QualificationEntry[] | undefined, 'req');

        if (Array.isArray(jdData.preferredQualifications) && jdData.preferredQualifications.length > 0 && typeof jdData.preferredQualifications[0] === 'string') {
            jdData.preferredQualifications = (jdData.preferredQualifications as string[]).map((text, index) => ({ id: `pref-${index}`, text }));
        }
        ensureTextObjectIds(jdData.preferredQualifications as QualificationEntry[] | undefined, 'pref');
    }

    if (documentType === 'cv') {
        if (!structuredData.personalInfo) structuredData.personalInfo = {};
        if (!structuredData.personalInfo.fullName && existingTitleOrName) {
            structuredData.personalInfo.fullName = existingTitleOrName;
        }
    } else if (documentType === 'jd' && !structuredData.jobTitle && existingTitleOrName) {
        structuredData.jobTitle = existingTitleOrName;
    }
    
    return structuredData as (StructuredCV | StructuredJD);

  } catch (error: any) {
    console.error(`Error structuring ${documentType} document:\n`, error.message);
    console.error("Original response text from AI (if available):\n", responseText || "N/A");
    const jsonAttemptedForParse = (prevJsonStr && prevJsonStr !== jsonStr && iterations > 1) ? prevJsonStr : jsonStr;
    console.error("Attempted repaired JSON string that failed parsing:\n", jsonAttemptedForParse);
    return null;
  }
};
