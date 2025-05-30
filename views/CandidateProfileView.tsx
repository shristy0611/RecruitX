import React, { useState, useEffect, ChangeEvent, useCallback } from 'react';
import { CVData, JobDescriptionData, MatchResult, AppSettings, CandidateStatus, StructuredCV, WorkExperienceEntry, EducationEntry, SkillEntry, ProjectEntry, PersonalInformation, Language } from '../types';
import { useLocalization } from '../hooks/useLocalization';
import ErrorAlert from '../components/ErrorAlert'; 
import RankedMatchCard from '../components/RankedMatchCard';
import { CANDIDATE_STATUS_OPTIONS } from '../constants';
import LoadingSpinner from '../components/LoadingSpinner';
import { getStructuredDocumentRepresentation } from '../services/geminiService';
import EditableField from '../components/EditableField';
import StructuredSection from '../components/StructuredSection';

interface CandidateProfileViewProps {
  candidate: CVData;
  onSave: (updatedCv: CVData) => void;
  onCancel: () => void;
  onDelete: (cvId: string, skipConfirm?: boolean) => void;
  extractFileContent: (file: File) => Promise<{content: string, mimeType: string, fileName: string}>;
  allMatchResults: MatchResult[];
  allJds: JobDescriptionData[];
  appSettings: AppSettings; 
  onViewJobProfile: (jobId: string) => void;
  onViewReport: (reportId: string) => void;
}

