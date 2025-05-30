
import React from 'react';
import LanguageSwitcher from './LanguageSwitcher';
import { useLocalization } from '../hooks/useLocalization';

const Header: React.FC = () => {
  const { t } = useLocalization();
  return (
    <header className="bg-neutral-900/70 backdrop-blur-lg text-neutral-100 p-4 shadow-xl-dark sticky top-0 z-50 h-[80px] flex items-center border-b border-neutral-800">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center">
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
              <span className="text-gradient-animated bg-gradient-to-r from-primary-light via-primary-DEFAULT to-primary-dark">{t('appName')}</span>
            </h1>
            <p className="text-xs sm:text-sm text-neutral-400 tracking-wide mt-0.5">{t('tagline')}</p>
          </div>
        </div>
        <LanguageSwitcher />
      </div>
    </header>
  );
};

export default Header;
