import axios from 'axios';

const BASE_URL = '/api';

const recruitxApi = {
  /**
   * Upload and analyze a resume
   * @param {File} file - The resume file to analyze
   * @param {String} language - The language for the analysis (en, ja, or auto)
   * @returns {Promise} - Promise with the analysis results
   */
  analyzeResume: async (file, language = 'en') => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post(`${BASE_URL}/analyze/resume?language=${language}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing resume:', error);
      throw error;
    }
  },

  /**
   * Upload and analyze a job description
   * @param {File} file - The job description file to analyze
   * @param {String} language - The language for the analysis (en, ja, or auto)
   * @returns {Promise} - Promise with the analysis results
   */
  analyzeJob: async (file, language = 'en') => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post(`${BASE_URL}/analyze/job?language=${language}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing job description:', error);
      throw error;
    }
  },

  /**
   * Match a resume against a job description
   * @param {Object} resumeData - Resume data from analysis
   * @param {Object} jobData - Job description data from analysis
   * @param {String} language - The language for the matching analysis (en, ja)
   * @returns {Promise} - Promise with the matching results
   */
  matchResumeToJob: async (resumeData, jobData, language = 'en') => {
    try {
      const response = await axios.post(`${BASE_URL}/match`, {
        resume_data: resumeData,
        job_data: jobData,
        language: language
      });
      return response.data;
    } catch (error) {
      console.error('Error matching resume to job:', error);
      throw error;
    }
  },
  
  /**
   * Check the health/status of the API
   * @returns {Promise} - Promise with the health status
   */
  checkHealth: async () => {
    try {
      const response = await axios.get(`${BASE_URL}/health`);
      return response.data;
    } catch (error) {
      console.error('Error checking API health:', error);
      throw error;
    }
  }
};

export default recruitxApi; 