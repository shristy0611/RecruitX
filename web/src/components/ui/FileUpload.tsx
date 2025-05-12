'use client';

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { FileType } from '@prisma/client';
import { Upload, X, FileText, CheckCircle } from 'lucide-react';

interface FileUploadProps {
  fileType: FileType;
  onFileUpload: (file: File) => Promise<void>;
  isUploading?: boolean;
}

export default function FileUpload({ fileType, onFileUpload, isUploading = false }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploadComplete, setUploadComplete] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const selectedFile = acceptedFiles[0];
    if (!selectedFile) return;
    
    setFile(selectedFile);
    setError(null);
    
    try {
      setUploadProgress(10);
      // Simulate progress before actual upload
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 300);
      
      await onFileUpload(selectedFile);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadComplete(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setUploadProgress(0);
    }
  }, [onFileUpload]);

  const removeFile = () => {
    setFile(null);
    setUploadProgress(0);
    setUploadComplete(false);
    setError(null);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
    disabled: isUploading || uploadComplete,
  });

  return (
    <div className="w-full">
      <div 
        className={`
          border-2 border-dashed rounded-lg p-6 
          ${isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300'} 
          ${error ? 'border-red-400 bg-red-50' : ''}
          ${isUploading ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'}
          ${uploadComplete ? 'border-green-400 bg-green-50' : ''}
          transition-all duration-200
        `}
      >
        {!file ? (
          <div {...getRootProps()} className="flex flex-col items-center justify-center py-4">
            <input {...getInputProps()} />
            <Upload className="w-10 h-10 text-gray-400 mb-2" />
            <p className="text-sm text-gray-600 font-medium">
              Drag & drop your {fileType} here, or click to select
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Supports PDF, DOC(X), XLS(X), TXT files
            </p>
          </div>
        ) : (
          <div className="flex flex-col">
            <div className="flex items-start justify-between">
              <div className="flex items-center">
                <FileText className="w-6 h-6 text-blue-500 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-700 truncate max-w-xs">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              
              {!isUploading && !uploadComplete && (
                <button 
                  onClick={removeFile}
                  className="text-gray-400 hover:text-red-500 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
              
              {uploadComplete && (
                <CheckCircle className="w-5 h-5 text-green-500" />
              )}
            </div>
            
            {(isUploading || uploadProgress > 0) && !uploadComplete && (
              <div className="w-full mt-4">
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-blue-500 h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <p className="text-xs text-right mt-1 text-gray-500">
                  {uploadProgress}%
                </p>
              </div>
            )}
            
            {error && (
              <p className="text-xs text-red-500 mt-2">{error}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
