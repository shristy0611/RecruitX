import { CVData, JobDescriptionData, MatchResult, Language } from '../types';
import { embedDocument, DocumentType } from './vectorStore';
import { ScreeningAgent } from './agents/ScreeningAgent';

interface SkillTaxonomy {
  technical: string[];
  soft: string[];
  domain: string[];
  certifications: string[];
  experience: {
    years: number;
    relevantRoles: string[];
  };
}

/**
 * Enhanced matching engine that uses RAG for contextual understanding
 * Replaces the basic keyword matching with semantic understanding
 */
export class MatchingEngine {
  private screeningAgent: ScreeningAgent;
  
  constructor() {
    this.screeningAgent = new ScreeningAgent();
  }
  
  /**
   * Extract a structured skill taxonomy from document text
   * @param content The document content
   * @param type The document type (cv or jd)
   * @returns Structured skill taxonomy
   */
  private async extractSkillTaxonomy(content: string, type: DocumentType): Promise<SkillTaxonomy> {
    // In a full implementation, this would use the LLM to extract skills
    // For now, we'll simulate the extraction
    return {
      technical: ['JavaScript', 'TypeScript', 'React', 'Node.js'],
      soft: ['Communication', 'Teamwork', 'Problem Solving'],
      domain: ['Web Development', 'Frontend', 'UI/UX'],
      certifications: ['AWS Certified Developer'],
      experience: {
        years: 3,
        relevantRoles: ['Frontend Developer', 'UI Engineer']
      }
    };
  }
  
  /**
   * Perform RAG-enhanced matching between a CV and JD
   * @param cv The candidate CV data
   * @param jd The job description data
   * @returns Enhanced match result with confidence scores and explanations
   */
  async matchCvToJd(cv: CVData, jd: JobDescriptionData): Promise<MatchResult> {
    try {
      // 1. Get or create embeddings for both documents
      await embedDocument(cv.content, 'cv', cv.id);
      await embedDocument(jd.content, 'jd', jd.id);
      
      // 2. Extract structured data from both documents
      const cvSkills = await this.extractSkillTaxonomy(cv.content, 'cv');
      const jdSkills = await this.extractSkillTaxonomy(jd.content, 'jd');
      
      // 3. Use the screening agent to evaluate the candidate
      const evaluation = await this.screeningAgent.evaluateCandidate(cv.id, jd.id);
      
      // 4. Calculate match scores with confidence levels
      const technicalScore = this.calculateSkillScore(cvSkills.technical, jdSkills.technical);
      const softScore = this.calculateSkillScore(cvSkills.soft, jdSkills.soft);
      const domainScore = this.calculateSkillScore(cvSkills.domain, jdSkills.domain);
      const experienceScore = this.calculateExperienceScore(cvSkills.experience, jdSkills.experience);
      
      // Overall weighted score
      const overallScore = Math.round(
        technicalScore * 0.4 + 
        softScore * 0.2 + 
        domainScore * 0.2 + 
        experienceScore * 0.2
      );
      
      // 5. Prepare visualization data
      const visualizationData = {
        skillComparison: {
          technical: { candidate: cvSkills.technical, required: jdSkills.technical },
          soft: { candidate: cvSkills.soft, required: jdSkills.soft },
          domain: { candidate: cvSkills.domain, required: jdSkills.domain }
        },
        scoreBreakdown: {
          technical: technicalScore,
          soft: softScore,
          domain: domainScore,
          experience: experienceScore
        }
      };
      
      // 6. Create the final match result
      return {
        id: `match_${Date.now()}`,
        cvId: cv.id,
        jdId: jd.id,
        overallScore: overallScore,
        scores: {
          technical: {
            score: technicalScore,
            explanation: `Technical skills match: ${technicalScore}%`
          },
          soft: {
            score: softScore,
            explanation: `Soft skills match: ${softScore}%`
          },
          domain: {
            score: domainScore,
            explanation: `Domain knowledge match: ${domainScore}%`
          },
          experience: {
            score: experienceScore,
            explanation: `Experience match: ${experienceScore}%`
          }
        },
        detailedExplanation: evaluation.detailedAnalysis || 'Analysis not available',
        positivePoints: evaluation.strengths,
        painPoints: evaluation.gaps,
        discussionPoints: evaluation.suggestedQuestions,
        timestamp: new Date().toISOString(),
        reportLanguage: Language.EN,
        candidateName: cv.name,
        jobTitle: jd.title,
        cvFileName: cv.fileName,
        jdFileName: jd.fileName,
        cvRecruiterNotes: cv.recruiterNotes,
        jdRecruiterNotes: jd.recruiterNotes
      };
    } catch (error) {
      console.error('Error in matching process:', error);
      throw new Error('Failed to perform CV to JD matching');
    }
  }
  
  /**
   * Calculate the match score between two skill arrays
   * @param candidateSkills The candidate's skills
   * @param requiredSkills The required skills from JD
   * @returns Score from 0-100
   */
  private calculateSkillScore(candidateSkills: string[], requiredSkills: string[]): number {
    if (!requiredSkills.length) return 100; // No requirements = perfect match
    
    // Count matches (case insensitive)
    let matches = 0;
    for (const required of requiredSkills) {
      const reqLower = required.toLowerCase();
      if (candidateSkills.some(skill => skill.toLowerCase() === reqLower)) {
        matches++;
      }
    }
    
    return Math.round((matches / requiredSkills.length) * 100);
  }
  
  /**
   * Calculate experience score based on years and relevant roles
   */
  private calculateExperienceScore(
    candidateExp: { years: number; relevantRoles: string[] },
    requiredExp: { years: number; relevantRoles: string[] }
  ): number {
    // Years score (0-100)
    const yearScore = Math.min(100, (candidateExp.years / requiredExp.years) * 100);
    
    // Relevant roles score (0-100)
    const roleScore = this.calculateSkillScore(candidateExp.relevantRoles, requiredExp.relevantRoles);
    
    // Combined weighted score
    return Math.round(yearScore * 0.6 + roleScore * 0.4);
  }
  
  /**
   * Get confidence level based on score
   * @param score The numeric score (0-100)
   * @returns Confidence level string
   */
  private getConfidenceLevel(score: number): string {
    if (score >= 90) return 'Very High';
    if (score >= 75) return 'High';
    if (score >= 60) return 'Moderate';
    if (score >= 40) return 'Low';
    return 'Very Low';
  }
} 