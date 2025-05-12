import React, { createContext, useContext, useState, ReactNode } from 'react';
import { ModelProvider as ModelType } from '../services/api';

interface ModelContextType {
  activeModel: ModelType;
  setActiveModel: (model: ModelType) => void;
  isModelLoading: boolean;
  setIsModelLoading: (loading: boolean) => void;
}

const ModelContext = createContext<ModelContextType | undefined>(undefined);

export const ModelContextProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [activeModel, setActiveModel] = useState<ModelType>('gemma');
  const [isModelLoading, setIsModelLoading] = useState(false);

  return (
    <ModelContext.Provider
      value={{
        activeModel,
        setActiveModel,
        isModelLoading,
        setIsModelLoading,
      }}
    >
      {children}
    </ModelContext.Provider>
  );
};

export const useModel = (): ModelContextType => {
  const context = useContext(ModelContext);
  if (context === undefined) {
    throw new Error('useModel must be used within a ModelContextProvider');
  }
  return context;
}; 