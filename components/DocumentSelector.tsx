
import React from 'react';
import { CVData, JobDescriptionData } from '../types';
import { useLocalization } from '../hooks/useLocalization';

interface DocumentSelectorProps {
  cvs: CVData[];
  jds: JobDescriptionData[];
  selectedCvIds: string[];
  setSelectedCvIds: (ids: string[]) => void;
  selectedJdIds: string[];
  setSelectedJdIds: (ids: string[]) => void;
}

const DocumentSelector: React.FC<DocumentSelectorProps> = ({
  cvs,
  jds,
  selectedCvIds,
  setSelectedCvIds,
  selectedJdIds,
  setSelectedJdIds,
}) => {
  const { t } = useLocalization();

  const handleCvSelection = (cvId: string) => {
    const newSelectedIds = selectedCvIds.includes(cvId)
      ? selectedCvIds.filter(id => id !== cvId)
      : [...selectedCvIds, cvId];
    setSelectedCvIds(newSelectedIds);
  };

  const handleJdSelection = (jdId: string) => {
    const newSelectedIds = selectedJdIds.includes(jdId)
      ? selectedJdIds.filter(id => id !== jdId)
      : [...selectedJdIds, jdId];
    setSelectedJdIds(newSelectedIds);
  };

  const handleSelectAllCvs = () => {
    if (selectedCvIds.length === cvs.length) {
      setSelectedCvIds([]); // Deselect all
    } else {
      setSelectedCvIds(cvs.map(cv => cv.id)); // Select all
    }
  };

  const handleSelectAllJds = () => {
    if (selectedJdIds.length === jds.length) {
      setSelectedJdIds([]); // Deselect all
    } else {
      setSelectedJdIds(jds.map(jd => jd.id)); // Select all
    }
  };

  const scrollbarClasses = "scrollbar-thin scrollbar-thumb-neutral-600 scrollbar-track-neutral-700/60 hover:scrollbar-thumb-neutral-500";

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="bg-neutral-800 p-6 rounded-xl shadow-lg-dark border border-neutral-700">
        <div className="flex justify-between items-center mb-3">
          <label className="block text-lg font-semibold text-neutral-100">
            {t('selectCV')}
          </label>
          {cvs.length > 0 && (
            <button
              onClick={handleSelectAllCvs}
              className="px-3 py-1 text-xs bg-neutral-600 hover:bg-neutral-500 text-neutral-200 rounded-md transition-colors shadow-sm"
            >
              {selectedCvIds.length === cvs.length ? t('deselectAll') : t('selectAll')}
            </button>
          )}
        </div>
        {cvs.length === 0 ? (
          <p className="text-neutral-400 italic text-sm">{t('noCVs')}</p>
        ) : (
          <div className={`h-48 overflow-y-auto border border-neutral-600 rounded-md p-2 space-y-1 bg-neutral-700/50 ${scrollbarClasses}`}>
            {cvs.map((cv) => (
              <label key={cv.id} className="flex items-center space-x-3 p-2.5 hover:bg-neutral-700 rounded-md cursor-pointer transition-colors duration-150">
                <input
                  type="checkbox"
                  className="form-checkbox h-4 w-4 text-primary-DEFAULT bg-neutral-600 border-neutral-500 rounded focus:ring-2 focus:ring-primary-light focus:ring-offset-2 focus:ring-offset-neutral-700/50 transition duration-150 ease-in-out"
                  checked={selectedCvIds.includes(cv.id)}
                  onChange={() => handleCvSelection(cv.id)}
                  aria-labelledby={`cv-label-${cv.id}`}
                />
                <span id={`cv-label-${cv.id}`} className="text-sm text-neutral-200 select-none truncate" title={cv.name}>{cv.name} <span className="text-xs text-neutral-400">({new Date(cv.createdAt).toLocaleDateString()})</span></span>
              </label>
            ))}
          </div>
        )}
        {cvs.length > 0 && <p className="text-xs text-neutral-400 mt-2">{selectedCvIds.length} CV(s) selected.</p>}
      </div>
      <div className="bg-neutral-800 p-6 rounded-xl shadow-lg-dark border border-neutral-700">
        <div className="flex justify-between items-center mb-3">
          <label className="block text-lg font-semibold text-neutral-100">
            {t('selectJD')}
          </label>
          {jds.length > 0 && (
             <button
              onClick={handleSelectAllJds}
              className="px-3 py-1 text-xs bg-neutral-600 hover:bg-neutral-500 text-neutral-200 rounded-md transition-colors shadow-sm"
            >
              {selectedJdIds.length === jds.length ? t('deselectAll') : t('selectAll')}
            </button>
          )}
        </div>
        {jds.length === 0 ? (
          <p className="text-neutral-400 italic text-sm">{t('noJDs')}</p>
        ) : (
          <div className={`h-48 overflow-y-auto border border-neutral-600 rounded-md p-2 space-y-1 bg-neutral-700/50 ${scrollbarClasses}`}>
            {jds.map((jd) => (
              <label key={jd.id} className="flex items-center space-x-3 p-2.5 hover:bg-neutral-700 rounded-md cursor-pointer transition-colors duration-150">
                <input
                  type="checkbox"
                  className="form-checkbox h-4 w-4 text-primary-DEFAULT bg-neutral-600 border-neutral-500 rounded focus:ring-2 focus:ring-primary-light focus:ring-offset-2 focus:ring-offset-neutral-700/50 transition duration-150 ease-in-out"
                  checked={selectedJdIds.includes(jd.id)}
                  onChange={() => handleJdSelection(jd.id)}
                   aria-labelledby={`jd-label-${jd.id}`}
                />
                <span id={`jd-label-${jd.id}`} className="text-sm text-neutral-200 select-none truncate" title={jd.title}>{jd.title} <span className="text-xs text-neutral-400">({new Date(jd.createdAt).toLocaleDateString()})</span></span>
              </label>
            ))}
          </div>
        )}
        {jds.length > 0 && <p className="text-xs text-neutral-400 mt-2">{selectedJdIds.length} JD(s) selected.</p>}
      </div>
    </div>
  );
};

export default DocumentSelector;
