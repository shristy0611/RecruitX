
import React from 'react';
import { MatchResult } from '../types';
import { useLocalization } from '../hooks/useLocalization';

interface RankedMatchCardProps {
  matchResult: MatchResult;
  itemName: string;
  itemType: 'candidate' | 'job';
  onViewProfile: () => void;
  onViewReport: (reportId: string) => void;
}

const RankedMatchCard: React.FC<RankedMatchCardProps> = ({ 
    matchResult, 
    itemName, 
    itemType, 
    onViewProfile, 
    onViewReport 
}) => {
  const { t } = useLocalization();
  const score = matchResult.overallScore;

  let scoreColorClass = 'text-danger-textDarkBg';
  let scoreBorderClass = 'border-danger-DEFAULT';
  let powerGlyphBgClass = 'bg-danger-DEFAULT';
  let powerGlyphPulseClass = '';

  if (score >= 90) {
    scoreColorClass = 'text-success-textDarkBg';
    scoreBorderClass = 'border-success-DEFAULT';
    powerGlyphBgClass = 'bg-success-DEFAULT';
    powerGlyphPulseClass = 'animate-pulse-strong'; // For very high scores
  } else if (score >= 80) {
    scoreColorClass = 'text-success-textDarkBg';
    scoreBorderClass = 'border-success-DEFAULT';
    powerGlyphBgClass = 'bg-success-DEFAULT';
  } else if (score >= 70) {
    scoreColorClass = 'text-primary-text'; // Using primary for good scores
    scoreBorderClass = 'border-primary-DEFAULT';
    powerGlyphBgClass = 'bg-primary-DEFAULT';
  } else if (score >= 60) {
    scoreColorClass = 'text-warning-textDarkBg';
    scoreBorderClass = 'border-warning-DEFAULT';
    powerGlyphBgClass = 'bg-warning-DEFAULT';
  }
  // Default is danger for scores below 60

  const PowerGlyph: React.FC<{ score: number, bgColorClass: string, pulseClass?: string }> = ({ score, bgColorClass, pulseClass }) => (
    <div className={`relative w-16 h-16 sm:w-20 sm:h-20 rounded-full flex items-center justify-center shadow-lg ${pulseClass || ''}`}>
      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 36 36">
        <path
          className="text-neutral-700"
          strokeWidth="3"
          stroke="currentColor"
          fill="none"
          d="M18 2.0845
             a 15.9155 15.9155 0 0 1 0 31.831
             a 15.9155 15.9155 0 0 1 0 -31.831"
        />
        <path
          className={`${bgColorClass.replace('bg-', 'text-')}`} // Use text color for stroke
          strokeWidth="3"
          strokeDasharray={`${score}, 100`}
          strokeLinecap="round"
          stroke="currentColor"
          fill="none"
          d="M18 2.0845
             a 15.9155 15.9155 0 0 1 0 31.831
             a 15.9155 15.9155 0 0 1 0 -31.831"
          style={{ transition: 'stroke-dasharray 0.5s ease-in-out' }}
        />
      </svg>
      <span className={`text-xl sm:text-2xl font-bold ${scoreColorClass}`}>{score}</span>
    </div>
  );

  return (
    <div className={`bg-neutral-800 p-4 sm:p-5 rounded-xl shadow-lg-dark border-l-4 ${scoreBorderClass} hover:shadow-xl-dark transition-all duration-200 ease-in-out subtle-hover-lift flex flex-col sm:flex-row items-center space-y-3 sm:space-y-0 sm:space-x-4`}>
      <div className="flex-shrink-0">
        <PowerGlyph score={score} bgColorClass={powerGlyphBgClass} pulseClass={powerGlyphPulseClass} />
      </div>
      <div className="flex-grow text-center sm:text-left min-w-0">
        <h4 className="text-md sm:text-lg font-semibold text-neutral-100 truncate" title={itemName}>
          {itemName}
        </h4>
        <p className="text-xs text-neutral-400">
          {t('analysisDate')}: {new Date(matchResult.timestamp).toLocaleDateString()}
        </p>
      </div>
      <div className="flex flex-col sm:flex-row items-center space-y-2 sm:space-y-0 sm:space-x-2 flex-shrink-0 pt-2 sm:pt-0">
        <button
          onClick={onViewProfile}
          className="w-full sm:w-auto px-3 py-1.5 text-xs bg-neutral-600 hover:bg-neutral-500 text-neutral-200 rounded-md transition-colors shadow-sm flex items-center justify-center"
          title={t('jumpToProfileButton')}
        >
         <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 mr-1.5">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-5.5-2.5a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zM10 12a5.99 5.99 0 00-4.793 2.39A6.483 6.483 0 0010 16.5a6.483 6.483 0 004.793-2.11A5.99 5.99 0 0010 12z" clipRule="evenodd" />
          </svg>
          {t('jumpToProfileButton')}
        </button>
        <button
          onClick={() => onViewReport(matchResult.id)}
          className="w-full sm:w-auto px-3 py-1.5 text-xs bg-primary-DEFAULT hover:bg-primary-dark text-white rounded-md transition-colors shadow-sm flex items-center justify-center"
          title={t('viewFullAnalysisButton')}
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 mr-1.5">
             <path d="M10 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z" />
             <path fillRule="evenodd" d="M.664 10.59a1.651 1.651 0 010-1.186A10.004 10.004 0 0110 3c4.257 0 7.893 2.66 9.336 6.41.147.381.146.804 0 1.186A10.004 10.004 0 0110 17c-4.257 0-7.893-2.66-9.336-6.41zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
          </svg>
          {t('viewFullAnalysisButton')}
        </button>
      </div>
    </div>
  );
};

export default RankedMatchCard;
