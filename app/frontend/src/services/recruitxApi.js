import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // Increase timeout to 60 seconds to accommodate Gemini API latency
});

// Add request interceptor for debugging
api.interceptors.request.use(
  config => {
    console.log(`Making ${config.method.toUpperCase()} request to ${config.url}`);
    return config;
  },
  error => {
    console.error('Request setup error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    console.error('API Error:', error);
    
    if (error.response) {
      // Server responded with a status code outside of 2xx range
      console.error('Response data:', error.response.data);
      console.error('Response status:', error.response.status);
      
      // Implement retry logic for timeouts and server errors
      if (error.response.status >= 500 && error.config && !error.config.__isRetryRequest) {
        console.log('Retrying request due to server error...');
        error.config.__isRetryRequest = true;
        return api(error.config);
      }
    } else if (error.request) {
      // Request was made but no response was received (likely timeout)
      console.error('No response received:', error.request);
      
      // Implement retry logic for timeouts
      if (error.code === 'ECONNABORTED' && error.config && !error.config.__isRetryRequest) {
        console.log('Retrying request due to timeout...');
        error.config.__isRetryRequest = true;
        error.config.timeout = 90000; // Increase timeout for retry attempt to 90 seconds
        return api(error.config);
      }
    } else {
      // Something happened in setting up the request
      console.error('Request setup error:', error.message);
    }
    return Promise.reject(error);
  }
);

// API methods
const recruitxApi = {
  /**
   * Upload and analyze a resume
   * @param {File} file - The resume file to analyze
   * @returns {Promise} - Promise with analysis results
   */
  analyzeResume: async (file) => {
    try {
      // Create a FormData object to send the file
      const formData = new FormData();
      formData.append('file', file);

      // Log the request
      console.log('Sending resume for analysis:', file.name);
      
      // Upload the file to the backend
      const response = await api.post('/analyze/resume', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Log the response
      console.log('Resume analysis response:', response.data);
      
      return response.data;
    } catch (error) {
      console.error('Resume analysis failed:', error);
      throw error;
    }
  },

  /**
   * Upload and analyze a job description
   * @param {File} file - The job description file to analyze
   * @returns {Promise} - Promise with analysis results
   */
  analyzeJob: async (file) => {
    try {
      // Create a FormData object to send the file
      const formData = new FormData();
      formData.append('file', file);

      // Log the request
      console.log('Sending job description for analysis:', file.name);
      
      // Upload the file to the backend
      const response = await api.post('/analyze/job', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Log the response
      console.log('Job analysis response:', response.data);
      
      return response.data;
    } catch (error) {
      console.error('Job analysis failed:', error);
      throw error;
    }
  },

  /**
   * Match resume data to job data
   * @param {Object} resumeData - Analyzed resume data
   * @param {Object} jobData - Analyzed job data
   * @returns {Promise} - Promise with matching results
   */
  matchResumeToJob: async (resumeData, jobData) => {
    try {
      // Log the request
      console.log('Sending match request', { 
        resumeSkills: resumeData.skills?.length || 0,
        jobSkills: jobData.required_skills?.length || 0 
      });
      
      // Send the matching request
      const response = await api.post('/match', {
        resume_data: resumeData,
        job_data: jobData,
      });

      // Log the response
      console.log('Match response:', response.data);
      
      return response.data;
    } catch (error) {
      console.error('Resume-job matching failed:', error);
      throw error;
    }
  },

  /**
   * Check if the API is available
   * @returns {Promise<boolean>} - Promise resolving to true if API is available
   */
  healthCheck: async () => {
    try {
      const response = await api.get('/health');
      console.log('Health check response:', response.data);
      return response.data.status === 'ok';
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
};

export default recruitxApi; 