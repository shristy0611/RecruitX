// API Service for LLM Integration

// Types
export type ModelProvider = 'gemma' | 'gemini';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatCompletionRequest {
  messages: ChatMessage[];
  model: ModelProvider;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatCompletionResponse {
  message: ChatMessage;
  model: string;
}

// Base API URL
const API_BASE_URL = 'http://localhost:5176/api';

// API endpoints
const ENDPOINTS = {
  GEMMA_CHAT: `${API_BASE_URL}/llm/local/gemma/chat`,
  GEMINI_CHAT: `${API_BASE_URL}/llm/cloud/gemini/chat`,
  ANALYZE_RESUME: `${API_BASE_URL}/recruiting/analyze-resume`,
  SCREEN_CANDIDATE: `${API_BASE_URL}/recruiting/screen-candidate`,
  GENERATE_JOB_DESCRIPTION: `${API_BASE_URL}/recruiting/generate-job-description`,
  MATCH_CANDIDATES: `${API_BASE_URL}/agents/matching`,
  AGENT_TRIGGER: `${API_BASE_URL}/agents/trigger`,
  UPLOAD_JOB: `${API_BASE_URL}/jobs/upload`,
  SOURCING_SEARCH: `${API_BASE_URL}/agents/sourcing`,
  ENGAGE_CANDIDATE: `${API_BASE_URL}/agents/engagement`,
};

// Error handling
const handleResponse = async (response: Response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `API Error: ${response.status}`);
  }
  return response.json();
};

// API Service
export interface ApiService {
  chatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse>;
  analyzeResume(resumeText: string, model?: ModelProvider): Promise<any>;
  screenCandidate(candidateData: any, jobDescription: string, model?: ModelProvider): Promise<any>;
  generateJobDescription(jobDetails: any, model?: ModelProvider): Promise<any>;
  uploadJob(formData: FormData): Promise<{ jobId: string; status: string }>;
  sourcingSearch(query: { query: string; model: string }): Promise<any[]>;
  matchCandidates(data: { jobId: string; model: string }): Promise<any[]>;
  engageCandidate(data: { candidateId: string; message: string; model: string }): Promise<any>;
  triggerAgentFlow(data: { jobId: string; agent: 'sourcing' | 'matching' | 'engagement' }): Promise<any>;
}

export const apiService: ApiService = {
  // Chat completion with selected model
  async chatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    const endpoint = request.model === 'gemma' ? ENDPOINTS.GEMMA_CHAT : ENDPOINTS.GEMINI_CHAT;
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: request.messages,
        temperature: request.temperature || 0.7,
        max_tokens: request.max_tokens || 1024,
      }),
    });

    return handleResponse(response);
  },

  // Analyze resume with AI
  async analyzeResume(resumeText: string, model: ModelProvider = 'gemma'): Promise<any> {
    const response = await fetch(ENDPOINTS.ANALYZE_RESUME, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        resume: resumeText,
        model,
      }),
    });

    return handleResponse(response);
  },

  // Screen candidate with AI
  async screenCandidate(candidateData: any, jobDescription: string, model: ModelProvider = 'gemma'): Promise<any> {
    const response = await fetch(ENDPOINTS.SCREEN_CANDIDATE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        candidate: candidateData,
        job_description: jobDescription,
        model,
      }),
    });

    return handleResponse(response);
  },

  // Generate job description with AI
  async generateJobDescription(jobDetails: any, model: ModelProvider = 'gemma'): Promise<any> {
    const response = await fetch(ENDPOINTS.GENERATE_JOB_DESCRIPTION, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        job_details: jobDetails,
        model,
      }),
    });

    return handleResponse(response);
  },

  // Match candidates to job
  async matchCandidates(data: { jobId: string; model: string }): Promise<any[]> {
    const response = await fetch(ENDPOINTS.MATCH_CANDIDATES, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Matching failed');
    return response.json();
  },

  // Upload job
  async uploadJob(formData: FormData): Promise<{ jobId: string; status: string }> {
    const response = await fetch(ENDPOINTS.UPLOAD_JOB, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Upload failed');
    return response.json();
  },

  // Sourcing search
  async sourcingSearch(query: { query: string; model: string }): Promise<any[]> {
    const response = await fetch(ENDPOINTS.SOURCING_SEARCH, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(query),
    });
    if (!response.ok) throw new Error('Sourcing search failed');
    return response.json();
  },

  // Engage candidate
  async engageCandidate(data: { candidateId: string; message: string; model: string }): Promise<any> {
    const response = await fetch(ENDPOINTS.ENGAGE_CANDIDATE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Engagement failed');
    return response.json();
  },

  // Trigger agent flow
  async triggerAgentFlow(data: { jobId: string; agent: 'sourcing' | 'matching' | 'engagement' }): Promise<any> {
    const response = await fetch(ENDPOINTS.AGENT_TRIGGER, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },
};

export default apiService;