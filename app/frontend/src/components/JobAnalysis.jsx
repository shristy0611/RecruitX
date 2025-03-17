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
      <h1 className="text-3xl font-bold mb-8 text-center">{t('job.title')}</h1>
      
      {!analysisResult && (
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">{t('job.upload')}</h2>
          <FileUpload onFileUpload={handleFileUpload} />
          
          {selectedFile && (
            <div className="mt-2 text-sm text-gray-600">
              <strong>{language === 'ja' ? '選択されたファイル:' : 'Selected file:'}</strong> {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </div>
          )}
        </div>
      )}

      {isLoading && (
        <div className="flex flex-col items-center justify-center p-8">
          <div className="animate-pulse flex space-x-4 items-center mb-4">
            <div className="h-12 w-12 bg-primary-200 rounded-full"></div>
            <div className="space-y-2">
              <div className="h-4 bg-primary-200 rounded w-36"></div>
              <div className="h-4 bg-primary-100 rounded w-24"></div>
            </div>
          </div>
          <p className="text-primary-600 font-medium">{t('job.analyzing')}</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start">
          <FiAlertCircle className="h-5 w-5 mr-2 mt-0.5 text-red-500" />
          <div>
            <p className="font-medium">{t('common.error')}</p>
            <p>{error}</p>
            <p className="mt-2 text-sm">{t('common.tryAgain')}</p>
          </div>
        </div>
      )}

      {analysisResult && (
        <div className="space-y-6">
          <div className="card bg-green-50 border border-green-100">
            <div className="flex items-center">
              <FiCheck className="h-6 w-6 text-green-500 mr-2" />
              <div>
                <h2 className="text-xl font-semibold text-green-700">{t('job.complete')}</h2>
                <p className="text-green-600">{t('job.success')}</p>
              </div>
            </div>
            <button 
              onClick={() => {
                setSelectedFile(null);
                setAnalysisResult(null);
              }} 
              className="mt-4 btn btn-outline-primary"
            >
              {t('job.upload')}
            </button>
          </div>

          <div className="card">
            <h2 className="text-xl font-semibold mb-6">{t('job.results')}</h2>
            
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium mb-2 text-primary-700">{t('job.requiredSkills')}</h3>
                {getItemText(analysisResult.required_skills)}
              </div>
              
              <div>
                <h3 className="text-lg font-medium mb-2 text-primary-700">{t('job.preferredSkills')}</h3>
                {getItemText(analysisResult.preferred_skills)}
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="text-lg font-medium mb-2 text-primary-700">{t('job.responsibilities')}</h3>
              {getItemText(analysisResult.responsibilities)}
            </div>
            
            <div className="mt-6">
              <h3 className="text-lg font-medium mb-2 text-primary-700">{t('job.qualifications')}</h3>
              {getItemText(analysisResult.qualifications)}
            </div>
            
            <div className="mt-6">
              <h3 className="text-lg font-medium mb-2 text-primary-700">{t('job.companyInfo')}</h3>
              {getItemText(analysisResult.company_info)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobAnalysis; 