
import React from 'react';
import { Language } from '../types';
import { useLocalization } from '../hooks/useLocalization';

const LanguageSwitcher: React.FC = () => {
  const { language, setLanguage } = useLocalization();

  const toggleLanguage = () => {
    setLanguage(language === Language.EN ? Language.JA : Language.EN);
  };

  return (
    <button
      onClick={toggleLanguage}
      className="px-4 py-2 bg-neutral-700 hover:bg-neutral-600 text-neutral-200 rounded-lg transition-colors duration-200 ease-in-out shadow-md hover:shadow-lg-dark focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-opacity-75 flex items-center subtle-hover-lift"
      aria-label={language === Language.EN ? "Switch to Japanese" : "Switch to English"}
    >
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 mr-2 opacity-80">
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 21l5.25-11.25L21 21m-9-3h7.5M3 5.621a48.474 48.474 0 016-.371m0 0c1.12 0 2.233.038 3.334.114M9 5.25V3m3.334 2.364C11.176 10.658 7.69 15.08 3 17.502m9.084-12.138c.386.058.772.128 1.158.205m3.454-3.454a.75.75 0 00-1.06-1.06l-3.45 3.454a.75.75 0 001.06 1.06l3.45-3.45z" />
      </svg>
      {language === Language.EN ? '日本語' : 'English'}
    </button>
  );
};

export default LanguageSwitcher;