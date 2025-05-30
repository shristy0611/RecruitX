
import React from 'react';
import { AnalysisProgressProps } from '../types';

const ProgressBar: React.FC<AnalysisProgressProps> = ({ progress }) => {
  const cappedProgress = Math.min(Math.max(progress, 0), 100); 

  return (
    <div className="w-full bg-neutral-700 rounded-full h-2.5 shadow-inner-dark my-2">
      <div 
        className="bg-gradient-to-r from-primary-light to-primary-DEFAULT h-2.5 rounded-full transition-all duration-300 ease-out shadow-sm" 
        style={{ width: `${cappedProgress}%` }}
        role="progressbar"
        aria-valuenow={cappedProgress}
        aria-valuemin={0}
        aria-valuemax={100}
      >
      </div>
    </div>
  );
};

export default ProgressBar;