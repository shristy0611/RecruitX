import React, { useState, useMemo, useRef, ChangeEvent } from 'react';
import { CVData, CandidateStatus } from '../types';
import { useLocalization } from '../hooks/useLocalization';
import { CANDIDATE_STATUS_OPTIONS, PDF_MAX_SIZE_MB } from '../constants';
import SimpleDocumentForm from '../components/SimpleDocumentForm'; 

interface CandidatesListViewProps {
  cvs: CVData[];
  onViewCandidate: (id: string) => void;
  onDeleteCv: (id: string) => void;
  onSaveNewCandidate: (data: { name: string; content: string; fileMimeType?: string; fileName?: string; recruiterNotes?: string; }) => Promise<void>;
  extractFileContent: (file: File) => Promise<{content: string, mimeType: string, fileName: string}>;
  generateNameFromFileName: (fileName: string) => string;
}

const getStatusBadgeClass = (status?: CandidateStatus): string => {
  if (!status) return 'bg-neutral-500 text-neutral-100';
  switch (status) {
    case 'ACTIVE_SEEKER':
      return 'bg-success-DEFAULT text-white';
    case 'OPEN_TO_OFFERS':
      return 'bg-primary-DEFAULT text-white';
    case 'PASSIVELY_LOOKING':
      return 'bg-accent-light text-neutral-800'; 
    case 'IN_PROCESS_INTERNAL':
      return 'bg-accent-dark text-white'; 
    case 'NOT_LOOKING':
      return 'bg-neutral-600 text-neutral-200';
    case 'ARCHIVED':
      return 'bg-neutral-700 text-neutral-300 opacity-80';
    default:
      return 'bg-neutral-500 text-neutral-100';
  }
};