const CandidateProfileView: React.FC<CandidateProfileViewProps> = ({ 
    candidate, 
    onSave, 
    onCancel, 
    onDelete, 
    extractFileContent,
    allMatchResults,
    allJds,
    appSettings,
    onViewJobProfile,
    onViewReport
}) => {
  const { t, language } = useLocalization();
  
  const [cvName, setCvName] = useState(candidate.name); 
  const [content, setContent] = useState(candidate.content); 
  const [recruiterNotes, setRecruiterNotes] = useState(candidate.recruiterNotes || '');
  const [fileMimeType, setFileMimeType] = useState(candidate.fileMimeType); 
  const [currentFileName, setCurrentFileName] = useState(candidate.fileName || null); 
  const [status, setStatus] = useState<CandidateStatus | undefined>(candidate.status);
  
  const [isProcessingFile, setIsProcessingFile] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [structuredCv, setStructuredCv] = useState<StructuredCV | null>(null);
  const [isStructuringCv, setIsStructuringCv] = useState(candidate.isStructuring || false);
  const [structuringCvError, setStructuringCvError] = useState<string | null>(null);

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const fetchStructuredCvData = useCallback(async (currentDocContent: string, currentDocNameForContext: string, forceRefresh: boolean = false) => {
    if (!currentDocContent.trim()) {
      setStructuredCv(null);
      setStructuringCvError(null);
      setIsStructuringCv(false);
      return;
    }

    // Use already loaded data if language matches and no force refresh
    if (candidate.structuredData && candidate.structuredData.sourceLanguage === language && !forceRefresh) {
        setStructuredCv(candidate.structuredData);
        if (candidate.structuredData.personalInfo?.fullName && (cvName === candidate.fileName || !cvName )) {
             setCvName(candidate.structuredData.personalInfo.fullName);
        }
        setIsStructuringCv(false);
        return;
    }
    
    // If candidate.isStructuring is true, it means it's being processed globally.
    // We still might want to show isStructuringCv for the local refresh button.
    setIsStructuringCv(true);
    setStructuringCvError(null);
    try {
      const result = await getStructuredDocumentRepresentation(currentDocContent, 'cv', language, currentDocNameForContext);
      if (result) {
        setStructuredCv(result as StructuredCV);
        if ((result as StructuredCV).personalInfo?.fullName && (cvName === candidate.fileName || !cvName )) {
            setCvName((result as StructuredCV).personalInfo!.fullName!);
        }
      } else {
        setStructuredCv(null);
        setStructuringCvError(t('failedToGenerateStructuredViewMessage'));
      }
    } catch (error) {
      console.error("Error fetching structured CV:", error);
      setStructuredCv(null);
      setStructuringCvError(t('failedToGenerateStructuredViewMessage'));
    } finally {
      setIsStructuringCv(false);
    }
  }, [language, t, candidate.structuredData, candidate.fileName, cvName, candidate.isStructuring /* ensure local effect reacts to global change */]);

  useEffect(() => {
    setCvName(candidate.name);
    setContent(candidate.content);
    setRecruiterNotes(candidate.recruiterNotes || '');
    setFileMimeType(candidate.fileMimeType);
    setCurrentFileName(candidate.fileName || null);
    setStatus(candidate.status);
    setFormError(null);
    
    setIsStructuringCv(candidate.isStructuring || false); // Reflect global structuring status

    if (candidate.structuredData && candidate.structuredData.sourceLanguage === language) {
        setStructuredCv(candidate.structuredData);
         if (candidate.structuredData.personalInfo?.fullName && (candidate.name === candidate.fileName || !candidate.name )) {
             setCvName(candidate.structuredData.personalInfo.fullName);
        }
    } else if (!candidate.isStructuring) { // Only fetch if not already being structured globally
        fetchStructuredCvData(candidate.content, candidate.name);
    } else { // Is structuring globally, so clear local structuredCv until it's done
        setStructuredCv(null);
    }
  }, [candidate, language, fetchStructuredCvData]);

  const handleFileReplaceChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsProcessingFile(true);
    setFormError(null);
    try {
      const { content: newContent, mimeType: newMimeType, fileName: newFileName } = await extractFileContent(file);
      setContent(newContent); 
      setFileMimeType(newMimeType); 
      setCurrentFileName(newFileName); 
      // Trigger save to update raw content, then allow fetch on next load or manual refresh
      // Or, directly fetch here if desired, but it makes this function async and longer
       const updatedCvData: CVData = {
        ...candidate,
        name: cvName.trim() || generateNameFromFileName(newFileName), // Use existing or generate
        content: newContent,
        fileMimeType: newMimeType,
        fileName: newFileName,
        // recruiterNotes, status, structuredData potentially cleared or marked for re-structuring
        structuredData: undefined, // Clear structured data as content changed
        isStructuring: true, // Mark for global re-structuring
      };
      onSave(updatedCvData); // This will trigger a re-render and useEffect will handle fetching
      // fetchStructuredCvData(newContent, cvName, true); // Or fetch directly

    } catch (e: any) {
      setFormError(e.message || t('errorParsingFile'));
    } finally {
      setIsProcessingFile(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = ""; 
      }
    }
  };
   const generateNameFromFileName = (fileName: string): string => {
    if (!fileName) return '';
    const lastDotIndex = fileName.lastIndexOf('.');
    const nameWithoutExtension = lastDotIndex > 0 ? fileName.substring(0, lastDotIndex) : fileName;
    return nameWithoutExtension.replace(/[_.-]/g, ' ').replace(/\s+/g, ' ').trim();
  };


  const handleSaveChanges = () => {
    if (!cvName.trim()) {
      setFormError(t('candidateIdentifierEmpty'));
      return;
    }
    const updatedCvData: CVData = {
      ...candidate,
      name: cvName.trim(),
      content, 
      recruiterNotes: recruiterNotes.trim() || undefined,
      fileMimeType, 
      fileName: currentFileName || undefined, 
      status: status,
      structuredData: structuredCv ? {...structuredCv, sourceLanguage: language } : undefined,
      isStructuring: structuredCv ? false : candidate.isStructuring // if we have local structuredCv, it's no longer structuring it here
    };
    onSave(updatedCvData);
  };

  const updateStructuredField = <K extends keyof StructuredCV>(section: K, data: StructuredCV[K]) => {
    setStructuredCv(prev => ({ ...prev, [section]: data } as StructuredCV));
  };
  
  const updatePersonalInfoField = <PK extends keyof PersonalInformation>(field: PK, value: PersonalInformation[PK]) => {
    setStructuredCv(prev => ({
        ...prev,
        personalInfo: {
            ...(prev?.personalInfo || {}),
            [field]: value
        }
    } as StructuredCV));
  };

  const allMatchesForCandidate = allMatchResults.filter(mr => mr.cvId === candidate.id);
  const candidateJobMatches = allMatchesForCandidate
    .filter(mr => mr.overallScore >= appSettings.nexusRankingScoreThreshold)
    .sort((a, b) => b.overallScore - a.overallScore);

  const originalFileInfoText = currentFileName 
    ? t('originalFileInfoText').replace('{fileName}', currentFileName).replace('{fileMimeType}', fileMimeType || 'N/A')
    : t('pastedTextContent');
  
  const personalInfoFields: Array<{key: keyof PersonalInformation, labelKey: string, placeholderKey?: string}> = [
      { key: 'fullName', labelKey: 'cvFieldFullName', placeholderKey: 'cvFieldFullName' },
      { key: 'age', labelKey: 'cvFieldAge', placeholderKey: 'cvFieldAge' },
      { key: 'sexGender', labelKey: 'cvFieldSexGender', placeholderKey: 'cvFieldSexGender' },
      { key: 'phone', labelKey: 'cvFieldPhone', placeholderKey: 'cvFieldPhone' },
      { key: 'email', labelKey: 'cvFieldEmail', placeholderKey: 'cvFieldEmail' },
      { key: 'address', labelKey: 'cvFieldAddress', placeholderKey: 'cvFieldAddress' },
      { key: 'linkedin', labelKey: 'cvFieldLinkedIn', placeholderKey: 'cvFieldLinkedIn' },
      { key: 'portfolio', labelKey: 'cvFieldPortfolio', placeholderKey: 'cvFieldPortfolio' },
  ];

  const workExperienceFields: Array<{key: keyof WorkExperienceEntry, labelKey: string, placeholderKey?: string, multiline?: boolean, isList?: boolean}> = [
      { key: 'title', labelKey: 'cvFieldJobTitle', placeholderKey: 'cvFieldJobTitle' },
      { key: 'company', labelKey: 'cvFieldCompany', placeholderKey: 'cvFieldCompany' },
      { key: 'dates', labelKey: 'cvFieldDates', placeholderKey: 'cvFieldDates' },
      { key: 'description', labelKey: 'cvFieldDescription', placeholderKey: 'cvFieldDescription', multiline: true },
      { key: 'responsibilities', labelKey: 'cvFieldResponsibilities', placeholderKey: 'cvFieldResponsibilities', multiline: true, isList: true },
      { key: 'achievements', labelKey: 'cvFieldAchievements', placeholderKey: 'cvFieldAchievements', multiline: true, isList: true },
  ];
   const educationFields: Array<{key: keyof EducationEntry, labelKey: string, placeholderKey?: string, multiline?: boolean}> = [
      { key: 'degree', labelKey: 'cvFieldDegree', placeholderKey: 'cvFieldDegree' },
      { key: 'institution', labelKey: 'cvFieldInstitution', placeholderKey: 'cvFieldInstitution' },
      { key: 'graduationDate', labelKey: 'cvFieldGraduationDate', placeholderKey: 'cvFieldGraduationDate' },
      { key: 'details', labelKey: 'cvFieldEduDetails', placeholderKey: 'cvFieldEduDetails', multiline: true },
  ];
  const projectFields: Array<{key: keyof ProjectEntry, labelKey: string, placeholderKey?: string, multiline?: boolean, isList?: boolean}> = [
      { key: 'name', labelKey: 'cvFieldProjectName', placeholderKey: 'cvFieldProjectName' },
      { key: 'role', labelKey: 'cvFieldProjectRole', placeholderKey: 'cvFieldProjectRole' },
      { key: 'dates', labelKey: 'cvFieldProjectDates', placeholderKey: 'cvFieldProjectDates' },
      { key: 'description', labelKey: 'cvFieldProjectDescription', placeholderKey: 'cvFieldProjectDescription', multiline: true },
      { key: 'technologiesUsed', labelKey: 'cvFieldTechnologiesUsed', placeholderKey: 'cvFieldTechnologiesUsed', multiline: true, isList: true },
  ];
  const skillsFields: Array<{key: keyof SkillEntry, labelKey: string, placeholderKey?: string, multiline?: boolean, isList?: boolean}> = [
      { key: 'category', labelKey: 'cvFieldSkillCategory', placeholderKey: 'cvFieldSkillCategory' },
      { key: 'skills', labelKey: 'cvFieldSkillsList', placeholderKey: 'cvFieldSkillsList', multiline: true, isList: true },
  ];

  // Global structuring in progress (from list view) OR local structuring (refresh button)
  const showGlobalStructuringSpinner = candidate.isStructuring && !structuredCv; 
  const showLocalStructuringSpinner = isStructuringCv;


  return (
    <div className="space-y-10">
        <div className="bg-neutral-850 p-6 md:p-8 rounded-xl shadow-xl-dark border border-neutral-700">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 pb-4 border-b border-neutral-700 gap-3">
                <h2 className="text-2xl sm:text-3xl font-bold text-neutral-100">
                    {t('editCandidateProfileTitle')}
                </h2>
                <div className="flex items-center space-x-3">
                    <button 
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isProcessingFile || showGlobalStructuringSpinner || showLocalStructuringSpinner}
                        className="px-3 py-1.5 text-xs bg-primary-dark hover:bg-primary-DEFAULT text-primary-text rounded-md transition-colors shadow-sm disabled:opacity-50 flex items-center"
                    >
                         <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 mr-1.5">
                            <path fillRule="evenodd" d="M15.312 11.469l-4.531 4.531a1.125 1.125 0 01-1.591 0L4.657 11.47a.75.75 0 011.06-1.06l3.47 3.47V3.75a.75.75 0 011.5 0v10.129l3.47-3.469a.75.75 0 111.061 1.06z" clipRule="evenodd" />
                            <path d="M1.5 13.125a.75.75 0 01.75-.75h15a.75.75 0 010 1.5h-15a.75.75 0 01-.75-.75z" />
                        </svg>
                        {isProcessingFile ? t('processingFile') : t('replaceFileButton')}
                    </button>
                     <input 
                        type="file" 
                        ref={fileInputRef} 
                        onChange={handleFileReplaceChange} 
                        className="hidden"
                        accept=".txt,.pdf,.doc,.docx,.xls,.xlsx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" 
                    />
                    <p className="text-xs text-neutral-400">{originalFileInfoText}</p>
                </div>
            </div>


            {formError && <ErrorAlert message={formError} onClose={() => setFormError(null)} />}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6 mb-8">
                <EditableField
                    label={t('cvNameLabel')}
                    value={cvName}
                    onSave={setCvName}
                    placeholder={t('cvNamePlaceholder')}
                    inputClassName="w-full px-3.5 py-2.5 bg-neutral-700 border border-neutral-600 text-neutral-100 rounded-md shadow-sm focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT sm:text-lg font-semibold transition-colors"
                />
                <div>
                    <label htmlFor="candidate-status" className="block text-xs font-medium text-neutral-400 mb-1 uppercase tracking-wider">
                        {t('documentStatusLabel')}
                    </label>
                    <select
                        id="candidate-status"
                        value={status || ''}
                        onChange={(e) => setStatus(e.target.value as CandidateStatus)}
                        className="w-full px-3.5 py-2.5 bg-neutral-700 border border-neutral-600 text-neutral-100 rounded-md shadow-sm focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT sm:text-sm transition-colors"
                    >
                        <option value="" disabled>{t('statusAll')}</option>
                        {CANDIDATE_STATUS_OPTIONS.filter(opt => opt.value !== 'ALL').map(option => (
                            <option key={option.value} value={option.value}>{t(option.labelKey)}</option>
                        ))}
                    </select>
                </div>
            </div>
            
            <section className="mb-8 p-4 bg-neutral-800 rounded-lg border border-neutral-700 shadow-md-dark">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-semibold text-primary-light">{t('structuredOverviewTitle')}</h3>
                    <button
                        onClick={() => fetchStructuredCvData(content, cvName, true)}
                        disabled={showGlobalStructuringSpinner || showLocalStructuringSpinner || isProcessingFile}
                        className="px-4 py-2 text-xs bg-neutral-600 hover:bg-neutral-500 text-neutral-200 rounded-lg transition-colors shadow-sm disabled:opacity-50 disabled:cursor-wait flex items-center"
                    >
                       <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className={`w-4 h-4 mr-1.5 ${(showGlobalStructuringSpinner || showLocalStructuringSpinner) ? 'animate-spin' : ''}`}>
                         <path fillRule="evenodd" d="M15.312 11.469l-4.531 4.531a1.125 1.125 0 01-1.591 0L4.657 11.47a.75.75 0 011.06-1.06l3.47 3.47V3.75a.75.75 0 011.5 0v10.129l3.47-3.469a.75.75 0 111.061 1.06z" clipRule="evenodd" />
                       </svg>
                        {(showGlobalStructuringSpinner || showLocalStructuringSpinner) ? t('structuringDocumentMessage') : t('refreshStructuredViewButton')}
                    </button>
                </div>
                {(showGlobalStructuringSpinner || showLocalStructuringSpinner) && 
                  <div className="my-2 p-1.5 bg-primary-DEFAULT/10 text-primary-text text-xs rounded-md flex items-center animate-pulse">
                      <svg className="w-3 h-3 mr-1.5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      {t('isStructuringMessage')}
                  </div>
                }
                {structuringCvError && !showGlobalStructuringSpinner && !showLocalStructuringSpinner && <ErrorAlert message={structuringCvError} />}
                
                {!showGlobalStructuringSpinner && !showLocalStructuringSpinner && !structuringCvError && structuredCv && (
                    <div className="space-y-6">
                        <section>
                            <h4 className="text-lg font-semibold text-neutral-100 mb-3">{t('cvSectionPersonalInfo')}</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-0 p-4 bg-neutral-700 rounded-lg">
                                {personalInfoFields.map(field => (
                                    <EditableField
                                        key={field.key}
                                        label={t(field.labelKey)}
                                        value={structuredCv.personalInfo?.[field.key]}
                                        onSave={(newValue) => updatePersonalInfoField(field.key, newValue)}
                                        placeholder={t(field.placeholderKey || field.labelKey)}
                                    />
                                ))}
                            </div>
                        </section>

                        <EditableField
                            label={t('cvSectionSummary')}
                            value={structuredCv.summary}
                            onSave={(newValue) => updateStructuredField('summary', newValue)}
                            placeholder={t('cvSectionSummary')}
                            multiline
                            containerClassName="p-4 bg-neutral-700 rounded-lg"
                        />
                        
                        <StructuredSection
                            titleKey="cvSectionWorkExperience"
                            data={structuredCv.workExperience || []}
                            fieldsConfig={workExperienceFields}
                            onUpdate={(updated) => updateStructuredField('workExperience', updated)}
                            newEntryTemplate={{ title: '', company: '', dates: '', description: '', responsibilities: [], achievements: [] }}
                        />
                        <StructuredSection
                            titleKey="cvSectionEducation"
                            data={structuredCv.education || []}
                            fieldsConfig={educationFields}
                            onUpdate={(updated) => updateStructuredField('education', updated)}
                            newEntryTemplate={{ degree: '', institution: '', graduationDate: '', details: '' }}
                        />
                        <section className="mb-6">
                            <h4 className="text-lg font-semibold text-neutral-100 mb-3">{t('cvSectionSkills')}</h4>
                            {Array.isArray(structuredCv.skills) && structuredCv.skills.every(s => typeof s === 'string') ? (
                                <EditableField
                                    label={t('cvFieldSkillsList')}
                                    value={(structuredCv.skills as string[]).join('\n')}
                                    onSave={(newValue) => updateStructuredField('skills', newValue.split('\n').map(s => s.trim()).filter(s => s))}
                                    placeholder={t('cvFieldSkillsList')}
                                    multiline
                                    containerClassName="p-4 bg-neutral-700 rounded-lg"
                                />
                            ) : (
                                <StructuredSection
                                    // titleKey="cvSectionSkills" // Title already rendered by h4
                                    titleKey="" // Pass empty or omit if title is external
                                    data={(structuredCv.skills || []) as SkillEntry[]}
                                    fieldsConfig={skillsFields}
                                    onUpdate={(updated) => updateStructuredField('skills', updated)}
                                    newEntryTemplate={{ category: '', skills: [] }}
                                />
                            )}
                        </section>

                        <StructuredSection
                            titleKey="cvSectionProjects"
                            data={structuredCv.projects || []}
                            fieldsConfig={projectFields}
                            onUpdate={(updated) => updateStructuredField('projects', updated)}
                            newEntryTemplate={{ name: '', description: '', technologiesUsed: [], role: '', dates: '' }}
                        />
                        
                        <EditableField
                            label={t('cvSectionCertifications')}
                            value={(structuredCv.certifications || []).join('\n')}
                            onSave={(newValue) => updateStructuredField('certifications', newValue.split('\n').map(s => s.trim()).filter(s => s))}
                            placeholder={t('cvSectionCertifications')}
                            multiline
                            containerClassName="p-4 bg-neutral-700 rounded-lg"

                        />
                        <EditableField
                            label={t('cvSectionAwards')}
                            value={(structuredCv.awards || []).join('\n')}
                            onSave={(newValue) => updateStructuredField('awards', newValue.split('\n').map(s => s.trim()).filter(s => s))}
                            placeholder={t('cvSectionAwards')}
                            multiline
                            containerClassName="p-4 bg-neutral-700 rounded-lg"
                        />
                         <EditableField
                            label={t('cvSectionLanguages')}
                            value={(structuredCv.languages || []).join('\n')}
                            onSave={(newValue) => updateStructuredField('languages', newValue.split('\n').map(s => s.trim()).filter(s => s))}
                            placeholder={t('cvSectionLanguages')}
                            multiline
                            containerClassName="p-4 bg-neutral-700 rounded-lg"
                        />
                    </div>
                )}
                 {!showGlobalStructuringSpinner && !showLocalStructuringSpinner && !structuringCvError && !structuredCv && (
                    <p className="text-center text-neutral-400 py-8">{t('failedToGenerateStructuredViewMessage')} {t('refreshStructuredViewButton')}</p>
                )}
                <p className="text-xs text-neutral-500 mt-6 italic">{t('structuredViewDisclaimer')}</p>
            </section>

            <div className="md:col-span-2 mt-6">
                <EditableField
                    label={t('recruiterNotesLabel')}
                    value={recruiterNotes}
                    onSave={setRecruiterNotes}
                    placeholder={t('recruiterNotesPlaceholder')}
                    multiline
                    containerClassName="p-4 bg-neutral-800 rounded-lg border border-neutral-700 shadow-md-dark"
                    inputClassName="w-full px-3.5 py-2.5 bg-neutral-700 border border-neutral-600 text-neutral-100 rounded-md shadow-sm focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT sm:text-sm transition-colors min-h-[100px]"
                />
            </div>

            <div className="mt-10 pt-6 border-t border-neutral-700 flex flex-col sm:flex-row justify-end space-y-3 sm:space-y-0 sm:space-x-4">
                <button
                    onClick={() => onDelete(candidate.id)}
                    className="px-6 py-2.5 bg-danger-DEFAULT text-white font-medium rounded-lg shadow-md hover:bg-danger-border focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-neutral-850 focus:ring-danger-DEFAULT transition-colors subtle-hover-lift order-first sm:order-none mr-auto"
                >
                    {t('deleteButton')}
                </button>
                <button
                onClick={onCancel}
                className="px-6 py-2.5 bg-neutral-600 text-neutral-100 font-medium rounded-lg shadow-md hover:bg-neutral-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-neutral-850 focus:ring-neutral-400 transition-colors subtle-hover-lift"
                >
                {t('cancelButton')}
                </button>
                <button
                onClick={handleSaveChanges}
                disabled={isProcessingFile || showGlobalStructuringSpinner || showLocalStructuringSpinner}
                className="px-8 py-2.5 bg-primary-DEFAULT text-white font-semibold rounded-lg shadow-md hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-neutral-850 focus:ring-primary-light disabled:opacity-60 disabled:bg-neutral-600 transition-colors subtle-hover-lift"
                >
                {t('saveChangesButton')}
                </button>
            </div>
        </div>

        <section className="bg-neutral-850 p-6 md:p-8 rounded-xl shadow-xl-dark border border-neutral-700">
            <h3 className="text-xl font-semibold text-primary-light mb-6 border-b border-neutral-600 pb-3">
                {t('bestJobFitsTitle')} for <span className="text-accent-DEFAULT">{cvName}</span>
            </h3>
            {allMatchesForCandidate.length === 0 ? (
                <div className="text-center py-8">
                     <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 mx-auto mb-3 text-neutral-600">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9.53v.01M6.343 6.343l-.01.01M17.657 6.343l-.01.01M6.343 17.657l-.01-.01M12 12.53v.01M17.657 17.657l-.01-.01M12 21.53v.01M4.5 12.53h.01M9.128 16.45a4.517 4.517 0 006.744 0m-8.242-8.909a4.517 4.517 0 006.744 0M2.25 12c0 5.385 4.365 9.75 9.75 9.75s9.75 4.365 9.75 9.75S17.385 2.25 12 2.25 2.25 6.615 2.25 12z" />
                    </svg>
                    <p className="text-neutral-400">{t('noMatchesYet')}</p>
                    <p className="text-sm text-neutral-500 mt-1">{t('nexusScanPendingMessage')}</p>
                </div>
            ) : candidateJobMatches.length === 0 ? (
                 <div className="text-center py-8">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 mx-auto mb-3 text-neutral-500">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-neutral-400">{t('noMatchesAboveThresholdMessage').replace('{threshold}', appSettings.nexusRankingScoreThreshold.toString())}</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {candidateJobMatches.map(match => {
                        const jobData = allJds.find(jd => jd.id === match.jdId);
                        return (
                            <RankedMatchCard
                                key={match.id}
                                matchResult={match}
                                itemName={jobData?.title || 'Unknown Job'}
                                itemType="job"
                                onViewProfile={() => jobData && onViewJobProfile(jobData.id)}
                                onViewReport={() => onViewReport(match.id)}
                            />
                        );
                    })}
                </div>
            )}
        </section>
    </div>
  );
};

export default CandidateProfileView;
