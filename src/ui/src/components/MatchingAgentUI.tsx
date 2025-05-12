import React from 'react';
import { Target, Loader2 } from 'lucide-react';
import { useModel } from '../contexts/ModelContext';
import { apiService } from '../services/api';

const MatchingAgentUI: React.FC = () => {
  const { activeModel, isModelLoading, setIsModelLoading } = useModel();
  const [jobId, setJobId] = React.useState('');
  const [matches, setMatches] = React.useState<any[]>([]);
  const [error, setError] = React.useState<string | null>(null);

  const handleMatch = async () => {
    if (!jobId) return;
    setIsModelLoading(true);
    setError(null);
    try {
      const response = await apiService.matchCandidates({ jobId, model: activeModel });
      setMatches(response.matches || []);
    } catch (err) {
      setError('Matching failed. Please try again.');
    } finally {
      setIsModelLoading(false);
    }
  };

  return (
    <div className="glass-card p-6 rounded-xl">
      <h3 className="text-lg font-medium mb-4">Matching Agent</h3>
      <input
        type="text"
        value={jobId}
        onChange={(e) => setJobId(e.target.value)}
        placeholder="Enter Job ID"
        className="border p-2 mb-4 w-full"
      />
      <button onClick={handleMatch} disabled={isModelLoading} className="bg-green-500 text-white p-2 rounded">
        {isModelLoading ? <Loader2 className="animate-spin" /> : 'Match Candidates'}
      </button>
      {error && <p className="text-red-500 mt-2">{error}</p>}
      <div className="mt-4">
        {matches.map((match, index) => (
          <div key={index} className="border p-2 mb-2">Candidate: {match.name}, Score: {match.score}</div>
        ))}
      </div>
    </div>
  );
};

export default MatchingAgentUI;
