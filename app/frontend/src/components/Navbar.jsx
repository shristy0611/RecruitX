import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { FiMenu, FiX } from 'react-icons/fi';
import LanguageSwitcher from './LanguageSwitcher';
import { useLanguage } from '../contexts/LanguageContext';

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { t } = useLanguage();

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  const navLinks = [
    { to: '/', label: t('navbar.dashboard') },
    { to: '/resume', label: t('navbar.resume') },
    { to: '/job', label: t('navbar.job') },
    { to: '/matching', label: t('navbar.matching') },
    { to: '/api-test', label: t('navbar.api') },
  ];

  return (
    <nav className="bg-white shadow-sm sticky top-0 z-10">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-primary-600 font-bold text-2xl">RecruitX</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  isActive
                    ? 'text-primary-600 font-medium'
                    : 'text-gray-600 hover:text-primary-500 transition-colors duration-200'
                }
              >
                {link.label}
              </NavLink>
            ))}
            <LanguageSwitcher />
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center space-x-4">
            <LanguageSwitcher />
            <button
              type="button"
              className="text-gray-600 hover:text-primary-500 focus:outline-none"
              onClick={toggleMenu}
            >
              {isMenuOpen ? (
                <FiX className="h-6 w-6" />
              ) : (
                <FiMenu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden py-2 space-y-2">
            {navLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `block py-2 px-4 rounded-md ${
                    isActive
                      ? 'bg-primary-50 text-primary-600 font-medium'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`
                }
                onClick={closeMenu}
              >
                {link.label}
              </NavLink>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar; 