import React, { useState } from 'react';
import { Upload, Loader2 } from 'lucide-react';
import { useModel } from '../contexts/ModelContext';
import { apiService } from '../services/api';

interface JobUploadResponse {
  jobId: string;
  status: string;
}

const JobUploader: React.FC = () => {
  const { activeModel, isModelLoading, setIsModelLoading } = useModel();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = e.target.files?.[0];
    if (!uploadedFile) return;
    setFile(uploadedFile);
    setError(null);
    setUploadStatus(null);
  };

  const submitJob = async () => {
    if (!file) {
      setError('Please select a file to upload.');
      return;
    }
    setIsModelLoading(true);
    setError(null);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('model', activeModel);

    try {
      const uploadResponse = await apiService.uploadJob(formData);
      setUploadStatus(`Job uploaded successfully with ID: ${uploadResponse.jobId}. Initiating candidate sourcing...`);
      
      // Trigger the sourcing agent flow
      try {
        await apiService.triggerAgentFlow({ jobId: uploadResponse.jobId, agent: 'sourcing' });
        setUploadStatus(`Job ID: ${uploadResponse.jobId}. Sourcing agent initiated successfully.`);
      } catch (agentError) {
        console.error('Failed to trigger sourcing agent:', agentError);
        // Update status to reflect upload success but trigger failure
        setUploadStatus(`Job ID: ${uploadResponse.jobId}. Upload successful, but failed to initiate sourcing.`); 
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsModelLoading(false);
    }
  };

  return (
    <div className="glass-card p-6 rounded-xl">
      <div className="flex items-center gap-3 mb-4">
        <Upload className="w-6 h-6 text-primary" />
        <h3 className="text-lg font-medium">Job Uploader</h3>
      </div>
      <input type="file" onChange={handleFileUpload} accept=".pdf,.doc,.docx,.txt" className="mb-4" />
      {error && <p className="text-red-500">{error}</p>}
      {uploadStatus && <p className="text-green-500">{uploadStatus}</p>}
      <button onClick={submitJob} disabled={isModelLoading} className="bg-primary text-white p-2 rounded">
        {isModelLoading ? <Loader2 className="animate-spin" /> : 'Upload Job'}
      </button>
    </div>
  );
};

export default JobUploader;
