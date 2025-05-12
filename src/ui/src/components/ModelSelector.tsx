import React from 'react';
import { useModel } from '../contexts/ModelContext';
import { Cloud, Cpu } from 'lucide-react';

const ModelSelector: React.FC = () => {
  const { activeModel, setActiveModel } = useModel();

  return (
    <div className="glass-card p-4 rounded-xl">
      <h3 className="text-sm font-medium mb-3">AI Model</h3>
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={() => setActiveModel('gemma')}
          className={`flex flex-col items-center justify-center p-3 rounded-lg border-2 transition-all ${
            activeModel === 'gemma'
              ? 'border-primary bg-primary/10'
              : 'border-transparent hover:bg-white/5'
          }`}
        >
          <Cpu className={`w-6 h-6 mb-2 ${activeModel === 'gemma' ? 'text-primary' : 'text-muted-foreground'}`} />
          <span className={activeModel === 'gemma' ? 'text-primary font-medium' : 'text-muted-foreground'}>
            Gemma 3
          </span>
          <span className="text-xs text-muted-foreground mt-1">Local Model</span>
        </button>

        <button
          onClick={() => setActiveModel('gemini')}
          className={`flex flex-col items-center justify-center p-3 rounded-lg border-2 transition-all ${
            activeModel === 'gemini'
              ? 'border-primary bg-primary/10'
              : 'border-transparent hover:bg-white/5'
          }`}
        >
          <Cloud
            className={`w-6 h-6 mb-2 ${activeModel === 'gemini' ? 'text-primary' : 'text-muted-foreground'}`}
          />
          <span className={activeModel === 'gemini' ? 'text-primary font-medium' : 'text-muted-foreground'}>
            Gemini
          </span>
          <span className="text-xs text-muted-foreground mt-1">Cloud Model</span>
        </button>
      </div>
    </div>
  );
};

export default ModelSelector; 