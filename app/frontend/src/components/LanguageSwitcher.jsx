import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';

const LanguageSwitcher = () => {
  const { language, toggleLanguage } = useLanguage();

  return (
    <div className="flex items-center space-x-2">
      <button
        onClick={toggleLanguage}
        className="flex items-center px-2 py-1 text-sm rounded-md hover:bg-gray-100 transition-colors duration-200"
        aria-label="Switch language"
      >
        <span className={`mr-1 ${language === 'en' ? 'font-bold text-primary-600' : 'text-gray-500'}`}>EN</span>
        <span>|</span>
        <span className={`ml-1 ${language === 'ja' ? 'font-bold text-primary-600' : 'text-gray-500'}`}>JP</span>
      </button>
    </div>
  );
};

export default LanguageSwitcher; 