
import React from 'react';
import { MatchResult, Language } from '../types';
import { useLocalization } from '../hooks/useLocalization';

interface RecentAnalysisItemProps {
  result: MatchResult;
  onViewReport: (reportId: string) => void;
  onDeleteMatchResult: (reportId: string) => void;
  cvName?: string;
  jdTitle?: string;
}

const RecentAnalysisItem: React.FC<RecentAnalysisItemProps> = ({ result, onViewReport, onDeleteMatchResult, cvName, jdTitle }) => {
  const { t, language } = useLocalization();

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(language === Language.JA ? 'ja-JP' : 'en-US', {
      year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  };

  let scoreBgClass = 'bg-danger-DEFAULT';
  let scoreBorderClass = 'border-danger-DEFAULT';
  let scoreTextClass = 'text-danger-text'; // Text color for the score itself

  if (result.overallScore >= 80) {
    scoreBgClass = 'bg-success-DEFAULT/20'; // More subtle background
    scoreBorderClass = 'border-success-DEFAULT';
    scoreTextClass = 'text-success-textDarkBg';
  } else if (result.overallScore >= 60) {
    scoreBgClass = 'bg-warning-DEFAULT/20'; // More subtle background
    scoreBorderClass = 'border-warning-DEFAULT';
    scoreTextClass = 'text-warning-textDarkBg';
  } else {
    scoreBgClass = 'bg-danger-DEFAULT/20'; // More subtle background
    scoreBorderClass = 'border-danger-DEFAULT';
    scoreTextClass = 'text-danger-textDarkBg';
  }


  return (
    <li className={`bg-neutral-850 p-4 sm:p-5 rounded-xl shadow-lg-dark hover:shadow-xl-dark transition-all duration-200 border border-neutral-800 border-l-4 ${scoreBorderClass} transform hover:scale-[1.01] hover:bg-neutral-800`}>
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between">
        <div className="flex-grow mb-3 sm:mb-0 mr-4 min-w-0">
          <h3 className="text-md sm:text-lg font-semibold text-primary-light truncate" title={result.candidateName || cvName}>
            {result.candidateName || cvName || 'N/A'}
          </h3>
          <p className="text-sm text-neutral-300 truncate mt-0.5" title={result.jobTitle || jdTitle}>
            {t('job')}: {result.jobTitle || jdTitle || 'N/A'}
          </p>
          <p className="text-xs text-neutral-500 mt-1.5">
            {t('analysisDate')}: {formatDate(result.timestamp)} ({result.reportLanguage.toUpperCase()})
          </p>
        </div>
        <div className="flex items-center space-x-2 sm:space-x-3 flex-shrink-0 w-full sm:w-auto justify-between sm:justify-end">
           <div className={`text-xl sm:text-2xl font-bold px-3.5 py-1.5 rounded-lg ${scoreBgClass} ${scoreTextClass} shadow-sm`}>
            {result.overallScore}<span className="text-sm opacity-70">/100</span>
          </div>
          <button
            onClick={() => onViewReport(result.id)}
            className="px-3 py-1.5 sm:px-4 sm:py-2 bg-primary-DEFAULT text-white text-xs sm:text-sm rounded-lg hover:bg-primary-dark transition-colors shadow-md subtle-hover-lift flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 mr-1.5 hidden sm:inline">
              <path d="M10 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z" />
              <path fillRule="evenodd" d="M.664 10.59a1.651 1.651 0 010-1.186A10.004 10.004 0 0110 3c4.257 0 7.893 2.66 9.336 6.41.147.381.146.804 0 1.186A10.004 10.004 0 0110 17c-4.257 0-7.893-2.66-9.336-6.41zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
            </svg>
            {t('viewReportButton')}
          </button>
          <button
            onClick={() => onDeleteMatchResult(result.id)}
            aria-label={t('deleteButton')}
            className="p-1.5 sm:p-2 bg-neutral-700 text-neutral-400 rounded-lg hover:bg-danger-DEFAULT/20 hover:text-danger-textDarkBg transition-colors shadow-sm"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 sm:w-5 sm:h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12.56 0c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
          </button>
        </div>
      </div>
    </li>
  );
};

export default RecentAnalysisItem;
