import { useState } from 'react';
import FileUpload from './FileUpload';
import SkillList from './SkillList';
import recruitxApi from '../services/recruitxApi';
import { FiLoader, FiCheck, FiAlertCircle, FiFile, FiBriefcase } from 'react-icons/fi';

const Matching = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resumeData, setResumeData] = useState(null);
  const [jobData, setJobData] = useState(null);
  const [matchResult, setMatchResult] = useState(null);
  const [resumeFile, setResumeFile] = useState(null);
  const [jobFile, setJobFile] = useState(null);
  const [step, setStep] = useState(1); // 1: Upload, 2: Analysis, 3: Results

  const handleResumeUpload = async (file) => {
    setResumeFile(file);
    setError(null);
    setIsLoading(true);

    try {
      const result = await recruitxApi.analyzeResume(file);
      
      // Check for API-specific errors in the response
      if (result && result.error) {
        throw new Error(`API Error: ${result.error} - ${result.message || ''}`);
      }
      
      setResumeData(result);
    } catch (err) {
      console.error('Resume analysis error:', err);
      
      // Create a more user-friendly error message
      let errorMsg = 'Failed to analyze resume. Please try again.';
      
      if (err.code === 'ECONNABORTED') {
        errorMsg = 'Analysis timed out. The server is taking too long to process your resume.';
      } else if (err.message && err.message.includes('Network Error')) {
        errorMsg = 'Network error. Please check your connection and try again.';
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
      const result = await recruitxApi.analyzeJob(file);
      
      // Check for API-specific errors in the response
      if (result && result.error) {
        throw new Error(`API Error: ${result.error} - ${result.message || ''}`);
      }
      
      setJobData(result);
    } catch (err) {
      console.error('Job analysis error:', err);
      
      // Create a more user-friendly error message
      let errorMsg = 'Failed to analyze job description. Please try again.';
      
      if (err.code === 'ECONNABORTED') {
        errorMsg = 'Analysis timed out. The server is taking too long to process your job description.';
      } else if (err.message && err.message.includes('Network Error')) {
        errorMsg = 'Network error. Please check your connection and try again.';
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
      const result = await recruitxApi.matchResumeToJob(resumeData, jobData);
      
      // Check for API-specific errors in the response
      if (result && result.error) {
        throw new Error(`API Error: ${result.error}`);
      }
      
      setMatchResult(result);
      setStep(3);
    } catch (err) {
      console.error('Matching error:', err);
      
      // Create a more user-friendly error message
      let errorMsg = 'Failed to match resume to job. Please try again.';
      
      if (err.code === 'ECONNABORTED') {
        errorMsg = 'Matching timed out. The server is taking too long to process your request.';
      } else if (err.message && err.message.includes('Network Error')) {
        errorMsg = 'Network error. Please check your connection and try again.';
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
              <div className="overflow-hidden h-2 text-xs flex rounded bg-gray-200">
                <div
                  className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-primary-500"
                  style={{ width: `${(step / 3) * 100}%` }}
                ></div>
              </div>
              <div className="flex justify-between text-xs text-gray-600 mt-2">
                <div className={`font-medium ${step >= 1 ? 'text-primary-600' : ''}`}>Upload Files</div>
                <div className={`font-medium ${step >= 2 ? 'text-primary-600' : ''}`}>Analysis</div>
                <div className={`font-medium ${step >= 3 ? 'text-primary-600' : ''}`}>Results</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Helper function to extract text from skill objects
  const getSkillText = (skill) => {
    if (typeof skill === 'string') {
      return skill;
    }
    
    // If it has a 'skill' property
    if (skill.skill) {
      const match_level = skill.match_level || skill.level || skill.proficiency || '';
      return match_level ? `${skill.skill} (${match_level})` : skill.skill;
    }
    
    // If it has a 'name' property
    if (skill.name) {
      const match_level = skill.match_level || skill.level || skill.proficiency || '';
      return match_level ? `${skill.name} (${match_level})` : skill.name;
    }
    
    // If it has any description or detail
    if (skill.description || skill.detail) {
      const base = skill.description || skill.detail;
      const level = skill.importance || skill.proficiency || '';
      return level ? `${base} (${level})` : base;
    }
    
    // Fallback
    return String(skill) !== '[object Object]' ? String(skill) : 'Skill details unavailable';
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Resume-Job Matching</h1>
      
      {renderProgressBar()}

      {step === 1 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card">
            <div className="flex items-center mb-4">
              <FiFile className="h-5 w-5 text-primary-500 mr-2" />
              <h2 className="text-xl font-semibold">Upload Resume</h2>
            </div>
            <FileUpload onFileUpload={handleResumeUpload} />
            {resumeFile && (
              <div className="mt-2 text-sm text-gray-600">
                <strong>Selected file:</strong> {resumeFile.name} ({(resumeFile.size / 1024).toFixed(1)} KB)
              </div>
            )}
            {resumeData && (
              <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200 text-green-700 text-sm">
                <FiCheck className="inline-block mr-1" /> Resume analyzed successfully
              </div>
            )}
          </div>

          <div className="card">
            <div className="flex items-center mb-4">
              <FiBriefcase className="h-5 w-5 text-primary-500 mr-2" />
              <h2 className="text-xl font-semibold">Upload Job Description</h2>
            </div>
            <FileUpload onFileUpload={handleJobUpload} />
            {jobFile && (
              <div className="mt-2 text-sm text-gray-600">
                <strong>Selected file:</strong> {jobFile.name} ({(jobFile.size / 1024).toFixed(1)} KB)
              </div>
            )}
            {jobData && (
              <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200 text-green-700 text-sm">
                <FiCheck className="inline-block mr-1" /> Job description analyzed successfully
              </div>
            )}
          </div>
        </div>
      )}

      {isLoading && (
        <div className="card flex items-center justify-center p-12 mt-6">
          <FiLoader className="h-8 w-8 text-primary-500 animate-spin" />
          <span className="ml-3 text-lg">Processing...</span>
        </div>
      )}

      {error && (
        <div className="card bg-red-50 border border-red-200 mt-6">
          <div className="flex items-start">
            <FiAlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-2" />
            <div>
              <h3 className="text-lg font-semibold text-red-800 mb-1">Error</h3>
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {resumeData && jobData && step === 1 && !isLoading && (
        <div className="flex justify-center mt-8">
          <button onClick={() => setStep(2)} className="btn btn-primary">
            Continue to Analysis
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-6 mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Resume Analysis</h2>
              <SkillList
                title="Skills"
                skills={resumeData.skills}
                className="mb-4"
                badgeColor="blue"
              />
              <div className="text-gray-700 text-sm">
                <strong>Experience:</strong> {resumeData.experience?.length || 0} entries
              </div>
              <div className="text-gray-700 text-sm">
                <strong>Education:</strong> {resumeData.education?.length || 0} entries
              </div>
            </div>

            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Job Analysis</h2>
              <SkillList
                title="Required Skills"
                skills={jobData.required_skills}
                className="mb-4"
                badgeColor="yellow"
              />
              <div className="text-gray-700 text-sm">
                <strong>Responsibilities:</strong> {jobData.responsibilities?.length || 0} entries
              </div>
              <div className="text-gray-700 text-sm">
                <strong>Qualifications:</strong> {jobData.qualifications?.length || 0} entries
              </div>
            </div>
          </div>

          <div className="flex justify-center mt-8 space-x-4">
            <button onClick={() => setStep(1)} className="btn btn-outline">
              Back
            </button>
            <button onClick={handleMatch} className="btn btn-primary">
              Match Resume to Job
            </button>
          </div>
        </div>
      )}

      {step === 3 && matchResult && (
        <div className="space-y-6 mt-6">
          <div className="card">
            <h2 className="text-2xl font-bold mb-6 text-center">Match Results</h2>
            
            <div className="flex justify-center mb-8">
              <div className="relative w-48 h-48">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-4xl font-bold text-primary-600">{matchResult.match_score}%</div>
                    <div className="text-sm text-gray-500">Match Score</div>
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
              <h3 className="text-xl font-semibold mb-4">Score Explanation</h3>
              <p className="text-gray-700">
                {typeof matchResult.score_explanation === 'string' 
                  ? matchResult.score_explanation 
                  : (matchResult.score_explanation?.description || matchResult.score_explanation?.text || JSON.stringify(matchResult.score_explanation))}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-xl font-semibold mb-4">Matching Skills</h3>
              <ul className="space-y-2">
                {matchResult.matching_skills?.map((skill, index) => (
                  <li key={index} className="flex items-start">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 flex items-center justify-center mt-0.5 mr-2">
                      <span className="text-green-600 text-xs">✓</span>
                    </div>
                    <span>{getSkillText(skill)}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="card">
              <h3 className="text-xl font-semibold mb-4">Missing Skills</h3>
              <ul className="space-y-2">
                {matchResult.missing_skills?.map((skill, index) => (
                  <li key={index} className="flex items-start">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-orange-100 flex items-center justify-center mt-0.5 mr-2">
                      <span className="text-orange-600 text-xs">!</span>
                    </div>
                    <span>{getSkillText(skill)}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="card">
            <h3 className="text-xl font-semibold mb-4">Recommendations</h3>
            <ul className="space-y-2">
              {matchResult.recommendations?.map((recommendation, index) => (
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
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-xl font-semibold mb-4">Experience Match</h3>
              <p className="text-gray-700">
                {typeof matchResult.matching_experience === 'string' 
                  ? matchResult.matching_experience 
                  : (matchResult.matching_experience?.description || matchResult.matching_experience?.text || JSON.stringify(matchResult.matching_experience))}
              </p>
            </div>
            <div className="card">
              <h3 className="text-xl font-semibold mb-4">Education Match</h3>
              <p className="text-gray-700">
                {typeof matchResult.matching_education === 'string' 
                  ? matchResult.matching_education 
                  : (matchResult.matching_education?.description || matchResult.matching_education?.text || JSON.stringify(matchResult.matching_education))}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-xl font-semibold mb-4">Strengths</h3>
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
              <h3 className="text-xl font-semibold mb-4">Areas for Improvement</h3>
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
              Start Over
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Matching; 