import { GoogleGenAI } from '@google/genai';

// Service to interact with LLM providers
class LLMService {
  private genAI: GoogleGenAI;
  private useMockImplementation: boolean;
  
  constructor() {
    // Check if we have a valid API key from various sources (with Vite prefix)
    const apiKey = process.env.VITE_GOOGLE_GENAI_API_KEY || 
                  (typeof import.meta !== 'undefined' ? import.meta.env?.VITE_GOOGLE_GENAI_API_KEY : undefined) || 
                  '';
                  
    this.useMockImplementation = !apiKey || apiKey === 'dummy-key-for-development' || apiKey === 'your-gemini-api-key-here';
    
    // Initialize with Gemini API
    this.genAI = new GoogleGenAI({ apiKey: apiKey || 'dummy-key-for-development' });
    
    if (this.useMockImplementation) {
      console.warn('No valid Google Gemini API key found. Using mock implementation for AI features.');
    }
  }
  
  /**
   * Call LLM with function calling capability
   * @param systemPrompt The system instructions for the model
   * @param userContext The user input/context for processing
   * @param functionCall The function to call with arguments
   * @returns The processed result from the model
   */
  async callWithFunctions(
    systemPrompt: string, 
    userContext: string, 
    functionCall: { name: string; arguments: Record<string, any> }
  ) {
    try {
      // If we're using mock implementation, return a demo response
      if (this.useMockImplementation) {
        return this.getMockResponse(functionCall.name, functionCall.arguments);
      }
      
      // For now, we're simulating function calling with Gemini
      // This will be replaced with proper function calling when Gemini fully supports it
      
      // Construct a prompt that includes system instructions, user context, and function call details
      const prompt = `
        ${systemPrompt}
        
        USER CONTEXT:
        ${userContext}
        
        FUNCTION TO EXECUTE:
        Function Name: ${functionCall.name}
        Function Arguments: ${JSON.stringify(functionCall.arguments, null, 2)}
        
        Please provide the result of executing this function with the given arguments.
        Respond in JSON format.
      `;
      
      // Use the gemini-2.0-flash model
      const model = this.genAI.models.generateContent({
        model: 'gemini-2.0-flash-001',
        contents: prompt,
      });
      
      const response = await model;
      const text = response.text || '';
      
      // Parse JSON response (with error handling)
      try {
        // Find JSON in the response
        const jsonMatch = text.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          return JSON.parse(jsonMatch[0]);
        }
        return { error: "No valid JSON found in response", rawResponse: text };
      } catch (parseError) {
        console.error("Error parsing LLM response as JSON:", parseError);
        return { error: "Failed to parse JSON response", rawResponse: text };
      }
    } catch (error) {
      console.error("Error calling LLM service:", error);
      throw new Error(`LLM service error: ${(error as Error).message}`);
    }
  }
  
  /**
   * Generate mock responses for demonstration purposes when no API key is available
   */
  private getMockResponse(functionName: string, args: Record<string, any>): any {
    // Default demo response
    const demoResponse = {
      status: "success",
      message: "This is a demo response. Please add a valid Google Gemini API key to use real AI features.",
    };
    
    // Generate different mock responses based on function name
    switch (functionName) {
      case "analyze_candidate_fit":
        return {
          overallScore: 85,
          candidateName: args.cv_content?.substring(0, 20) + "...",
          jobTitle: args.jd_content?.substring(0, 20) + "...",
          scores: {
            technicalSkills: 82,
            experience: 88,
            education: 90,
            softSkills: 80,
          },
          detailedExplanation: "This is a mock candidate evaluation. The candidate appears to be a good match for the position based on the provided information.",
          positivePoints: [
            "Strong technical background",
            "Relevant industry experience",
            "Good communication skills"
          ],
          painPoints: [
            "May need additional training in some areas",
            "Limited leadership experience"
          ],
          discussionPoints: [
            "Discuss previous project experience",
            "Explore interest in professional development"
          ]
        };
        
      case "identify_candidates":
        return {
          candidates: [
            { name: "Demo Candidate 1", matchScore: 92, summary: "Experienced professional with strong skills" },
            { name: "Demo Candidate 2", matchScore: 88, summary: "Recent graduate with excellent technical abilities" },
            { name: "Demo Candidate 3", matchScore: 75, summary: "Mid-level professional seeking new opportunities" }
          ],
          searchCriteria: args.search_criteria,
          totalResults: 3
        };
        
      case "plan_interview":
        return {
          interviewPlan: {
            recommendedFormat: "Panel interview",
            duration: "60 minutes",
            focusAreas: ["Technical skills", "Cultural fit", "Problem-solving abilities"],
            suggestedQuestions: [
              "Describe a challenging project you worked on recently",
              "How do you approach learning new technologies?",
              "Give an example of how you've resolved a conflict in a team"
            ]
          },
          candidateName: args.candidate_name || "Candidate",
          jobTitle: args.job_title || "Position"
        };
        
      default:
        return demoResponse;
    }
  }
}

// Singleton instance of LLM service
const llmService = new LLMService();

/**
 * Base Agent class for all specialized agents in the system
 * Provides common functionality for interacting with LLMs and processing results
 */
export class BaseAgent {
  protected systemPrompt: string;
  protected userContext: string;
  protected settings: Record<string, any>;
  
  /**
   * Create a new agent instance
   * @param systemPrompt Instructions that define the agent's behavior
   * @param initialContext Initial context for the agent
   * @param settings Agent-specific settings
   */
  constructor(
    systemPrompt: string,
    initialContext: string = "",
    settings: Record<string, any> = {}
  ) {
    this.systemPrompt = systemPrompt;
    this.userContext = initialContext;
    this.settings = settings;
  }
  
  /**
   * Update the agent's context with new information
   * @param newContext The new context to add
   * @param replace Whether to replace existing context (default: false)
   */
  updateContext(newContext: string, replace: boolean = false) {
    if (replace) {
      this.userContext = newContext;
    } else {
      this.userContext += "\n\n" + newContext;
    }
  }
  
  /**
   * Update agent settings
   * @param newSettings Settings to update
   */
  updateSettings(newSettings: Record<string, any>) {
    this.settings = { ...this.settings, ...newSettings };
  }
  
  /**
   * Call a function using the LLM
   * @param functionName Name of the function to call
   * @param args Arguments for the function
   * @returns The processed result
   */
  async callFunction(functionName: string, args: Record<string, any>) {
    const result = await llmService.callWithFunctions(
      this.systemPrompt,
      this.userContext,
      { name: functionName, arguments: args }
    );
    
    return this.processResult(result);
  }
  
  /**
   * Process the result from an LLM call
   * Override in derived classes for specialized processing
   * @param result The raw result from the LLM
   * @returns The processed result
   */
  protected processResult(result: any) {
    // Basic implementation - derived classes should override
    if (result.error) {
      console.error("Error in LLM response:", result.error);
      throw new Error(`Agent error: ${result.error}`);
    }
    
    return result;
  }
}

export default BaseAgent; 