import { BaseAgent } from './BaseAgent';
import { CVData, JobDescriptionData } from '../../types';

/**
 * Specialized agent for interview preparation and evaluation
 * Helps with interview question generation, candidate assessment, and feedback
 */
export class InterviewAgent extends BaseAgent {
  /**
   * Create a new interview agent with specialized system prompt
   */
  constructor() {
    const systemPrompt = `
      You are an expert AI Recruitment Assistant specializing in interview preparation and evaluation.
      Your task is to help recruiters prepare for interviews and evaluate candidates effectively.
      
      For each interview preparation task:
      1. Analyze the job description and candidate CV to identify key areas to explore
      2. Generate tailored interview questions based on the role requirements and candidate background
      3. Create a structured interview plan with evaluation criteria
      4. Help assess candidate responses against job requirements
      5. Provide objective feedback and scoring based on candidate responses
    `;
    
    super(systemPrompt);
  }
  
  /**
   * Generate an interview plan based on CV and JD
   * @param cv The candidate CV data
   * @param jd The job description data
   * @returns Interview plan with questions, criteria, and structure
   */
  async createInterviewPlan(cv: CVData, jd: JobDescriptionData): Promise<InterviewPlan> {
    try {
      // For now, we'll simulate this response
      // In a full implementation, this would use the LLM
      
      // Extract key areas to assess
      const assessmentAreas = this.identifyAssessmentAreas(jd.content);
      
      // Generate questions based on CV and JD
      const questions = this.generateInterviewQuestions(cv, jd, assessmentAreas);
      
      // Create evaluation criteria
      const evaluationCriteria = this.createEvaluationCriteria(assessmentAreas);
      
      // Create interview structure
      const interviewStructure = this.createInterviewStructure(questions);
      
      return {
        candidateName: cv.name,
        jobTitle: jd.title,
        assessmentAreas,
        questions,
        evaluationCriteria,
        interviewStructure,
        suggestedDuration: 60, // minutes
        prepNotes: this.generatePrepNotes(cv)
      };
    } catch (error) {
      console.error('Error creating interview plan:', error);
      throw new Error('Failed to create interview plan');
    }
  }
  
