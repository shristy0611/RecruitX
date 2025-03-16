import { useState } from 'react';
import FileUpload from './FileUpload';
import SkillList from './SkillList';
import recruitxApi from '../services/recruitxApi';
import { FiLoader, FiCheck, FiAlertCircle } from 'react-icons/fi';

const JobAnalysis = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileUpload = async (file) => {
    setSelectedFile(file);
    setIsLoading(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const result = await recruitxApi.analyzeJob(file);
      setAnalysisResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze job description. Please try again.');
      console.error('Job analysis error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to extract text from possibly nested API response objects
  const getItemText = (item) => {
    if (typeof item === 'string') {
      return item;
    }
    
    // For responsibilities
    if (item.responsibility) {
      return item.description ? `${item.responsibility}: ${item.description}` : item.responsibility;
    }
    
    // For qualifications
    if (item.qualification) {
      return item.importance 
        ? `${item.qualification} (${item.importance})` 
        : item.qualification;
    }
    
    // Fallback - try to convert to string or return a placeholder
    return String(item) !== '[object Object]' ? String(item) : 'Item details unavailable';
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Job Description Analysis</h1>
      
      <div className="card mb-8">
        <h2 className="text-xl font-semibold mb-4">Upload Job Description</h2>
        <FileUpload onFileUpload={handleFileUpload} />
        
        {selectedFile && (
          <div className="mt-2 text-sm text-gray-600">
            <strong>Selected file:</strong> {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
          </div>
        )}
      </div>

      {isLoading && (
        <div className="card flex items-center justify-center p-12">
          <FiLoader className="h-8 w-8 text-primary-500 animate-spin" />
          <span className="ml-3 text-lg">Analyzing job description...</span>
        </div>
      )}

      {error && (
        <div className="card bg-red-50 border border-red-200">
          <div className="flex items-start">
            <FiAlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-2" />
            <div>
              <h3 className="text-lg font-semibold text-red-800 mb-1">Analysis Failed</h3>
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
                <h3 className="text-lg font-semibold text-green-800 mb-1">Analysis Complete</h3>
                <p className="text-green-700">Job description successfully analyzed.</p>
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-xl font-semibold mb-6">Analysis Results</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div>
                <SkillList 
                  title="Required Skills" 
                  skills={analysisResult.required_skills} 
                  className="mb-6" 
                  badgeColor="yellow" 
                />
              </div>
              
              {analysisResult.preferred_skills && analysisResult.preferred_skills.length > 0 && (
                <div>
                  <SkillList 
                    title="Preferred Skills" 
                    skills={analysisResult.preferred_skills} 
                    className="mb-6" 
                    badgeColor="blue" 
                  />
                </div>
              )}
            </div>
            
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">Responsibilities</h3>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {analysisResult.responsibilities?.map((resp, index) => (
                  <li key={index}>{getItemText(resp)}</li>
                ))}
              </ul>
            </div>
            
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">Qualifications</h3>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {analysisResult.qualifications?.map((qual, index) => (
                  <li key={index}>{getItemText(qual)}</li>
                ))}
              </ul>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {analysisResult.job_benefits && analysisResult.job_benefits.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Job Benefits</h3>
                  <ul className="space-y-2">
                    {analysisResult.job_benefits.map((benefit, index) => (
                      <li key={index} className="flex items-start">
                        <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 flex items-center justify-center mt-0.5 mr-2">
                          <span className="text-green-600 text-xs">✓</span>
                        </div>
                        <span>{getItemText(benefit)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {analysisResult.company_culture && analysisResult.company_culture.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Company Culture</h3>
                  <ul className="space-y-2">
                    {analysisResult.company_culture.map((culture, index) => (
                      <li key={index} className="flex items-start">
                        <div className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center mt-0.5 mr-2">
                          <span className="text-blue-600 text-xs">i</span>
                        </div>
                        <span>{getItemText(culture)}</span>
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
              Analyze Another Job Description
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobAnalysis; 