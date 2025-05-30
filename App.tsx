import React, { useState, useCallback, useEffect, ChangeEvent } from 'react';
import { LocalizationProvider, useLocalization } from './hooks/useLocalization';
import Header from './components/Header';
import Footer from './components/Footer';
import ScoreReport from './components/ScoreReport';
import ErrorAlert from './components/ErrorAlert';
import Navbar from './components/Navbar'; 
import DashboardView from './views/DashboardView';
import CandidatesListView from './views/CandidatesListView';
import CandidateProfileView from './views/CandidateProfileView';
import JobsListView from './views/JobsListView';
import JobProfileView from './views/JobProfileView';
import SettingsView from './views/SettingsView'; 
import MatchingView from './views/MatchingView'; 
import SuccessCheckAnimation from './components/SuccessCheckAnimation';
import { 
    CVData, JobDescriptionData, MatchResult, Language, View, AppSettings, 
    StructuredCV, StructuredJD 
} from './types'; 
import { analyzeCvJdMatch, getStructuredDocumentRepresentation } from './services/geminiService';
import { PDF_MAX_SIZE_MB, DEFAULT_APP_SETTINGS } from './constants'; 

import * as pdfjsLib from 'pdfjs-dist/build/pdf.mjs';
import mammoth from 'mammoth';
import * as XLSX from 'xlsx';
import AIAssistantView from './views/AIAssistantView';
import AgentsDemoView from './views/AgentsDemoView';

// Configure PDF.js
const pdfWorkerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.4.168/build/pdf.worker.min.js';
try {
  if (typeof window !== 'undefined') {
    pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerSrc;
  }
} catch (e) {
  console.warn("Could not configure pdf.js. PDF processing might be affected.", e);
}

// Interface for data from SimpleDocumentForm
interface NewDocumentData {
  name: string;
  content: string;
  fileMimeType?: string;
  fileName?: string;
  recruiterNotes?: string;
}


