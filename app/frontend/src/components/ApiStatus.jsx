import { useEffect, useState } from 'react';
import recruitxApi from '../services/recruitxApi';
import { FiCheckCircle, FiAlertCircle } from 'react-icons/fi';

const ApiStatus = () => {
  const [status, setStatus] = useState({
    isChecking: true,
    isConnected: false,
    testMode: false,
    error: null
  });

  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        setStatus(prev => ({ ...prev, isChecking: true }));
        const response = await recruitxApi.healthCheck();
        setStatus({
          isChecking: false,
          isConnected: true,
          testMode: response.testing_mode,
          error: null
        });
      } catch (error) {
        console.error('API status check failed:', error);
        setStatus({
          isChecking: false,
          isConnected: false,
          testMode: false,
          error: error.message || 'Could not connect to API'
        });
      }
    };

    checkApiStatus();
    // Check every 30 seconds
    const interval = setInterval(checkApiStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3 flex items-center gap-2 border border-gray-200 dark:border-gray-700">
        {status.isChecking ? (
          <>
            <div className="animate-pulse w-3 h-3 rounded-full bg-yellow-400"></div>
            <span className="text-sm text-gray-600 dark:text-gray-300">Checking API...</span>
          </>
        ) : status.isConnected ? (
          <>
            <FiCheckCircle className="text-green-500" />
            <span className="text-sm text-gray-700 dark:text-gray-200">
              API Connected 
              {status.testMode && <span className="ml-1 text-xs text-blue-500">(Test Mode)</span>}
            </span>
          </>
        ) : (
          <>
            <FiAlertCircle className="text-red-500" />
            <span className="text-sm text-gray-700 dark:text-gray-200">API Disconnected</span>
            {status.error && (
              <span className="text-xs text-red-500 ml-1">{status.error}</span>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ApiStatus; 