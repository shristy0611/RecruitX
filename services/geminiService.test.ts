
// FIX: Declare Jest global functions and types to avoid TypeScript errors when @types/jest is not available.
declare var describe: any;
declare var it: any;
declare var expect: any;
declare var beforeEach: any;

// Declare the jest global object
declare var jest: {
  // Typing for jest.fn() to return our defined jest.Mock type
  fn: <T = any, Y extends any[] = any>() => jest.Mock<T, Y>;
  clearAllMocks: () => void;
  // Typing for jest.mock()
  mock: (moduleName: string, factory?: () => any, options?: object) => typeof jest;
  // Add other jest properties/methods if needed, e.g., spyOn
};

// Declare the jest namespace for types like jest.Mock
declare namespace jest {
  // Basic definition for jest.Mock type
  interface Mock<T = any, Y extends any[] = any> extends Function {
    (...args: Y): T;
    mock: {
      calls: Y[];
      instances: any[]; 
      invocationCallOrder: number[];
      results: Array<{ type: 'return' | 'throw', value: any }>;
      lastCall?: Y;
    };
    mockClear(): void;
    mockReset(): void;
    mockRestore(): void;
    mockReturnValue(value: T): this;
    mockReturnValueOnce(value: T): this;
    mockResolvedValue(value: any): this; 
    mockResolvedValueOnce(value: any): this;
    mockRejectedValue(value: any): this;
    mockRejectedValueOnce(value: any): this;
    mockImplementation(fn: (...args: Y) => T): this;
    mockImplementationOnce(fn: (...args: Y) => T): this;
    getMockName(): string;
  }
}


import { analyzeCvJdMatch, parseGeminiResponse } from './geminiService'; 
import { 
    DEFAULT_APP_SETTINGS, 
    DEFAULT_ASSESSMENT_DIMENSIONS, 
    GEMINI_MODEL_TEXT 
} from '../constants';
import { Language, GeminiAnalysisResponse, AppSettings, ScoreComponent, CachedAnalysisItem } from '../types';
import { GoogleGenAI } from '@google/genai';

// Mocking @google/genai
jest.mock('@google/genai', () => {
  const mockGenerateContent = jest.fn();
  return {
    GoogleGenAI: jest.fn().mockImplementation(() => ({
      models: {
        generateContent: mockGenerateContent,
      },
    })),
  };
});

// Mocking localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mocking crypto.subtle for sha256
Object.defineProperty(globalThis, 'crypto', {
  value: {
    subtle: {
      digest: jest.fn().mockImplementation(async (algorithm: any, data: any) => {
        const MOCKED_HASH_BUFFER_EMPTY = new Uint8Array([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]).buffer;
        if (data instanceof ArrayBuffer && data.byteLength > 0) {
             const dataView = new Uint8Array(data);
             let sum = 0;
             for(let i=0; i< dataView.length; i++){
                 sum = (sum + dataView[i]) % 256;
             }
             const hash = new Uint8Array(32); 
             hash.fill(sum);
             return hash.buffer;
        }
        return MOCKED_HASH_BUFFER_EMPTY; 
      }),
    },
    getRandomValues: jest.fn(), 
  },
  writable: true, 
});


