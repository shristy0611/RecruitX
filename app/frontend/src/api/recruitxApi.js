import axios from 'axios';

const BASE_URL = '/api';

const recruitxApi = {
  /**
   * Upload and analyze a resume
   * @param {File} file - The resume file to analyze
   * @returns {Promise} - Promise with the analysis results
   */
  analyzeResume: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post(`${BASE_URL}/analyze/resume`, formData, {
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
   * @returns {Promise} - Promise with the analysis results
   */
  analyzeJob: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post(`${BASE_URL}/analyze/job`, formData, {
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
   * @returns {Promise} - Promise with the matching results
   */
  matchResumeToJob: async (resumeData, jobData) => {
    try {
      const response = await axios.post(`${BASE_URL}/match`, {
        resume_data: resumeData,
        job_data: jobData
      });
      return response.data;
    } catch (error) {
      console.error('Error matching resume to job:', error);
      throw error;
    }
  }
};

export default recruitxApi; 