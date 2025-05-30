import React, { useState, useEffect } from 'react';
import ConversationalInterface from '../components/ConversationalInterface';
import { documentService } from '../services/documentService';
import { CVData, JobDescriptionData } from '../types';
import { useLocalization } from '../hooks/useLocalization';

const AIAssistantView: React.FC = () => {
  const { t } = useLocalization();
  const [cvs, setCvs] = useState<CVData[]>([]);
  const [jds, setJds] = useState<JobDescriptionData[]>([]);
  const [selectedCvId, setSelectedCvId] = useState<string | undefined>(undefined);
  const [selectedJdId, setSelectedJdId] = useState<string | undefined>(undefined);
  const [analysisResult, setAnalysisResult] = useState<any | null>(null);
  
  // Load documents from local storage
  useEffect(() => {
    try {
      const storedCvsString = localStorage.getItem('recruitx_cvs');
      if (storedCvsString) setCvs(JSON.parse(storedCvsString) as CVData[]);
      
      const storedJdsString = localStorage.getItem('recruitx_jds');
      if (storedJdsString) setJds(JSON.parse(storedJdsString) as JobDescriptionData[]);
    } catch (e) {
      console.error("Error loading data from localStorage:", e);
    }
  }, []);
  
  const handleAnalysisComplete = (result: any) => {
    setAnalysisResult(result);
  };
  
  return (
    <div className="flex flex-col h-full p-4 gap-4">
      <h1 className="text-2xl font-bold mb-4">{t('aiAssistantTitle')}</h1>
      
      <div className="flex flex-row gap-4 mb-4">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-2">{t('selectCvLabel')}</label>
          <select 
            className="w-full p-2 bg-neutral-800 text-white rounded"
            value={selectedCvId || ""}
            onChange={(e) => setSelectedCvId(e.target.value || undefined)}
          >
            <option value="">{t('selectCvPlaceholder')}</option>
            {cvs.map(cv => (
              <option key={cv.id} value={cv.id}>{cv.name}</option>
            ))}
          </select>
        </div>
        
        <div className="flex-1">
          <label className="block text-sm font-medium mb-2">{t('selectJdLabel')}</label>
          <select 
            className="w-full p-2 bg-neutral-800 text-white rounded"
            value={selectedJdId || ""}
            onChange={(e) => setSelectedJdId(e.target.value || undefined)}
          >
            <option value="">{t('selectJdPlaceholder')}</option>
            {jds.map(jd => (
              <option key={jd.id} value={jd.id}>{jd.title}</option>
            ))}
          </select>
        </div>
      </div>
      
      <div className="flex flex-row gap-4 flex-1">
        <div className="flex-1">
          <ConversationalInterface 
            cvId={selectedCvId} 
            jdId={selectedJdId} 
            onAnalysisComplete={handleAnalysisComplete}
          />
        </div>
        
        {analysisResult && (
          <div className="flex-1 bg-neutral-900 rounded-lg p-4 overflow-y-auto">
            <h2 className="text-xl font-semibold mb-4">{t('analysisResultsTitle')}</h2>
            
            <div className="mb-4">
              <div className="text-lg font-medium">{t('matchScoreLabel')}</div>
              <div className="text-3xl font-bold">{analysisResult.score}/100</div>
            </div>
            
            <div className="mb-4">
              <div className="text-lg font-medium mb-2">{t('strengthsLabel')}</div>
              <ul className="list-disc pl-5 space-y-1">
                {analysisResult.strengths.map((strength: string, idx: number) => (
                  <li key={idx}>{strength}</li>
                ))}
              </ul>
            </div>
            
            <div className="mb-4">
              <div className="text-lg font-medium mb-2">{t('areasForImprovementLabel')}</div>
              <ul className="list-disc pl-5 space-y-1">
                {analysisResult.gaps.map((gap: string, idx: number) => (
                  <li key={idx}>{gap}</li>
                ))}
              </ul>
            </div>
            
            <div>
              <div className="text-lg font-medium mb-2">{t('suggestedQuestionsLabel')}</div>
              <ul className="list-disc pl-5 space-y-1">
                {analysisResult.suggestedQuestions.map((question: string, idx: number) => (
                  <li key={idx}>{question}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIAssistantView; 