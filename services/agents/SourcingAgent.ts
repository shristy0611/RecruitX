import { BaseAgent } from './BaseAgent';
import { JobDescriptionData } from '../../types';

/**
 * Specialized agent for sourcing potential candidates
 * Helps identify and discover talent based on job requirements
 */
export class SourcingAgent extends BaseAgent {
  /**
   * Create a new sourcing agent with specialized system prompt
   */
  constructor() {
    const systemPrompt = `
      You are an expert AI Recruitment Assistant specializing in candidate sourcing.
      Your task is to help recruiters find potential candidates based on job requirements.
      
      For each sourcing task:
      1. Analyze the job description to identify key requirements and qualifications
      2. Generate search strategies and keywords to find relevant candidates
      3. Recommend platforms and channels where ideal candidates may be found
      4. Create outreach message templates tailored to the role
      5. Provide interview questions to assess fit against key requirements
    `;
    
    super(systemPrompt);
  }
  
  /**
   * Analyze job description to create a sourcing strategy
   * @param jdId The job description ID
   * @returns Sourcing strategy with keywords, platforms, and messaging
   */
  async createSourcingStrategy(jd: JobDescriptionData): Promise<SourcingStrategy> {
    try {
      // For now, we'll create a simulated response
      // In a full implementation, this would use the LLM
      
      // Extract skills and requirements from JD
      const keyRequirements = this.extractKeyRequirements(jd.content);
      
      // Generate search keywords
      const searchKeywords = this.generateSearchKeywords(keyRequirements);
      
      // Determine best platforms for sourcing
      const platforms = this.determineSourcingPlatforms(keyRequirements);
      
      // Create outreach templates
      const outreachTemplates = this.createOutreachTemplates(jd);
      
      // Generate screening questions
      const screeningQuestions = this.generateScreeningQuestions(keyRequirements);
      
      return {
        jobTitle: jd.title,
        keyRequirements,
        searchKeywords,
        platforms,
        outreachTemplates,
        screeningQuestions
      };
    } catch (error) {
      console.error('Error creating sourcing strategy:', error);
      throw new Error('Failed to create sourcing strategy');
    }
  }
  
  /**
   * Extract key requirements from job description
   */
  private extractKeyRequirements(content: string): string[] {
    // Simulated function that would extract requirements
    return [
      'React & TypeScript experience (3+ years)',
      'Experience with state management (Redux, MobX, etc.)',
      'Experience with API integration',
      'Understanding of CI/CD pipelines',
      'Bachelor\'s degree in CS or related field',
      'Strong communication skills'
    ];
  }
  
  /**
   * Generate search keywords based on requirements
   */
  private generateSearchKeywords(requirements: string[]): string[] {
    // Simulated function to create boolean search strings
    return [
      'React AND TypeScript AND (Redux OR MobX OR "state management")',
      'frontend AND (React OR ReactJS) AND TypeScript',
      '"React developer" AND TypeScript AND (Redux OR MobX)',
      '(frontend OR "front end" OR "front-end") AND React AND TypeScript'
    ];
  }
  
  /**
   * Determine best platforms for sourcing based on role
   */
  private determineSourcingPlatforms(requirements: string[]): SourcingPlatform[] {
    // Simulated function to recommend platforms
    return [
      {
        name: 'LinkedIn',
        relevanceScore: 90,
        searchTips: 'Use the boolean search strings in the LinkedIn Recruiter search. Filter for candidates with 3+ years of experience.'
      },
      {
        name: 'GitHub',
        relevanceScore: 85,
        searchTips: 'Search for TypeScript and React repositories. Look for contributors with substantial commit history.'
      },
      {
        name: 'Stack Overflow',
        relevanceScore: 70,
        searchTips: 'Search for users with high reputation in React and TypeScript tags.'
      },
      {
        name: 'Tech meetups',
        relevanceScore: 65,
        searchTips: 'Look for React and TypeScript meetup groups in target locations.'
      }
    ];
  }
  
  /**
   * Create personalized outreach templates
   */
  private createOutreachTemplates(jd: JobDescriptionData): OutreachTemplate[] {
    // Simulated function to create templates
    return [
      {
        channel: 'LinkedIn',
        subject: `${jd.title} opportunity at [Company Name]`,
        message: `Hello [Candidate Name],

I came across your profile and was impressed by your experience with React and TypeScript. We're looking for a talented developer to join our team as a ${jd.title}.

Would you be open to a quick chat about this opportunity?

Best regards,
[Recruiter Name]`,
        notes: 'Personalize by mentioning specific projects or experience that caught your attention.'
      },
      {
        channel: 'Email',
        subject: `Your React expertise & our ${jd.title} role`,
        message: `Hi [Candidate Name],

I'm [Recruiter Name] from [Company Name], and we're building a team of talented developers for our growing product.

Your background in React and frontend development stood out to me, and I'd love to tell you about our ${jd.title} position that might align well with your skills and career goals.

Are you available for a 15-minute call this week to discuss?

Thanks,
[Recruiter Name]
[Contact Information]`,
        notes: 'For cold emails, keep it brief and highlight what makes your company unique.'
      }
    ];
  }
  
  /**
   * Generate screening questions based on requirements
   */
  private generateScreeningQuestions(requirements: string[]): string[] {
    // Simulated function to create screening questions
    return [
      'Can you describe a complex React component you built recently and the state management approach you used?',
      'How do you handle API integration in React applications? Any specific libraries you prefer?',
      'What TypeScript features do you find most valuable when developing React applications?',
      'How do you approach testing in React applications?',
      'Can you walk me through your experience with CI/CD pipelines?'
    ];
  }
}

/**
 * Sourcing strategy with targeting and outreach information
 */
export interface SourcingStrategy {
  jobTitle: string;
  keyRequirements: string[];
  searchKeywords: string[];
  platforms: SourcingPlatform[];
  outreachTemplates: OutreachTemplate[];
  screeningQuestions: string[];
}

/**
 * Platform recommendation for sourcing
 */
interface SourcingPlatform {
  name: string;
  relevanceScore: number; // 0-100
  searchTips: string;
}

/**
 * Template for candidate outreach
 */
interface OutreachTemplate {
  channel: 'LinkedIn' | 'Email' | 'InMail' | 'Other';
  subject: string;
  message: string;
  notes?: string;
} 