
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { MatchResult, ScoreComponent, Language, AppSettings } from '../types';
import { useLocalization } from '../hooks/useLocalization';

interface ScoreReportProps {
  result: MatchResult;
  appSettings: AppSettings; // To get dimension labels
}

const ScoreCard: React.FC<{ title: string; score: number; explanation: string; details?: React.ReactNode }> = ({ title, score, explanation, details }) => {
  
  let scoreColorClass = 'text-danger-textDarkBg';
  let scoreBorderClass = 'border-danger-DEFAULT'; 
  if (score >= 80) {
    scoreColorClass = 'text-success-textDarkBg';
    scoreBorderClass = 'border-success-DEFAULT'; 
  } else if (score >= 60) {
    scoreColorClass = 'text-warning-textDarkBg';
    scoreBorderClass = 'border-warning-DEFAULT'; 
  }

  return (
    <div className={`p-6 bg-neutral-800 rounded-xl shadow-lg-dark hover:shadow-xl-dark transition-shadow duration-300 border-t-4 ${scoreBorderClass} subtle-hover-lift`}>
      <h4 className="text-xl font-semibold text-neutral-100 mb-2">{title}</h4>
      <p className={`text-4xl font-bold mb-3 ${scoreColorClass}`}>{score}<span className="text-2xl text-neutral-400">/100</span></p>
      <p className="text-sm text-neutral-300 mb-3 whitespace-pre-line leading-relaxed">{explanation}</p>
      {details && <div className="text-xs text-neutral-400 mt-3 pt-3 border-t border-neutral-700">{details}</div>}
    </div>
  );
};

