
// FIX: Import React for React.createElement and other React functionalities
import React, { useState, useCallback, createContext, useContext, ReactNode } from 'react';
import { Language } from '../types';
import { TRANSLATIONS, DEFAULT_LANGUAGE } from '../constants';

interface LocalizationContextType {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: string) => string;
}

const LocalizationContext = createContext<LocalizationContextType | undefined>(undefined);

export const LocalizationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<Language>(DEFAULT_LANGUAGE);

  const t = useCallback((key: string): string => {
    return TRANSLATIONS[language][key] || TRANSLATIONS[DEFAULT_LANGUAGE][key] || key;
  }, [language]);

  // FIX: Use React.createElement instead of JSX syntax.
  // This is necessary because this is a .ts file, not a .tsx file,
  // and JSX syntax <LocalizationContext.Provider ...> would be misinterpreted
  // leading to parsing errors (e.g., "<" treated as comparison operator).
  return React.createElement(
    LocalizationContext.Provider,
    { value: { language, setLanguage, t } },
    children
  );
};

export const useLocalization = (): LocalizationContextType => {
  const context = useContext(LocalizationContext);
  if (!context) {
    throw new Error('useLocalization must be used within a LocalizationProvider');
  }
  return context;
};
