import { useState } from 'react';
import FileUpload from './FileUpload';
import SkillList from './SkillList';
import recruitxApi from '../api/recruitxApi';
import { FiLoader, FiCheck, FiAlertCircle } from 'react-icons/fi';
import { useLanguage } from '../contexts/LanguageContext';

const ResumeAnalysis = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const { t, language } = useLanguage();

  const handleFileUpload = async (file) => {
    setSelectedFile(file);
    setIsLoading(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const result = await recruitxApi.analyzeResume(file, language);
      setAnalysisResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || t('common.error'));
      console.error('Resume analysis error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to extract text from possibly nested API response objects
  const getItemText = (item) => {
    if (typeof item === 'string') {
      return item;
    }
    
    // If it has typical object properties, try to format them nicely
    if (item.role || item.position || item.title) {
      const position = item.role || item.position || item.title;
      const company = item.company || item.organization || '';
      const duration = item.duration || '';
      const years = item.years || '';
      
      let result = position;
      if (company) result += language === 'ja' ? ` - ${company}` : ` at ${company}`;
      if (duration) result += ` (${duration})`;
      if (years) result += ` - ${years}`;
      
      return result;
    }
    
    // If it has degree/institution (for education)
    if (item.degree || item.institution) {
      const degree = item.degree || '';
      const institution = item.institution || '';
      const year = item.year || item.graduationYear || '';
      
      let result = degree;
      if (institution) result += language === 'ja' ? ` - ${institution}` : ` from ${institution}`;
      if (year) result += ` (${year})`;
      
      return result;
    }
    
    // Fallback - try to convert to string or return a placeholder
    return String(item) !== '[object Object]' ? String(item) : language === 'ja' ? '詳細が利用できません' : 'Item details unavailable';
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">{t('resume.title')}</h1>
      
      <div className="card mb-8">
        <h2 className="text-xl font-semibold mb-4">{t('resume.upload')}</h2>
        <FileUpload onFileUpload={handleFileUpload} />
        
        {selectedFile && (
          <div className="mt-2 text-sm text-gray-600">
            <strong>{language === 'ja' ? '選択されたファイル:' : 'Selected file:'}</strong> {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
          </div>
        )}
      </div>

      {isLoading && (
        <div className="card flex items-center justify-center p-12">
          <FiLoader className="h-8 w-8 text-primary-500 animate-spin" />
          <span className="ml-3 text-lg">{t('common.loading')}</span>
        </div>
      )}

      {error && (
        <div className="card bg-red-50 border border-red-200">
          <div className="flex items-start">
            <FiAlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-2" />
            <div>
              <h3 className="text-lg font-semibold text-red-800 mb-1">{language === 'ja' ? '分析に失敗しました' : 'Analysis Failed'}</h3>
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {analysisResult && (
        <div className="space-y-6">
          <div className="card bg-green-50 border border-green-200">
            <div className="flex items-start">
              <FiCheck className="h-5 w-5 text-green-500 mt-0.5 mr-2" />
              <div>
                <h3 className="text-lg font-semibold text-green-800 mb-1">{language === 'ja' ? '分析完了' : 'Analysis Complete'}</h3>
                <p className="text-green-700">{language === 'ja' ? '履歴書の分析が完了しました。' : 'Resume successfully analyzed.'}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-xl font-semibold mb-6">{language === 'ja' ? '分析結果' : 'Analysis Results'}</h2>
            
            <SkillList 
              title={t('resume.skills')} 
              skills={analysisResult.skills} 
              className="mb-6" 
              badgeColor="blue" 
            />
            
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">{t('resume.experience')}</h3>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {analysisResult.experience?.details?.map((exp, index) => (
                  <li key={index}>{getItemText(exp)}</li>
                ))}
              </ul>
            </div>
            
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">{t('resume.education')}</h3>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {analysisResult.education?.details?.map((edu, index) => (
                  <li key={index}>{getItemText(edu)}</li>
                ))}
              </ul>
            </div>
            
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">{t('resume.achievements')}</h3>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {analysisResult.achievements?.details?.map((achievement, index) => (
                  <li key={index}>{getItemText(achievement)}</li>
                ))}
              </ul>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {analysisResult.key_strengths && analysisResult.key_strengths.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">{t('resume.keyStrengths')}</h3>
                  <ul className="space-y-2">
                    {analysisResult.key_strengths.map((strength, index) => (
                      <li key={index} className="flex items-start">
                        <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 flex items-center justify-center mt-0.5 mr-2">
                          <span className="text-green-600 text-xs">+</span>
                        </div>
                        <span>{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {analysisResult.development_areas && analysisResult.development_areas.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">{t('resume.developmentAreas')}</h3>
                  <ul className="space-y-2">
                    {analysisResult.development_areas.map((area, index) => (
                      <li key={index} className="flex items-start">
                        <div className="flex-shrink-0 w-5 h-5 rounded-full bg-yellow-100 flex items-center justify-center mt-0.5 mr-2">
                          <span className="text-yellow-600 text-xs">↑</span>
                        </div>
                        <span>{area}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
          
          <div className="flex justify-center">
            <button
              onClick={() => {
                setSelectedFile(null);
                setAnalysisResult(null);
              }}
              className="btn btn-outline"
            >
              {language === 'ja' ? '別の履歴書を分析する' : 'Analyze Another Resume'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResumeAnalysis; 