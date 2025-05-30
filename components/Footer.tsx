
import React from 'react';
import { useLocalization } from '../hooks/useLocalization';

const Footer: React.FC = () => {
  const { t } = useLocalization();
  return (
    <footer className="bg-neutral-900 text-neutral-500 text-center p-8 mt-16 border-t border-neutral-800">
      <p className="text-sm">{t('footerText')}</p>
      <p className="text-xs mt-1 opacity-70">{t('tagline')}</p>
    </footer>
  );
};

export default Footer;