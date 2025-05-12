import React from 'react';
import { MessageSquare, Loader2 } from 'lucide-react';
import { useModel } from '../contexts/ModelContext';
import { apiService } from '../services/api';

const EngagementAgentUI: React.FC = () => {
  const { activeModel, isModelLoading, setIsModelLoading } = useModel();
  const [candidateId, setCandidateId] = React.useState('');
  const [message, setMessage] = React.useState('');
  const [error, setError] = React.useState<string | null>(null);

  const handleEngage = async () => {
    if (!candidateId || !message) return;
    setIsModelLoading(true);
    setError(null);
    try {
      const response = await apiService.engageCandidate({ candidateId, message, model: activeModel });
      setMessage(''); // Clear message after sending
      alert('Engagement sent successfully!');
    } catch (err) {
      setError('Engagement failed. Please try again.');
    } finally {
      setIsModelLoading(false);
    }
  };

  return (
    <div className="glass-card p-6 rounded-xl">
      <h3 className="text-lg font-medium mb-4">Engagement Agent</h3>
      <input
        type="text"
        value={candidateId}
        onChange={(e) => setCandidateId(e.target.value)}
        placeholder="Enter Candidate ID"
        className="border p-2 mb-4 w-full"
      />
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Enter engagement message"
        className="border p-2 mb-4 w-full"
      />
      <button onClick={handleEngage} disabled={isModelLoading} className="bg-purple-500 text-white p-2 rounded">
        {isModelLoading ? <Loader2 className="animate-spin" /> : 'Send Engagement'}
      </button>
      {error && <p className="text-red-500 mt-2">{error}</p>}
    </div>
  );
};

export default EngagementAgentUI;
