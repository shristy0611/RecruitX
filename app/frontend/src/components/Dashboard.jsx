import { Link } from 'react-router-dom';
import { FiFileText, FiBriefcase, FiUsers } from 'react-icons/fi';

const Dashboard = () => {
  const features = [
    {
      icon: <FiFileText className="h-10 w-10 text-primary-500" />,
      title: 'Resume Analysis',
      description: 'Upload and analyze resumes to extract key skills, experience, and qualifications.',
      link: '/resume',
      linkText: 'Analyze Resume',
    },
    {
      icon: <FiBriefcase className="h-10 w-10 text-primary-500" />,
      title: 'Job Description Analysis',
      description: 'Extract required skills, responsibilities, and qualifications from job descriptions.',
      link: '/job',
      linkText: 'Analyze Job',
    },
    {
      icon: <FiUsers className="h-10 w-10 text-primary-500" />,
      title: 'Resume-Job Matching',
      description: 'Match resumes against job descriptions to find the perfect candidate.',
      link: '/matching',
      linkText: 'Start Matching',
    },
  ];

  return (
    <div className="max-w-5xl mx-auto">
      <section className="bg-gradient-to-r from-primary-500 to-secondary-500 rounded-2xl p-8 md:p-12 text-white mb-12">
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
          AI-Powered Recruitment Matching
        </h1>
        <p className="text-lg md:text-xl mb-8 max-w-3xl text-white opacity-90">
          RecruitX leverages cutting-edge AI to transform your recruitment process.
          Analyze resumes, job descriptions, and find the perfect match with precision.
        </p>
        <Link to="/matching" className="inline-block bg-white text-primary-600 font-medium px-6 py-3 rounded-lg hover:bg-gray-100 transition-colors duration-200">
          Get Started
        </Link>
      </section>

      <section className="mb-12">
        <h2 className="text-2xl font-bold mb-8 text-center">How It Works</h2>
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
          <h2 className="text-2xl font-bold mb-4">Why Choose RecruitX?</h2>
          <ul className="space-y-3">
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Advanced AI-powered analysis using state-of-the-art language models</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Precise matching between resumes and job descriptions</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Support for multiple file formats (PDF, DOCX, TXT)</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Detailed analysis with skills extraction and matching scores</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Modern, intuitive interface for a seamless user experience</span>
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
};

export default Dashboard; 