describe('geminiService', () => {
  let mockGenerateContentFn: jest.Mock;

  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
    const mockAiInstance = new GoogleGenAI({ apiKey: 'test-key' });
    mockGenerateContentFn = mockAiInstance.models.generateContent as jest.Mock;
  });

  describe('parseGeminiResponse', () => {
    const activeDimensions = DEFAULT_ASSESSMENT_DIMENSIONS.filter(d => d.isActive);
    const fallbackCvName = "Test CV";
    const fallbackJdTitle = "Test JD";

    it('should parse a valid full JSON response correctly', () => {
      const validResponseData = {
        candidateName: "Jane Doe",
        jobTitle: "Software Engineer",
        scores: {
          skill_assessment: { score: 85, explanation: "Good skills", details: { matched: ["React"], missing: ["Angular"] } },
          experience_alignment: { score: 90, explanation: "Relevant experience" },
          professionalism_collaboration: {score: 80, explanation: "Good"},
          problem_solving_complexity: {score: 80, explanation: "Good"},
          impact_achievements_quantified: {score: 80, explanation: "Good"},
          learning_agility_adaptability: {score: 80, explanation: "Good"},
          leadership_initiative: {score: 80, explanation: "Good"},
          communication_clarity_cv: {score: 80, explanation: "Good"},
          key_term_technology_alignment: {score: 80, explanation: "Good"},
          holistic_impression_xfactor: {score: 80, explanation: "Good"},
        },
        overallScore: 88,
        detailedExplanation: "Overall a good fit.",
        positivePoints: ["Strong in React"],
        painPoints: ["Lacks Angular"],
        discussionPoints: ["Discuss Angular projects"]
      };
      const validResponseText = JSON.stringify(validResponseData);
      const result = parseGeminiResponse(validResponseText, fallbackCvName, fallbackJdTitle, activeDimensions);
      expect(result.candidateName).toBe("Jane Doe");
      expect(result.overallScore).toBe(88);
      expect(result.scores.skill_assessment?.score).toBe(85);
      expect(result.positivePoints).toEqual(["Strong in React"]);
      expect(result.painPoints).toEqual(["Lacks Angular"]);
      expect(result.discussionPoints).toEqual(["Discuss Angular projects"]);
    });

    it('should handle JSON wrapped in markdown code fences', () => {
       const responseData = {
        candidateName: "Jane Doe",
        jobTitle: "Software Engineer",
        scores: { skill_assessment: { score: 70, explanation: "Okay" }, 
            experience_alignment: { score: 90, explanation: "Relevant experience" },
            professionalism_collaboration: {score: 80, explanation: "Good"},
            problem_solving_complexity: {score: 80, explanation: "Good"},
            impact_achievements_quantified: {score: 80, explanation: "Good"},
            learning_agility_adaptability: {score: 80, explanation: "Good"},
            leadership_initiative: {score: 80, explanation: "Good"},
            communication_clarity_cv: {score: 80, explanation: "Good"},
            key_term_technology_alignment: {score: 80, explanation: "Good"},
            holistic_impression_xfactor: {score: 80, explanation: "Good"},
        },
        overallScore: 75,
        detailedExplanation: "Decent."
      };
      const fencedResponseText = "```json\n" + JSON.stringify(responseData) + "\n```";
      const result = parseGeminiResponse(fencedResponseText, fallbackCvName, fallbackJdTitle, activeDimensions);
      expect(result.overallScore).toBe(75);
      expect(result.scores.skill_assessment?.explanation).toBe("Okay");
    });
    
    it('should return fallback structure on invalid JSON', () => {
      const invalidJson = "{ candidateName: 'Test', score: 100 "; // Malformed
      const result = parseGeminiResponse(invalidJson, fallbackCvName, fallbackJdTitle, activeDimensions);
      expect(result.overallScore).toBe(0);
      expect(result.detailedExplanation).toContain("Critical Error: The AI's response could not be reliably parsed");
      activeDimensions.forEach(dim => {
        expect(result.scores[dim.id]?.score).toBe(0);
        expect(result.scores[dim.id]?.explanation).toContain("Error: AI response parsing failed");
      });
    });

    it('should return fallback if a required active dimension score is missing', () => {
        const missingDimensionJson = JSON.stringify({
            candidateName: "Jane Doe",
            jobTitle: "Software Engineer",
            scores: { 
              skill_assessment: { score: 85, explanation: "Good skills" },
            },
            overallScore: 88,
            detailedExplanation: "Overall a good fit.",
        });
        const result = parseGeminiResponse(missingDimensionJson, fallbackCvName, fallbackJdTitle, activeDimensions);
        expect(result.overallScore).toBe(0); 
        expect(result.detailedExplanation).toContain("Critical Error");
    });

    it('should correctly parse when optional fields like positivePoints are missing', () => {
      const minimalValidResponseData = {
        candidateName: "Min Doe",
        jobTitle: "Intern",
        scores: { skill_assessment: { score: 60, explanation: "Basic" },
            experience_alignment: { score: 90, explanation: "Relevant experience" },
            professionalism_collaboration: {score: 80, explanation: "Good"},
            problem_solving_complexity: {score: 80, explanation: "Good"},
            impact_achievements_quantified: {score: 80, explanation: "Good"},
            learning_agility_adaptability: {score: 80, explanation: "Good"},
            leadership_initiative: {score: 80, explanation: "Good"},
            communication_clarity_cv: {score: 80, explanation: "Good"},
            key_term_technology_alignment: {score: 80, explanation: "Good"},
            holistic_impression_xfactor: {score: 80, explanation: "Good"},
        },
        overallScore: 65,
        detailedExplanation: "Basic fit."
      };
      const minimalValidResponse = JSON.stringify(minimalValidResponseData);
      const result = parseGeminiResponse(minimalValidResponse, fallbackCvName, fallbackJdTitle, activeDimensions);
      expect(result.overallScore).toBe(65);
      expect(result.positivePoints).toBeUndefined();
      expect(result.painPoints).toBeUndefined();
      expect(result.discussionPoints).toBeUndefined();
    });

    it('should apply heuristic to fix missing comma between object properties', () => {
      const malformedJson = `{
        "candidateName": "Test",
        "jobTitle": "Test Job",
        "scores": {
          "skill_assessment": { "score": 80, "explanation": "Good" } 
          "experience_alignment": { "score": 70, "explanation": "Okay" },
          "professionalism_collaboration": { "score": 70, "explanation": "Okay" },
          "problem_solving_complexity": { "score": 70, "explanation": "Okay" },
          "impact_achievements_quantified": { "score": 70, "explanation": "Okay" },
          "learning_agility_adaptability": { "score": 70, "explanation": "Okay" },
          "leadership_initiative": { "score": 70, "explanation": "Okay" },
          "communication_clarity_cv": { "score": 70, "explanation": "Okay" },
          "key_term_technology_alignment": { "score": 70, "explanation": "Okay" },
          "holistic_impression_xfactor": { "score": 70, "explanation": "Okay" }
        },
        "overallScore": 75,
        "detailedExplanation": "Heuristic test"
      }`;
      const result = parseGeminiResponse(malformedJson, "FallbackName", "FallbackTitle", activeDimensions);
      expect(result.overallScore).toBe(75);
      expect(result.scores.skill_assessment?.score).toBe(80);
      expect(result.scores.experience_alignment?.score).toBe(70);
    });
  });

  describe('analyzeCvJdMatch', () => {
    const cvContent = "Test CV Content";
    const cvMimeType = "text/plain";
    const jdContent = "Test JD Content";
    const jdMimeType = "text/plain";
    const cvName = "Candidate Test";
    const jdTitle = "Job Test";
    const currentLanguage = Language.EN;
    const appSettings = DEFAULT_APP_SETTINGS;
     const ragSpecificContextString = `CONCEPTUAL_RAG_CONTEXT:
This is placeholder text simulating retrieved information. In a full Agentic RAG system, this section would contain dynamically fetched, highly relevant data from RecruitX's curated knowledge base. Examples:
- Skill Definition for 'Kubernetes': Includes understanding of pods, services, deployments, Helm charts, and basic cluster administration. Proficiency levels: Basic (can deploy existing charts), Intermediate (can create custom charts, troubleshoot common issues), Advanced (can design and manage complex cluster architectures, optimize performance).
- Company Insight for '${jdTitle.includes("Acme") ? "Acme Corp" : "Target Company"}': Known for a fast-paced, innovative environment valuing collaboration and continuous learning. Engineering teams often use agile methodologies.
- Role Benchmark for '${jdTitle}': Similar roles typically require X-Y years of experience in Z technology. Common career progression leads to Lead/Architect positions.
This retrieved context MUST be used to ground your analysis, enhance understanding of specific terms, and provide deeper context.
--- END OF CONCEPTUAL RAG CONTEXT ---
`;


    const mockApiResponse = (data: Partial<GeminiAnalysisResponse>) => {
      const fullDefaultScores: Record<string, ScoreComponent> = {};
       DEFAULT_ASSESSMENT_DIMENSIONS.filter(d=>d.isActive).forEach(dim => {
            fullDefaultScores[dim.id] = { score: 50, explanation: `Default for ${dim.label}` };
        });

      mockGenerateContentFn.mockResolvedValueOnce({
        text: JSON.stringify({
          candidateName: cvName,
          jobTitle: jdTitle,
          scores: data.scores || fullDefaultScores,
          overallScore: data.overallScore || 0,
          detailedExplanation: data.detailedExplanation || "Mocked explanation",
          positivePoints: data.positivePoints || [],
          painPoints: data.painPoints || [],
          discussionPoints: data.discussionPoints || [],
        }),
      });
    };

    it('should call Gemini API with a system prompt reflecting appSettings', async () => {
      mockApiResponse({ overallScore: 77 });
      
      const customSettings: AppSettings = {
        ...DEFAULT_APP_SETTINGS,
        assessmentDimensions: DEFAULT_ASSESSMENT_DIMENSIONS.map((dim, i) => ({
          ...dim,
          isActive: i < 2, // Only first 2 dimensions active
          promptGuidance: `Custom guidance for ${dim.label}`
        }))
      };

      await analyzeCvJdMatch(cvContent, cvMimeType, jdContent, jdMimeType, cvName, jdTitle, Language.JA, customSettings);

      expect(mockGenerateContentFn).toHaveBeenCalledTimes(1);
      const apiCallArgs = mockGenerateContentFn.mock.calls[0][0];
      
      expect(apiCallArgs.model).toBe(GEMINI_MODEL_TEXT);
      const systemInstruction = apiCallArgs.config.systemInstruction;

      expect(systemInstruction).toContain("All textual output MUST be in Japanese.");
      expect(systemInstruction).toContain("Employ a balanced and fair interpretation of matches");


      expect(systemInstruction).toContain(`**${customSettings.assessmentDimensions[0].label} (ID: ${customSettings.assessmentDimensions[0].id}):** Custom guidance for ${customSettings.assessmentDimensions[0].label}`);
      expect(systemInstruction).toContain(`**${customSettings.assessmentDimensions[1].label} (ID: ${customSettings.assessmentDimensions[1].id}):** Custom guidance for ${customSettings.assessmentDimensions[1].label}`);
      if (customSettings.assessmentDimensions.length > 2 && customSettings.assessmentDimensions[2]) { 
         expect(systemInstruction).not.toContain(customSettings.assessmentDimensions[2].label); 
      }
      expect(systemInstruction).toContain('"positivePoints":');
      expect(systemInstruction).toContain('"painPoints":');
      expect(systemInstruction).toContain('"discussionPoints":');

      const userParts = apiCallArgs.contents[0].parts;
      expect(userParts.some((p: any) => p.text && p.text.includes(ragSpecificContextString))).toBe(true);
    });

    it('should use cache if valid item exists', async () => {
       const defaultScores: Record<string, ScoreComponent> = {};
        DEFAULT_ASSESSMENT_DIMENSIONS.filter(d => d.isActive).forEach(dim => {
            defaultScores[dim.id] = { score: 99, explanation: `Cached for ${dim.label}` };
        });
      const cachedResponse: GeminiAnalysisResponse = {
        candidateName: cvName,
        jobTitle: jdTitle,
        scores: defaultScores,
        overallScore: 99,
        detailedExplanation: "From cache",
      };
      const cachedItem: CachedAnalysisItem = {
        timestamp: Date.now() - 1000, // Recent
        geminiResponse: cachedResponse,
        appSettingsSnapshot: appSettings, // Ensure this matches the current AppSettings structure (no aiStrictness)
      };
      
      const cacheKeyMaterial = [
        cvContent, cvMimeType, jdContent, jdMimeType,
        cvName, jdTitle, currentLanguage,
        "", "", 
        GEMINI_MODEL_TEXT,
        JSON.stringify(appSettings), // AppSettings without aiStrictness
        ragSpecificContextString
      ].join('||');
      
      const testBuffer = new TextEncoder().encode(cacheKeyMaterial);
      const mockedDigestBuffer = await globalThis.crypto.subtle.digest('SHA-256', testBuffer);
      const mockHashHex = Array.from(new Uint8Array(mockedDigestBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
      const cacheStorageKey = `recruitx_analysis_cache_${mockHashHex}`;

      localStorageMock.setItem(cacheStorageKey, JSON.stringify(cachedItem));

      const { analysis, cacheUsed } = await analyzeCvJdMatch(cvContent, cvMimeType, jdContent, jdMimeType, cvName, jdTitle, currentLanguage, appSettings);
      
      expect(cacheUsed).toBe(true);
      expect(analysis.overallScore).toBe(99);
      expect(mockGenerateContentFn).not.toHaveBeenCalled();
    });

    it('should call API if cache is expired', async () => {
      const defaultScoresExpired: Record<string, ScoreComponent> = {};
        DEFAULT_ASSESSMENT_DIMENSIONS.filter(d => d.isActive).forEach(dim => {
            defaultScoresExpired[dim.id] = { score: 10, explanation: `Expired for ${dim.label}` };
        });
      const expiredCachedResponse: GeminiAnalysisResponse = { candidateName: "Expired", jobTitle: "Old Job", overallScore: 10, scores: defaultScoresExpired, detailedExplanation: "Expired" };
      const expiredCachedItem: CachedAnalysisItem = {
        timestamp: Date.now() - (2 * 24 * 60 * 60 * 1000), // Expired
        geminiResponse: expiredCachedResponse,
        appSettingsSnapshot: appSettings,
      };
      const cacheKeyMaterial = [ 
          cvContent, cvMimeType, jdContent, jdMimeType,
          cvName, jdTitle, currentLanguage,
          "", "", 
          GEMINI_MODEL_TEXT,
          JSON.stringify(appSettings),
          ragSpecificContextString
       ].join('||');
      const testBuffer = new TextEncoder().encode(cacheKeyMaterial);
      const mockedDigestBuffer = await globalThis.crypto.subtle.digest('SHA-256', testBuffer);
      const mockHashHex = Array.from(new Uint8Array(mockedDigestBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
      const cacheStorageKey = `recruitx_analysis_cache_${mockHashHex}`;

      localStorageMock.setItem(cacheStorageKey, JSON.stringify(expiredCachedItem));
      
      const defaultScoresNew: Record<string, ScoreComponent> = {};
        DEFAULT_ASSESSMENT_DIMENSIONS.filter(d => d.isActive).forEach(dim => {
            defaultScoresNew[dim.id] = { score: 78, explanation: `New for ${dim.label}` };
        });
      mockApiResponse({ overallScore: 78, scores: defaultScoresNew });

      const { analysis, cacheUsed } = await analyzeCvJdMatch(cvContent, cvMimeType, jdContent, jdMimeType, cvName, jdTitle, currentLanguage, appSettings);

      expect(cacheUsed).toBe(false);
      expect(analysis.overallScore).toBe(78);
      expect(mockGenerateContentFn).toHaveBeenCalledTimes(1);
      expect(localStorageMock.getItem(cacheStorageKey)).not.toBeNull(); 
    });

    it('should incorporate recruiter notes into the prompt parts', async () => {
        const defaultScoresNotes: Record<string, ScoreComponent> = {};
        DEFAULT_ASSESSMENT_DIMENSIONS.filter(d => d.isActive).forEach(dim => {
            defaultScoresNotes[dim.id] = { score: 70, explanation: `Notes test for ${dim.label}` };
        });
        mockApiResponse({ overallScore: 70, scores: defaultScoresNotes });
        const cvNotes = "CV Note: Focus on leadership";
        const jdNotes = "JD Note: Needs strong communication";

        await analyzeCvJdMatch(cvContent, cvMimeType, jdContent, jdMimeType, cvName, jdTitle, currentLanguage, appSettings, cvNotes, jdNotes);
        
        expect(mockGenerateContentFn).toHaveBeenCalledTimes(1);
        const apiCallArgs = mockGenerateContentFn.mock.calls[0][0];
        const parts = apiCallArgs.contents[0].parts;

        const cvNotesPart = parts.find((p: any) => p.text?.includes(cvNotes));
        const jdNotesPart = parts.find((p: any) => p.text?.includes(jdNotes));

        expect(cvNotesPart).toBeDefined();
        expect(cvNotesPart.text).toContain("Recruiter Notes for CV (\"Candidate Test\") (Highest Priority):");
        expect(jdNotesPart).toBeDefined();
        expect(jdNotesPart.text).toContain("Recruiter Notes for JD (\"Job Test\") (Highest Priority):");
    });
  });
});
