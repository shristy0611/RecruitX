import React, { useState, useEffect, ChangeEvent, useCallback } from 'react';
import { JobDescriptionData, CVData, MatchResult, AppSettings, JobStatus, StructuredJD, QualificationEntry, ResponsibilityEntry, Language } from '../types';
import { useLocalization } from '../hooks/useLocalization';
import ErrorAlert from '../components/ErrorAlert';
import RankedMatchCard from '../components/RankedMatchCard';
import { JOB_STATUS_OPTIONS } from '../constants';
import LoadingSpinner from '../components/LoadingSpinner';
import { getStructuredDocumentRepresentation } from '../services/geminiService';
import EditableField from '../components/EditableField';
import StructuredSection from '../components/StructuredSection';


interface JobProfileViewProps {
  job: JobDescriptionData;
  onSave: (updatedJd: JobDescriptionData) => void;
  onCancel: () => void;
  onDelete: (jdId: string, skipConfirm?: boolean) => void;
  extractFileContent: (file: File) => Promise<{content: string, mimeType: string, fileName: string}>;
  allMatchResults: MatchResult[];
  allCvs: CVData[];
  appSettings: AppSettings; 
  onViewCandidateProfile: (candidateId: string) => void;
  onViewReport: (reportId: string) => void;
}


const JobProfileView: React.FC<JobProfileViewProps> = ({ 
    job, 
    onSave, 
    onCancel, 
    onDelete, 
    extractFileContent,
    allMatchResults,
    allCvs,
    appSettings,
    onViewCandidateProfile,
    onViewReport
}) => {
  const { t, language } = useLocalization();

  const [jobTitle, setJobTitle] = useState(job.title); 
  const [content, setContent] = useState(job.content); 
  const [recruiterNotes, setRecruiterNotes] = useState(job.recruiterNotes || '');
  const [fileMimeType, setFileMimeType] = useState(job.fileMimeType); 
  const [currentFileName, setCurrentFileName] = useState(job.fileName || null); 
  const [status, setStatus] = useState<JobStatus | undefined>(job.status);
  
  const [isProcessingFile, setIsProcessingFile] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [structuredJd, setStructuredJd] = useState<StructuredJD | null>(null);
  const [isStructuringJd, setIsStructuringJd] = useState(job.isStructuring || false);
  const [structuringJdError, setStructuringJdError] = useState<string | null>(null);
  
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const fetchStructuredJdData = useCallback(async (currentDocContent: string, currentDocTitleForContext: string, forceRefresh: boolean = false) => {
    if (!currentDocContent.trim()) {
      setStructuredJd(null);
      setStructuringJdError(null);
      setIsStructuringJd(false);
      return;
    }
     if (job.structuredData && job.structuredData.sourceLanguage === language && !forceRefresh) {
        setStructuredJd(job.structuredData);
         if (job.structuredData.jobTitle && (jobTitle === job.fileName || !jobTitle)) {
             setJobTitle(job.structuredData.jobTitle);
        }
        setIsStructuringJd(false);
        return;
    }

    setIsStructuringJd(true);
    setStructuringJdError(null);
    try {
      const result = await getStructuredDocumentRepresentation(currentDocContent, 'jd', language, currentDocTitleForContext);
      if (result) {
        setStructuredJd(result as StructuredJD);
        if ((result as StructuredJD).jobTitle && (jobTitle === job.fileName || !jobTitle)) {
           setJobTitle((result as StructuredJD).jobTitle!);
        }
      } else {
        setStructuredJd(null);
        setStructuringJdError(t('failedToGenerateStructuredViewMessage'));
      }
    } catch (error) {
      console.error("Error fetching structured JD:", error);
      setStructuredJd(null);
      setStructuringJdError(t('failedToGenerateStructuredViewMessage'));
    } finally {
      setIsStructuringJd(false);
    }
  }, [language, t, job.structuredData, job.fileName, jobTitle, job.isStructuring]);

  useEffect(() => {
    setJobTitle(job.title);
    setContent(job.content);
    setRecruiterNotes(job.recruiterNotes || '');
    setFileMimeType(job.fileMimeType);
    setCurrentFileName(job.fileName || null);
    setStatus(job.status);
    setFormError(null);

    setIsStructuringJd(job.isStructuring || false);

    if (job.structuredData && job.structuredData.sourceLanguage === language) {
        setStructuredJd(job.structuredData);
        if (job.structuredData.jobTitle && (job.title === job.fileName || !job.title )) {
             setJobTitle(job.structuredData.jobTitle);
        }
    } else if (!job.isStructuring) {
        fetchStructuredJdData(job.content, job.title);
    } else {
        setStructuredJd(null);
    }
  }, [job, language, fetchStructuredJdData]);

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
      
      const updatedJdData: JobDescriptionData = {
        ...job,
        title: jobTitle.trim() || generateNameFromFileName(newFileName),
        content: newContent,
        fileMimeType: newMimeType,
        fileName: newFileName,
        structuredData: undefined, 
        isStructuring: true, 
      };
      onSave(updatedJdData);

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
    if (!jobTitle.trim()) {
      setFormError(t('jobTitleEmpty'));
      return;
    }
    const updatedJdData: JobDescriptionData = {
      ...job,
      title: jobTitle.trim(),
      content, 
      recruiterNotes: recruiterNotes.trim() || undefined,
      fileMimeType, 
      fileName: currentFileName || undefined, 
      status: status,
      structuredData: structuredJd ? {...structuredJd, sourceLanguage: language } : undefined,
      isStructuring: structuredJd ? false : job.isStructuring
    };
    onSave(updatedJdData);
  };

  const updateStructuredField = <K extends keyof StructuredJD>(section: K, data: StructuredJD[K]) => {
    setStructuredJd(prev => ({ ...prev, [section]: data } as StructuredJD));
  };
  
  const allMatchesForJob = allMatchResults.filter(mr => mr.jdId === job.id);
  const jobCandidateMatches = allMatchesForJob
    .filter(mr => mr.overallScore >= appSettings.nexusRankingScoreThreshold)
    .sort((a, b) => b.overallScore - a.overallScore);

  const originalFileInfoText = currentFileName 
    ? t('originalFileInfoText').replace('{fileName}', currentFileName).replace('{fileMimeType}', fileMimeType || 'N/A')
    : t('pastedTextContent');

  const jdResponsibilitiesFields: Array<{key: keyof ResponsibilityEntry, labelKey: string, placeholderKey?: string, multiline?: boolean, isList?: boolean}> = [
    { key: 'text', labelKey: 'jdSectionKeyResponsibilities', placeholderKey: 'jdSectionKeyResponsibilities', multiline: true },
  ];
  const jdQualificationsFields: Array<{key: keyof QualificationEntry, labelKey: string, placeholderKey?: string, multiline?: boolean, isList?: boolean}> = [
    { key: 'text', labelKey: 'jdSectionRequiredQualifications', placeholderKey: 'jdSectionRequiredQualifications', multiline: true },
  ];

  const showGlobalStructuringSpinner = job.isStructuring && !structuredJd; 
  const showLocalStructuringSpinner = isStructuringJd;

  return (
    <div className="space-y-10">
        <div className="bg-neutral-850 p-6 md:p-8 rounded-xl shadow-xl-dark border border-neutral-700">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 pb-4 border-b border-neutral-700 gap-3">
                <h2 className="text-2xl sm:text-3xl font-bold text-neutral-100">
                    {t('editJobProfileTitle')}
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
                    label={t('jdTitleLabel')}
                    value={jobTitle}
                    onSave={setJobTitle}
                    placeholder={t('jdTitlePlaceholder')}
                    inputClassName="w-full px-3.5 py-2.5 bg-neutral-700 border border-neutral-600 text-neutral-100 rounded-md shadow-sm focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT sm:text-lg font-semibold transition-colors"
                    data-testid={`job-profile-title-${job.id}`}
                />
                <div>
                    <label htmlFor="job-status" className="block text-xs font-medium text-neutral-400 mb-1 uppercase tracking-wider">
                        {t('documentStatusLabel')}
                    </label>
                    <select
                        id="job-status"
                        value={status || ''}
                        onChange={(e) => setStatus(e.target.value as JobStatus)}
                        className="w-full px-3.5 py-2.5 bg-neutral-700 border border-neutral-600 text-neutral-100 rounded-md shadow-sm focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT sm:text-sm transition-colors"
                    >
                        <option value="" disabled>{t('statusAll')}</option>
                        {JOB_STATUS_OPTIONS.filter(opt => opt.value !== 'ALL').map(option => (
                            <option key={option.value} value={option.value}>{t(option.labelKey)}</option>
                        ))}
                    </select>
                </div>
            </div>
            
            <section className="mb-8 p-4 bg-neutral-800 rounded-lg border border-neutral-700 shadow-md-dark">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-semibold text-primary-light">{t('structuredOverviewTitle')}</h3>
                    <button
                        onClick={() => fetchStructuredJdData(content, jobTitle, true)}
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
                {structuringJdError && !showGlobalStructuringSpinner && !showLocalStructuringSpinner && <ErrorAlert message={structuringJdError} />}
                
                {!showGlobalStructuringSpinner && !showLocalStructuringSpinner && !structuringJdError && structuredJd && (
                    <div className="space-y-6">
                         <EditableField label={t('jdFieldJobTitle')} value={structuredJd.jobTitle} onSave={(val) => updateStructuredField('jobTitle', val)} containerClassName="p-4 bg-neutral-700 rounded-lg"/>
                         <EditableField label={t('jdSectionCompanyOverview')} value={structuredJd.companyOverview} onSave={(val) => updateStructuredField('companyOverview', val)} multiline containerClassName="p-4 bg-neutral-700 rounded-lg"/>
                         <EditableField label={t('jdSectionRoleSummary')} value={structuredJd.roleSummary} onSave={(val) => updateStructuredField('roleSummary', val)} multiline containerClassName="p-4 bg-neutral-700 rounded-lg"/>
                         
                         <StructuredSection
                            titleKey="jdSectionKeyResponsibilities"
                            data={(structuredJd.keyResponsibilities || []).map(r => typeof r === 'string' ? {id: `resp-${Math.random().toString(36).substring(2,7)}`, text: r} : r) as ResponsibilityEntry[]}
                            fieldsConfig={jdResponsibilitiesFields}
                            onUpdate={(updated) => updateStructuredField('keyResponsibilities', updated.map(item => item.text))} // Storing as string[]
                            newEntryTemplate={{ text: '' }}
                        />
                        <StructuredSection
                            titleKey="jdSectionRequiredQualifications"
                            data={(structuredJd.requiredQualifications || []).map(q => typeof q === 'string' ? { id: `req-${Math.random().toString(36).substring(2,7)}`, text: q} : q) as QualificationEntry[]}
                            fieldsConfig={jdQualificationsFields.map(f => ({...f, labelKey: 'jdSectionRequiredQualifications'}))}
                            onUpdate={(updated) => updateStructuredField('requiredQualifications', updated.map(item => item.text))} // Storing as string[]
                            newEntryTemplate={{ text: '' }}
                        />
                         <StructuredSection
                            titleKey="jdSectionPreferredQualifications"
                            data={(structuredJd.preferredQualifications || []).map(q => typeof q === 'string' ? {id: `pref-${Math.random().toString(36).substring(2,7)}`, text: q} : q) as QualificationEntry[]}
                            fieldsConfig={jdQualificationsFields.map(f => ({...f, labelKey: 'jdSectionPreferredQualifications'}))}
                            onUpdate={(updated) => updateStructuredField('preferredQualifications', updated.map(item => item.text))} // Storing as string[]
                            newEntryTemplate={{ text: '' }}
                        />

                        <EditableField label={t('jdSectionTechnicalSkills')} value={(structuredJd.technicalSkillsRequired || []).join('\n')} onSave={(val) => updateStructuredField('technicalSkillsRequired', val.split('\n').filter(s=>s.trim()))} multiline containerClassName="p-4 bg-neutral-700 rounded-lg"/>
                        <EditableField label={t('jdSectionSoftSkills')} value={(structuredJd.softSkillsRequired || []).join('\n')} onSave={(val) => updateStructuredField('softSkillsRequired', val.split('\n').filter(s=>s.trim()))} multiline containerClassName="p-4 bg-neutral-700 rounded-lg"/>
                        <EditableField label={t('jdSectionBenefits')} value={Array.isArray(structuredJd.benefits) ? structuredJd.benefits.join('\n') : structuredJd.benefits} onSave={(val) => updateStructuredField('benefits', val.split('\n').filter(s=>s.trim()))} multiline containerClassName="p-4 bg-neutral-700 rounded-lg"/>
                        <EditableField label={t('jdSectionLocation')} value={structuredJd.location} onSave={(val) => updateStructuredField('location', val)} containerClassName="p-4 bg-neutral-700 rounded-lg"/>
                        <EditableField label={t('jdSectionSalary')} value={structuredJd.salaryRange} onSave={(val) => updateStructuredField('salaryRange', val)} containerClassName="p-4 bg-neutral-700 rounded-lg"/>
                    </div>
                )}
                {!showGlobalStructuringSpinner && !showLocalStructuringSpinner && !structuringJdError && !structuredJd && (
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
                    onClick={() => onDelete(job.id)}
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
                {t('topCandidateMatchesTitle')} for <span className="text-accent-DEFAULT">{jobTitle}</span>
            </h3>
            {allMatchesForJob.length === 0 ? (
                <div className="text-center py-8">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 mx-auto mb-3 text-neutral-600">
                         <path strokeLinecap="round" strokeLinejoin="round" d="M12 9.53v.01M6.343 6.343l-.01.01M17.657 6.343l-.01.01M6.343 17.657l-.01-.01M12 12.53v.01M17.657 17.657l-.01-.01M12 21.53v.01M4.5 12.53h.01M9.128 16.45a4.517 4.517 0 006.744 0m-8.242-8.909a4.517 4.517 0 006.744 0M2.25 12c0 5.385 4.365 9.75 9.75 9.75s9.75 4.365 9.75 9.75S17.385 2.25 12 2.25 2.25 6.615 2.25 12z" />
                    </svg>
                    <p className="text-neutral-400">{t('noMatchesYet')}</p>
                    <p className="text-sm text-neutral-500 mt-1">{t('nexusScanPendingMessage')}</p>
                </div>
            ) : jobCandidateMatches.length === 0 ? (
                <div className="text-center py-8">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 mx-auto mb-3 text-neutral-500">
                         <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-neutral-400">{t('noMatchesAboveThresholdMessage').replace('{threshold}', appSettings.nexusRankingScoreThreshold.toString())}</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {jobCandidateMatches.map(match => {
                        const cvData = allCvs.find(cv => cv.id === match.cvId);
                        return (
                            <RankedMatchCard
                                key={match.id}
                                matchResult={match}
                                itemName={cvData?.name || 'Unknown Candidate'}
                                itemType="candidate"
                                onViewProfile={() => cvData && onViewCandidateProfile(cvData.id)}
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

export default JobProfileView;
