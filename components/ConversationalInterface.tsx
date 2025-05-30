import React, { useState, useCallback, useRef, useEffect } from 'react';
import { ScreeningAgent } from '../services/agents/ScreeningAgent';
import { useLocalization } from '../hooks/useLocalization';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

interface ConversationalInterfaceProps {
  cvId?: string;
  jdId?: string;
  onAnalysisComplete?: (result: any) => void;
}

const ConversationalInterface: React.FC<ConversationalInterfaceProps> = ({ 
  cvId,
  jdId,
  onAnalysisComplete
}) => {
  const { t } = useLocalization();
  const [query, setQuery] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [agent] = useState(() => new ScreeningAgent());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Scroll to bottom of messages
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);
  
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);
  
  // Add a message to the chat
  const addMessage = useCallback((content: string, sender: 'user' | 'assistant') => {
    const newMessage: Message = {
      id: `msg-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
      content,
      sender,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newMessage]);
  }, []);
  
  // Handle user query submission
  const handleQuery = async () => {
    if (!query.trim() || isProcessing) return;
    
    addMessage(query, 'user');
    setIsProcessing(true);
    setQuery("");
    
    try {
      if (!cvId || !jdId) {
        addMessage("Please select both a CV and a job description to analyze.", 'assistant');
        setIsProcessing(false);
        return;
      }
      
      // Process query based on content
      if (query.toLowerCase().includes('analyze') || 
          query.toLowerCase().includes('evaluate') || 
          query.toLowerCase().includes('match')) {
        
        addMessage("I'll analyze this candidate against the job requirements...", 'assistant');
        
        const result = await agent.evaluateCandidate(cvId, jdId);
        
        // Safely handle potentially undefined properties
        const strengths = result.strengths || [];
        const gaps = result.gaps || [];
        const suggestedQuestions = result.suggestedQuestions || [];
        
        // Format the response
        const response = `
          **${t('matchScoreLabel')}** ${result.score || 'N/A'}/100
          
          **${t('strengthsLabel')}:**
          ${strengths.map((s: string) => `- ${s}`).join('\n')}
          
          **${t('areasForImprovementLabel')}:**
          ${gaps.map((g: string) => `- ${g}`).join('\n')}
          
          **${t('suggestedQuestionsLabel')}:**
          ${suggestedQuestions.map((q: string) => `- ${q}`).join('\n')}
          
          ${result.detailedAnalysis || ''}
        `;
        
        addMessage(response, 'assistant');
        
        if (onAnalysisComplete) {
          onAnalysisComplete(result);
        }
      } 
      else if (query.toLowerCase().includes('question') || 
               query.toLowerCase().includes('ask')) {
        
        addMessage("Generating personalized interview questions...", 'assistant');
        
        const result = await agent.generateFollowUpQuestions(cvId, jdId);
        
        // Safely handle potentially undefined properties
        const questions = result.questions || [];
        const focusAreas = result.focusAreas || [];
        
        const response = `
          **${t('suggestedQuestionsLabel')}:**
          ${questions.map((q: string, i: number) => `${i+1}. ${q}`).join('\n\n')}
          
          These questions focus on: ${focusAreas.join(', ')}
        `;
        
        addMessage(response, 'assistant');
      }
      else {
        // Default response
        addMessage("I can help you evaluate this candidate against the job description or generate interview questions. Just let me know what you need!", 'assistant');
      }
    } catch (error) {
      console.error("Error processing query:", error);
      addMessage(`Sorry, I encountered an error: ${(error as Error).message}`, 'assistant');
    } finally {
      setIsProcessing(false);
    }
  };
  
  return (
    <div className="flex flex-col p-4 bg-neutral-900 rounded-lg h-full max-h-[500px]">
      <div className="flex-1 overflow-y-auto mb-4">
        {messages.length === 0 ? (
          <div className="text-neutral-500 text-center py-8">
            {t('askMeAboutPrompt')}
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map(message => (
              <div 
                key={message.id} 
                className={`p-3 rounded-lg ${
                  message.sender === 'user' 
                    ? 'bg-neutral-800 ml-8' 
                    : 'bg-neutral-700 mr-8'
                }`}
              >
                <div className="text-sm text-neutral-400 mb-1">
                  {message.sender === 'user' ? t('messageSenderYou') : t('messageSenderAI')}
                </div>
                <div className="whitespace-pre-line">
                  {message.content}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
      
      <div className="flex items-center">
        <input 
          className="flex-1 p-3 rounded-l bg-neutral-800 text-white focus:outline-none"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('messagePlaceholder')}
          onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
          disabled={isProcessing}
        />
        <button 
          className="p-3 bg-primary text-white rounded-r focus:outline-none disabled:bg-neutral-600"
          onClick={handleQuery}
          disabled={isProcessing || !query.trim()}
        >
          {isProcessing ? t('processingAgentRequest') : t('sendButton')}
        </button>
      </div>
    </div>
  );
};

export default ConversationalInterface; 