  /**
   * Evaluate candidate responses to interview questions
   * @param plan The original interview plan
   * @param responses Object mapping question IDs to candidate responses
   * @returns Evaluation with scores and feedback
   */
  async evaluateInterviewResponses(
    plan: InterviewPlan, 
    responses: Record<string, string>
  ): Promise<InterviewEvaluation> {
    try {
      // For now, we'll create a simulated response
      // In a full implementation, this would use the LLM
      
      // Evaluate each response against criteria
      const questionEvaluations: QuestionEvaluation[] = [];
      
      for (const question of plan.questions) {
        const response = responses[question.id];
        if (response) {
          // Simulate scoring and feedback
          const score = Math.floor(Math.random() * 5) + 1; // 1-5 score
          
          questionEvaluations.push({
            questionId: question.id,
            score,
            feedback: this.generateFeedback(question, response, score)
          });
        }
      }
      
      // Calculate area scores
      const areaScores: Record<string, number> = {};
      
      for (const area of plan.assessmentAreas) {
        const areaQuestionEvals = questionEvaluations.filter(
          qe => plan.questions.find(q => q.id === qe.questionId)?.area === area
        );
        
        if (areaQuestionEvals.length > 0) {
          const areaScore = areaQuestionEvals.reduce((sum, qe) => sum + qe.score, 0) / areaQuestionEvals.length;
          areaScores[area] = Math.round(areaScore * 10) / 10; // Round to 1 decimal
        }
      }
      
      // Calculate overall score
      const overallScore = Object.values(areaScores).reduce((sum, score) => sum + score, 0) / 
        Object.values(areaScores).length;
      
      // Generate strengths and improvement areas
      const strengths = this.generateStrengths(questionEvaluations, plan);
      const improvementAreas = this.generateImprovementAreas(questionEvaluations, plan);
      
      return {
        candidateName: plan.candidateName,
        jobTitle: plan.jobTitle,
        overallScore: Math.round(overallScore * 10) / 10,
        areaScores,
        questionEvaluations,
        strengths,
        improvementAreas,
        hiringRecommendation: this.generateHiringRecommendation(overallScore),
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('Error evaluating interview responses:', error);
      throw new Error('Failed to evaluate interview responses');
    }
  }
  
  /**
   * Identify key areas to assess from job description
   */
  private identifyAssessmentAreas(jobDescription: string): string[] {
    // Simulated function
    return [
      'Technical Expertise',
      'Problem Solving',
      'Communication Skills',
      'Team Collaboration',
      'Project Management'
    ];
  }
  
  /**
   * Generate interview questions based on CV, JD, and assessment areas
   */
  private generateInterviewQuestions(
    cv: CVData,
    jd: JobDescriptionData,
    areas: string[]
  ): InterviewQuestion[] {
    // Simulated function
    return [
      {
        id: 'q1',
        text: 'Can you describe a complex technical challenge you faced in your previous role and how you solved it?',
        area: 'Technical Expertise',
        purpose: 'Assess depth of technical knowledge and problem-solving approach',
        followups: [
          'What technologies did you use?',
          'What would you do differently now?'
        ]
      },
      {
        id: 'q2',
        text: 'How do you approach learning new technologies or frameworks?',
        area: 'Technical Expertise',
        purpose: 'Evaluate adaptability and learning mindset',
        followups: [
          'Can you give an example of a technology you recently learned?'
        ]
      },
      {
        id: 'q3',
        text: 'Tell me about a time when you had to explain a complex technical concept to non-technical stakeholders.',
        area: 'Communication Skills',
        purpose: 'Assess ability to communicate technical information clearly',
        followups: [
          'How did you ensure they understood?',
          'How would you handle it if they still didn\'t understand?'
        ]
      },
      {
        id: 'q4',
        text: 'Describe a situation where you had a disagreement with a team member about a technical approach. How did you resolve it?',
        area: 'Team Collaboration',
        purpose: 'Evaluate conflict resolution and collaboration skills',
        followups: [
          'What did you learn from this experience?'
        ]
      },
      {
        id: 'q5',
        text: 'How do you prioritize tasks when working on multiple projects with competing deadlines?',
        area: 'Project Management',
        purpose: 'Assess time management and prioritization skills',
        followups: [
          'Can you provide a specific example?'
        ]
      }
    ];
  }
  
  /**
   * Create evaluation criteria for each assessment area
   */
  private createEvaluationCriteria(areas: string[]): Record<string, string[]> {
    // Simulated function
    return {
      'Technical Expertise': [
        'Demonstrates deep understanding of relevant technologies',
        'Shows problem-solving ability and creative thinking',
        'Has experience with similar technical challenges'
      ],
      'Problem Solving': [
        'Approaches problems systematically',
        'Considers multiple solutions',
        'Evaluates trade-offs effectively'
      ],
      'Communication Skills': [
        'Articulates ideas clearly and concisely',
        'Adapts communication style to audience',
        'Listens actively and responds thoughtfully'
      ],
      'Team Collaboration': [
        'Works effectively with diverse team members',
        'Handles disagreements constructively',
        'Contributes positively to team dynamics'
      ],
      'Project Management': [
        'Sets realistic timelines and priorities',
        'Adapts to changing requirements',
        'Balances quality with delivery speed'
      ]
    };
  }
  
  /**
   * Create a structured interview plan
   */
  private createInterviewStructure(questions: InterviewQuestion[]): InterviewPhase[] {
    // Simulated function
    return [
      {
        name: 'Introduction',
        duration: 5,
        description: 'Welcome the candidate, introduce the interview team, and explain the interview process.'
      },
      {
        name: 'Background and Experience',
        duration: 10,
        description: 'Discuss the candidate\'s background, experience, and interest in the role.'
      },
      {
        name: 'Technical Assessment',
        duration: 20,
        description: 'Ask technical and problem-solving questions to evaluate expertise.',
        questionIds: ['q1', 'q2']
      },
      {
        name: 'Behavioral Assessment',
        duration: 15,
        description: 'Assess soft skills, collaboration, and communication.',
        questionIds: ['q3', 'q4', 'q5']
      },
      {
        name: 'Candidate Questions',
        duration: 5,
        description: 'Allow the candidate to ask questions about the role and company.'
      },
      {
        name: 'Conclusion',
        duration: 5,
        description: 'Thank the candidate and explain next steps in the process.'
      }
    ];
  }
  
  /**
   * Generate preparation notes for the interviewer
   */
  private generatePrepNotes(cv: CVData): string {
    // Simulated function
    return `
Review the candidate's experience with React and TypeScript highlighted in their CV.
Note that they mentioned experience with Redux for state management, which aligns with our tech stack.
Their previous role at XYZ Company involved similar responsibilities to this position.
They mentioned an interest in frontend optimization in their CV, which we should explore further.
    `;
  }
  
  /**
   * Generate feedback for a question response
   */
  private generateFeedback(
    question: InterviewQuestion, 
    response: string, 
    score: number
  ): string {
    // Simulated function - in a real implementation, this would analyze the response
    const feedbacks = [
      'The candidate demonstrated a clear understanding of the concepts and provided specific examples.',
      'The response was adequate but lacked specific examples or depth.',
      'The candidate showed good communication but could improve on technical depth.',
      'The answer was comprehensive and demonstrated both technical knowledge and practical experience.',
      'The response was somewhat vague and could benefit from more concrete examples.'
    ];
    
    return feedbacks[Math.floor(Math.random() * feedbacks.length)];
  }
  
  /**
   * Generate strengths based on evaluation
   */
  private generateStrengths(
    evaluations: QuestionEvaluation[], 
    plan: InterviewPlan
  ): string[] {
    // Simulated function
    return [
      'Strong technical knowledge in frontend development',
      'Excellent communication skills with clear articulation of complex concepts',
      'Demonstrated problem-solving ability with practical examples',
      'Good understanding of collaborative development processes'
    ];
  }
  
  /**
   * Generate improvement areas based on evaluation
   */
  private generateImprovementAreas(
    evaluations: QuestionEvaluation[], 
    plan: InterviewPlan
  ): string[] {
    // Simulated function
    return [
      'Could provide more specific examples when discussing past projects',
      'May benefit from deeper knowledge of performance optimization techniques',
      'Consider expanding knowledge of backend integration patterns'
    ];
  }
  
  /**
   * Generate hiring recommendation based on overall score
   */
  private generateHiringRecommendation(overallScore: number): string {
    // Simulated function
    if (overallScore >= 4.5) return 'Strong Hire - Excellent candidate who exceeds requirements';
    if (overallScore >= 3.5) return 'Hire - Solid candidate who meets all key requirements';
    if (overallScore >= 2.5) return 'Borderline - Meets some requirements but has notable gaps';
    return 'Do Not Hire - Does not meet the core requirements for the role';
  }
}

/**
 * Structured interview plan
 */
export interface InterviewPlan {
  candidateName: string;
  jobTitle: string;
  assessmentAreas: string[];
  questions: InterviewQuestion[];
  evaluationCriteria: Record<string, string[]>;
  interviewStructure: InterviewPhase[];
  suggestedDuration: number; // minutes
  prepNotes: string;
}

/**
 * Individual interview question
 */
interface InterviewQuestion {
  id: string;
  text: string;
  area: string;
  purpose: string;
  followups?: string[];
}

/**
 * Phase of the interview process
 */
interface InterviewPhase {
  name: string;
  duration: number; // minutes
  description: string;
  questionIds?: string[];
}

/**
 * Evaluation of a candidate's interview performance
 */
export interface InterviewEvaluation {
  candidateName: string;
  jobTitle: string;
  overallScore: number; // 1-5 scale
  areaScores: Record<string, number>;
  questionEvaluations: QuestionEvaluation[];
  strengths: string[];
  improvementAreas: string[];
  hiringRecommendation: string;
  timestamp: string;
}

/**
 * Evaluation of a single question response
 */
interface QuestionEvaluation {
  questionId: string;
  score: number; // 1-5 scale
  feedback: string;
} 