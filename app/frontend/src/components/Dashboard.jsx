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
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-4 gradient-bg">
          {t('dashboard.title')}
        </h1>
        <p className="text-lg md:text-xl mb-8 max-w-3xl text-white opacity-90 gradient-bg">
          {t('dashboard.subtitle')}
        </p>
        <Link to="/matching" className="inline-block bg-white text-primary-600 font-medium px-6 py-3 rounded-lg hover:bg-gray-100 transition-colors duration-200 shadow-md">
          {language === 'ja' ? '始める' : 'Get Started'}
        </Link>
      </section>

      <section className="mb-12">
        <h2 className="text-2xl font-bold mb-8 text-center text-high-contrast">
          {language === 'ja' ? '使い方' : 'How It Works'}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="card hover:shadow-md transition-shadow duration-200 flex flex-col h-full">
              <div className="mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold mb-2 text-high-contrast">{feature.title}</h3>
              <p className="text-medium-contrast mb-4 flex-grow">{feature.description}</p>
              <Link 
                to={feature.link} 
                className="mt-auto inline-flex items-center justify-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors duration-200"
              >
                {feature.linkText}
              </Link>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl p-8 md:p-12 text-white mb-12">
        <h2 className="text-2xl md:text-3xl font-bold text-white mb-4 gradient-bg">
          {language === 'ja' ? 'RecruitXを選ぶ理由' : 'Why Choose RecruitX'}
        </h2>
        <ul className="space-y-4 text-white">
          <li className="flex items-start">
            <svg className="h-6 w-6 text-white mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="gradient-bg">{language === 'ja' ? '高度なAI技術で人間によるレビューと同等の分析結果' : 'Advanced AI technology providing human-level review results'}</span>
          </li>
          <li className="flex items-start">
            <svg className="h-6 w-6 text-white mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="gradient-bg">{language === 'ja' ? '履歴書と求人情報の正確なマッチング' : 'Accurate matching between resumes and job descriptions'}</span>
          </li>
          <li className="flex items-start">
            <svg className="h-6 w-6 text-white mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="gradient-bg">{language === 'ja' ? '主要ファイル形式（PDF、DOCX、TXT）のサポート' : 'Support for major file formats (PDF, DOCX, TXT)'}</span>
          </li>
          <li className="flex items-start">
            <svg className="h-6 w-6 text-white mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="gradient-bg">{language === 'ja' ? 'スキル比較とマッチングスコアによる客観的な評価' : 'Objective evaluation with skill comparison and matching scores'}</span>
          </li>
          <li className="flex items-start">
            <svg className="h-6 w-6 text-white mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="gradient-bg">{language === 'ja' ? 'ユーザーフレンドリーで直感的に操作できるインターフェース' : 'User-friendly and intuitive interface'}</span>
          </li>
        </ul>
      </section>
    </div>
  );
};

export default Dashboard; 