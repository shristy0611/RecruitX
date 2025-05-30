import React, { useState, useEffect, type FC } from 'react';
import { AppSettings, AssessmentDimensionSetting } from '../types';
import { useLocalization } from '../hooks/useLocalization';
import { DEFAULT_ASSESSMENT_DIMENSIONS, DEFAULT_NEXUS_RANKING_SCORE_THRESHOLD } from '../constants'; // For reset

interface SettingsViewProps {
  currentSettings: AppSettings;
  onSaveSettings: (newSettings: AppSettings) => void;
  onResetSettings: () => void;
}

const SettingsView: React.FC<SettingsViewProps> = ({ currentSettings, onSaveSettings, onResetSettings }) => {
  const { t } = useLocalization();
  const [dimensions, setDimensions] = useState<AssessmentDimensionSetting[]>([]);
  const [nexusRankingScoreThreshold, setNexusRankingScoreThreshold] = useState<number>(currentSettings.nexusRankingScoreThreshold);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initialDimensions: AssessmentDimensionSetting[] = (currentSettings.assessmentDimensions && currentSettings.assessmentDimensions.length > 0)
      ? JSON.parse(JSON.stringify(currentSettings.assessmentDimensions))
      : JSON.parse(JSON.stringify(DEFAULT_ASSESSMENT_DIMENSIONS));

    const synchronizedDimensions: AssessmentDimensionSetting[] = DEFAULT_ASSESSMENT_DIMENSIONS.map((defaultDim) => {
        const userModifiedDim = initialDimensions.find((d: AssessmentDimensionSetting) => d.id === defaultDim.id);
        if (userModifiedDim) {
            return {
                ...defaultDim, 
                promptGuidance: userModifiedDim.promptGuidance, 
                isActive: userModifiedDim.isActive, 
            };
        }
        return defaultDim;
    });

    setDimensions(synchronizedDimensions);
    setNexusRankingScoreThreshold(currentSettings.nexusRankingScoreThreshold);
  }, [currentSettings]);

  const handleDimensionChange = (index: number, key: keyof AssessmentDimensionSetting, value: any) => {
    const newDimensions = [...dimensions];
    if (key === 'isActive' && typeof value === 'boolean') {
        const activeCount = newDimensions.filter((dim: AssessmentDimensionSetting) => dim.isActive).length;
        if (activeCount === 1 && newDimensions[index].isActive && !value) {
            setError(t('errorMinDimensions'));
            setTimeout(() => setError(null), 3000);
            return;
        }
    }
    if (key === 'promptGuidance' || key === 'isActive') {
        newDimensions[index] = { ...newDimensions[index], [key]: value };
        setDimensions(newDimensions);
    }
    setError(null); 
  };

  const handleSaveChanges = () => {
    if (dimensions.filter(d => d.isActive).length === 0) {
      setError(t('errorMinDimensions'));
      return;
    }
    for (const dim of dimensions) {
        if (dim.isActive && !dim.promptGuidance.trim()) {
            setError(`Active dimension "${dim.label}" must have prompt guidance.`);
            return;
        }
    }
    onSaveSettings({ 
        assessmentDimensions: dimensions, 
        nexusRankingScoreThreshold
    });
    setError(null);
  };
  
  const handleResetToDefaults = () => {
    const freshDefaultDimensions = JSON.parse(JSON.stringify(DEFAULT_ASSESSMENT_DIMENSIONS));
    setDimensions(freshDefaultDimensions);
    setNexusRankingScoreThreshold(DEFAULT_NEXUS_RANKING_SCORE_THRESHOLD);
    onResetSettings(); 
  };


  return (
    <div className="bg-neutral-850 p-6 md:p-8 rounded-xl shadow-xl-dark border border-neutral-700">
      <h2 className="text-2xl sm:text-3xl font-bold text-neutral-100 mb-8 pb-4 border-b border-neutral-700">
        Settings
      </h2>
      
      {error && (
        <div className="mb-4 p-3 bg-danger-DEFAULT/10 border-l-4 border-danger-DEFAULT text-danger-text rounded-md shadow-md-dark text-sm">
          {error}
        </div>
      )}

      {/* Assessment Dimensions Section */}
      <div role="region" aria-label="Assessment Dimensions Section" className="mb-10">
        <span className="text-xl font-semibold text-primary-light mb-2 block">{t('assessmentDimensionsSectionTitle')}</span>
        <p className="text-sm text-neutral-400 mb-5">{t('dimensionProcessingTimeWarning')}</p>
        <div className="space-y-6">
          {dimensions.map((dim: AssessmentDimensionSetting, index: number) => (
            <div key={dim.id} className="assessment-dimension bg-neutral-800 p-5 rounded-lg shadow-md-dark border border-neutral-700 relative">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
                <div>
                  <span className="block text-sm font-medium text-neutral-300 mb-1 dimension-name">
                    {dim.label}
                  </span>
                  <p className="w-full px-3 py-2.5 bg-neutral-700/50 border border-neutral-600 text-neutral-200 rounded-md sm:text-sm">
                    {dim.label}
                  </p>
                </div>
                <div className="flex items-center mt-3 md:mt-7 space-x-4">
                  <label htmlFor={`dim-active-${dim.id}`} className="flex items-center text-sm font-medium text-neutral-300 cursor-pointer">
                    <input
                      type="checkbox"
                      id={`dim-active-${dim.id}`}
                      checked={dim.isActive}
                      onChange={(e) => handleDimensionChange(index, 'isActive', e.target.checked)}
                      className="form-checkbox h-5 w-5 text-primary-DEFAULT bg-neutral-600 border-neutral-500 rounded focus:ring-2 focus:ring-primary-light focus:ring-offset-2 focus:ring-offset-neutral-800"
                    />
                    <span className="ml-2">{t('dimensionIsActiveLabel')}</span>
                  </label>
                </div>
                <div className="md:col-span-2">
                  <label htmlFor={`dim-guidance-${dim.id}`} className="block text-sm font-medium text-neutral-300 mb-1">
                    {t('dimensionPromptGuidanceLabel')}
                  </label>
                  <textarea
                    id={`dim-guidance-${dim.id}`}
                    rows={3}
                    value={dim.promptGuidance}
                    onChange={(e) => handleDimensionChange(index, 'promptGuidance', e.target.value)}
                    placeholder={t('dimensionPromptGuidancePlaceholder')}
                    className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 text-neutral-100 rounded-md sm:text-sm focus:ring-primary-DEFAULT focus:border-primary-DEFAULT"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Ranking & Display Settings Section */}
      <div role="region" aria-label="Ranking & Display Settings Section" className="mb-10">
        <span className="text-xl font-semibold text-primary-light mb-5 block">{t('rankingDisplaySettingsSectionTitle')}</span>
        <div className="bg-neutral-800 p-5 rounded-lg shadow-md-dark border border-neutral-700">
          <label htmlFor="nexus-ranking-threshold" className="block text-sm font-medium text-neutral-300 mb-1.5">
            Nexus Ranking Score Threshold
          </label>
          <input
            type="number"
            id="nexus-ranking-threshold"
            aria-label="Nexus Ranking Score Threshold"
            value={nexusRankingScoreThreshold}
            onChange={(e) => {
              const val = parseInt(e.target.value, 10);
              setNexusRankingScoreThreshold(isNaN(val) ? 0 : Math.max(0, Math.min(100, val)));
            }}
            min="0"
            max="100"
            className="w-full md:w-1/4 px-3 py-2.5 bg-neutral-700 border border-neutral-600 text-neutral-100 rounded-md sm:text-sm focus:ring-primary-DEFAULT focus:border-primary-DEFAULT"
          />
          <p className="text-xs text-neutral-400 mt-1.5">{t('nexusRankingScoreThresholdDescription')}</p>
        </div>
      </div>

      {/* Save/Reset Buttons */}
      <div className="mt-10 pt-6 border-t border-neutral-700 flex flex-col sm:flex-row justify-end space-y-3 sm:space-y-0 sm:space-x-4">
        <button
          onClick={handleResetToDefaults}
          className="px-6 py-2.5 bg-neutral-600 text-neutral-100 font-medium rounded-lg shadow-md hover:bg-neutral-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-neutral-850 focus:ring-neutral-400 transition-colors subtle-hover-lift"
        >
          {t('resetSettingsButton')}
        </button>
        <button
          onClick={handleSaveChanges}
          className="px-8 py-2.5 bg-primary-DEFAULT text-white font-semibold rounded-lg shadow-md hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-neutral-850 focus:ring-primary-light transition-colors subtle-hover-lift"
        >
          Save All Settings
        </button>
      </div>
    </div>
  );
};

export default SettingsView;
