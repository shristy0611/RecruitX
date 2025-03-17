import { Link } from 'react-router-dom';
import { FiFileText, FiBriefcase, FiUsers } from 'react-icons/fi';
import { useLanguage } from '../contexts/LanguageContext';

const Dashboard = () => {
  const { t, language } = useLanguage();
  
  const features = [
    {
      icon: <FiFileText className="h-10 w-10 text-primary-500" />,
      title: t('dashboard.resumeCard'),
      description: t('dashboard.resumeDescription'),
      link: '/resume',
      linkText: language === 'ja' ? '履歴書を分析' : 'Analyze Resume',
    },
    {
      icon: <FiBriefcase className="h-10 w-10 text-primary-500" />,
      title: t('dashboard.jobCard'),
      description: t('dashboard.jobDescription'),
      link: '/job',
      linkText: language === 'ja' ? '求人を分析' : 'Analyze Job',
    },
    {
      icon: <FiUsers className="h-10 w-10 text-primary-500" />,
      title: t('dashboard.matchingCard'),
      description: t('dashboard.matchingDescription'),
      link: '/matching',
      linkText: language === 'ja' ? 'マッチングを開始' : 'Start Matching',
    },
  ];

  return (
    <div className="max-w-5xl mx-auto">
      <section className="bg-gradient-to-r from-primary-500 to-secondary-500 rounded-2xl p-8 md:p-12 text-white mb-12">
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
          {t('dashboard.title')}
        </h1>
        <p className="text-lg md:text-xl mb-8 max-w-3xl text-white opacity-90">
          {t('dashboard.subtitle')}
        </p>
        <Link to="/matching" className="inline-block bg-white text-primary-600 font-medium px-6 py-3 rounded-lg hover:bg-gray-100 transition-colors duration-200">
          {language === 'ja' ? '始める' : 'Get Started'}
        </Link>
      </section>

      <section className="mb-12">
        <h2 className="text-2xl font-bold mb-8 text-center">
          {language === 'ja' ? '使い方' : 'How It Works'}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="card flex flex-col items-center text-center">
              <div className="mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-gray-600 mb-6">{feature.description}</p>
              <Link
                to={feature.link}
                className="mt-auto btn btn-primary"
              >
                {feature.linkText}
              </Link>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-12">
        <div className="card">
          <h2 className="text-2xl font-bold mb-4">
            {language === 'ja' ? 'RecruitXを選ぶ理由' : 'Why Choose RecruitX?'}
          </h2>
          <ul className="space-y-3">
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>
                {language === 'ja' 
                  ? '最先端の言語モデルを使用した高度なAI分析' 
                  : 'Advanced AI-powered analysis using state-of-the-art language models'}
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>
                {language === 'ja' 
                  ? '履歴書と求人情報の正確なマッチング' 
                  : 'Precise matching between resumes and job descriptions'}
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>
                {language === 'ja' 
                  ? '複数のファイル形式（PDF、DOCX、TXT）のサポート' 
                  : 'Support for multiple file formats (PDF, DOCX, TXT)'}
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>
                {language === 'ja' 
                  ? 'スキル抽出とマッチングスコアによる詳細な分析' 
                  : 'Detailed analysis with skills extraction and matching scores'}
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>
                {language === 'ja' 
                  ? 'シームレスなユーザー体験のためのモダンで直感的なインターフェース' 
                  : 'Modern, intuitive interface for a seamless user experience'}
              </span>
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
};

export default Dashboard; 