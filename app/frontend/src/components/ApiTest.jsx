import { useState, useEffect } from 'react';
import recruitxApi from '../services/recruitxApi';
import apiTestDirectFetch from '../services/apiTestDirectFetch';
import FileUpload from './FileUpload';

const ApiTest = () => {
  const [testStatus, setTestStatus] = useState({
    loading: true,
    success: false,
    message: 'Testing API connection...',
    details: null
  });
  
  const [directFetchStatus, setDirectFetchStatus] = useState({
    loading: true,
    success: false,
    message: 'Testing direct fetch...',
    details: null
  });
  
  const [proxiedFetchStatus, setProxiedFetchStatus] = useState({
    loading: true,
    success: false,
    message: 'Testing proxied fetch...',
    details: null
  });
  
  const [uploadStatus, setUploadStatus] = useState({
    loading: false,
    success: false,
    message: 'Ready for upload test',
    details: null
  });

  useEffect(() => {
    const testConnections = async () => {
      // Test using recruitxApi (axios)
      try {
        setTestStatus({
          loading: true,
          success: false,
          message: 'Testing API connection with axios...',
          details: null
        });

        console.log('Testing health endpoint with axios...');
        const healthResponse = await recruitxApi.healthCheck();
        console.log('Axios health response:', healthResponse);

        setTestStatus({
          loading: false,
          success: true,
          message: 'API connection successful with axios!',
          details: { 
            health: healthResponse,
            testMode: healthResponse.testing_mode
          }
        });
      } catch (error) {
        console.error('Axios API test failed:', error);
        
        // More specific error messages based on error type
        let errorMessage = 'API connection failed with axios';
        if (error.code === 'ECONNABORTED') {
          errorMessage = 'API connection timed out - the server is taking too long to respond';
        } else if (error.message && error.message.includes('Network Error')) {
          errorMessage = 'Network error - check if the backend server is running';
        } else if (error.response && error.response.status) {
          errorMessage = `API returned error status: ${error.response.status} - ${error.response.statusText}`;
        }
        
        setTestStatus({
          loading: false,
          success: false,
          message: errorMessage,
          details: {
            error: error.message,
            stack: error.stack,
            response: error.response?.data
          }
        });
      }
      
      // Test direct fetch
      try {
        setDirectFetchStatus({
          loading: true,
          success: false,
          message: 'Testing direct fetch to backend...',
          details: null
        });
        
        const directResult = await apiTestDirectFetch.testDirectHealth();
        setDirectFetchStatus({
          loading: false,
          success: true,
          message: 'Direct fetch successful!',
          details: directResult
        });
      } catch (error) {
        console.error('Direct fetch test failed:', error);
        setDirectFetchStatus({
          loading: false,
          success: false,
          message: 'Direct fetch failed (possibly CORS)',
          details: {
            error: error.message
          }
        });
      }
      
      // Test proxied fetch
      try {
        setProxiedFetchStatus({
          loading: true,
          success: false,
          message: 'Testing proxied fetch to backend...',
          details: null
        });
        
        const proxiedResult = await apiTestDirectFetch.testProxiedHealth();
        setProxiedFetchStatus({
          loading: false,
          success: true,
          message: 'Proxied fetch successful!',
          details: proxiedResult
        });
      } catch (error) {
        console.error('Proxied fetch test failed:', error);
        setProxiedFetchStatus({
          loading: false,
          success: false,
          message: 'Proxied fetch failed',
          details: {
            error: error.message
          }
        });
      }
    };

    testConnections();
  }, []);
  
  const handleFileUpload = async (file) => {
    setUploadStatus({
      loading: true,
      success: false,
      message: 'Testing file upload...',
      details: null
    });
    
    try {
      // Try to upload a resume
      console.log('Testing resume upload with file:', file.name);
      const result = await recruitxApi.analyzeResume(file);
      
      setUploadStatus({
        loading: false,
        success: true,
        message: 'File upload successful!',
        details: result
      });
    } catch (error) {
      console.error('File upload test failed:', error);
      setUploadStatus({
        loading: false,
        success: false,
        message: 'File upload failed',
        details: {
          error: error.message,
          response: error.response?.data
        }
      });
    }
  };

  const renderTestResult = (status, title) => {
    return (
      <div className="card mb-4">
        <h2 className="text-xl font-semibold mb-4">{title}</h2>
        <div className={`p-3 rounded-lg mb-4 ${
          status.loading ? 'bg-yellow-50 text-yellow-700 border border-yellow-200' :
          status.success ? 'bg-green-50 text-green-700 border border-green-200' :
          'bg-red-50 text-red-700 border border-red-200'
        }`}>
          <p>
            {status.loading ? '⏳ ' : status.success ? '✅ ' : '❌ '}
            {status.message}
          </p>
        </div>
        
        {status.details && (
          <div className="mt-4 p-4 bg-gray-100 rounded-lg overflow-auto">
            <pre className="whitespace-pre-wrap">{JSON.stringify(status.details, null, 2)}</pre>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">API Connection Test</h1>
      
      {renderTestResult(testStatus, 'Axios API Connection Test')}
      {renderTestResult(directFetchStatus, 'Direct Fetch Test')}
      {renderTestResult(proxiedFetchStatus, 'Proxied Fetch Test')}
      
      <div className="card mb-4">
        <h2 className="text-xl font-semibold mb-4">File Upload Test</h2>
        <p className="mb-4">Upload a sample resume or job description file to test the file upload API:</p>
        
        <FileUpload onFileUpload={handleFileUpload} />
        
        {uploadStatus.loading && (
          <div className="p-3 bg-yellow-50 text-yellow-700 border border-yellow-200 rounded-lg">
            ⏳ Uploading and processing file...
          </div>
        )}
        
        {!uploadStatus.loading && uploadStatus.message !== 'Ready for upload test' && (
          <div className={`p-3 rounded-lg mt-4 ${
            uploadStatus.success ? 'bg-green-50 text-green-700 border border-green-200' : 
            'bg-red-50 text-red-700 border border-red-200'
          }`}>
            <p>
              {uploadStatus.success ? '✅ ' : '❌ '}
              {uploadStatus.message}
            </p>
          </div>
        )}
        
        {uploadStatus.details && (
          <div className="mt-4 p-4 bg-gray-100 rounded-lg overflow-auto">
            <pre className="whitespace-pre-wrap">{JSON.stringify(uploadStatus.details, null, 2)}</pre>
          </div>
        )}
      </div>
      
      <div className="card">
        <h3 className="font-semibold mb-2">Debug Information:</h3>
        <ul className="list-disc list-inside space-y-1">
          <li>Backend URL: <code className="bg-gray-100 px-1 rounded">http://localhost:8000</code></li>
          <li>Proxy Settings: <code className="bg-gray-100 px-1 rounded">/api → http://localhost:8000</code></li>
          <li>Testing Mode: <code className="bg-gray-100 px-1 rounded">{testStatus.details?.testMode ? 'Enabled' : 'Disabled'}</code></li>
          <li>Browser: <code className="bg-gray-100 px-1 rounded">{navigator.userAgent}</code></li>
        </ul>
      </div>
    </div>
  );
};

export default ApiTest; 