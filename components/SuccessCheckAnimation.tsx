
import React from 'react';

const SuccessCheckAnimation: React.FC = () => {
  return (
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-neutral-900/70 backdrop-blur-sm animate-fade-in-out-scale"
      aria-hidden="true" // Decorative, main feedback is via infoMessage
    >
      <div className="w-24 h-24 sm:w-32 sm:h-32 p-2">
        <svg viewBox="0 0 52 52" className="w-full h-full">
          <circle 
            className="text-success-DEFAULT/30" 
            cx="26" 
            cy="26" 
            r="24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="3"
          />
          <path 
            className="text-success-DEFAULT animate-checkmark-draw" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="5" 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeDasharray="48" // Approximate length of the checkmark path
            strokeDashoffset="48" // Start with the path hidden
            d="M14 27l7.688 7.688L38 19" 
          />
        </svg>
      </div>
    </div>
  );
};

export default SuccessCheckAnimation;
