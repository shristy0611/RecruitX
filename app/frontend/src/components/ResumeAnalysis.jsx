import { useState } from 'react';
import FileUpload from './FileUpload';
import SkillList from './SkillList';
import recruitxApi from '../services/recruitxApi';
import { FiLoader, FiCheck, FiAlertCircle } from 'react-icons/fi';

const ResumeAnalysis = () => {
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
      const result = await recruitxApi.analyzeResume(file);
      setAnalysisResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze resume. Please try again.');
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
      if (company) result += ` at ${company}`;
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
      if (institution) result += ` from ${institution}`;
      if (year) result += ` (${year})`;
      
      return result;
    }
    
    // Fallback - try to convert to string or return a placeholder
    return String(item) !== '[object Object]' ? String(item) : 'Item details unavailable';
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Resume Analysis</h1>
      
      <div className="card mb-8">
        <h2 className="text-xl font-semibold mb-4">Upload Resume</h2>
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
          <span className="ml-3 text-lg">Analyzing resume...</span>
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
                <p className="text-green-700">Resume successfully analyzed.</p>
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-xl font-semibold mb-6">Analysis Results</h2>
            
            <SkillList 
              title="Skills" 
              skills={analysisResult.skills} 
              className="mb-6" 
              badgeColor="blue" 
            />
            
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">Experience</h3>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {analysisResult.experience?.map((exp, index) => (
                  <li key={index}>{getItemText(exp)}</li>
                ))}
              </ul>
            </div>
            
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">Education</h3>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {analysisResult.education?.map((edu, index) => (
                  <li key={index}>{getItemText(edu)}</li>
                ))}
              </ul>
            </div>

            {analysisResult.achievements && analysisResult.achievements.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-2">Achievements</h3>
                <ul className="list-disc list-inside space-y-1 text-gray-700">
                  {analysisResult.achievements.map((achievement, index) => (
                    <li key={index}>{getItemText(achievement)}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {analysisResult.key_strengths && analysisResult.key_strengths.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Key Strengths</h3>
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
                  <h3 className="text-lg font-semibold mb-2">Areas for Development</h3>
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
              Analyze Another Resume
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResumeAnalysis; 