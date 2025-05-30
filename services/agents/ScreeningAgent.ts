import { BaseAgent } from './BaseAgent';
import { documentService } from '../documentService';

/**
 * Specialized agent for screening candidates against job descriptions
 * Evaluates candidate fit, analyzes qualifications, and generates follow-up questions
 */
export class ScreeningAgent extends BaseAgent {
  /**
   * Create a new screening agent with specialized system prompt
   */
  constructor() {
    const systemPrompt = `
      You are an expert AI Recruitment Assistant specializing in candidate screening.
      Your task is to carefully analyze candidate CVs against job descriptions to evaluate fit.
      
      For each evaluation:
      1. Extract key qualifications, skills, and experience from both the CV and JD
      2. Compare candidate's qualifications against JD requirements
      3. Identify strengths and gaps in the candidate's profile
      4. Calculate an overall match score (0-100)
      5. Generate thoughtful follow-up questions for areas that need clarification
      
      Provide structured analysis with:
      - Overall score with justification
      - Key strengths with specific evidence
      - Qualification gaps with specific details
      - Follow-up questions to clarify potential gaps
      
      Be objective, focus on evidence, and avoid bias in your assessments.
    `;
    
    super(systemPrompt);
  }
  
  /**
   * Evaluate a candidate against a job description
   * @param cvId The ID of the candidate's CV
   * @param jdId The ID of the job description
   * @returns Detailed evaluation of the candidate's fit for the role
   */
  async evaluateCandidate(cvId: string, jdId: string) {
    try {
      const cv = await documentService.getDocumentById(cvId);
      const jd = await documentService.getDocumentById(jdId);
      
      if (!cv || !jd) {
        throw new Error(`Document not found: ${!cv ? 'CV' : 'JD'}`);
      }
      
      // Update context with document contents
      this.updateContext(`
        CV CONTENT:
        ${cv.content}
        
        JD CONTENT:
        ${jd.content}
        
        EVALUATION CRITERIA:
        ${JSON.stringify(this.settings.evaluationCriteria || {})}
      `);
      
      const analysis = await this.callFunction("analyze_candidate_fit", {
        cv_id: cvId,
        jd_id: jdId,
        cv_content: cv.content,
        jd_content: jd.content,
        evaluation_criteria: this.settings.evaluationCriteria || {}
      });
      
      return {
        candidateId: cvId,
        jobId: jdId,
        score: analysis.overallScore,
        strengths: analysis.strengths,
        gaps: analysis.gaps,
        suggestedQuestions: analysis.followUpQuestions,
        detailedAnalysis: analysis.detailedAnalysis
      };
    } catch (error) {
      console.error("Error in candidate evaluation:", error);
      throw new Error(`Screening agent error: ${(error as Error).message}`);
    }
  }
  
  /**
   * Generate personalized follow-up questions for a candidate
   * @param cvId The ID of the candidate's CV
   * @param jdId The ID of the job description
   * @param focusAreas Areas to focus questions on (optional)
   * @returns List of personalized follow-up questions
   */
  async generateFollowUpQuestions(cvId: string, jdId: string, focusAreas?: string[]) {
    try {
      const cv = await documentService.getDocumentById(cvId);
      const jd = await documentService.getDocumentById(jdId);
      
      if (!cv || !jd) {
        throw new Error(`Document not found: ${!cv ? 'CV' : 'JD'}`);
      }
      
      // Update context with document contents
      this.updateContext(`
        CV CONTENT:
        ${cv.content}
        
        JD CONTENT:
        ${jd.content}
        
        FOCUS AREAS:
        ${focusAreas ? focusAreas.join(', ') : 'All relevant areas'}
      `);
      
      const result = await this.callFunction("generate_follow_up_questions", {
        cv_id: cvId,
        jd_id: jdId,
        focus_areas: focusAreas || []
      });
      
      return {
        candidateId: cvId,
        jobId: jdId,
        questions: result.questions,
        focusAreas: result.focusAreas
      };
    } catch (error) {
      console.error("Error generating follow-up questions:", error);
      throw new Error(`Screening agent error: ${(error as Error).message}`);
    }
  }
} 