const IntelligenceSection: React.FC<{ title: string; points: string[] | undefined; icon: React.ReactNode; colorClass: string }> = ({ title, points, icon, colorClass }) => {
  if (!points || points.length === 0) {
    return null;
  }
  return (
    <div className={`mt-8 bg-neutral-800 p-6 md:p-8 rounded-xl shadow-xl-dark border border-neutral-700 border-l-4 ${colorClass}`}>
      <h3 className={`text-xl sm:text-2xl font-semibold text-neutral-100 mb-5 flex items-center ${colorClass.replace('border-', 'text-')}`}>
        {icon}
        {title}
      </h3>
      <ul className="list-none space-y-2 pl-1">
        {points.map((point, index) => (
          <li key={index} className="flex items-start text-neutral-300">
            <span className={`mr-2 mt-1 flex-shrink-0 w-1.5 h-1.5 rounded-full ${colorClass.replace('border-', 'bg-')}`}></span>
            <span className="whitespace-pre-line leading-relaxed">{point}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

const MethodologyPoint: React.FC<{title: string, detail: string, icon: React.ReactNode}> = ({title, detail, icon}) => (
    <div className="flex items-start space-x-4 p-4 bg-neutral-700/50 rounded-lg">
        <div className="flex-shrink-0 text-primary-light mt-1">
            {icon}
        </div>
        <div>
            <h4 className="text-md font-semibold text-neutral-100 mb-1">{title}</h4>
            <p className="text-sm text-neutral-300 leading-relaxed">{detail}</p>
        </div>
    </div>
);


const ScoreReport: React.FC<ScoreReportProps> = ({ result, appSettings }) => {
  const { t, language: currentAppLanguage } = useLocalization();

  const getDimensionLabel = (dimensionId: string): string => {
    const dimension = (result.appSettingsSnapshot || appSettings).assessmentDimensions.find(d => d.id === dimensionId);
    return dimension ? dimension.label : dimensionId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()); // Fallback to formatted ID
  };
  
  const chartData = Object.entries(result.scores).map(([id, scoreComp]) => ({
    name: getDimensionLabel(id),
    score: scoreComp.score,
    fillKey: id, 
  })).sort((a,b) => { 
    const orderA = (result.appSettingsSnapshot || appSettings).assessmentDimensions.findIndex(d => d.id === a.fillKey);
    const orderB = (result.appSettingsSnapshot || appSettings).assessmentDimensions.findIndex(d => d.id === b.fillKey);
    if (orderA !== -1 && orderB !== -1) return orderA - orderB;
    return a.name.localeCompare(b.name);
  });
  
  const getScoreCategoryFill = (score: number) => {
    if (score >= 80) return 'url(#colorSuccess)';
    if (score >= 60) return 'url(#colorWarning)';
    return 'url(#colorDanger)';
  };


  const renderScoreComponentDetails = (scoreComp: ScoreComponent) => {
    if (!scoreComp.details) return null;
    if (Array.isArray(scoreComp.details)) {
      return (
        <ul className="list-disc list-inside space-y-1 pl-1">
          {scoreComp.details.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      );
    }
    if (typeof scoreComp.details === 'object' && scoreComp.details !== null) {
      const detailsObj = scoreComp.details as any; 
      if (detailsObj.matchedSkills || detailsObj.missingSkills) {
         return (
           <div className="space-y-2">
             {detailsObj.matchedSkills && Array.isArray(detailsObj.matchedSkills) && detailsObj.matchedSkills.length > 0 && (
               <div>
                 <strong className="text-neutral-200">Matched:</strong>
                 <ul className="list-disc list-inside space-y-1 pl-1 text-xs">
                   {detailsObj.matchedSkills.map((item:string, index:number) => <li key={`match-${index}`}>{item}</li>)}
                 </ul>
               </div>
             )}
             {detailsObj.missingSkills && Array.isArray(detailsObj.missingSkills) && detailsObj.missingSkills.length > 0 && (
               <div>
                 <strong className="text-neutral-200">Missing/Not Evident:</strong>
                 <ul className="list-disc list-inside space-y-1 pl-1 text-xs">
                   {detailsObj.missingSkills.map((item:string, index:number) => <li key={`miss-${index}`}>{item}</li>)}
                 </ul>
               </div>
             )}
           </div>
         );
      }
      return (
        <ul className="space-y-1">
          {Object.entries(scoreComp.details).map(([key, value]) => (
            <li key={key}><strong className="capitalize text-neutral-200">{key.replace(/([A-Z])/g, ' $1').trim()}:</strong> {String(value)}</li>
          ))}
        </ul>
      );
    }
    return <p>{String(scoreComp.details)}</p>;
  };

  const reportLanguageName = result.reportLanguage === Language.EN ? 'English' : '日本語';
  const currentAppLanguageName = currentAppLanguage === Language.EN ? 'English' : '日本語';
  const showLanguageMismatchWarning = result.reportLanguage !== currentAppLanguage;

  return (
    <div className="mt-2 p-6 md:p-8 bg-neutral-850 rounded-xl shadow-2xl-dark border border-neutral-700">
      <header className="text-center mb-8 pb-6 border-b border-neutral-700">
        <h2 className="text-3xl sm:text-4xl font-bold text-neutral-100 mb-2">
          {t('reportTitle')}
        </h2>
        <p className="text-md text-neutral-300">
          {t('matchDetailsFor')} <strong className="text-primary-light">{result.candidateName}</strong> {result.cvFileName ? `(${result.cvFileName})` : ''}
        </p>
        <p className="text-md text-neutral-300">
          {t('and')} <strong className="text-primary-light">{result.jobTitle}</strong> {result.jdFileName ? `(${result.jdFileName})` : ''}
        </p>
      </header>

      {showLanguageMismatchWarning && (
        <div className="mb-8 p-4 bg-primary-DEFAULT/10 border-l-4 border-primary-DEFAULT text-primary-text rounded-md shadow-md-dark">
          <p className="font-semibold text-sm mb-1 text-neutral-100">Language Information:</p>
          <p className="text-sm mb-1">
            {t('reportGeneratedInLabel')?.replace('{lang}', reportLanguageName)}
          </p>
          <p className="text-sm mb-1">
            {t('appLanguageIsLabel')?.replace('{lang}', currentAppLanguageName)}
          </p>
          <p className="text-sm mt-2">
            {t('considerReanalyzingPrompt')?.replace('{lang}', currentAppLanguageName)}
          </p>
        </div>
      )}

      {(result.cvRecruiterNotes || result.jdRecruiterNotes) && (
        <div className="mb-10 p-6 bg-neutral-800 border border-neutral-700 rounded-lg shadow-md-dark">
          <h4 className="text-lg font-semibold text-accent-text mb-3 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5 mr-2 text-accent-DEFAULT">
              <path fillRule="evenodd" d="M10 2c-1.716 0-3.408.106-5.07.31C3.806 2.45 3.25 3.472 3.25 4.504v.093c0 .832.448 1.554 1.108 2.017l.21.14a10.032 10.032 0 004.358 1.412c.836.203 1.69.304 2.55.304.86 0 1.714-.101 2.55-.304a10.032 10.032 0 004.358-1.412l.21-.14c.66-.463 1.108-1.185 1.108-2.017v-.093c0-1.032-.556-2.054-1.68-2.194A19.095 19.095 0 0010 2zm-5.507 8.545A9.027 9.027 0 0010 11c1.54 0 2.983-.388 4.255-.98a.75.75 0 01.582 1.341A10.477 10.477 0 0110 12.5c-1.802 0-3.505-.49-4.978-1.346a.75.75 0 01.53-1.364l.002-.001.002-.001.002-.001zM2 14.25a.75.75 0 01.75-.75h14.5a.75.75 0 010 1.5H2.75a.75.75 0 01-.75-.75z" clipRule="evenodd" />
            </svg>
            {t('recruiterNotesLabel')}
          </h4>
          {result.cvRecruiterNotes && (
            <div className="mb-3">
              <p className="text-sm font-medium text-neutral-300">{t('cvRecruiterNotes')}:</p>
              <p className="text-sm text-neutral-300 whitespace-pre-line italic bg-neutral-700/50 p-3 rounded-md border border-neutral-600">{result.cvRecruiterNotes}</p>
            </div>
          )}
          {result.jdRecruiterNotes && (
             <div>
              <p className="text-sm font-medium text-neutral-300">{t('jdRecruiterNotes')}:</p>
              <p className="text-sm text-neutral-300 whitespace-pre-line italic bg-neutral-700/50 p-3 rounded-md border border-neutral-600">{result.jdRecruiterNotes}</p>
            </div>
          )}
        </div>
      )}

      <div className="text-center mb-10 p-8 bg-neutral-800 text-neutral-100 rounded-xl shadow-xl-dark border border-neutral-700">
        <h3 className="text-2xl font-medium text-neutral-300 mb-2 tracking-wide">{t('overallMatchScore')}</h3>
        <p className={`text-7xl font-extrabold ${result.overallScore >= 80 ? 'text-accent-DEFAULT' : 'text-primary-light'}`}>{result.overallScore} <span className="text-4xl font-light text-neutral-400 opacity-80">/100</span></p>
      </div>

      <section id="aiMethodology" className="my-12 p-6 md:p-8 bg-neutral-800 rounded-xl shadow-xl-dark border border-neutral-700">
        <h3 className="text-2xl sm:text-3xl font-semibold text-neutral-100 mb-6 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-7 h-7 mr-3 text-primary-light opacity-90">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068M15.75 21H8.25A2.25 2.25 0 016 18.75V5.25A2.25 2.25 0 018.25 3h7.5A2.25 2.25 0 0118 5.25v8.25A2.25 2.25 0 0115.75 21v0z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 12c0-5.02-4.03-9-9-9s-9 3.98-9 9 4.03 9 9 9c.352 0 .696-.023 1.033-.065" />
            </svg>
            {t('aiMethodologySectionTitle')}
        </h3>
        <p className="text-neutral-300 mb-6 leading-relaxed">{t('aiMethodologyIntro')}</p>
        <div className="space-y-5">
            <MethodologyPoint 
                title={t('aiMethodologyPointEvidenceTitle')}
                detail={t('aiMethodologyPointEvidenceDetail')}
                icon={<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>}
            />
            <MethodologyPoint 
                title={t('aiMethodologyPointNotesTitle')}
                detail={t('aiMethodologyPointNotesDetail')}
                icon={<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" /></svg>}
            />
            <MethodologyPoint 
                title={t('aiMethodologyPointFairnessTitle')}
                detail={t('aiMethodologyPointFairnessDetail')}
                icon={<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52l2.25-1.352M6.75 4.97l-2.25-1.352M12 4.5c-2.291 0-4.545.16-6.75.47M12 4.5C9.709 4.5 7.455 4.34 5.25 4.03m6.75 16.22c-2.291 0-4.545-.16-6.75-.47M18.75 20.03A48.416 48.416 0 0112 20.5c-2.291 0-4.545-.16-6.75-.47M12 20.5c2.291 0 4.545.16 6.75.47m-13.5 0c-1.01-.143-2.01-.317-3-.52m3 .52l-2.25 1.352M6.75 20.03l2.25 1.352M12 20.5c2.291 0 4.545.16 6.75.47" /></svg>}
            />
            <MethodologyPoint 
                title={t('aiMethodologyPointStructuredTitle')}
                detail={t('aiMethodologyPointStructuredDetail')}
                icon={<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M6.75 7.5l3 2.25-3 2.25m4.5 0h3m-9 8.25h13.5A2.25 2.25 0 0021 18V6a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 6v12a2.25 2.25 0 002.25 2.25z" /></svg>}
            />
             <MethodologyPoint 
                title={t('aiMethodologyPointHumanExpertiseTitle')}
                detail={t('aiMethodologyPointHumanExpertiseDetail')}
                icon={<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M17.982 18.725A7.488 7.488 0 0012 15.75a7.488 7.488 0 00-5.982 2.975m11.963 0a9 9 0 10-11.963 0m11.963 0A8.966 8.966 0 0112 21a8.966 8.966 0 01-5.982-2.275M15 9.75a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" d="M12 1.5V4.5M12 19.5V22.5M4.5 12H1.5M22.5 12H19.5M5.636 5.636l2.122 2.122M16.242 16.242l2.122 2.122M5.636 18.364l2.122-2.122M16.242 7.758l2.122-2.122" /></svg>}
            />
        </div>
    </section>


      <div className="mb-12">
        <h3 className="text-2xl sm:text-3xl font-semibold text-neutral-100 mb-8 text-center">{t('scoreBreakdown')}</h3>
        <div className={`grid md:grid-cols-${Math.min(Object.keys(result.scores).length, 3)} gap-6 sm:gap-8 mb-10`}>
          {Object.entries(result.scores).map(([id, scoreComp]) => (
            <ScoreCard 
              key={id}
              title={getDimensionLabel(id)} 
              score={scoreComp.score} 
              explanation={scoreComp.explanation} 
              details={renderScoreComponentDetails(scoreComp)} 
            />
          ))}
        </div>
        
        {chartData.length > 0 && (
        <div className="h-96 bg-neutral-800 p-6 rounded-xl shadow-xl-dark border border-neutral-700">
           <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 10 }}>
              <defs>
                <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#059669" stopOpacity={0.9}/>
                </linearGradient>
                <linearGradient id="colorWarning" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#d97706" stopOpacity={0.9}/>
                </linearGradient>
                <linearGradient id="colorDanger" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#dc2626" stopOpacity={0.9}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" /> 
              <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 14 }} /> 
              <YAxis domain={[0, 100]} tick={{ fill: '#9ca3af', fontSize: 14 }} />
              <Tooltip
                cursor={{fill: 'rgba(55, 65, 81, 0.5)'}} 
                contentStyle={{ backgroundColor: '#1f2937', borderRadius: '0.5rem', borderColor: '#374151', boxShadow: '0 4px 12px rgba(0,0,0,0.3)' }} 
                itemStyle={{ color: '#e5e7eb' }} 
                labelStyle={{ fontWeight: 'bold', color: '#f3f4f6', marginBottom: '0.5rem', display: 'block', borderBottom: '1px solid #374151', paddingBottom: '0.5rem' }} 
              />
              <Legend wrapperStyle={{ color: '#d1d5db', fontSize: 14, paddingTop: '10px' }} /> 
              <Bar dataKey="score" barSize={Math.max(30, 150 / Math.max(1,chartData.length))} radius={[6, 6, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getScoreCategoryFill(entry.score)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        )}
      </div>

      <IntelligenceSection
        title={t('keyStrengthsTitle')}
        points={result.positivePoints}
        icon={<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-6 h-6 mr-3 opacity-90"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" /></svg>}
        colorClass="border-success-DEFAULT"
      />

      <IntelligenceSection
        title={t('areasForClarificationTitle')}
        points={result.painPoints}
        icon={<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-6 h-6 mr-3 opacity-90"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM8.94 6.94a.75.75 0 11-1.06-1.061 3.5 3.5 0 111.06 1.061zM10 12.25a.75.75 0 01.75-.75h.008a.75.75 0 01.75.75v.008a.75.75 0 01-.75.75H10.75a.75.75 0 01-.75-.75V12.25z" clipRule="evenodd" /></svg>}
        colorClass="border-warning-DEFAULT"
      />

      <IntelligenceSection
        title={t('strategicDiscussionPointsTitle')}
        points={result.discussionPoints}
        icon={<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-6 h-6 mr-3 opacity-90"><path fillRule="evenodd" d="M10 2a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 2zM10 15a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 15zM4.134 5.866a.75.75 0 010-1.06 5.523 5.523 0 017.812 0 .75.75 0 01-1.06 1.06A3.999 3.999 0 005.195 7.022a.75.75 0 01-1.061-1.156zM14.804 12.977a3.999 3.999 0 00-5.656 0A.75.75 0 017.977 14.19a5.523 5.523 0 017.812 0 .75.75 0 01-1.06 1.06zM18 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 0118 10zM5 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 015 10z" clipRule="evenodd" /></svg>}
        colorClass="border-primary-DEFAULT"
      />

      <div className="mt-10 bg-neutral-800 p-6 md:p-8 rounded-xl shadow-xl-dark border border-neutral-700">
        <h3 className="text-2xl sm:text-3xl font-semibold text-neutral-100 mb-6 flex items-center">
           <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7 mr-3 text-primary-light opacity-90">
            <path fillRule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm8.706-1.442c1.146-.573 2.437.463 2.126 1.706l-.709 2.836.042-.02a.75.75 0 01.67 1.34l-.04.022c-1.147.573-2.438-.463-2.127-1.706l.71-2.836-.042.02a.75.75 0 11-.671-1.34l.041-.022zM12 9a.75.75 0 100-1.5.75.75 0 000 1.5z" clipRule="evenodd" />
          </svg>
          {t('detailedAnalysis')}
        </h3>
        <div className="prose prose-invert max-w-none text-neutral-300 whitespace-pre-line leading-relaxed text-justify">
            <p>{result.detailedExplanation}</p>
        </div>
      </div>

      <p className="mt-12 text-xs text-center text-neutral-500 italic px-4">{t('biasWarning')}</p>
    </div>
  );
};

export default ScoreReport;
