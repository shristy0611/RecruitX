import React from 'react';
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

const App = () => {
  return (
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
  );
};

export default App; 