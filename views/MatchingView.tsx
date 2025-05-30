import React, { useState, useEffect, useRef } from 'react';
import { useLocalization } from '../hooks/useLocalization';
import { CVData, JobDescriptionData, MatchResult, AppSettings, Language } from '../types';
import DocumentSelector from '../components/DocumentSelector';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';
import ScoreReport from '../components/ScoreReport';
import ProgressBar from '../components/ProgressBar';
import { ANALYSIS_DURATION_ESTIMATE_MS } from '../constants';

interface MatchingViewProps {
  cvs: CVData[];
  jds: JobDescriptionData[];
  appSettings: AppSettings;
  currentLanguage: Language;
  onPerformSingleAnalysis: (cv: CVData, jd: JobDescriptionData) => Promise<MatchResult | null>;
  onPerformBulkAnalysis: (cvs: CVData[], jds: JobDescriptionData[]) => Promise<{ successfulResults: MatchResult[], errorsEncountered: string[] }>;
  onAnalysisComplete: (results: MatchResult[], errors?: string[]) => void; // To update global state
  onViewReport: (reportId: string) => void; 
  activeMatchResultForDisplay: MatchResult | null; // Passed down if a report is active
  setActiveMatchResultForDisplay: (result: MatchResult | null) => void; // To clear it
}

const analysisStages: Array<{ key: string; threshold: number }> = [
  { key: 'stagePreparingEnv', threshold: 0 },
  { key: 'stageProcessingCv', threshold: 10 }, // Assuming bulk processing for stages
  { key: 'stageProcessingJd', threshold: 30 },
  { key: 'stagePrioritizingNotes', threshold: 50 },
  { key: 'stageCrossReferencing', threshold: 60 },
  { key: 'stageCalculatingScores', threshold: 80 },
  { key: 'stageGeneratingReport', threshold: 95 },
];

