import { useState } from 'react';
import FileUpload from './FileUpload';
import SkillList from './SkillList';
import recruitxApi from '../api/recruitxApi';
import { FiLoader, FiCheck, FiAlertCircle } from 'react-icons/fi';
import { useLanguage } from '../contexts/LanguageContext';

const JobAnalysis = () => {
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
      const result = await recruitxApi.analyzeJob(file, language);
      setAnalysisResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || t('common.error'));
      console.error('Job analysis error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to extract text from possibly nested API response objects
  const getItemText = (item) => {
    if (!item || !item.details || item.details.length === 0) {
      return <p className="text-gray-500 italic">{t('job.noItems')}</p>;
    }

    return (
      <ul className="list-disc list-inside space-y-1">
        {item.details.map((detail, index) => (
          <li key={index}>{detail}</li>
        ))}
      </ul>
    );
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-high-contrast">{t('job.title')}</h1>
      
      <div className="card mb-8">
        <h2 className="text-xl font-semibold mb-4 text-high-contrast">{t('job.upload')}</h2>
        <FileUpload onFileUpload={handleFileUpload} />
        
        {selectedFile && (
          <div className="mt-2 text-sm text-medium-contrast">
            <strong>{language === 'ja' ? '選択されたファイル:' : 'Selected file:'}</strong> {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
          </div>
        )}
      </div>

      {isLoading && (
        <div className="card flex items-center justify-center p-12">
          <FiLoader className="h-8 w-8 text-primary-500 animate-spin" />
          <span className="ml-3 text-lg text-medium-contrast">{t('common.loading')}</span>
        </div>
      )}

      {error && (
        <div className="card bg-red-50 border border-red-200 dark:bg-red-900 dark:border-red-800">
          <div className="flex items-start">
            <FiAlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-2 dark:text-red-300" />
            <div>
              <h3 className="text-lg font-semibold text-red-800 mb-1 dark:text-red-200">{language === 'ja' ? '分析に失敗しました' : 'Analysis Failed'}</h3>
              <p className="text-red-700 dark:text-red-300">{error}</p>
            </div>
          </div>
        </div>
      )}

      {analysisResult && (
        <div className="space-y-6">
          <div className="card bg-green-50 border border-green-200 dark:bg-green-900 dark:border-green-800">
            <div className="flex items-start">
              <FiCheck className="h-5 w-5 text-green-500 mt-0.5 mr-2 dark:text-green-300" />
              <div>
                <h3 className="text-lg font-semibold text-green-800 mb-1 dark:text-green-200">{language === 'ja' ? '分析完了' : 'Analysis Complete'}</h3>
                <p className="text-green-700 dark:text-green-300">{language === 'ja' ? '求人情報の分析が完了しました。' : 'Job description successfully analyzed.'}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-xl font-semibold mb-6 text-high-contrast">{language === 'ja' ? '分析結果' : 'Analysis Results'}</h2>
            
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold mb-2 text-high-contrast">{t('job.requiredSkills')}</h3>
                {getItemText(analysisResult.required_skills)}
              </div>
              
              <div>
                <h3 className="text-lg font-semibold mb-2 text-high-contrast">{t('job.preferredSkills')}</h3>
                {getItemText(analysisResult.preferred_skills)}
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-2 text-high-contrast">{t('job.responsibilities')}</h3>
              {getItemText(analysisResult.responsibilities)}
            </div>
            
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-2 text-high-contrast">{t('job.qualifications')}</h3>
              {getItemText(analysisResult.qualifications)}
            </div>
            
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-2 text-high-contrast">{t('job.companyInfo')}</h3>
              {getItemText(analysisResult.company_info)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobAnalysis; 