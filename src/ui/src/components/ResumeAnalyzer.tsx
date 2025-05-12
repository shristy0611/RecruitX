import React, { useState, useRef } from 'react';
import { FileText, Upload, Loader2, Check, X, FileUp } from 'lucide-react';
import { apiService } from '../services/api';
import { useModel } from '../contexts/ModelContext';

interface SkillMatch {
  skill: string;
  level: 'beginner' | 'intermediate' | 'expert';
  relevance: number;
}

interface ResumeAnalysis {
  name: string;
  email: string;
  phone?: string;
  summary: string;
  yearsOfExperience: number;
  skills: SkillMatch[];
  education: string[];
  strengths: string[];
  weaknesses: string[];
  recommendation: string;
  fitScore: number;
}

const ResumeAnalyzer: React.FC = () => {
  const { activeModel, isModelLoading, setIsModelLoading } = useModel();
  const [resumeText, setResumeText] = useState('');
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAnalyzeResume = async () => {
    if (!resumeText.trim() || isModelLoading) return;

    setIsModelLoading(true);
    setError(null);

    try {
      const result = await apiService.analyzeResume(resumeText, activeModel);
      setAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze resume');
      console.error(err);
    } finally {
      setIsModelLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file) return;

      setFileName(file.name);
      setError(null);

      // Check file type
      if (file.type !== 'application/pdf' && 
          file.type !== 'application/msword' && 
          file.type !== 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' &&
          file.type !== 'text/plain') {
        setError('Please upload a PDF, Word document, or text file');
        return;
      }

      // Check file size (limit to 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('File is too large. Please upload a file smaller than 5MB');
        return;
      }

      setIsModelLoading(true);

      try {
        // For demo purposes, we'll simulate reading the file
        // In a real app, we'd send the file to the backend
        const reader = new FileReader();
        
        reader.onload = async (event) => {
          const fileContent = event.target?.result as string;
          // For text files, use the content directly
          // For other types, we'd normally extract text on the server
          // but for the demo we'll just use a sample text with the filename
        
          const extractedText = file.type === 'text/plain' 
            ? fileContent 
            : `${file.name}\n\nJohn Smith\njohn.smith@example.com\n\nSUMMARY\nSenior Software Engineer with 5 years of experience in full-stack development. Proficient in JavaScript, React, and Node.js. Led multiple projects from conception to deployment.`;
        
          setResumeText(extractedText);
        
          // Delay the analysis a bit to show loading state for the demo
          setTimeout(async () => {
            try {
              const result = await apiService.analyzeResume(extractedText, activeModel);
              setAnalysis(result);
            } catch (err) {
              setError(err instanceof Error ? err.message : 'Failed to analyze resume');
              console.error(err);
            } finally {
              setIsModelLoading(false);
            }
          }, 1500);
        };
        
        reader.onerror = () => {
          setError('Failed to read file');
          setIsModelLoading(false);
        };
        
        if (file.type === 'text/plain') {
          reader.readAsText(file);
        } else {
          // For non-text files, we would normally send to server for processing
          // but for demo we'll simulate success after a delay
          setTimeout(() => {
            reader.onload({ target: { result: '' } } as any);
          }, 1000);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to process file');
        setIsModelLoading(false);
      }
    }
  };

  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  const handleSampleResume = () => {
    const sampleResume = `JANE DOE
jane.doe@example.com | (555) 123-4567 | linkedin.com/in/janedoe

SUMMARY
Senior Frontend Developer with 6 years of experience building responsive web applications. Expertise in React, TypeScript, and modern JavaScript frameworks. Passionate about creating intuitive user interfaces and improving application performance.

SKILLS
• Programming: JavaScript (ES6+), TypeScript, HTML5, CSS3, Sass
• Frameworks/Libraries: React, Redux, Next.js, Angular, Vue.js
• Testing: Jest, React Testing Library, Cypress
• Tools: Webpack, Git, npm, Yarn, VS Code
• Design: Figma, Adobe XD, responsive design principles

EXPERIENCE
TECH INNOVATIONS INC.
Senior Frontend Developer | Jan 2020 - Present
• Led the development of a React-based dashboard that increased user engagement by 35%
• Implemented performance optimizations that reduced load time by 40%
• Mentored junior developers and conducted code reviews
• Collaborated with UX designers to improve user experience across all platforms

DIGITAL SOLUTIONS CORP.
Frontend Developer | Mar 2017 - Dec 2019
• Built responsive web applications using Angular and later React
• Created reusable component libraries that improved development speed by 25%
• Implemented unit and integration tests that caught 95% of bugs before production

EDUCATION
UNIVERSITY OF TECHNOLOGY
Bachelor of Science in Computer Science | 2013 - 2017
• GPA: 3.8/4.0
• Relevant coursework: Web Development, User Interface Design, Algorithms

CERTIFICATIONS
• AWS Certified Developer - Associate
• React Native Advanced Concepts
• Advanced JavaScript Patterns`;

    setResumeText(sampleResume);
  };

  return (
    <div className="glass-card p-6 rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 rounded-full bg-primary/20">
          <FileText className="w-5 h-5 text-primary" />
        </div>
        <h3 className="text-lg font-medium">Resume Analyzer</h3>
      </div>

      {!analysis ? (
        <div className="space-y-4">
          <div className="p-4 border border-dashed border-white/20 rounded-lg">
            {fileName ? (
              <div className="flex flex-col items-center justify-center py-4">
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="w-6 h-6 text-primary" />
                  <span className="font-medium">{fileName}</span>
                </div>
                <p className="text-sm text-muted-foreground mb-3">
                  File uploaded successfully. Click analyze to process the resume.
                </p>
                <button
                  onClick={triggerFileUpload}
                  className="px-3 py-1.5 text-sm rounded-lg border border-white/10 hover:bg-white/5"
                >
                  Upload a different file
                </button>
              </div>
            ) : (
              <textarea
                className="w-full h-40 bg-transparent text-foreground resize-none focus:outline-none"
                placeholder="Paste resume content here..."
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                disabled={isModelLoading}
              />
            )}
          </div>

          {error && (
            <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-lg">
              <p>{error}</p>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              className="hidden"
              accept=".pdf,.doc,.docx,.txt"
              disabled={isModelLoading}
            />
            
            <button
              onClick={triggerFileUpload}
              disabled={isModelLoading}
              className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-white/10 hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FileUp className="w-4 h-4" />
              Upload Resume
            </button>
            
            <button
              onClick={handleSampleResume}
              disabled={isModelLoading}
              className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-white/10 hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FileText className="w-4 h-4" />
              Use Sample Resume
            </button>

            <button
              onClick={handleAnalyzeResume}
              disabled={!resumeText.trim() || isModelLoading}
              className="flex-1 flex items-center justify-center gap-2 p-2 rounded-lg bg-primary text-primary-foreground font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isModelLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  Analyze with {activeModel === 'gemma' ? 'Gemma 3' : 'Gemini'}
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex justify-between items-start">
            <div>
              <h4 className="text-xl font-medium">{analysis.name}</h4>
              <p className="text-sm text-muted-foreground">{analysis.email}</p>
              {analysis.phone && <p className="text-sm text-muted-foreground">{analysis.phone}</p>}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Fit Score:</span>
                <div className="w-24 h-6 bg-muted/50 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${analysis.fitScore}%`,
                      background: `linear-gradient(to right, 
                        ${analysis.fitScore < 40 ? '#ef4444' : analysis.fitScore < 70 ? '#f59e0b' : '#10b981'}, 
                        ${analysis.fitScore < 40 ? '#f87171' : analysis.fitScore < 70 ? '#fbbf24' : '#34d399'})`,
                    }}
                  />
                </div>
                <span className="text-sm font-medium">{analysis.fitScore}%</span>
              </div>
            </div>
          </div>

          <div className="p-4 bg-muted/20 rounded-lg">
            <h5 className="font-medium mb-2">Summary</h5>
            <p className="text-sm">{analysis.summary}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h5 className="font-medium">Skills</h5>
              <div className="space-y-1.5">
                {analysis.skills.map((skill, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm">{skill.skill}</span>
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded-full ${
                          skill.level === 'expert'
                            ? 'bg-green-500/20 text-green-500'
                            : skill.level === 'intermediate'
                            ? 'bg-blue-500/20 text-blue-500'
                            : 'bg-gray-500/20 text-gray-500'
                        }`}
                      >
                        {skill.level}
                      </span>
                    </div>
                    <div className="w-20 h-2 bg-muted/50 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${skill.relevance * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h5 className="font-medium mb-2">Experience & Education</h5>
              <p className="text-sm mb-1">Years of Experience: {analysis.yearsOfExperience}</p>
              <div className="space-y-1">
                {analysis.education.map((edu, index) => (
                  <p key={index} className="text-sm">
                    • {edu}
                  </p>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h5 className="font-medium mb-2 flex items-center gap-1">
                <Check className="w-4 h-4 text-green-500" /> Strengths
              </h5>
              <div className="space-y-1">
                {analysis.strengths.map((strength, index) => (
                  <p key={index} className="text-sm">
                    • {strength}
                  </p>
                ))}
              </div>
            </div>

            <div>
              <h5 className="font-medium mb-2 flex items-center gap-1">
                <X className="w-4 h-4 text-destructive" /> Areas for Improvement
              </h5>
              <div className="space-y-1">
                {analysis.weaknesses.map((weakness, index) => (
                  <p key={index} className="text-sm">
                    • {weakness}
                  </p>
                ))}
              </div>
            </div>
          </div>

          <div className="p-4 border border-primary/20 bg-primary/5 rounded-lg">
            <h5 className="font-medium mb-2">Recommendation</h5>
            <p className="text-sm">{analysis.recommendation}</p>
          </div>

          <div className="flex flex-col sm:flex-row justify-between gap-3">
            <button
              onClick={() => {
                setAnalysis(null);
                setFileName(null);
              }}
              className="px-4 py-2 rounded-lg border border-white/10 hover:bg-white/5"
            >
              Analyze Another Resume
            </button>
            <button className="px-4 py-2 rounded-lg bg-primary text-primary-foreground">
              Save Analysis
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResumeAnalyzer; 