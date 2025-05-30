
import React, { useState, useEffect, useRef } from 'react';
import { useLocalization } from '../hooks/useLocalization';

interface EditableFieldProps {
  label: string;
  value: string | undefined;
  onSave: (newValue: string) => void;
  placeholder?: string;
  multiline?: boolean;
  inputClassName?: string;
  labelClassName?: string;
  containerClassName?: string;
  isInitiallyEditing?: boolean;
  onBlurSave?: boolean; // If true, saves on blur
}

const EditableField: React.FC<EditableFieldProps> = ({
  label,
  value,
  onSave,
  placeholder,
  multiline = false,
  inputClassName = "w-full px-3 py-2 bg-neutral-600 border border-neutral-500 text-neutral-100 rounded-md shadow-sm focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT sm:text-sm transition-colors",
  labelClassName = "block text-xs font-medium text-neutral-400 mb-1 uppercase tracking-wider",
  containerClassName = "mb-3",
  isInitiallyEditing = false,
  onBlurSave = true,
}) => {
  const { t } = useLocalization();
  const [isEditing, setIsEditing] = useState(isInitiallyEditing);
  const [currentValue, setCurrentValue] = useState(value || '');
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  useEffect(() => {
    setCurrentValue(value || '');
  }, [value]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      if (inputRef.current instanceof HTMLInputElement || inputRef.current instanceof HTMLTextAreaElement) {
          inputRef.current.select(); // Select all text when editing starts
      }
    }
  }, [isEditing]);

  const handleSave = () => {
    if (currentValue.trim() !== (value || '').trim()) {
      onSave(currentValue.trim());
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !multiline) {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      setCurrentValue(value || ''); // Revert
      setIsEditing(false);
    }
  };

  const handleBlur = () => {
    if (onBlurSave) {
      handleSave();
    } else {
      // If not saving on blur, and value is different, revert to original and exit edit mode.
      // Or, keep changes and require explicit save/cancel? For now, let's try saving on blur as default.
      // If onBlurSave is false, the user needs explicit save/cancel buttons not provided by this component.
      // So if onBlurSave=false, it might be better to keep it in edit mode until explicit action.
      // For simplicity, this component assumes blur = save or explicit Enter/Escape.
      // If onBlurSave is false, we might just revert to display mode without saving.
      setCurrentValue(value || ''); 
      setIsEditing(false);
    }
  };

  return (
    <div className={containerClassName}>
      <label htmlFor={`editable-${label.replace(/\s+/g, '-').toLowerCase()}`} className={labelClassName}>
        {label}
      </label>
      {isEditing ? (
        <div className="relative">
          {multiline ? (
            <textarea
              id={`editable-${label.replace(/\s+/g, '-').toLowerCase()}`}
              ref={inputRef as React.RefObject<HTMLTextAreaElement>}
              value={currentValue}
              onChange={(e) => setCurrentValue(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              placeholder={placeholder || t('cvFieldDescription')}
              className={`${inputClassName} min-h-[80px] resize-y`}
              rows={3}
            />
          ) : (
            <input
              type="text"
              id={`editable-${label.replace(/\s+/g, '-').toLowerCase()}`}
              ref={inputRef as React.RefObject<HTMLInputElement>}
              value={currentValue}
              onChange={(e) => setCurrentValue(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              placeholder={placeholder || label}
              className={inputClassName}
            />
          )}
           <button
            onClick={handleSave}
            className="absolute top-1/2 right-2 transform -translate-y-1/2 p-1 text-success-textDarkBg hover:text-success-DEFAULT focus:outline-none"
            title={t('doneButtonLabel')}
            aria-label={t('doneButtonLabel')}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
              <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      ) : (
        <div 
          onClick={() => setIsEditing(true)} 
          className={`w-full px-3 py-2.5 bg-neutral-700/70 border border-transparent hover:border-neutral-500 text-neutral-100 rounded-md sm:text-sm cursor-pointer min-h-[42px] flex items-center whitespace-pre-wrap break-words transition-colors group relative`}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter') setIsEditing(true);}}
          aria-label={`${t('editButtonLabel')} ${label}`}
        >
          {currentValue || <span className="text-neutral-400 italic">{placeholder || `Enter ${label}`}</span>}
           <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 text-neutral-400 group-hover:text-primary-light opacity-0 group-hover:opacity-100 transition-opacity absolute top-1/2 right-2 transform -translate-y-1/2">
            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
          </svg>
        </div>
      )}
    </div>
  );
};

export default EditableField;
