
import React, { useState, useMemo } from 'react';
import { CVData, JobDescriptionData, MatchResult, AppSettings } from '../types';
import { useLocalization } from '../hooks/useLocalization';
import StatCard from '../components/StatCard';
import RecentAnalysisItem from '../components/RecentAnalysisItem';

interface DashboardViewProps {
  cvs: CVData[];
  jds: JobDescriptionData[];
  matchResults: MatchResult[];
  onViewReport: (reportId: string) => void;
  onDeleteCv: (id: string) => void;
  onDeleteJd: (id: string) => void;
  onDeleteMatchResult: (id: string) => void;
  onStartNewAnalysis: () => void;
}

type DimensionCountFilterValue = 'all' | '1-3' | '4-6' | '7-10';

const DashboardView: React.FC<DashboardViewProps> = ({ 
    cvs, 
    jds, 
    matchResults, 
    onViewReport, 
    onDeleteCv,
    onDeleteJd,
    onDeleteMatchResult,
    onStartNewAnalysis
}) => {
  const { t } = useLocalization();
  const [dimensionCountFilter, setDimensionCountFilter] = useState<DimensionCountFilterValue>('all');
  const [scoreThresholdFilter, setScoreThresholdFilter] = useState<number>(0);
  const [dateRangeFilter, setDateRangeFilter] = useState<{ startDate: string | null, endDate: string | null }>({ startDate: null, endDate: null });


  const getCvNameById = (id: string) => cvs.find(cv => cv.id === id)?.name;
  const getJdTitleById = (id: string) => jds.find(jd => jd.id === id)?.title;

  const filteredAndSortedMatchResults = useMemo(() => {
    let filteredResults = [...matchResults];

    // Dimension Count Filter
    if (dimensionCountFilter !== 'all') {
      filteredResults = filteredResults.filter(result => {
        if (!result.appSettingsSnapshot || !result.appSettingsSnapshot.assessmentDimensions) {
          return false; 
        }
        const activeDimensionsCount = result.appSettingsSnapshot.assessmentDimensions.filter(dim => dim.isActive).length;
        
        switch (dimensionCountFilter) {
          case '1-3':
            return activeDimensionsCount >= 1 && activeDimensionsCount <= 3;
          case '4-6':
            return activeDimensionsCount >= 4 && activeDimensionsCount <= 6;
          case '7-10':
            return activeDimensionsCount >= 7 && activeDimensionsCount <= 10;
          default:
            return true;
        }
      });
    }

    // Score Threshold Filter
    if (scoreThresholdFilter > 0) {
      filteredResults = filteredResults.filter(result => result.overallScore >= scoreThresholdFilter);
    }

    // Date Range Filter
    if (dateRangeFilter.startDate) {
      const start = new Date(dateRangeFilter.startDate);
      start.setHours(0, 0, 0, 0); // Compare from start of day
      filteredResults = filteredResults.filter(result => new Date(result.timestamp) >= start);
    }

    if (dateRangeFilter.endDate) {
      const end = new Date(dateRangeFilter.endDate);
      end.setHours(23, 59, 59, 999); // Compare to end of day
      filteredResults = filteredResults.filter(result => new Date(result.timestamp) <= end);
    }

    return filteredResults.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [matchResults, dimensionCountFilter, scoreThresholdFilter, dateRangeFilter]);


  const scrollbarClasses = "scrollbar-thin scrollbar-thumb-neutral-700 scrollbar-track-neutral-850/60 hover:scrollbar-thumb-neutral-600";

  const handleScoreThresholdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    setScoreThresholdFilter(isNaN(value) ? 0 : Math.max(0, Math.min(100, value)));
  };

  const handleDateChange = (field: 'startDate' | 'endDate', value: string) => {
    setDateRangeFilter(prev => ({ ...prev, [field]: value || null }));
  };
  
  const clearDateFilters = () => {
    setDateRangeFilter({ startDate: null, endDate: null });
  };

  const getNoResultsMessage = () => {
    if (dimensionCountFilter !== 'all' || scoreThresholdFilter > 0 || dateRangeFilter.startDate || dateRangeFilter.endDate) {
      return t('noAnalysesWithScoreDateFilter');
    }
    return t('noRecentAnalyses');
  };


  return (
    <div className="space-y-12"> {/* Increased spacing between sections */}
      <section id="overview_stats">
        <h2 className="text-3xl font-bold text-neutral-100 mb-2">{t('dashboardTitle')}</h2>
        <p className="text-md text-neutral-400 mb-8">{t('overview')}</p> {/* Increased bottom margin */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard 
            title={t('cvsManaged')} 
            value={cvs.length} 
            icon={
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8"> {/* Slightly smaller icon */}
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
              </svg>
            }
          />
          <StatCard 
            title={t('jdsManaged')} 
            value={jds.length} 
            icon={
               <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25H5.625a2.25 2.25 0 01-2.25-2.25V7.5c0-.621.504-1.125 1.125-1.125H7.5m3-4.5V5.25m0 0A2.25 2.25 0 0112.75 3h.006A2.25 2.25 0 0115 5.25m0 0V7.5m-7.5 6V9m6 3V9m0 0a2.25 2.25 0 00-2.25-2.25H9.75A2.25 2.25 0 007.5 9m0 0V6.75M7.5 6.75A2.25 2.25 0 005.25 4.5H4.5" />
              </svg>
            }
          />
          <StatCard 
            title={t('analysesPerformed')} 
            value={matchResults.length} 
            icon={
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" />
              </svg>
            }
          />
        </div>
      </section>

      <section id="recent_analyses_filters" className="bg-neutral-850 p-6 md:p-8 rounded-xl shadow-xl-dark border border-neutral-800">
        <div className="flex flex-col md:flex-row justify-between items-center mb-6 pb-4 border-b border-neutral-700 gap-4">
            <h2 className="text-2xl font-semibold text-neutral-100">{t('recentAnalyses')}</h2>
            <button
                onClick={onStartNewAnalysis}
                className="w-full md:w-auto px-5 py-2.5 bg-primary-DEFAULT text-white font-medium rounded-lg shadow-md hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-neutral-900 focus:ring-primary-light transition-colors duration-150 ease-in-out subtle-hover-lift flex items-center justify-center"
            >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5 mr-2">
                    <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
                </svg>
                {t('startNewAnalysis')}
            </button>
        </div>

        {/* Filters Section */}
        <div className="mb-6 p-4 bg-neutral-800 rounded-lg border border-neutral-700 shadow-md-dark">
            <h3 className="text-lg font-semibold text-neutral-200 mb-3">{t('filtersSectionTitle')}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-4 items-end">
                <div>
                    <label htmlFor="dimensionFilter" className="block text-sm font-medium text-neutral-300 mb-1">{t('filterByDimensionCountLabel')}</label>
                    <select 
                        id="dimensionFilter"
                        value={dimensionCountFilter}
                        onChange={(e) => setDimensionCountFilter(e.target.value as DimensionCountFilterValue)}
                        className="w-full px-3 py-2.5 bg-neutral-700 border border-neutral-600 text-neutral-200 rounded-lg shadow-sm focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT sm:text-sm transition-colors"
                    >
                        <option value="all">{t('filterOptionAllReports')}</option>
                        <option value="1-3">{t('filterOption1to3Dimensions')}</option>
                        <option value="4-6">{t('filterOption4to6Dimensions')}</option>
                        <option value="7-10">{t('filterOption7to10Dimensions')}</option>
                    </select>
                 </div>
                 <div>
                    <label htmlFor="scoreThresholdFilter" className="block text-sm font-medium text-neutral-300 mb-1">{t('filterByScoreThresholdLabel')}</label>
                    <input
                        type="number"
                        id="scoreThresholdFilter"
                        value={scoreThresholdFilter}
                        onChange={handleScoreThresholdChange}
                        min="0" max="100"
                        placeholder="0-100"
                        className="w-full px-3 py-2.5 bg-neutral-700 border border-neutral-600 text-neutral-200 rounded-lg shadow-sm focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT sm:text-sm transition-colors"
                    />
                 </div>
                 <div className="lg:col-span-1 grid grid-cols-2 gap-x-3 items-end">
                    <div>
                        <label htmlFor="startDateFilter" className="block text-sm font-medium text-neutral-300 mb-1">{t('filterStartDateLabel')}</label>
                        <input
                            type="date"
                            id="startDateFilter"
                            value={dateRangeFilter.startDate || ''}
                            onChange={(e) => handleDateChange('startDate', e.target.value)}
                            className="w-full px-3 py-2.5 bg-neutral-700 border border-neutral-600 text-neutral-200 rounded-lg shadow-sm focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT sm:text-sm transition-colors"
                        />
                    </div>
                     <div>
                        <label htmlFor="endDateFilter" className="block text-sm font-medium text-neutral-300 mb-1">{t('filterEndDateLabel')}</label>
                        <input
                            type="date"
                            id="endDateFilter"
                            value={dateRangeFilter.endDate || ''}
                            onChange={(e) => handleDateChange('endDate', e.target.value)}
                            min={dateRangeFilter.startDate || undefined}
                            className="w-full px-3 py-2.5 bg-neutral-700 border border-neutral-600 text-neutral-200 rounded-lg shadow-sm focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT sm:text-sm transition-colors"
                        />
                    </div>
                 </div>
                 {(dateRangeFilter.startDate || dateRangeFilter.endDate) && (
                    <div className="lg:col-start-3 flex justify-end mt-2 lg:mt-0">
                        <button onClick={clearDateFilters} className="px-3 py-1.5 text-xs bg-neutral-600 hover:bg-neutral-500 text-neutral-200 rounded-md transition-colors shadow-sm">
                            {t('clearDateFilterButton')}
                        </button>
                    </div>
                 )}
            </div>
        </div>

        {filteredAndSortedMatchResults.length === 0 ? (
          <div className="text-center py-12 bg-neutral-800 rounded-lg shadow-md-dark border border-neutral-700 mt-6">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.2} stroke="currentColor" className="w-16 h-16 mx-auto mb-4 text-neutral-600">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.182 16.318A4.486 4.486 0 0012.016 15a4.486 4.486 0 00-3.198 1.318M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.79-.44 1.06M9.75 9.75V8.25m0 1.5H8.25m2.25 0V8.25m0 1.5c0 .414.168.79.44 1.06M15 9.75c0 .414.168.79.44 1.06M15 9.75V8.25m0 1.5H13.5m2.25 0V8.25m0 1.5c0 .414-.168.79.44 1.06M12 6v2.25h.008l.004-.004h-.012z" />
            </svg>
            <p className="text-neutral-400 text-lg">
              {getNoResultsMessage()}
            </p>
          </div>
        ) : (
          <ul className="space-y-4 mt-6">
            {filteredAndSortedMatchResults.map(result => (
              <RecentAnalysisItem 
                key={result.id} 
                result={result} 
                onViewReport={onViewReport}
                onDeleteMatchResult={onDeleteMatchResult}
                cvName={getCvNameById(result.cvId)}
                jdTitle={getJdTitleById(result.jdId)}
              />
            ))}
          </ul>
        )}
      </section>
      
       <section id="manage_documents" className="mt-12 bg-neutral-850 p-6 md:p-8 rounded-xl shadow-xl-dark border border-neutral-800">
          <h2 className="text-xl font-semibold text-neutral-100 mb-6 pb-4 border-b border-neutral-700">Managed Documents</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-neutral-800 p-4 rounded-lg shadow-md-dark border border-neutral-700">
              <h3 className="text-lg font-medium text-neutral-200 mb-3">{t('cvsManaged')} ({cvs.length})</h3>
              {cvs.length === 0 ? <p className="text-sm text-neutral-500 italic">{t('noCVs')}</p> : (
                <ul className={`max-h-60 overflow-y-auto space-y-2 pr-1 ${scrollbarClasses}`}>
                  {cvs.map(cv => (
                    <li key={cv.id} className="flex justify-between items-center text-sm p-2.5 rounded-md bg-neutral-700/40 hover:bg-neutral-700/70 transition-colors">
                      <span className="truncate text-neutral-300" title={cv.name}>{cv.name}</span>
                      <button onClick={() => onDeleteCv(cv.id)} className="text-neutral-500 hover:text-danger-textDarkBg p-1 transition-colors" aria-label={`Delete CV ${cv.name}`}>
                         <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12.56 0c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                         </svg>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="bg-neutral-800 p-4 rounded-lg shadow-md-dark border border-neutral-700">
              <h3 className="text-lg font-medium text-neutral-200 mb-3">{t('jdsManaged')} ({jds.length})</h3>
              {jds.length === 0 ? <p className="text-sm text-neutral-500 italic">{t('noJDs')}</p> : (
                 <ul className={`max-h-60 overflow-y-auto space-y-2 pr-1 ${scrollbarClasses}`}>
                  {jds.map(jd => (
                    <li key={jd.id} className="flex justify-between items-center text-sm p-2.5 rounded-md bg-neutral-700/40 hover:bg-neutral-700/70 transition-colors">
                      <span className="truncate text-neutral-300" title={jd.title}>{jd.title}</span>
                       <button onClick={() => onDeleteJd(jd.id)} className="text-neutral-500 hover:text-danger-textDarkBg p-1 transition-colors" aria-label={`Delete JD ${jd.title}`}>
                         <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                           <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12.56 0c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                         </svg>
                       </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
      </section>
    </div>
  );
};

export default DashboardView;
