import React from 'react';
import { Search, Loader2 } from 'lucide-react';
import { useModel } from '../contexts/ModelContext';
import { apiService } from '../services/api';

const SourcingAgentUI: React.FC = () => {
  const { activeModel, isModelLoading, setIsModelLoading } = useModel();
  const [query, setQuery] = React.useState('');
  const [results, setResults] = React.useState<any[]>([]);
  const [error, setError] = React.useState<string | null>(null);

  const handleSearch = async () => {
    if (!query) return;
    setIsModelLoading(true);
    setError(null);
    try {
      const response = await apiService.sourcingSearch({ query, model: activeModel });
      setResults(response.results || []);
    } catch (err) {
      setError('Search failed. Please try again.');
    } finally {
      setIsModelLoading(false);
    }
  };

  return (
    <div className="glass-card p-6 rounded-xl">
      <h3 className="text-lg font-medium mb-4">Sourcing Agent</h3>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter sourcing query"
        className="border p-2 mb-4 w-full"
      />
      <button onClick={handleSearch} disabled={isModelLoading} className="bg-blue-500 text-white p-2 rounded">
        {isModelLoading ? <Loader2 className="animate-spin" /> : 'Search'}
      </button>
      {error && <p className="text-red-500 mt-2">{error}</p>}
      <div className="mt-4">
        {results.map((result, index) => (
          <div key={index} className="border p-2 mb-2">{result.name}</div>
        ))}
      </div>
    </div>
  );
};

export default SourcingAgentUI;
