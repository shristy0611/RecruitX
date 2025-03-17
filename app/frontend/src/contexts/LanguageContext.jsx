import React, { createContext, useContext, useState, useEffect } from 'react';

// Define available languages
export const LANGUAGES = {
  EN: 'en',
  JA: 'ja',
};

// Translation object with English and Japanese strings
const translations = {
  en: {
    // Navbar
    'navbar.dashboard': 'Dashboard',
    'navbar.resume': 'Resume Analysis',
    'navbar.job': 'Job Analysis',
    'navbar.matching': 'Matching',
    'navbar.api': 'API Test',
    
    // Dashboard
    'dashboard.title': 'AI-Powered Recruitment Matching',
    'dashboard.subtitle': 'RecruitX leverages cutting-edge AI to transform your recruitment process. Analyze resumes, job descriptions, and find the perfect match with precision.',
    'dashboard.resumeCard': 'Resume Analysis',
    'dashboard.resumeDescription': 'Upload and analyze resumes to extract key skills, experience, and qualifications.',
    'dashboard.jobCard': 'Job Description Analysis',
    'dashboard.jobDescription': 'Extract required skills, responsibilities, and qualifications from job descriptions.',
    'dashboard.matchingCard': 'Resume-Job Matching',
    'dashboard.matchingDescription': 'Match resumes against job descriptions to find the perfect candidate.',
    
    // Resume Analysis
    'resume.title': 'Resume Analysis',
    'resume.upload': 'Upload Resume',
    'resume.analyzing': 'Analyzing resume...',
    'resume.complete': 'Analysis Complete',
    'resume.success': 'Resume successfully analyzed.',
    'resume.results': 'Analysis Results',
    'resume.skills': 'Skills',
    'resume.experience': 'Experience',
    'resume.education': 'Education',
    'resume.achievements': 'Achievements',
    'resume.noItems': 'No items found',
    'resume.error': 'Error analyzing resume',
    
    // Job Analysis
    'job.title': 'Job Analysis',
    'job.upload': 'Upload Job Description',
    'job.analyzing': 'Analyzing job description...',
    'job.complete': 'Analysis Complete',
    'job.success': 'Job description successfully analyzed.',
    'job.results': 'Analysis Results',
    'job.requiredSkills': 'Required Skills',
    'job.preferredSkills': 'Preferred Skills',
    'job.responsibilities': 'Responsibilities',
    'job.qualifications': 'Qualifications',
    'job.companyInfo': 'Company Information',
    'job.noItems': 'No items found',
    'job.error': 'Error analyzing job description',
    
    // Matching
    'matching.title': 'Resume-Job Matching',
    'matching.uploadFiles': 'Upload Files',
    'matching.analysis': 'Analysis',
    'matching.results': 'Results',
    'matching.processing': 'Processing...',
    'matching.uploadResume': 'Upload Resume',
    'matching.uploadJob': 'Upload Job Description',
    'matching.resumeAnalysis': 'Resume Analysis',
    'matching.jobAnalysis': 'Job Analysis',
    'matching.continue': 'Continue',
    'matching.back': 'Back',
    'matching.match': 'Match Resume to Job',
    'matching.matchResults': 'Match Results',
    'matching.matchScore': 'Match Score',
    'matching.explanation': 'Explanation',
    'matching.matchingSkills': 'Matching Skills',
    'matching.missingSkills': 'Missing Skills',
    'matching.recommendations': 'Recommendations',
    'matching.experienceMatch': 'Experience Match',
    'matching.educationMatch': 'Education Match',
    'matching.strengths': 'Strengths',
    'matching.improvements': 'Areas for Improvement',
    'matching.startOver': 'Start Over',
    
    // Common
    'common.error': 'An error occurred',
    'common.tryAgain': 'Please try again',
    'common.loading': 'Loading...',
    'common.noData': 'No data available',
    'common.entries': 'entries',
    'common.entriesJa': 'entries',
  },
  ja: {
    // Navbar
    'navbar.dashboard': 'ダッシュボード',
    'navbar.resume': '履歴書分析',
    'navbar.job': '求人分析',
    'navbar.matching': 'マッチング',
    'navbar.api': 'APIテスト',
    
    // Dashboard
    'dashboard.title': 'AI搭載の採用マッチングシステム',
    'dashboard.subtitle': 'RecruitXは最先端のAIを活用して採用プロセスを変革します。履歴書や求人情報を分析し、精度の高いマッチングを実現します。',
    'dashboard.resumeCard': '履歴書分析',
    'dashboard.resumeDescription': '履歴書をアップロードして、主要なスキル、経験、資格を抽出・分析します。',
    'dashboard.jobCard': '求人情報分析',
    'dashboard.jobDescription': '求人情報から必要なスキル、責任、資格要件を抽出します。',
    'dashboard.matchingCard': '履歴書-求人マッチング',
    'dashboard.matchingDescription': '履歴書と求人情報を照合し、最適な候補者を見つけます。',
    
    // Resume Analysis
    'resume.title': '履歴書分析',
    'resume.upload': '履歴書をアップロード',
    'resume.analyzing': '履歴書を分析中...',
    'resume.complete': '分析完了',
    'resume.success': '履歴書の分析が完了しました。',
    'resume.results': '分析結果',
    'resume.skills': 'スキル',
    'resume.experience': '経験',
    'resume.education': '学歴',
    'resume.achievements': '実績',
    'resume.noItems': '項目が見つかりません',
    'resume.error': '履歴書の分析中にエラーが発生しました',
    
    // Job Analysis
    'job.title': '求人分析',
    'job.upload': '求人情報をアップロード',
    'job.analyzing': '求人情報を分析中...',
    'job.complete': '分析完了',
    'job.success': '求人情報の分析が完了しました。',
    'job.results': '分析結果',
    'job.requiredSkills': '必須スキル',
    'job.preferredSkills': '歓迎スキル',
    'job.responsibilities': '職務内容',
    'job.qualifications': '資格要件',
    'job.companyInfo': '企業情報',
    'job.noItems': '項目が見つかりません',
    'job.error': '求人情報の分析中にエラーが発生しました',
    
    // Matching
    'matching.title': '履歴書-求人マッチング',
    'matching.uploadFiles': 'ファイルをアップロード',
    'matching.analysis': '分析',
    'matching.results': '結果',
    'matching.processing': '処理中...',
    'matching.uploadResume': '履歴書をアップロード',
    'matching.uploadJob': '求人情報をアップロード',
    'matching.resumeAnalysis': '履歴書分析',
    'matching.jobAnalysis': '求人分析',
    'matching.continue': '続ける',
    'matching.back': '戻る',
    'matching.match': '履歴書と求人をマッチング',
    'matching.matchResults': 'マッチング結果',
    'matching.matchScore': 'マッチングスコア',
    'matching.explanation': '説明',
    'matching.matchingSkills': 'マッチするスキル',
    'matching.missingSkills': '不足しているスキル',
    'matching.recommendations': '推奨事項',
    'matching.experienceMatch': '経験のマッチ',
    'matching.educationMatch': '学歴のマッチ',
    'matching.strengths': '強み',
    'matching.improvements': '改善点',
    'matching.startOver': '最初からやり直す',
    
    // Common
    'common.error': 'エラーが発生しました',
    'common.tryAgain': 'もう一度お試しください',
    'common.loading': '読み込み中...',
    'common.noData': 'データがありません',
    'common.entries': 'エントリー',
    'common.entriesJa': 'エントリー',
  }
};

// Create context
const LanguageContext = createContext();

// Language provider component
export const LanguageProvider = ({ children }) => {
  // Get saved language from localStorage or default to 'en'
  const [language, setLanguage] = useState(() => {
    const savedLanguage = localStorage.getItem('language');
    return savedLanguage || 'en';
  });

  // Update localStorage when language changes
  useEffect(() => {
    localStorage.setItem('language', language);
  }, [language]);

  // Toggle language between 'en' and 'ja'
  const toggleLanguage = () => {
    setLanguage(prevLanguage => prevLanguage === 'en' ? 'ja' : 'en');
  };

  // Translation function
  const t = (key) => {
    return translations[language][key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

// Custom hook to use the language context
export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

export default LanguageContext; 