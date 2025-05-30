
import React from 'react';
import { useLocalization } from '../hooks/useLocalization';

interface ErrorAlertProps {
  message: string;
  onClose?: () => void;
}

const ErrorAlert: React.FC<ErrorAlertProps> = ({ message, onClose }) => {
  const { t } = useLocalization();
  return (
    <div className="bg-danger-DEFAULT/10 border-l-4 border-danger-DEFAULT text-danger-text p-4 my-4 rounded-md shadow-md-dark" role="alert">
      <div className="flex">
        <div className="py-1">
          <svg className="fill-current h-6 w-6 text-danger-DEFAULT mr-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
            <path d="M2.93 17.07A10 10 0 1 1 17.07 2.93 10 10 0 0 1 2.93 17.07zM10 16a6 6 0 1 0 0-12 6 6 0 0 0 0 12zm0-3a1 1 0 1 1 0-2 1 1 0 0 1 0 2zm0-4a1 1 0 0 1-1-1V6a1 1 0 1 1 2 0v2a1 1 0 0 1-1 1z"/>
          </svg>
        </div>
        <div>
          <p className="font-bold text-neutral-100">{t('errorTitle')}</p>
          <p className="text-sm text-danger-text">{message}</p>
        </div>
        {onClose && (
          <button 
            onClick={onClose} 
            className="ml-auto text-neutral-400 hover:text-neutral-200 p-1 rounded-md hover:bg-danger-DEFAULT/30 transition-colors"
            aria-label="Close error alert"
          >
            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorAlert;