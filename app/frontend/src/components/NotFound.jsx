import { Link } from 'react-router-dom';
import { FiAlertTriangle } from 'react-icons/fi';

const NotFound = () => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <FiAlertTriangle className="h-20 w-20 text-yellow-500 mb-6" />
      <h1 className="text-4xl font-bold mb-4">Page Not Found</h1>
      <p className="text-xl text-gray-600 mb-8 max-w-lg">
        The page you are looking for doesn't exist or has been moved.
      </p>
      <Link
        to="/"
        className="btn btn-primary"
      >
        Return to Dashboard
      </Link>
    </div>
  );
};

export default NotFound; 