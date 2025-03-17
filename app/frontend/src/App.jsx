import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Dashboard from './components/Dashboard';
import ResumeAnalysis from './components/ResumeAnalysis';
import JobAnalysis from './components/JobAnalysis';
import Matching from './components/Matching';
import NotFound from './components/NotFound';
import ApiStatus from './components/ApiStatus';
import ApiTest from './components/ApiTest';
import { LanguageProvider } from './contexts/LanguageContext';

const App = () => {
  // Detect system dark mode preference and apply class to html element
  useEffect(() => {
    // Check if the user prefers dark mode
    const prefersDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Apply dark mode class if preferred
    if (prefersDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }

    // Listen for changes in the user's preference
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e) => {
      if (e.matches) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    };

    // Add listener
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
    } else {
      // Fallback for older browsers
      mediaQuery.addListener(handleChange);
    }

    // Cleanup
    return () => {
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handleChange);
      } else {
        // Fallback for older browsers
        mediaQuery.removeListener(handleChange);
      }
    };
  }, []);

  return (
    <LanguageProvider>
      <BrowserRouter>
        <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-gray-900">
          <Navbar />
          <main className="flex-grow container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/resume" element={<ResumeAnalysis />} />
              <Route path="/job" element={<JobAnalysis />} />
              <Route path="/matching" element={<Matching />} />
              <Route path="/api-test" element={<ApiTest />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
          <Footer />
          <ApiStatus />
        </div>
      </BrowserRouter>
    </LanguageProvider>
  );
};

export default App; 