const AppContent: React.FC = () => {
  const { t, language } = useLocalization();

  const [currentView, setCurrentViewInternal] = useState<View>('dashboard');
  
  const [cvs, setCvs] = useState<CVData[]>([]);
  const [jds, setJds] = useState<JobDescriptionData[]>([]);
  const [matchResults, setMatchResults] = useState<MatchResult[]>([]);
  const [appSettings, setAppSettings] = useState<AppSettings>(DEFAULT_APP_SETTINGS);
  
  const [activeMatchResult, setActiveMatchResult] = useState<MatchResult | null>(null);
  const [globalError, setGlobalError] = useState<string | null>(null); 
  const [globalInfoMessage, setGlobalInfoMessage] = useState<string | null>(null); 

  const [editingCandidateId, setEditingCandidateId] = useState<string | null>(null);
  const [editingJobId, setEditingJobId] = useState<string | null>(null);

  const [showSettingsSaveSuccessAnimation, setShowSettingsSaveSuccessAnimation] = useState(false);


  const setCurrentView = useCallback((view: View) => {
    if (view !== 'report_details') setActiveMatchResult(null);
    setGlobalError(null);

    if (view !== 'settings' && !(globalInfoMessage && (globalInfoMessage.includes(t('settingsSavedSuccess')) || globalInfoMessage.includes(t('settingsResetSuccess'))))){
        setGlobalInfoMessage(null);
    }
    
    if (view !== 'candidate_profile') setEditingCandidateId(null);
    if (view !== 'job_profile') setEditingJobId(null);
    setCurrentViewInternal(view);

    if (view === 'settings' && (globalInfoMessage && (globalInfoMessage.includes(t('settingsSavedSuccess')) || globalInfoMessage.includes(t('settingsResetSuccess'))))){
        setTimeout(() => setGlobalInfoMessage(null), 3000);
    }
  }, [globalInfoMessage, t]);


  useEffect(() => {
    try {
      const storedCvsString = localStorage.getItem('recruitx_cvs');
      if (storedCvsString) setCvs(JSON.parse(storedCvsString) as CVData[]);

      const storedJdsString = localStorage.getItem('recruitx_jds');
      if (storedJdsString) setJds(JSON.parse(storedJdsString) as JobDescriptionData[]);
      
      const storedMatchResults = localStorage.getItem('recruitx_match_results');
      if (storedMatchResults) setMatchResults(JSON.parse(storedMatchResults));
      
      const storedAppSettings = localStorage.getItem('recruitx_app_settings');
      if (storedAppSettings) {
        const parsedSettings = JSON.parse(storedAppSettings) as AppSettings;
        // Validate the structure of parsedSettings, especially after removing aiStrictness
        if (parsedSettings && parsedSettings.assessmentDimensions && typeof parsedSettings.nexusRankingScoreThreshold === 'number' && !('aiStrictness' in parsedSettings)) {
           setAppSettings(parsedSettings);
        } else {
            // If structure is old or invalid, reset to default
            setAppSettings(DEFAULT_APP_SETTINGS);
            localStorage.setItem('recruitx_app_settings', JSON.stringify(DEFAULT_APP_SETTINGS));
        }
      } else {
        setAppSettings(DEFAULT_APP_SETTINGS); 
        localStorage.setItem('recruitx_app_settings', JSON.stringify(DEFAULT_APP_SETTINGS));
      }
    } catch (e) {
      console.error("Error loading data from localStorage:", e);
      setGlobalError(t('errorLoadingData'));
      setAppSettings(DEFAULT_APP_SETTINGS); 
      localStorage.setItem('recruitx_app_settings', JSON.stringify(DEFAULT_APP_SETTINGS));
    }
  }, []);

  useEffect(() => { try { localStorage.setItem('recruitx_cvs', JSON.stringify(cvs)); } catch (e) { console.error("Error saving CVs to localStorage:", e); }}, [cvs]);
  useEffect(() => { try { localStorage.setItem('recruitx_jds', JSON.stringify(jds)); } catch (e) { console.error("Error saving JDs to localStorage:", e); }}, [jds]);
  useEffect(() => { try { localStorage.setItem('recruitx_match_results', JSON.stringify(matchResults)); } catch (e) { console.error("Error saving MatchResults to localStorage:", e); }}, [matchResults]);
  useEffect(() => { try { localStorage.setItem('recruitx_app_settings', JSON.stringify(appSettings)); } catch (e) { console.error("Error saving AppSettings to localStorage:", e); }}, [appSettings]);

  const generateNameFromFileName = (fName: string): string => {
    if (!fName) return t('untitledDocument');
    const lastDotIndex = fName.lastIndexOf('.');
    const nameWithoutExtension = lastDotIndex > 0 ? fName.substring(0, lastDotIndex) : fName;
    return nameWithoutExtension.replace(/[_.-]/g, ' ').replace(/\s+/g, ' ').trim() || t('untitledDocument');
  };

  const extractFileContent = useCallback(async (file: File): Promise<{content: string, mimeType: string, fileName: string}> => {
      const fileNameLower = file.name.toLowerCase();
      if (file.type === 'application/pdf' || fileNameLower.endsWith(".pdf")) {
        if (file.size > PDF_MAX_SIZE_MB * 1024 * 1024) {
          throw new Error(t('errorFileSizeTooLarge'));
        }
        try {
          const arrayBuffer = await file.arrayBuffer();
          const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
          const pdf = await loadingTask.promise;
          let fullText = '';
          for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const textContent = await page.getTextContent();
            const pageText = textContent.items.map(item => ('str' in item ? item.str : '')).join(' ');
            fullText += pageText + '\n';
          }
          return { content: fullText.trim() || `[PDF content extracted but appears to be empty or contains only images]`, mimeType: file.type || 'application/pdf', fileName: file.name };
        } catch (pdfError) {
          console.error("Error processing PDF file:", pdfError);
          // Provide a fallback when PDF.js fails
          return { 
            content: `[Unable to extract text from PDF. The file may be password-protected, corrupted, or contain only images.]\n\nFile: ${file.name}\nSize: ${(file.size / 1024).toFixed(2)} KB`, 
            mimeType: file.type || 'application/pdf', 
            fileName: file.name 
          };
        }
      } else if (file.type === 'text/plain' || fileNameLower.endsWith(".txt")) { 
        const text = await file.text();
        return { content: text, mimeType: file.type || 'text/plain', fileName: file.name };
      } else if (file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || fileNameLower.endsWith('.docx')) {
        const arrayBuffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer });
        return { content: result.value, mimeType: file.type || 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', fileName: file.name };
      } else if ((file.type === 'application/msword' && fileNameLower.endsWith('.doc'))) {
         // .doc is problematic and often fails with mammoth.js or requires more complex handling.
         // For now, explicitly state it's not fully supported to manage expectations.
         throw new Error(t('errorUnsupportedFileType') + ` (.doc files have limited support, recommend .docx)`);
      } else if (file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || fileNameLower.endsWith('.xlsx') || file.type === 'application/vnd.ms-excel' || fileNameLower.endsWith('.xls')) {
        const arrayBuffer = await file.arrayBuffer();
        const workbook = XLSX.read(arrayBuffer, { type: 'array' });
        let fullText = '';
        workbook.SheetNames.forEach(sheetName => {
          const worksheet = workbook.Sheets[sheetName];
          const text = XLSX.utils.sheet_to_txt(worksheet, { strip: true });
          fullText += text + '\n\n';
        });
        return { content: fullText.trim(), mimeType: file.type || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', fileName: file.name };
      } else {
        // Fallback for other file types - try to read as text
        try {
            const text = await file.text();
             // Basic check for binary-like content: presence of many null characters or non-printable ASCII
            let nonPrintableChars = 0;
            for (let i = 0; i < Math.min(text.length, 500); i++) { // Check first 500 chars
                const charCode = text.charCodeAt(i);
                if (charCode === 0 || (charCode < 32 && charCode !== 9 && charCode !== 10 && charCode !== 13)) {
                    nonPrintableChars++;
                }
            }
            if (text.length > 0 && nonPrintableChars < (text.length * 0.1)) { // If less than 10% non-printable, assume text
                 console.warn(`Unknown file type '${file.type}' for '${file.name}', attempting to read as text.`);
                 return { content: text, mimeType: 'text/plain', fileName: file.name };
            } else {
                 throw new Error(t('errorUnsupportedFileType') + ` (Type: ${file.type || 'unknown'})`);
            }
        } catch (textReadError) {
            console.error("Error attempting to read unknown file as text:", textReadError);
            throw new Error(t('errorUnsupportedFileType') + ` (Type: ${file.type || 'unknown'})`);
        }
      }
  }, [t]);

  const handleAddCv = useCallback(async (data: NewDocumentData) => {
    const newCv: CVData = { 
      id: `cv-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`, 
      name: data.name, 
      content: data.content,
      fileMimeType: data.fileMimeType || 'text/plain',
      fileName: data.fileName,
      recruiterNotes: data.recruiterNotes,
      createdAt: new Date().toISOString(),
      isStructuring: true, 
    };
    setCvs(prev => [newCv, ...prev]);
    
    try {
      const structuredData = await getStructuredDocumentRepresentation(newCv.content, 'cv', language, newCv.name);
      setCvs(prevCvs => prevCvs.map(cv =>
        cv.id === newCv.id ? { ...cv, structuredData: structuredData as StructuredCV, sourceLanguage: language, isStructuring: false } : cv
      ));
    } catch (err) {
      console.error("Failed to structure CV in background:", err);
      setCvs(prevCvs => prevCvs.map(cv =>
        cv.id === newCv.id ? { ...cv, isStructuring: false, structuredData: undefined } : cv
      ));
    }
  }, [language]);

  const handleAddJd = useCallback(async (data: NewDocumentData) => {
    const newJd: JobDescriptionData = { 
      id: `jd-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`, 
      title: data.name, 
      content: data.content,
      fileMimeType: data.fileMimeType || 'text/plain',
      fileName: data.fileName,
      recruiterNotes: data.recruiterNotes,
      createdAt: new Date().toISOString(),
      isStructuring: true, 
    };
    setJds(prev => [newJd, ...prev]);

     try {
      const structuredData = await getStructuredDocumentRepresentation(newJd.content, 'jd', language, newJd.title);
      setJds(prevJds => prevJds.map(jd =>
        jd.id === newJd.id ? { ...jd, structuredData: structuredData as StructuredJD, sourceLanguage: language, isStructuring: false } : jd
      ));
    } catch (err) {
      console.error("Failed to structure JD in background:", err);
      setJds(prevJds => prevJds.map(jd =>
        jd.id === newJd.id ? { ...jd, isStructuring: false, structuredData: undefined } : jd
      ));
    }
  }, [language]);


  const handleUpdateCvData = useCallback((updatedCv: CVData) => {
    setCvs(prevCvs => prevCvs.map(cv => cv.id === updatedCv.id ? updatedCv : cv));
    setGlobalInfoMessage(t('settingsSavedSuccess')); 
    setCurrentView('candidates_list');
  }, [t, setCurrentView]);

  const handleUpdateJdData = useCallback((updatedJd: JobDescriptionData) => {
    setJds(prevJds => prevJds.map(jd => jd.id === updatedJd.id ? updatedJd : jd));
    setGlobalInfoMessage(t('settingsSavedSuccess')); 
    setCurrentView('jobs_list');
  }, [t, setCurrentView]);


  const performSingleAnalysis = async (cv: CVData, jd: JobDescriptionData): Promise<MatchResult | null> => {
    try {
      const { analysis } = await analyzeCvJdMatch( 
        cv.content, cv.fileMimeType, jd.content, jd.fileMimeType,
        cv.name, jd.title, language, appSettings, 
        cv.recruiterNotes, jd.recruiterNotes
      );
      
      return {
        id: `match-${cv.id.slice(-4)}-${jd.id.slice(-4)}-${Date.now()}`, 
        cvId: cv.id, jdId: jd.id, candidateName: analysis.candidateName || cv.name, jobTitle: analysis.jobTitle || jd.title,
        overallScore: analysis.overallScore,
        scores: analysis.scores, 
        detailedExplanation: analysis.detailedExplanation, 
        positivePoints: analysis.positivePoints,
        painPoints: analysis.painPoints,
        discussionPoints: analysis.discussionPoints,
        timestamp: new Date().toISOString(), reportLanguage: language,
        cvFileName: cv.fileName, jdFileName: jd.fileName, cvRecruiterNotes: cv.recruiterNotes, jdRecruiterNotes: jd.recruiterNotes,
        appSettingsSnapshot: JSON.parse(JSON.stringify(appSettings)) 
      };
    } catch (e: any) {
      console.error(`Matching error for ${cv.name} & ${jd.title}:`, e);
      throw e; 
    }
  };
  
  const performBulkAnalysis = async (
    selectedCvs: CVData[], 
    selectedJds: JobDescriptionData[]
  ): Promise<{ successfulResults: MatchResult[], errorsEncountered: string[] }> => {
      const analysisPairs: Array<{ cv: CVData, jd: JobDescriptionData}> = [];
      for (const cv of selectedCvs) {
          for (const jd of selectedJds) {
              analysisPairs.push({ cv, jd });
          }
      }

      const analysisPromises = analysisPairs.map(pair => 
          performSingleAnalysis(pair.cv, pair.jd)
              .then(result => ({ status: 'fulfilled' as const, value: result, pair }))
              .catch(reason => ({ status: 'rejected' as const, reason, pair }))
      );

      const settledResults = await Promise.all(analysisPromises);
      const successfulResults: MatchResult[] = [];
      const errorsEncountered: string[] = [];

      settledResults.forEach(settledResult => {
          if (settledResult.status === 'fulfilled' && settledResult.value) {
              successfulResults.push(settledResult.value);
          } else if (settledResult.status === 'rejected') {
              const errorMsg = settledResult.reason instanceof Error ? settledResult.reason.message : String(settledResult.reason);
              errorsEncountered.push(`Error for ${settledResult.pair.cv.name} & ${settledResult.pair.jd.title}: ${errorMsg}`);
          }
      });
      return { successfulResults, errorsEncountered };
  };

  const handleAnalysisCompleteInMatchingView = (results: MatchResult[], errors?: string[]) => {
    if (results.length > 0) {
        setMatchResults(prev => {
            const existingIds = new Set(prev.map(r => r.id));
            const trulyNewResults = results.filter(nmr => nmr && nmr.id && !existingIds.has(nmr.id));
            return [...trulyNewResults, ...prev];
        });
    }
  };


  const viewReport = (reportId: string) => {
    const report = matchResults.find(r => r.id === reportId);
    if (report) {
      setActiveMatchResult(report);
      setCurrentViewInternal('report_details');
    }
  };

  const deleteCv = useCallback((id: string, skipConfirm = false) => {
    const confirmed = skipConfirm || window.confirm(t('confirmDeleteCandidateMessage'));
    if (confirmed) {
      setCvs(prev => prev.filter(cv => cv.id !== id));
      setMatchResults(prev => prev.filter(mr => mr.cvId !== id));
      if (editingCandidateId === id) {
        setEditingCandidateId(null);
        setCurrentView('candidates_list');
      }
    }
  }, [t, editingCandidateId, setCurrentView]); 

  const deleteJd = useCallback((id: string, skipConfirm = false) => {
    const confirmed = skipConfirm || window.confirm(t('confirmDeleteJobMessage'));
    if (confirmed) {
      setJds(prev => prev.filter(jd => jd.id !== id));
      setMatchResults(prev => prev.filter(mr => mr.jdId !== id));
      if (editingJobId === id) {
        setEditingJobId(null);
        setCurrentView('jobs_list');
      }
    }
  }, [t, editingJobId, setCurrentView]);

  const deleteMatchResult = useCallback((id: string) => {
    const confirmed = window.confirm(t('confirmDeleteMessage'));
    if (confirmed) {
      setMatchResults(prev => prev.filter(mr => mr.id !== id));
      if (activeMatchResult?.id === id) {
        setActiveMatchResult(null);
        setCurrentView('dashboard'); 
      }
    }
  }, [t, activeMatchResult, setCurrentView]);

  const handleViewCandidateProfile = (candidateId: string) => {
    setEditingCandidateId(candidateId);
    setCurrentView('candidate_profile');
  };

  const handleViewJobProfile = (jobId: string) => {
    setEditingJobId(jobId);
    setCurrentView('job_profile');
  };

  const handleUpdateAppSettings = useCallback((newSettings: AppSettings) => {
    setAppSettings(newSettings);
    setGlobalInfoMessage(t('settingsSavedSuccess'));
    setShowSettingsSaveSuccessAnimation(true);
    setTimeout(() => {
      setShowSettingsSaveSuccessAnimation(false);
    }, 2000);
  },[t]);


  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <DashboardView 
          cvs={cvs} 
          jds={jds} 
          matchResults={matchResults} 
          onDeleteMatchResult={deleteMatchResult}
          onViewReport={viewReport}
          onDeleteCv={deleteCv}
          onDeleteJd={deleteJd}
          onStartNewAnalysis={() => setCurrentView('matching')}
        />;
      case 'matching':
        return <MatchingView 
          cvs={cvs} 
          jds={jds}
          appSettings={appSettings}
          currentLanguage={language}
          onPerformSingleAnalysis={performSingleAnalysis}
          onPerformBulkAnalysis={performBulkAnalysis}
          onAnalysisComplete={handleAnalysisCompleteInMatchingView}
          onViewReport={viewReport}
          activeMatchResultForDisplay={activeMatchResult}
          setActiveMatchResultForDisplay={setActiveMatchResult}
        />;
      case 'report_details':
        return activeMatchResult ? <ScoreReport result={activeMatchResult} appSettings={activeMatchResult.appSettingsSnapshot || appSettings} /> : null;
      case 'candidates_list':
        return <CandidatesListView 
          cvs={cvs} 
          onDeleteCv={deleteCv} 
          onViewCandidate={handleViewCandidateProfile}
          extractFileContent={extractFileContent}
          generateNameFromFileName={generateNameFromFileName}
          onSaveNewCandidate={handleAddCv}
        />;
      case 'candidate_profile':
        const candidateToEdit = cvs.find(cv => cv.id === editingCandidateId);
        return candidateToEdit ? <CandidateProfileView 
                                  candidate={candidateToEdit} 
                                  onSave={handleUpdateCvData} 
                                  onCancel={() => setCurrentView('candidates_list')}
                                  onDelete={deleteCv}
                                  extractFileContent={extractFileContent}
                                  allMatchResults={matchResults} 
                                  allJds={jds} 
                                  appSettings={appSettings} 
                                  onViewJobProfile={handleViewJobProfile}
                                  onViewReport={viewReport}
                                /> : <div className="text-center py-10 text-neutral-400">{t('candidateNotFound')} <button onClick={() => setCurrentView('candidates_list')} className="text-primary-light hover:underline">{t('returnToList')}</button></div>;
      case 'jobs_list':
        return <JobsListView 
          jds={jds} 
          onDeleteJd={deleteJd} 
          onViewJob={handleViewJobProfile}
          extractFileContent={extractFileContent}
          generateNameFromFileName={generateNameFromFileName}
          onSaveNewJob={handleAddJd}
        />;
      case 'job_profile':
        const jobToEdit = jds.find(jd => jd.id === editingJobId);
        return jobToEdit ? <JobProfileView 
                              job={jobToEdit} 
                              onSave={handleUpdateJdData} 
                              onCancel={() => setCurrentView('jobs_list')}
                              onDelete={deleteJd}
                              extractFileContent={extractFileContent}
                              allMatchResults={matchResults} 
                              allCvs={cvs} 
                              appSettings={appSettings} 
                              onViewCandidateProfile={handleViewCandidateProfile}
                              onViewReport={viewReport}
                            /> : <div className="text-center py-10 text-neutral-400">{t('jobNotFound')} <button onClick={() => setCurrentView('jobs_list')} className="text-primary-light hover:underline">{t('returnToList')}</button></div>;
      case 'settings':
        return <SettingsView 
          currentSettings={appSettings}
          onSaveSettings={handleUpdateAppSettings}
          onResetSettings={() => {
            setAppSettings(DEFAULT_APP_SETTINGS);
            setGlobalInfoMessage(t('settingsResetSuccess'));
            setShowSettingsSaveSuccessAnimation(true);
            setTimeout(() => {
              setShowSettingsSaveSuccessAnimation(false);
            }, 2000);
          }}
        />;
      case 'ai_assistant':
        return <AIAssistantView />;
      case 'agents_demo':
        return <AgentsDemoView />;
      default:
        return <div>View not found</div>;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-neutral-900">
      {showSettingsSaveSuccessAnimation && <SuccessCheckAnimation />}
      <Header />
      <Navbar currentView={currentView} setCurrentView={setCurrentView} />
      <main className="container mx-auto px-4 py-8 flex-grow">
        {globalError && 
            <ErrorAlert message={globalError} onClose={() => setGlobalError(null)} />
        }
        {globalInfoMessage && currentView !== 'settings' && 
            <div className="mb-4 p-3 bg-primary-DEFAULT/10 border-l-4 border-primary-DEFAULT text-primary-text rounded-md shadow-md-dark text-sm">
                {globalInfoMessage}
            </div>
        }
        {globalInfoMessage && currentView === 'settings' && !showSettingsSaveSuccessAnimation && (
            <div className="mb-4 p-3 bg-primary-DEFAULT/10 border-l-4 border-primary-DEFAULT text-primary-text rounded-md shadow-md-dark text-sm">
                {globalInfoMessage}
            </div>
         )}
        {renderView()}
      </main>
      <Footer />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <LocalizationProvider>
      <AppContent />
    </LocalizationProvider>
  );
};

export default App;
