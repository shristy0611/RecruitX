import { useState } from 'react';
import FileUpload from './FileUpload';
import SkillList from './SkillList';
import recruitxApi from '../api/recruitxApi';
import { FiLoader, FiCheck, FiAlertCircle, FiFile, FiBriefcase } from 'react-icons/fi';
import { useLanguage } from '../contexts/LanguageContext';

const Matching = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resumeData, setResumeData] = useState(null);
  const [jobData, setJobData] = useState(null);
  const [matchResult, setMatchResult] = useState(null);
  const [resumeFile, setResumeFile] = useState(null);
  const [jobFile, setJobFile] = useState(null);
  const [step, setStep] = useState(1); // 1: Upload, 2: Analysis, 3: Results
  const { t, language } = useLanguage();

  const handleResumeUpload = async (file) => {
    setResumeFile(file);
    setError(null);
    setIsLoading(true);

    try {
      const result = await recruitxApi.analyzeResume(file, language);
      
      // Check for API-specific errors in the response
      if (result && result.error) {
        throw new Error(`API Error: ${result.error} - ${result.message || ''}`);
      }
      
      setResumeData(result);
    } catch (err) {
      console.error('Resume analysis error:', err);
      
      // Create a more user-friendly error message
      let errorMsg = language === 'ja' ? '履歴書の分析に失敗しました。もう一度お試しください。' : 'Failed to analyze resume. Please try again.';
      
      if (err.code === 'ECONNABORTED') {
        errorMsg = language === 'ja' ? '分析がタイムアウトしました。サーバーが履歴書の処理に時間がかかっています。' : 'Analysis timed out. The server is taking too long to process your resume.';
      } else if (err.message && err.message.includes('Network Error')) {
        errorMsg = language === 'ja' ? 'ネットワークエラー。接続を確認して、もう一度お試しください。' : 'Network error. Please check your connection and try again.';
      } else if (err.message && err.message.includes('API Error')) {
        errorMsg = err.message;
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      }
      
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleJobUpload = async (file) => {
    setJobFile(file);
    setError(null);
    setIsLoading(true);

    try {
      const result = await recruitxApi.analyzeJob(file, language);
      
      // Check for API-specific errors in the response
      if (result && result.error) {
        throw new Error(`API Error: ${result.error} - ${result.message || ''}`);
      }
      
      setJobData(result);
    } catch (err) {
      console.error('Job analysis error:', err);
      
      // Create a more user-friendly error message
      let errorMsg = language === 'ja' ? '求人情報の分析に失敗しました。もう一度お試しください。' : 'Failed to analyze job description. Please try again.';
      
      if (err.code === 'ECONNABORTED') {
        errorMsg = language === 'ja' ? '分析がタイムアウトしました。サーバーが求人情報の処理に時間がかかっています。' : 'Analysis timed out. The server is taking too long to process your job description.';
      } else if (err.message && err.message.includes('Network Error')) {
        errorMsg = language === 'ja' ? 'ネットワークエラー。接続を確認して、もう一度お試しください。' : 'Network error. Please check your connection and try again.';
      } else if (err.message && err.message.includes('API Error')) {
        errorMsg = err.message;
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      }
      
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMatch = async () => {
    setError(null);
    setIsLoading(true);
    setMatchResult(null);

    try {
      const result = await recruitxApi.matchResumeToJob(resumeData, jobData, language);
      
      // Check for API-specific errors in the response
      if (result && result.error) {
        throw new Error(`API Error: ${result.error}`);
      }
      
      setMatchResult(result);
      setStep(3);
    } catch (err) {
      console.error('Matching error:', err);
      
      // Create a more user-friendly error message
      let errorMsg = language === 'ja' ? '履歴書と求人情報のマッチングに失敗しました。もう一度お試しください。' : 'Failed to match resume to job. Please try again.';
      
      if (err.code === 'ECONNABORTED') {
        errorMsg = language === 'ja' ? 'マッチングがタイムアウトしました。サーバーがリクエストの処理に時間がかかっています。' : 'Matching timed out. The server is taking too long to process your request.';
      } else if (err.message && err.message.includes('Network Error')) {
        errorMsg = language === 'ja' ? 'ネットワークエラー。接続を確認して、もう一度お試しください。' : 'Network error. Please check your connection and try again.';
      } else if (err.message && err.message.includes('API Error')) {
        errorMsg = err.message;
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      }
      
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const resetAll = () => {
    setResumeFile(null);
    setJobFile(null);
    setResumeData(null);
    setJobData(null);
    setMatchResult(null);
    setError(null);
    setStep(1);
  };

  const renderProgressBar = () => {
    return (
      <div className="w-full mb-8">
        <div className="flex items-center justify-between">
          <div className="w-full">
            <div className="relative">
              <div className="overflow-hidden h-2 text-xs flex rounded bg-gray-200 dark:bg-gray-700">
                <div
                  className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-primary-500"
                  style={{ width: `${(step / 3) * 100}%` }}
                ></div>
              </div>
              <div className="flex justify-between text-xs mt-2">
                <div className={`font-medium ${step >= 1 ? 'text-primary-600 dark:text-primary-400' : 'text-gray-600 dark:text-gray-400'}`}>
                  {language === 'ja' ? 'ファイルのアップロード' : 'Upload Files'}
                </div>
                <div className={`font-medium ${step >= 2 ? 'text-primary-600 dark:text-primary-400' : 'text-gray-600 dark:text-gray-400'}`}>
                  {language === 'ja' ? '分析' : 'Analysis'}
                </div>
                <div className={`font-medium ${step >= 3 ? 'text-primary-600 dark:text-primary-400' : 'text-gray-600 dark:text-gray-400'}`}>
                  {language === 'ja' ? '結果' : 'Results'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Helper function to extract text from skill objects with potentially different formats
  const getSkillText = (skill) => {
    if (!skill) return '';
    
    if (typeof skill === 'string') {
      return skill;
    }
    
    // If it has a 'skill' property (some API responses use this format)
    if (skill.skill) {
      return skill.level ? `${skill.skill} (${skill.level})` : skill.skill;
    }
    
    // If it has a 'name' property (some API responses use this format)
    if (skill.name) {
      return skill.level ? `${skill.name} (${skill.level})` : skill.name;
    }
    
    // Fallback - stringify the object if possible
    return String(skill) !== '[object Object]' ? String(skill) : 'Unknown skill';
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-high-contrast">{t('matching.title')}</h1>
      
      {renderProgressBar()}

      {step === 1 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card">
            <div className="flex items-center mb-4">
              <FiFile className="h-5 w-5 text-primary-500 mr-2" />
              <h2 className="text-xl font-semibold text-high-contrast">{t('matching.uploadResume')}</h2>
            </div>
            <FileUpload onFileUpload={handleResumeUpload} />
            {resumeFile && (
              <div className="mt-2 text-sm text-medium-contrast">
                <strong>{language === 'ja' ? '選択されたファイル:' : 'Selected file:'}</strong> {resumeFile.name} ({(resumeFile.size / 1024).toFixed(1)} KB)
              </div>
            )}
            {resumeData && (
              <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200 text-green-700 text-sm dark:bg-green-900 dark:border-green-800 dark:text-green-300">
                <FiCheck className="inline-block mr-1" /> {language === 'ja' ? '履歴書の分析が完了しました' : 'Resume analyzed successfully'}
              </div>
            )}
          </div>

          <div className="card">
            <div className="flex items-center mb-4">
              <FiBriefcase className="h-5 w-5 text-primary-500 mr-2" />
              <h2 className="text-xl font-semibold text-high-contrast">{t('matching.uploadJob')}</h2>
            </div>
            <FileUpload onFileUpload={handleJobUpload} />
            {jobFile && (
              <div className="mt-2 text-sm text-medium-contrast">
                <strong>{language === 'ja' ? '選択されたファイル:' : 'Selected file:'}</strong> {jobFile.name} ({(jobFile.size / 1024).toFixed(1)} KB)
              </div>
            )}
            {jobData && (
              <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200 text-green-700 text-sm dark:bg-green-900 dark:border-green-800 dark:text-green-300">
                <FiCheck className="inline-block mr-1" /> {language === 'ja' ? '求人情報の分析が完了しました' : 'Job description analyzed successfully'}
              </div>
            )}
          </div>
        </div>
      )}

      {isLoading && (
        <div className="card flex items-center justify-center p-12 mt-6">
          <FiLoader className="h-8 w-8 text-primary-500 animate-spin" />
          <span className="ml-3 text-lg text-high-contrast">{t('common.loading')}</span>
        </div>
      )}

      {error && (
        <div className="card bg-red-50 border border-red-200 mt-6 dark:bg-red-900 dark:border-red-800">
          <div className="flex items-start">
            <FiAlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-2 dark:text-red-300" />
            <div>
              <h3 className="text-lg font-semibold text-red-800 mb-1 dark:text-red-200">{language === 'ja' ? 'エラー' : 'Error'}</h3>
              <p className="text-red-700 dark:text-red-300">{error}</p>
            </div>
          </div>
        </div>
      )}

      {resumeData && jobData && step === 1 && !isLoading && (
        <div className="flex justify-center mt-8">
          <button onClick={() => setStep(2)} className="btn btn-primary">
            {t('matching.continue')}
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-6 mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="text-xl font-semibold mb-4 text-high-contrast">{t('matching.resumeAnalysis')}</h2>
              <SkillList
                title={t('resume.skills')}
                skills={resumeData.skills}
                className="mb-4"
                badgeColor="blue"
              />
              <div className="text-medium-contrast text-sm mb-2">
                <strong className="text-high-contrast">{t('resume.experience')}:</strong> {resumeData.experience?.details?.length || 0} {t(language === 'ja' ? 'common.entriesJa' : 'common.entries')}
              </div>
              {resumeData.experience?.details?.length > 0 && (
                <ul className="mb-3 text-sm text-medium-contrast pl-5 list-disc">
                  {resumeData.experience.details.slice(0, 3).map((exp, index) => (
                    <li key={index}>{typeof exp === 'string' ? exp : (exp.position || exp.title || String(exp))}</li>
                  ))}
                  {resumeData.experience.details.length > 3 && (
                    <li className="italic">+{resumeData.experience.details.length - 3} more</li>
                  )}
                </ul>
              )}
              <div className="text-medium-contrast text-sm mb-2">
                <strong className="text-high-contrast">{t('resume.education')}:</strong> {resumeData.education?.details?.length || 0} {t(language === 'ja' ? 'common.entriesJa' : 'common.entries')}
              </div>
              {resumeData.education?.details?.length > 0 && (
                <ul className="mb-3 text-sm text-medium-contrast pl-5 list-disc">
                  {resumeData.education.details.slice(0, 2).map((edu, index) => (
                    <li key={index}>{typeof edu === 'string' ? edu : (edu.degree || edu.institution || String(edu))}</li>
                  ))}
                  {resumeData.education.details.length > 2 && (
                    <li className="italic">+{resumeData.education.details.length - 2} more</li>
                  )}
                </ul>
              )}
            </div>

            <div className="card">
              <h2 className="text-xl font-semibold mb-4 text-high-contrast">{t('matching.jobAnalysis')}</h2>
              <SkillList
                title={t('job.requiredSkills')}
                skills={jobData.required_skills}
                className="mb-4"
                badgeColor="yellow"
              />
              <div className="text-medium-contrast text-sm mb-2">
                <strong className="text-high-contrast">{t('job.responsibilities')}:</strong> {jobData.responsibilities?.details?.length || 0} {t(language === 'ja' ? 'common.entriesJa' : 'common.entries')}
              </div>
              {jobData.responsibilities?.details?.length > 0 && (
                <ul className="mb-3 text-sm text-medium-contrast pl-5 list-disc">
                  {jobData.responsibilities.details.slice(0, 3).map((resp, index) => (
                    <li key={index}>{typeof resp === 'string' ? resp : String(resp)}</li>
                  ))}
                  {jobData.responsibilities.details.length > 3 && (
                    <li className="italic">+{jobData.responsibilities.details.length - 3} more</li>
                  )}
                </ul>
              )}
              <div className="text-medium-contrast text-sm mb-2">
                <strong className="text-high-contrast">{t('job.qualifications')}:</strong> {jobData.qualifications?.details?.length || 0} {t(language === 'ja' ? 'common.entriesJa' : 'common.entries')}
              </div>
              {jobData.qualifications?.details?.length > 0 && (
                <ul className="mb-3 text-sm text-medium-contrast pl-5 list-disc">
                  {jobData.qualifications.details.slice(0, 2).map((qual, index) => (
                    <li key={index}>{typeof qual === 'string' ? qual : String(qual)}</li>
                  ))}
                  {jobData.qualifications.details.length > 2 && (
                    <li className="italic">+{jobData.qualifications.details.length - 2} more</li>
                  )}
                </ul>
              )}
            </div>
          </div>

          <div className="flex justify-center mt-8 space-x-4">
            <button onClick={() => setStep(1)} className="btn btn-outline">
              {t('matching.back')}
            </button>
            <button onClick={handleMatch} className="btn btn-primary">
              {t('matching.match')}
            </button>
          </div>
        </div>
      )}

      {step === 3 && matchResult && (
        <div className="space-y-6 mt-6">
          <div className="card">
            <h2 className="text-2xl font-bold mb-6 text-center">{language === 'ja' ? 'マッチング結果' : 'Match Results'}</h2>
            
            <div className="flex justify-center mb-8">
              <div className="relative w-48 h-48">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-4xl font-bold text-primary-600">{matchResult.match_score}%</div>
                    <div className="text-sm text-gray-500">{t('matching.matchScore')}</div>
                  </div>
                </div>
                <svg className="w-full h-full" viewBox="0 0 100 100">
                  <circle
                    className="text-gray-200 stroke-current"
                    strokeWidth="10"
                    cx="50"
                    cy="50"
                    r="40"
                    fill="transparent"
                  ></circle>
                  <circle
                    className="text-primary-500 stroke-current"
                    strokeWidth="10"
                    strokeLinecap="round"
                    cx="50"
                    cy="50"
                    r="40"
                    fill="transparent"
                    strokeDasharray={`${2 * Math.PI * 40}`}
                    strokeDashoffset={`${2 * Math.PI * 40 * (1 - matchResult.match_score / 100)}`}
                    transform="rotate(-90 50 50)"
                  ></circle>
                </svg>
              </div>
            </div>
            
            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-xl font-semibold mb-4">{t('matching.explanation')}</h3>
              <p className="text-gray-700">
                {typeof matchResult.score_explanation === 'string' 
                  ? matchResult.score_explanation 
                  : (matchResult.score_explanation?.description || matchResult.score_explanation?.text || JSON.stringify(matchResult.score_explanation))}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-xl font-semibold mb-4">{t('matching.matchingSkills')}</h3>
              {Array.isArray(matchResult.matching_skills) ? (
                <ul className="space-y-2">
                  {matchResult.matching_skills.map((skill, index) => (
                    <li key={index} className="flex items-start">
                      <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 flex items-center justify-center mt-0.5 mr-2">
                        <span className="text-green-600 text-xs">✓</span>
                      </div>
                      <span>{getSkillText(skill)}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500 italic">{t('common.noData')}</p>
              )}
            </div>

            <div className="card">
              <h3 className="text-xl font-semibold mb-4">{t('matching.missingSkills')}</h3>
              {Array.isArray(matchResult.missing_skills) ? (
                <ul className="space-y-2">
                  {matchResult.missing_skills.map((skill, index) => (
                    <li key={index} className="flex items-start">
                      <div className="flex-shrink-0 w-5 h-5 rounded-full bg-orange-100 flex items-center justify-center mt-0.5 mr-2">
                        <span className="text-orange-600 text-xs">!</span>
                      </div>
                      <span>{getSkillText(skill)}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500 italic">{t('common.noData')}</p>
              )}
            </div>
          </div>

          <div className="card">
            <h3 className="text-xl font-semibold mb-4">{t('matching.recommendations')}</h3>
            {Array.isArray(matchResult.recommendations) ? (
              <ul className="space-y-2">
                {matchResult.recommendations.map((recommendation, index) => (
                  <li key={index} className="flex items-start">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center mt-0.5 mr-2">
                      <span className="text-blue-600 text-xs">i</span>
                    </div>
                    <span>
                      {typeof recommendation === 'string' 
                        ? recommendation 
                        : (recommendation.description || recommendation.text || recommendation.recommendation || String(recommendation))}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic">{t('common.noData')}</p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-xl font-semibold mb-4">{language === 'ja' ? '経験のマッチ' : 'Experience Match'}</h3>
              <p className="text-gray-700">
                {typeof matchResult.matching_experience === 'string' 
                  ? matchResult.matching_experience 
                  : (matchResult.matching_experience?.description || matchResult.matching_experience?.text || JSON.stringify(matchResult.matching_experience))}
              </p>
            </div>
            <div className="card">
              <h3 className="text-xl font-semibold mb-4">{language === 'ja' ? '学歴のマッチ' : 'Education Match'}</h3>
              <p className="text-gray-700">
                {typeof matchResult.matching_education === 'string' 
                  ? matchResult.matching_education 
                  : (matchResult.matching_education?.description || matchResult.matching_education?.text || JSON.stringify(matchResult.matching_education))}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-xl font-semibold mb-4">{language === 'ja' ? '強み' : 'Strengths'}</h3>
              <ul className="space-y-2">
                {matchResult.strengths?.map((strength, index) => (
                  <li key={index} className="flex items-start">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 flex items-center justify-center mt-0.5 mr-2">
                      <span className="text-green-600 text-xs">+</span>
                    </div>
                    <span>{typeof strength === 'string' ? strength : (strength.description || strength.detail || String(strength))}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="card">
              <h3 className="text-xl font-semibold mb-4">{language === 'ja' ? '改善点' : 'Areas for Improvement'}</h3>
              <ul className="space-y-2">
                {matchResult.areas_for_improvement?.map((area, index) => (
                  <li key={index} className="flex items-start">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-yellow-100 flex items-center justify-center mt-0.5 mr-2">
                      <span className="text-yellow-600 text-xs">↑</span>
                    </div>
                    <span>{typeof area === 'string' ? area : (area.description || area.detail || String(area))}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="flex justify-center mt-8 space-x-4">
            <button onClick={resetAll} className="btn btn-primary">
              {language === 'ja' ? '最初からやり直す' : 'Start Over'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Matching; 