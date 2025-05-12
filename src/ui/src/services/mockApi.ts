import { ChatCompletionRequest, ChatCompletionResponse, ChatMessage, ModelProvider } from './api';

// Mock delay to simulate API call
const mockDelay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Sample responses for the mock API
const mockResponses = {
  gemma: {
    greeting: "Hello! I'm Gemma 3, a locally-hosted AI model designed to help with recruitment tasks. How can I assist you today?",
    resumeAnalysis: (name: string) => ({
      name,
      email: `${name.toLowerCase().replace(/\s/g, '.')}@example.com`,
      phone: '+1 (555) 123-4567',
      summary: `${name} is an experienced professional with a strong background in software development and engineering. They demonstrate excellent technical skills combined with leadership abilities and a track record of delivering high-quality projects.`,
      yearsOfExperience: 5,
      skills: [
        { skill: 'JavaScript', level: 'expert', relevance: 0.9 },
        { skill: 'React', level: 'expert', relevance: 0.95 },
        { skill: 'TypeScript', level: 'intermediate', relevance: 0.8 },
        { skill: 'Node.js', level: 'intermediate', relevance: 0.75 },
        { skill: 'Python', level: 'beginner', relevance: 0.6 }
      ],
      education: [
        'Bachelor of Science in Computer Science, Stanford University',
        'Web Development Bootcamp, Coding Academy'
      ],
      strengths: [
        'Strong front-end development skills with React and TypeScript',
        'Experience with modern JavaScript frameworks and libraries',
        'Good problem-solving abilities and analytical thinking',
        'Team collaboration and communication skills'
      ],
      weaknesses: [
        'Limited experience with backend technologies',
        'Could benefit from more exposure to cloud infrastructure',
        'No formal experience with mobile development'
      ],
      recommendation: `${name} would be an excellent fit for front-end development roles, particularly those focusing on React. Consider them for senior developer positions that require JavaScript expertise. They may need additional training or mentoring for backend-heavy roles.`,
      fitScore: 85
    }),
    jobDescription: (title: string) => ({
      title,
      company: 'TechCorp Inc.',
      location: 'San Francisco, CA (Hybrid)',
      salary: '$120,000 - $150,000',
      description: `We are seeking an experienced ${title} to join our growing team. The ideal candidate will have strong technical skills, excellent communication abilities, and a passion for building innovative products.`,
      requirements: [
        'At least 3+ years of experience in a similar role',
        'Proficiency in JavaScript, TypeScript, and React',
        'Experience with state management libraries (Redux, MobX, etc.)',
        'Understanding of modern web development practices and tools',
        "Bachelor's degree in Computer Science or related field (or equivalent experience)"
      ],
      benefits: [
        'Competitive salary and equity package',
        'Health, dental, and vision insurance',
        'Flexible work-from-home policy',
        'Professional development budget',
        '401(k) matching'
      ],
      keyResponsibilities: [
        'Develop and maintain high-quality web applications',
        'Collaborate with product managers and designers',
        'Write clean, maintainable, and efficient code',
        'Participate in code reviews and technical discussions',
        'Mentor junior developers and share knowledge'
      ]
    })
  },
  gemini: {
    greeting: "Hi there! I'm Gemini, a cloud-based AI model with advanced capabilities. I can help you with various recruitment tasks like analyzing resumes, creating job descriptions, and more. What would you like to do today?",
    resumeAnalysis: (name: string) => ({
      name,
      email: `${name.toLowerCase().replace(/\s/g, '.')}@example.com`,
      phone: '+1 (555) 987-6543',
      summary: `${name} is a highly qualified professional with extensive experience in software engineering and team leadership. They have a proven track record of successful project deliveries and technical innovation across various domains.`,
      yearsOfExperience: 7,
      skills: [
        { skill: 'JavaScript', level: 'expert', relevance: 0.95 },
        { skill: 'React', level: 'expert', relevance: 0.9 },
        { skill: 'TypeScript', level: 'expert', relevance: 0.85 },
        { skill: 'Node.js', level: 'intermediate', relevance: 0.8 },
        { skill: 'Python', level: 'intermediate', relevance: 0.7 },
        { skill: 'AWS', level: 'intermediate', relevance: 0.75 }
      ],
      education: [
        'Master of Science in Computer Science, MIT',
        'Bachelor of Engineering, Computer Science, UC Berkeley'
      ],
      strengths: [
        'Full-stack development expertise with particular strength in frontend technologies',
        'Experience leading development teams of 5-10 engineers',
        'Strong architectural design skills and system thinking',
        'Excellent communication and stakeholder management abilities',
        'Proven track record of delivering complex projects on time'
      ],
      weaknesses: [
        'Limited experience with mobile development frameworks',
        'Could benefit from more exposure to AI/ML technologies',
        'May need additional training for DevOps-heavy roles'
      ],
      recommendation: `${name} would be an excellent addition to any engineering team, particularly in a senior role or technical lead position. They bring a strong combination of technical expertise and leadership skills. Consider them for roles that require both hands-on coding and team guidance.`,
      fitScore: 92
    }),
    jobDescription: (title: string) => ({
      title,
      company: 'InnovateTech Solutions',
      location: 'New York, NY (Remote Available)',
      salary: '$140,000 - $180,000',
      description: `InnovateTech Solutions is looking for an exceptional ${title} to help drive our technology vision forward. This role combines technical expertise with strategic thinking to create impactful digital experiences for our clients.`,
      requirements: [
        '5+ years of professional software development experience',
        'Deep understanding of JavaScript ecosystem, particularly React and TypeScript',
        'Experience with backend technologies like Node.js, Python, or Java',
        'Familiarity with cloud platforms (AWS, Google Cloud, or Azure)',
        'Track record of mentoring junior developers and technical leadership',
        'Excellent communication and collaboration skills'
      ],
      benefits: [
        'Competitive compensation package with performance bonuses',
        'Comprehensive health, dental, and vision coverage',
        'Unlimited PTO policy',
        '401(k) with generous company match',
        'Remote-first work environment with flexible hours',
        'Dedicated professional development budget',
        'Home office stipend and latest equipment'
      ],
      keyResponsibilities: [
        'Design and implement robust, scalable applications',
        'Collaborate with cross-functional teams to define and implement new features',
        'Establish best practices and coding standards',
        'Participate in architectural decisions and technical planning',
        'Mentor and guide junior team members',
        'Contribute to a positive team culture of innovation and excellence'
      ]
    })
  }
};