const CandidatesListView: React.FC<CandidatesListViewProps> = ({ 
    cvs, 
    onViewCandidate, 
    onDeleteCv, 
    onSaveNewCandidate,
    extractFileContent,
    generateNameFromFileName
}) => {
  const { t } = useLocalization();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<CandidateStatus | 'ALL'>('ALL');
  const [showAddForm, setShowAddForm] = useState(false);
  const [formMessage, setFormMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [bulkUploadMessage, setBulkUploadMessage] = useState<string | null>(null);
  const [isBulkProcessing, setIsBulkProcessing] = useState(false);

  const bulkFileCVCandidateInputRef = useRef<HTMLInputElement>(null);


  const filteredCvs = useMemo(() => {
    return cvs
      .filter(cv => {
        const termMatch = 
          cv.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (cv.fileName && cv.fileName.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (cv.recruiterNotes && cv.recruiterNotes.toLowerCase().includes(searchTerm.toLowerCase()));
        
        const statusMatch = statusFilter === 'ALL' || cv.status === statusFilter;
        
        return termMatch && statusMatch;
      })
      .sort((a,b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }, [cvs, searchTerm, statusFilter]);

  const scrollbarClasses = "scrollbar-thin scrollbar-thumb-neutral-600 scrollbar-track-neutral-700/60 hover:scrollbar-thumb-neutral-500";

  const handleSaveFromForm = async (data: { name: string; content: string; fileMimeType?: string; fileName?: string; recruiterNotes?: string; }) => {
    try {
      await onSaveNewCandidate({
        ...data,
        fileMimeType: data.fileMimeType || 'text/plain',
      });
      setFormMessage({type: 'success', text: t('documentAddedSuccess').replace('{docType}', t('cv')).replace('{name}', data.name) });
      setShowAddForm(false); 
      setTimeout(() => setFormMessage(null), 3000);
    } catch (error: any) {
      setFormMessage({type: 'error', text: error.message || t('genericSaveError') });
    }
  };

  const handleBulkFilesSelected = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) {
        setBulkUploadMessage(t('noFilesSelectedForBulkUpload'));
        setTimeout(() => setBulkUploadMessage(null), 3000);
        return;
    }

    setIsBulkProcessing(true);
    setBulkUploadMessage(`${t('filesProcessingLabel')} ${files.length} CV(s)...`);
    let successCount = 0;
    let errorCount = 0;
    const errorMessages: string[] = [];

    const newFilesArray = Array.from(files);

    for (const file of newFilesArray) {
        setBulkUploadMessage(`${t('fileStatusProcessing')} ${file.name}...`);
        try {
            const name = file.name.toLowerCase();
            const isTxt = name.endsWith('.txt');
            const isPdf = name.endsWith('.pdf');
            const isDocx = name.endsWith('.docx');
            const isDoc = name.endsWith('.doc');
            const isXlsx = name.endsWith('.xlsx');
            const isXls = name.endsWith('.xls');

            const extensionValid = isTxt || isPdf || isDocx || isDoc || isXlsx || isXls;
            
            if (!extensionValid && !['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'].includes(file.type)) {
                throw new Error(t('errorUnsupportedFileType'));
            }
            if (file.type === 'application/pdf' && file.size > PDF_MAX_SIZE_MB * 1024 * 1024) {
                throw new Error(t('errorFileSizeTooLarge'));
            }

            const { content: fileContent, mimeType, fileName: extractedFileName } = await extractFileContent(file);
            const candidateName = generateNameFromFileName(extractedFileName);
            
            await onSaveNewCandidate({
                name: candidateName,
                content: fileContent,
                fileMimeType: mimeType,
                fileName: extractedFileName,
                recruiterNotes: '', // Batch recruiter notes could be added via a separate input if needed
            });
            successCount++;
        } catch (error: any) {
            console.error(`Error processing file ${file.name} in bulk:`, error);
            errorCount++;
            errorMessages.push(`${file.name}: ${error.message}`);
        }
    }

    let summaryMessage = t('bulkUploadSummary')
        .replace('{successCount}', successCount.toString())
        .replace('{errorCount}', errorCount.toString());
    if (errorCount > 0) {
        summaryMessage += ` ${t('errorTitle')}: ${errorMessages.slice(0,2).join(', ')}${errorMessages.length > 2 ? '...' : ''}`;
    }
    setBulkUploadMessage(summaryMessage);
    setIsBulkProcessing(false);
    
    if (bulkFileCVCandidateInputRef.current) {
        bulkFileCVCandidateInputRef.current.value = ""; // Reset file input
    }

    setTimeout(() => setBulkUploadMessage(null), errorCount > 0 ? 7000 : 4000);
  };


  return (
    <div className="bg-neutral-850 p-6 md:p-8 rounded-xl shadow-xl-dark border border-neutral-700">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-6 pb-4 border-b border-neutral-700 gap-4">
        <h2 className="text-2xl sm:text-3xl font-bold text-neutral-100 whitespace-nowrap">
          {t('allCandidatesTitle')} ({cvs.length})
        </h2>
        <div className="flex flex-row flex-wrap items-center justify-end gap-3 w-full sm:w-auto">
          <div className="w-full sm:w-auto">
            <input 
              type="text"
              placeholder={`${t('searchButton') || 'Search'} ${t('candidatesNav').toLowerCase()}...`}
              className="px-4 py-2.5 bg-neutral-700 border border-neutral-600 text-neutral-100 rounded-lg shadow-sm focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT sm:text-sm transition-all duration-150 w-full"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              aria-label={`${t('searchButton')} ${t('candidatesNav').toLowerCase()}`}
            />
          </div>
          <div className="w-full sm:w-auto">
            <select
              id="candidateStatusFilter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as CandidateStatus | 'ALL')}
              className="w-full px-3 py-2.5 bg-neutral-700 border border-neutral-600 text-neutral-200 rounded-lg shadow-sm focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT sm:text-sm transition-colors"
              aria-label={t('filterByStatusLabel')}
            >
              {CANDIDATE_STATUS_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>{t(option.labelKey)}</option>
              ))}
            </select>
          </div>
          <div className="w-full sm:w-auto">
             <button
              onClick={() => { setShowAddForm(!showAddForm); setFormMessage(null); }}
              className="w-full px-3 py-2 bg-primary-dark text-white font-medium rounded-lg shadow-md hover:bg-primary-DEFAULT focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-neutral-850 focus:ring-primary-light transition-colors duration-150 ease-in-out subtle-hover-lift flex items-center justify-center text-xs sm:text-sm"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5 mr-1.5">
                  <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
              </svg>
              {showAddForm ? t('cancelButton') : t('addCandidateButton')}
            </button>
          </div>
          <input 
            type="file" 
            multiple 
            ref={bulkFileCVCandidateInputRef} 
            onChange={handleBulkFilesSelected} 
            className="hidden"
            accept=".txt,.pdf,.doc,.docx,.xls,.xlsx,text/plain,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            aria-labelledby="bulk-cv-upload-button"
          />
          <div className="w-full sm:w-auto">
            <button
              id="bulk-cv-upload-button"
              onClick={() => bulkFileCVCandidateInputRef.current?.click()}
              disabled={isBulkProcessing}
              className="w-full px-4 py-2.5 bg-accent-DEFAULT text-neutral-900 font-semibold rounded-lg shadow-lg hover:bg-accent-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-neutral-850 focus:ring-accent-light transition-all duration-200 ease-in-out transform hover:scale-105 subtle-hover-lift flex items-center justify-center text-sm disabled:opacity-70 disabled:cursor-not-allowed"
              aria-busy={isBulkProcessing}
            >
               <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 mr-2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 8.25H7.5a2.25 2.25 0 00-2.25 2.25v9a2.25 2.25 0 002.25 2.25h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25H15m0-3l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              {isBulkProcessing ? (t('filesProcessingLabel') + '...') : t('bulkUploadCvsButton')}
            </button>
          </div>
        </div>
      </div>

      {showAddForm && (
        <SimpleDocumentForm 
          docType="cv"
          onAddDocument={handleSaveFromForm}
          onCancel={() => { setShowAddForm(false); setFormMessage(null); }}
          extractFileContent={extractFileContent}
        />
      )}

      {formMessage && (
        <div className={`my-4 p-3 text-sm rounded-md ${formMessage.type === 'success' ? 'bg-success-DEFAULT/10 text-success-text border-success-DEFAULT' : 'bg-danger-DEFAULT/10 text-danger-text border-danger-DEFAULT'} border-l-4`} role={formMessage.type === 'error' ? 'alert' : 'status'}>
            {formMessage.text}
        </div>
      )}
      {bulkUploadMessage && (
        <div className={`my-4 p-3 text-sm rounded-md ${bulkUploadMessage.includes(t('errorTitle')) || bulkUploadMessage.includes(t('noFilesSelectedForBulkUpload')) ? 'bg-danger-DEFAULT/10 text-danger-text border-danger-DEFAULT' : 'bg-primary-DEFAULT/10 text-primary-text border-primary-DEFAULT'} border-l-4`} role={bulkUploadMessage.includes(t('errorTitle')) ? 'alert' : 'status'}>
            {bulkUploadMessage}
        </div>
      )}


      {filteredCvs.length === 0 && !showAddForm ? (
        <div className="text-center py-12 bg-neutral-800 rounded-lg shadow-md-dark border border-neutral-700">
           <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.2} stroke="currentColor" className="w-16 h-16 mx-auto mb-4 text-neutral-600">
             <path strokeLinecap="round" strokeLinejoin="round" d="M15.182 16.318A4.486 4.486 0 0012.016 15a4.486 4.486 0 00-3.198 1.318M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.79-.44 1.06M9.75 9.75V8.25m0 1.5H8.25m2.25 0V8.25m0 1.5c0 .414.168.79.44 1.06M15 9.75c0 .414.168.79.44 1.06M15 9.75V8.25m0 1.5H13.5m2.25 0V8.25m0 1.5c0 .414-.168.79.44 1.06M12 6v2.25h.008l.004-.004h-.012z" />
           </svg>
          <p className="text-neutral-400 text-lg">
            {searchTerm || statusFilter !== 'ALL' ? t('noCandidatesWithStatusFilter') : t('noCandidatesManaged')}
          </p>
        </div>
      ) : (
        <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${filteredCvs.length > 6 ? scrollbarClasses : ''} max-h-[70vh] overflow-y-auto p-1`}>
          {filteredCvs.map(cv => (
            <div key={cv.id} className="bg-neutral-800 p-5 rounded-xl shadow-lg-dark border border-neutral-700 hover:border-primary-dark transition-all duration-200 flex flex-col justify-between subtle-hover-lift" data-testid="candidate-card">
              <div>
                <div className="flex justify-between items-start mb-1">
                  <h3 className="text-lg font-semibold text-primary-light truncate mr-2" title={cv.name} data-testid="candidate-name">{cv.name}</h3>
                  {cv.status && (
                    <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full whitespace-nowrap ${getStatusBadgeClass(cv.status)}`}>
                      {t(CANDIDATE_STATUS_OPTIONS.find(opt => opt.value === cv.status)?.labelKey || '')}
                    </span>
                  )}
                </div>
                {cv.fileName && <p className="text-xs text-neutral-500 mb-1 truncate" title={cv.fileName}>{t('fileNameLabel')} {cv.fileName}</p>}
                <p className="text-xs text-neutral-400 mb-3">{t('analysisDate')}: {new Date(cv.createdAt).toLocaleDateString()}</p> {/* Using analysisDate as generic "Added" */}
                {cv.recruiterNotes && (
                  <p className="text-sm text-neutral-300 italic line-clamp-2 mb-3" title={cv.recruiterNotes}>
                    {t('recruiterNotesLabel')}: {cv.recruiterNotes}
                  </p>
                )}
                {cv.isStructuring && (
                    <div className="my-2 p-1.5 bg-sky-500/10 text-sky-400 text-xs rounded-md flex items-center animate-pulse">
                        <svg className="w-3 h-3 mr-1.5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        {t('isStructuringMessage')}
                    </div>
                )}
              </div>
              <div className="mt-auto pt-4 flex items-center justify-end space-x-2 border-t border-neutral-700/50">
                <button
                  onClick={() => onViewCandidate(cv.id)}
                  className="px-3.5 py-2 text-xs bg-primary-DEFAULT text-white rounded-md hover:bg-primary-dark transition-colors shadow-sm flex items-center"
                  title={t('viewEditProfileButton')}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 mr-1.5">
                    <path d="M10 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z" />
                    <path fillRule="evenodd" d="M.664 10.59a1.651 1.651 0 010-1.186A10.004 10.004 0 0110 3c4.257 0 7.893 2.66 9.336 6.41.147.381.146.804 0 1.186A10.004 10.004 0 0110 17c-4.257 0-7.893-2.66-9.336-6.41zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                  </svg>
                  {t('viewEditProfileButton')}
                </button>
                <button
                  onClick={() => onDeleteCv(cv.id)}
                  className="p-2 bg-neutral-700 text-danger-textDarkBg rounded-md hover:bg-danger-DEFAULT/30 hover:text-danger-text transition-colors shadow-sm"
                  aria-label={`${t('deleteButton')} ${cv.name}`}
                  title={`${t('deleteButton')} ${cv.name}`}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12.56 0c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CandidatesListView;
