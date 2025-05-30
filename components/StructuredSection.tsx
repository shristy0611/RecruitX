import React, { useState } from 'react';
import EditableField from './EditableField';
import { useLocalization } from '../hooks/useLocalization';

interface FieldConfig {
  key: string;
  labelKey: string; // Translation key for the label
  placeholderKey?: string; // Translation key for placeholder
  multiline?: boolean;
  isList?: boolean; // If true, renders as a list of strings, editable as a single textarea with items on new lines
}

interface StructuredSectionProps<T extends Record<string, any>> {
  titleKey: string;
  data: T[];
  fieldsConfig: FieldConfig[];
  onUpdate: (updatedData: T[]) => void;
  newEntryTemplate: Omit<T, 'id'>; // Template for adding a new entry, ID will be generated
  itemClassName?: string;
  listClassName?: string;
}

const StructuredSection = <T extends { id?: string; [key: string]: any }>({
  titleKey,
  data,
  fieldsConfig,
  onUpdate,
  newEntryTemplate,
  itemClassName = "bg-neutral-700 p-4 rounded-lg shadow-md border border-neutral-600",
  listClassName = "space-y-4"
}: StructuredSectionProps<T>) => {
  const { t } = useLocalization();

  const handleFieldUpdate = (index: number, fieldKey: string, newValue: string) => {
    const newData = [...data];
    const entryToUpdate = { ...newData[index] };

    if (fieldsConfig.find(f => f.key === fieldKey)?.isList) {
      (entryToUpdate as any)[fieldKey] = newValue.split('\n').map(s => s.trim()).filter(s => s);
    } else {
      (entryToUpdate as any)[fieldKey] = newValue;
    }
    newData[index] = entryToUpdate;
    onUpdate(newData);
  };

  const handleAddItem = () => {
    const newItem: T = {
      ...newEntryTemplate,
      id: `${titleKey.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`
    } as T;
    onUpdate([...data, newItem]);
  };

  const handleDeleteItem = (index: number) => {
    if (window.confirm(t('confirmDeleteEntryMessage'))) {
      const newData = data.filter((_, i) => i !== index);
      onUpdate(newData);
    }
  };

  return (
    <section className="mb-6">
      <div className="flex justify-between items-center mb-3">
        <h4 className="text-lg font-semibold text-neutral-100">{t(titleKey)}</h4>
        <button
          onClick={handleAddItem}
          className="px-3 py-1.5 text-xs bg-primary-dark hover:bg-primary-DEFAULT text-primary-text rounded-md transition-colors shadow-sm flex items-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 mr-1.5">
            <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
          </svg>
          {t('addNewEntryButtonLabel')}
        </button>
      </div>
      {data.length === 0 ? (
        <p className="text-sm text-neutral-400 italic py-2">{t('noEntriesFound') || 'No entries yet.'}</p>
      ) : (
      <div className={listClassName}>
        {data.map((item: T, index) => (
          <div key={item.id || index} className={`${itemClassName} relative group`}>
            <button
                onClick={() => handleDeleteItem(index)}
                className="absolute top-2 right-2 p-1.5 bg-neutral-600 hover:bg-danger-DEFAULT text-neutral-300 hover:text-white rounded-full opacity-50 group-hover:opacity-100 transition-opacity"
                aria-label={t('deleteButton')}
                title={t('deleteButton')}
            >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                <path fillRule="evenodd" d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.58.177-2.365.297a.75.75 0 00-.526.69LV2.76 15.2A2.25 2.25 0 005.008 18h9.984a2.25 2.25 0 002.248-2.802l-.34-10.022a.75.75 0 00-.527-.69c-.784-.12-1.57-.199-2.365-.297V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.5.66 1.5 1.5V6h-3V5.5A1.5 1.5 0 0110 4zM8.088 15.567L9.25 7.752a.75.75 0 011.493-.033l.22 1.852a.75.75 0 001.478-.255l-.203-2.184a.75.75 0 111.48.204l.228 2.449a.75.75 0 01-1.47.16l-.207-2.213a.75.75 0 00-1.486.116l-.22 1.852a.75.75 0 11-1.478-.255l.202-2.184a.75.75 0 011.48-.204l.228 2.449a.75.75 0 001.47.16l-.207-2.213a.75.75 0 011.486.116l.272 2.264a.75.75 0 11-1.45.352l-.23-1.912a.75.75 0 00-1.457.056L10.75 15.5l-1.102.067a.75.75 0 01-.787-.78l.155-2.325a.75.75 0 111.48-.204l-.17 2.034a.75.75 0 001.456.123l.814-2.034a.75.75 0 111.358.543l-.864 2.159a.75.75 0 01-1.41.14L10 7.898l-1.138 7.61a.75.75 0 01-1.487-.222l.783-5.22a.75.75 0 00-1.443-.218L5.75 14.75l-.042.003a.75.75 0 01-.748-.742L5.25 5.522a.75.75 0 111.5 0L6.5 13.75l.028.002a.75.75 0 00.748-.742L7.5 5.522a.75.75 0 011.5 0l-.25 7.478a.75.75 0 101.492.169l.792-2.375a.75.75 0 011.41.471l-.791 2.374a.75.75 0 001.492.169l.156-.467a.75.75 0 111.433.488l-.156.467a.75.75 0 01-1.492-.169L10.75 7.5h.001l.022.001a.75.75 0 11-.023-1.5L10 6h.001c.008 0 .016.004.023.01a.75.75 0 010 1.48.755.755 0 01-.023.01H10v.001a.75.75 0 000 1.5V10h.001a.75.75 0 110 1.5H10v.001a.75.75 0 100 1.5V13h.001a.75.75 0 110 1.5H10z" clipRule="evenodd" />
                </svg>
            </button>
            {fieldsConfig.map(field => (
              <EditableField
                key={field.key}
                label={t(field.labelKey)}
                value={
                  field.isList && Array.isArray(item[field.key]) 
                    ? (item[field.key] as string[]).join('\n') 
                    : item[field.key] as string | undefined
                }
                onSave={(newValue) => handleFieldUpdate(index, field.key, newValue)}
                placeholder={field.placeholderKey ? t(field.placeholderKey) : t(field.labelKey)}
                multiline={field.multiline || field.isList}
              />
            ))}
          </div>
        ))}
      </div>
      )}
    </section>
  );
};

export default StructuredSection;