// Extract name from resume text
const extractNameFromResume = (resumeText: string): string => {
  // Simple regex to find a name pattern at the beginning of the resume
  const nameMatch = resumeText.match(/^([A-Z][a-z]+ [A-Z][a-z]+)/);
  return nameMatch ? nameMatch[1] : 'John Doe';
};

// Extract job title from job description
const extractJobTitleFromDescription = (jobText: string): string => {
  // Simple regex to find job title patterns
  const titleMatch = jobText.match(/(Senior|Junior)?\s*(Software|Frontend|Backend|Full Stack|UI\/UX)?\s*(Developer|Engineer|Designer)/i);
  return titleMatch ? titleMatch[0] : 'Software Engineer';
};

// Mock API Service
export const mockApiService = {
  // Chat completion with selected model
  async chatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    // Simulate API delay
    await mockDelay(1000);
    
    const lastMessage = request.messages[request.messages.length - 1];
    let responseContent = '';
    
    // Generate different responses based on model and input
    if (request.messages.length === 1) {
      // First message - return greeting
      responseContent = request.model === 'gemma' 
        ? mockResponses.gemma.greeting 
        : mockResponses.gemini.greeting;
    } else {
      // Generate a contextual response based on the last message
      if (lastMessage.content.toLowerCase().includes('resume')) {
        responseContent = `I can help analyze resumes! You can either paste the resume text or upload a resume file in the Resume Analyzer section.`;
      } else if (lastMessage.content.toLowerCase().includes('job')) {
        responseContent = `I can help create job descriptions! Let me know the position, and I'll generate a comprehensive job posting for you.`;
      } else if (lastMessage.content.toLowerCase().includes('candidate')) {
        responseContent = `I can help evaluate candidates! Upload their resume, and I'll provide a detailed analysis of their skills and fit for your roles.`;
      } else {
        responseContent = `I'm here to help with your recruitment needs! I can analyze resumes, create job descriptions, evaluate candidates, and answer questions about the recruitment process. What specific task would you like assistance with today?`;
      }
    }
    
    return {
      message: {
        role: 'assistant',
        content: responseContent
      },
      model: request.model === 'gemma' ? 'Gemma 3.0' : 'Gemini Pro'
    };
  },

  // Analyze resume with AI
  async analyzeResume(resumeText: string, model: ModelProvider = 'gemma'): Promise<any> {
    // Simulate API delay
    await mockDelay(2000);
    
    // Extract a name from the resume or use default
    const name = extractNameFromResume(resumeText);
    
    // Return mock analysis based on the selected model
    return model === 'gemma' 
      ? mockResponses.gemma.resumeAnalysis(name)
      : mockResponses.gemini.resumeAnalysis(name);
  },

  // Generate job description with AI
  async generateJobDescription(jobDetails: any, model: ModelProvider = 'gemma'): Promise<any> {
    // Simulate API delay
    await mockDelay(1500);
    
    // Extract or use provided job title
    const title = jobDetails.title || 'Software Engineer';
    
    // Return mock job description based on the selected model
    return model === 'gemma'
      ? mockResponses.gemma.jobDescription(title)
      : mockResponses.gemini.jobDescription(title);
  },

  // Screen candidate with AI
  async screenCandidate(candidateData: any, jobDescription: string, model: ModelProvider = 'gemma'): Promise<any> {
    // Simulate API delay
    await mockDelay(2000);
    
    // For demo purposes, return a slightly modified version of resume analysis
    const analysis = model === 'gemma'
      ? mockResponses.gemma.resumeAnalysis(candidateData.name || 'Candidate')
      : mockResponses.gemini.resumeAnalysis(candidateData.name || 'Candidate');
    
    // Add job match score
    return {
      ...analysis,
      jobMatch: {
        score: Math.floor(Math.random() * 30) + 70, // Random score between 70-99
        strengths: analysis.strengths,
        gaps: analysis.weaknesses,
        recommendation: `Based on the candidate's profile and the job requirements, ${candidateData.name || 'the candidate'} appears to be a ${Math.random() > 0.5 ? 'strong' : 'good'} match for this position.`
      }
    };
  },

  // Match candidates to job
  async matchCandidates(jobId: string, model: ModelProvider = 'gemma'): Promise<any> {
    // Simulate API delay
    await mockDelay(1800);
    
    // Generate mock candidate matches
    return {
      job: {
        id: jobId,
        title: 'Senior Frontend Developer',
        department: 'Engineering',
        location: 'San Francisco, CA'
      },
      matches: [
        { name: 'Emily Johnson', score: 92, status: 'New' },
        { name: 'Michael Chen', score: 88, status: 'Contacted' },
        { name: 'Sarah Williams', score: 85, status: 'Interview Scheduled' },
        { name: 'David Rodriguez', score: 82, status: 'New' },
        { name: 'Jessica Taylor', score: 78, status: 'New' }
      ]
    };
  }
}; 