const MatchingView: React.FC<MatchingViewProps> = ({
  cvs,
  jds,
  appSettings,
  currentLanguage,
  onPerformSingleAnalysis,
  onPerformBulkAnalysis,
  onAnalysisComplete,
  onViewReport,
  activeMatchResultForDisplay,
  setActiveMatchResultForDisplay,
}) => {
  const { t } = useLocalization();

  const [selectedCvIds, setSelectedCvIds] = useState<string[]>([]);
  const [selectedJdIds, setSelectedJdIds] = useState<string[]>([]);
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  const [analysisProgress, setAnalysisProgress] = useState(0);
  const progressIntervalRef = useRef<number | null>(null);
  const [currentAnalysisStageKey, setCurrentAnalysisStageKey] = useState<string | null>(null);
  const stageMessageTimeoutRef = useRef<number | null>(null);


  useEffect(() => {
    if (isLoading) {
      setAnalysisProgress(0); 
      setCurrentAnalysisStageKey(analysisStages[0].key); 
      const increment = 100 / (ANALYSIS_DURATION_ESTIMATE_MS / 100); 
      
      progressIntervalRef.current = window.setInterval(() => {
        setAnalysisProgress(prev => {
          if (prev >= 95) { 
             if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
            return 95;
          }
          return prev + increment;
        });
      }, 100);
    } else {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
      setAnalysisProgress(100); 
      
      if (stageMessageTimeoutRef.current) clearTimeout(stageMessageTimeoutRef.current);

      if (!error && infoMessage?.includes('Analysis Complete')) { 
          setCurrentAnalysisStageKey('stageAnalysisComplete');
      } else if (error) {
          setCurrentAnalysisStageKey('stageAnalysisFailed');
      } else {
          setCurrentAnalysisStageKey(null); 
      }
      
      stageMessageTimeoutRef.current = window.setTimeout(() => {
        setCurrentAnalysisStageKey(null);
      }, 4000); 
    }
    return () => {
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
      if (stageMessageTimeoutRef.current) clearTimeout(stageMessageTimeoutRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoading, error, infoMessage]); // Dependencies for progress bar management

  useEffect(() => {
    if (isLoading && analysisProgress < 95) { 
      let currentStage = analysisStages[0].key;
      for (let i = analysisStages.length - 1; i >= 0; i--) {
        if (analysisProgress >= analysisStages[i].threshold) {
          currentStage = analysisStages[i].key;
          break;
        }
      }
      setCurrentAnalysisStageKey(currentStage);
    }
  }, [analysisProgress, isLoading]);


  const handleSingleMatch = async () => {
    if (selectedCvIds.length !== 1 || selectedJdIds.length !== 1) {
      setError(t('selectCVAndJD')); 
      return;
    }
    setError(null);
    setInfoMessage(null);
    setIsLoading(true);
    setActiveMatchResultForDisplay(null);

    const cv = cvs.find(c => c.id === selectedCvIds[0]);
    const jd = jds.find(j => j.id === selectedJdIds[0]);

    if (!cv || !jd) {
      setError(t('selectedCvOrJdNotFound'));
      setIsLoading(false);
      return;
    }
    
    try {
        const analysisResult = await onPerformSingleAnalysis(cv, jd);
        if (analysisResult) {
            onAnalysisComplete([analysisResult]);
            setActiveMatchResultForDisplay(analysisResult); // Display immediately
            setInfoMessage(t('stageAnalysisComplete'));
        } else {
            setError(t('analysisDidNotProduceResult'));
        }
    } catch (e: any) {
        console.error(`Matching error for ${cv.name} & ${jd.title}:`, e);
        setError(e.message || t('unexpectedErrorDuringAnalysis'));
    } finally {
        setIsLoading(false);
    }
  };

  const handleBulkMatch = async () => {
    if (selectedCvIds.length === 0 || selectedJdIds.length === 0) {
      setError(t('selectMultipleCvAndJd'));
      return;
    }
    setError(null);
    setInfoMessage(null);
    setIsLoading(true); 
    setActiveMatchResultForDisplay(null);

    const selectedCvs = cvs.filter(cv => selectedCvIds.includes(cv.id));
    const selectedJds = jds.filter(jd => selectedJdIds.includes(jd.id));

    if (selectedCvs.length === 0 || selectedJds.length === 0) {
        setError(t('noValidCvsOrJdsForBulk'));
        setIsLoading(false);
        return;
    }
    
    try {
        const { successfulResults, errorsEncountered } = await onPerformBulkAnalysis(selectedCvs, selectedJds);
        
        let message = "";
        if (successfulResults.length > 0) {
            message += t('bulkAnalysisComplete').replace('{count}', successfulResults.length.toString());
        }
        if (errorsEncountered.length > 0) {
            message += t('bulkAnalysisErrors').replace('{count}', errorsEncountered.length.toString());
            setError(t('errorBulkOperation')
                .replace('{errorCount}', errorsEncountered.length.toString())
                .replace('{errorMessages}', errorsEncountered.map(e => `- ${e}`).join('\n')));
        }
        
        onAnalysisComplete(successfulResults, errorsEncountered.length > 0 ? errorsEncountered : undefined);
        setInfoMessage(message || t('bulkAnalysisProcessed'));

    } catch (e: any) {
        console.error("Error during bulk match orchestrator:", e);
        setError(e.message || t('unexpectedErrorDuringBulkAnalysis'));
    } finally {
        setIsLoading(false);
    }
  };
  
  const handleResetSelections = () => {
    setSelectedCvIds([]);
    setSelectedJdIds([]);
    setError(null);
    setInfoMessage(null);
    setActiveMatchResultForDisplay(null);
  };

  const showSingleMatchButton = selectedCvIds.length === 1 && selectedJdIds.length === 1;
  const totalPairs = selectedCvIds.length * selectedJdIds.length;
  const showBulkMatchButton = totalPairs > 0 && !showSingleMatchButton;


  if (activeMatchResultForDisplay) {
    return (
      <div className="pb-10">
         <button onClick={() => setActiveMatchResultForDisplay(null)} className="mb-6 flex items-center px-4 py-2 bg-primary-DEFAULT text-white rounded-md hover:bg-primary-dark transition-colors shadow-md-dark subtle-hover-lift">
             <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 mr-2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" /></svg>
             {t('backToDashboard')} {/* Or "Back to Matching Selections" */}
         </button>
         {infoMessage && ( 
            <div className="mb-4 p-3 bg-primary-DEFAULT/10 border-l-4 border-primary-DEFAULT text-primary-text rounded-md shadow-md-dark text-sm">
              {infoMessage}
            </div>
          )}
        <ScoreReport result={activeMatchResultForDisplay} appSettings={activeMatchResultForDisplay.appSettingsSnapshot || appSettings} />
      </div>
    );
  }


  return (
    <div className="space-y-8">
      <section id="selection" className="bg-neutral-850 p-6 md:p-8 rounded-xl shadow-xl-dark border border-neutral-700">
        <h2 className="text-2xl font-semibold text-neutral-100 mb-6 border-b border-neutral-700 pb-4">
          {t('selectCVsAndJDsForMatching')}
        </h2>
        {error && <ErrorAlert message={error} onClose={() => setError(null)} />}
        {infoMessage && !isLoading && (
          <div className="mb-4 p-3 bg-primary-DEFAULT/10 border-l-4 border-primary-DEFAULT text-primary-text rounded-md shadow-md-dark text-sm">
            {infoMessage}
          </div>
        )}
        <DocumentSelector 
            cvs={cvs} 
            jds={jds} 
            selectedCvIds={selectedCvIds} 
            setSelectedCvIds={setSelectedCvIds} 
            selectedJdIds={selectedJdIds} 
            setSelectedJdIds={setSelectedJdIds} 
        />
      </section>

      <section id="controls" className="text-center py-4 space-y-4 sm:space-y-0 sm:flex sm:justify-center sm:space-x-4">
        <button 
          onClick={handleSingleMatch} 
          disabled={selectedCvIds.length !== 1 || selectedJdIds.length !== 1 || isLoading} 
          className="px-8 py-3 bg-primary-DEFAULT text-white font-semibold text-lg rounded-lg shadow-md-dark hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-neutral-900 focus:ring-primary-light disabled:opacity-60 disabled:bg-neutral-600 disabled:cursor-not-allowed transition-colors duration-150 ease-in-out subtle-hover-lift"
        >
          {isLoading ? t('loadingMessage') : t('performMatchAnalysisButton')}
        </button>
        {showBulkMatchButton && (
            <button 
                onClick={handleBulkMatch} 
                disabled={isLoading} 
                className="px-8 py-3 bg-primary-dark text-white font-semibold text-lg rounded-lg shadow-md-dark hover:bg-primary-DEFAULT focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-neutral-900 focus:ring-primary-light disabled:opacity-60 disabled:bg-neutral-600 disabled:cursor-not-allowed transition-colors duration-150 ease-in-out subtle-hover-lift"
            >
                {isLoading ? t('loadingMessage') : t('performBulkMatchAnalysisButton')}
            </button>
        )}
        {(!showSingleMatchButton && !showBulkMatchButton && totalPairs === 0 && (selectedCvIds.length > 0 || selectedJdIds.length > 0)) && ( 
          <p className="text-sm text-neutral-400 mt-2">{selectedCvIds.length === 0 ? t('pleaseSelectAtLeastOneCV') : t('pleaseSelectAtLeastOneJD')}</p>
        )}
          <button 
            onClick={handleResetSelections} 
            disabled={isLoading} 
            className="px-6 py-3 bg-neutral-600 text-neutral-100 font-medium rounded-lg shadow-md-dark hover:bg-neutral-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-neutral-900 focus:ring-neutral-400 disabled:bg-neutral-700 disabled:opacity-70 transition-colors"
        >
            {t('clearSelectionsButton')}
        </button>
      </section>

      {isLoading && (
        <div className="pt-5 text-center">
            <ProgressBar progress={analysisProgress} />
            <p className="text-sm text-neutral-400 mt-2">{t('analysisProgressMessage').replace('{progress}', Math.min(analysisProgress, 100).toFixed(0))}</p>
            {currentAnalysisStageKey && (
                  <p className="text-sm text-primary-light mt-1 font-medium animate-pulse">{t('currentStageLabel')} {t(currentAnalysisStageKey)}</p>
            )}
        </div>
      )}
      {!isLoading && currentAnalysisStageKey && (currentAnalysisStageKey === 'stageAnalysisComplete' || currentAnalysisStageKey === 'stageAnalysisFailed') && (
        <div className="pt-5 text-center">
              <p className={`text-md font-semibold mt-1 ${currentAnalysisStageKey === 'stageAnalysisComplete' ? 'text-success-textDarkBg' : 'text-danger-textDarkBg'}`}>{t(currentAnalysisStageKey)}</p>
        </div>
      )}
    </div>
  );
};

export default MatchingView;
