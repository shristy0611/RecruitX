import React, { useState, useEffect } from 'react';
import { ScreeningAgent } from '../services/agents/ScreeningAgent';
import { SourcingAgent } from '../services/agents/SourcingAgent';
import { InterviewAgent } from '../services/agents/InterviewAgent';
import { CVData, JobDescriptionData, MatchResult } from '../types';
import ConversationalInterface from '../components/ConversationalInterface';

/**
 * Demo view to showcase all three agent types
 * Allows testing each agent's capabilities
 */
const AgentsDemoView: React.FC = () => {
  const [selectedCvId, setSelectedCvId] = useState<string | undefined>(undefined);
  const [selectedJdId, setSelectedJdId] = useState<string | undefined>(undefined);
  const [cvs, setCvs] = useState<CVData[]>([]);
  const [jds, setJds] = useState<JobDescriptionData[]>([]);
  const [activeAgent, setActiveAgent] = useState<'screening' | 'sourcing' | 'interview'>('screening');
  const [demoResult, setDemoResult] = useState<any | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  
  // Load documents from localStorage
  useEffect(() => {
    try {
      const storedCvsString = localStorage.getItem('recruitx_cvs');
      if (storedCvsString) setCvs(JSON.parse(storedCvsString) as CVData[]);
      
      const storedJdsString = localStorage.getItem('recruitx_jds');
      if (storedJdsString) setJds(JSON.parse(storedJdsString) as JobDescriptionData[]);
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  }, []);
  
  // Handle agent selection
  const handleAgentChange = (agent: 'screening' | 'sourcing' | 'interview') => {
    setActiveAgent(agent);
    setDemoResult(null); // Clear previous results
  };
  
  // Run demo for selected agent
  const runAgentDemo = async () => {
    setIsProcessing(true);
    
    try {
      let result;
      
      // Get selected documents
      const selectedCv = cvs.find(cv => cv.id === selectedCvId);
      const selectedJd = jds.find(jd => jd.id === selectedJdId);
      
      if (!selectedCv && activeAgent !== 'sourcing') {
        throw new Error('Please select a CV');
      }
      
      if (!selectedJd) {
        throw new Error('Please select a job description');
      }
      
      // Run appropriate agent
      switch (activeAgent) {
        case 'screening':
          result = await runScreeningAgent(selectedCv!, selectedJd);
          break;
        case 'sourcing':
          result = await runSourcingAgent(selectedJd);
          break;
        case 'interview':
          result = await runInterviewAgent(selectedCv!, selectedJd);
          break;
      }
      
      setDemoResult(result);
    } catch (error) {
      console.error(`Error running ${activeAgent} agent:`, error);
      alert(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Run screening agent demo
  const runScreeningAgent = async (cv: CVData, jd: JobDescriptionData) => {
    const agent = new ScreeningAgent();
    return await agent.evaluateCandidate(cv.id, jd.id);
  };
  
  // Run sourcing agent demo
  const runSourcingAgent = async (jd: JobDescriptionData) => {
    const agent = new SourcingAgent();
    return await agent.createSourcingStrategy(jd);
  };
  
  // Run interview agent demo
  const runInterviewAgent = async (cv: CVData, jd: JobDescriptionData) => {
    const agent = new InterviewAgent();
    return await agent.createInterviewPlan(cv, jd);
  };
  
  // Render demo result based on agent type
  const renderDemoResult = () => {
    if (!demoResult) return null;
    
    switch (activeAgent) {
      case 'screening':
        return renderScreeningResult(demoResult);
      case 'sourcing':
        return renderSourcingResult(demoResult);
      case 'interview':
        return renderInterviewResult(demoResult);
      default:
        return <div>No result to display</div>;
    }
  };
  
  // Render screening agent result
  const renderScreeningResult = (result: any) => (
    <div className="bg-neutral-800 p-4 rounded-lg">
      <h3 className="text-xl font-semibold mb-4">Candidate Evaluation</h3>
      
      <div className="mb-4">
        <div className="text-lg font-semibold">Score: {result.score}/100</div>
      </div>
      
      <div className="mb-4">
        <h4 className="text-lg font-semibold mb-2">Strengths</h4>
        <ul className="list-disc pl-5">
          {result.strengths?.map((strength: string, i: number) => (
            <li key={i} className="text-primary-text">{strength}</li>
          ))}
        </ul>
      </div>
      
      <div className="mb-4">
        <h4 className="text-lg font-semibold mb-2">Areas for Improvement</h4>
        <ul className="list-disc pl-5">
          {result.gaps?.map((gap: string, i: number) => (
            <li key={i} className="text-neutral-300">{gap}</li>
          ))}
        </ul>
      </div>
      
      <div className="mb-4">
        <h4 className="text-lg font-semibold mb-2">Suggested Follow-up Questions</h4>
        <ul className="list-disc pl-5">
          {result.suggestedQuestions?.map((question: string, i: number) => (
            <li key={i} className="text-accent-text">{question}</li>
          ))}
        </ul>
      </div>
    </div>
  );
  
  // Render sourcing agent result
  const renderSourcingResult = (result: any) => (
    <div className="bg-neutral-800 p-4 rounded-lg">
      <h3 className="text-xl font-semibold mb-4">Sourcing Strategy for {result.jobTitle}</h3>
      
      <div className="mb-4">
        <h4 className="text-lg font-semibold mb-2">Key Requirements</h4>
        <ul className="list-disc pl-5">
          {result.keyRequirements?.map((req: string, i: number) => (
            <li key={i} className="text-neutral-300">{req}</li>
          ))}
        </ul>
      </div>
      
      <div className="mb-4">
        <h4 className="text-lg font-semibold mb-2">Recommended Search Keywords</h4>
        <ul className="list-disc pl-5">
          {result.searchKeywords?.map((keyword: string, i: number) => (
            <li key={i} className="text-primary-text">{keyword}</li>
          ))}
        </ul>
      </div>
      
      <div className="mb-4">
        <h4 className="text-lg font-semibold mb-2">Recommended Platforms</h4>
        {result.platforms?.map((platform: any, i: number) => (
          <div key={i} className="mb-2 p-2 bg-neutral-700 rounded">
            <div className="font-semibold">{platform.name} ({platform.relevanceScore}%)</div>
            <div className="text-sm text-neutral-300">{platform.searchTips}</div>
          </div>
        ))}
      </div>
      
      <div className="mb-4">
        <h4 className="text-lg font-semibold mb-2">Outreach Templates</h4>
        {result.outreachTemplates?.map((template: any, i: number) => (
          <div key={i} className="mb-3 p-2 bg-neutral-700 rounded">
            <div className="font-semibold">For {template.channel}</div>
            <div className="font-medium">Subject: {template.subject}</div>
            <div className="whitespace-pre-line text-neutral-300 border-l-2 border-primary pl-2 mt-1">{template.message}</div>
            {template.notes && <div className="text-sm text-accent-text mt-1">Note: {template.notes}</div>}
          </div>
        ))}
      </div>
    </div>
  );
  
  // Render interview agent result
  const renderInterviewResult = (result: any) => (
    <div className="bg-neutral-800 p-4 rounded-lg">
      <h3 className="text-xl font-semibold mb-4">Interview Plan for {result.candidateName}</h3>
      <div className="text-sm text-neutral-400 mb-4">For {result.jobTitle} position</div>
      
      <div className="mb-4">
        <h4 className="text-lg font-semibold mb-2">Assessment Areas</h4>
        <div className="flex flex-wrap gap-2">
          {result.assessmentAreas?.map((area: string, i: number) => (
            <span key={i} className="px-2 py-1 bg-primary-dark text-white rounded-full text-sm">{area}</span>
          ))}
        </div>
      </div>
      
      <div className="mb-4">
        <h4 className="text-lg font-semibold mb-2">Interview Structure ({result.suggestedDuration} min)</h4>
        <div className="space-y-2">
          {result.interviewStructure?.map((phase: any, i: number) => (
            <div key={i} className="p-2 bg-neutral-700 rounded">
              <div className="font-semibold">{phase.name} ({phase.duration} min)</div>
              <div className="text-sm text-neutral-300">{phase.description}</div>
              {phase.questionIds && (
                <div className="mt-1 text-sm text-primary-text">
                  Questions: {phase.questionIds.join(', ')}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      
      <div className="mb-4">
        <h4 className="text-lg font-semibold mb-2">Key Questions</h4>
        <div className="space-y-3">
          {result.questions?.map((q: any) => (
            <div key={q.id} className="p-2 bg-neutral-700 rounded">
              <div className="font-medium">{q.id}: {q.text}</div>
              <div className="text-sm text-accent-text">Area: {q.area}</div>
              <div className="text-xs text-neutral-400">Purpose: {q.purpose}</div>
              {q.followups && q.followups.length > 0 && (
                <div className="mt-1">
                  <div className="text-xs font-medium">Follow-ups:</div>
                  <ul className="list-disc pl-5 text-xs text-neutral-300">
                    {q.followups.map((f: string, i: number) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      
      <div className="mt-4 p-2 bg-neutral-700 rounded">
        <h4 className="text-md font-semibold mb-1">Interviewer Prep Notes</h4>
        <div className="whitespace-pre-line text-neutral-300 text-sm">{result.prepNotes}</div>
      </div>
    </div>
  );
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">AI Recruitment Agents Demo</h1>
      
      {/* Agent selection tabs */}
      <div className="flex border-b border-neutral-700 mb-6">
        <button 
          className={`px-4 py-2 border-b-2 ${activeAgent === 'screening' 
            ? 'border-primary text-primary-light' 
            : 'border-transparent text-neutral-400 hover:text-neutral-200'}`}
          onClick={() => handleAgentChange('screening')}
        >
          Screening Agent
        </button>
        <button 
          className={`px-4 py-2 border-b-2 ${activeAgent === 'sourcing' 
            ? 'border-primary text-primary-light' 
            : 'border-transparent text-neutral-400 hover:text-neutral-200'}`}
          onClick={() => handleAgentChange('sourcing')}
        >
          Sourcing Agent
        </button>
        <button 
          className={`px-4 py-2 border-b-2 ${activeAgent === 'interview' 
            ? 'border-primary text-primary-light' 
            : 'border-transparent text-neutral-400 hover:text-neutral-200'}`}
          onClick={() => handleAgentChange('interview')}
        >
          Interview Agent
        </button>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <div className="bg-neutral-800 p-4 rounded-lg mb-6">
            <h2 className="text-xl font-semibold mb-4">Agent Configuration</h2>
            
            {/* Document selection */}
            <div className="space-y-4">
              {activeAgent !== 'sourcing' && (
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    Select Candidate CV
                  </label>
                  <select
                    className="w-full bg-neutral-700 border border-neutral-600 rounded-md py-2 px-3 text-neutral-200"
                    value={selectedCvId || ''}
                    onChange={(e) => setSelectedCvId(e.target.value || undefined)}
                  >
                    <option value="">-- Select a CV --</option>
                    {cvs.map((cv) => (
                      <option key={cv.id} value={cv.id}>
                        {cv.name} - {cv.fileName || 'Untitled CV'}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Select Job Description
                </label>
                <select
                  className="w-full bg-neutral-700 border border-neutral-600 rounded-md py-2 px-3 text-neutral-200"
                  value={selectedJdId || ''}
                  onChange={(e) => setSelectedJdId(e.target.value || undefined)}
                >
                  <option value="">-- Select a JD --</option>
                  {jds.map((jd) => (
                    <option key={jd.id} value={jd.id}>
                      {jd.title} - {jd.fileName || 'Untitled JD'}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="pt-2">
                <button 
                  className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-2 px-4 rounded transition-colors"
                  onClick={runAgentDemo}
                  disabled={isProcessing || (!selectedJdId || (activeAgent !== 'sourcing' && !selectedCvId))}
                >
                  {isProcessing ? 'Processing...' : `Run ${activeAgent.charAt(0).toUpperCase() + activeAgent.slice(1)} Agent`}
                </button>
              </div>
            </div>
          </div>
          
          <div className="bg-neutral-800 p-4 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Conversational Interface</h2>
            <ConversationalInterface 
              cvId={selectedCvId}
              jdId={selectedJdId}
              onAnalysisComplete={(result) => console.log('Analysis complete:', result)}
            />
          </div>
        </div>
        
        <div>
          <div className="bg-neutral-800 p-4 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Agent Result</h2>
            
            {demoResult ? (
              renderDemoResult()
            ) : (
              <div className="text-center p-6 text-neutral-400">
                {isProcessing ? (
                  <div>
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto"></div>
                    <div className="mt-4">Processing your request...</div>
                  </div>
                ) : (
                  <div>
                    <p>Select documents and run the agent to see results</p>
                    <p className="mt-2 text-sm text-neutral-500">
                      Results will appear here after processing
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentsDemoView; 