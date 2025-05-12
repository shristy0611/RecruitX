'use client';

import React, { useState } from 'react';
import { useSession } from 'next-auth/react';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { FileType } from '@prisma/client';
import FileUpload from './ui/FileUpload';

const uploadSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  fileType: z.nativeEnum(FileType),
});

type UploadFormValues = z.infer<typeof uploadSchema>;

export default function UploadDocuments() {
  const { data: session } = useSession();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFileIds, setUploadedFileIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, watch, formState: { errors } } = useForm<UploadFormValues>({
    resolver: zodResolver(uploadSchema),
    defaultValues: {
      title: '',
      fileType: FileType.CV,
    }
  });

  const selectedFileType = watch('fileType');

  const handleFileUpload = async (file: File) => {
    if (!session?.user) {
      throw new Error('You must be logged in to upload files');
    }
    
    setIsUploading(true);
    setError(null);
    
    try {
      // 1. Request a presigned URL from our API
      const response = await fetch('/api/upload/s3', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fileName: file.name,
          fileType: selectedFileType,
          contentType: file.type,
        }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to get upload URL');
      }
      
      const { fileId, uploadUrl, fields } = await response.json();
      
      // 2. Upload the file directly to S3/MinIO using the presigned URL
      const formData = new FormData();
      Object.entries(fields).forEach(([key, value]) => {
        formData.append(key, value as string);
      });
      formData.append('file', file);
      
      const uploadResponse = await fetch(uploadUrl, {
        method: 'POST',
        body: formData,
      });
      
      if (!uploadResponse.ok) {
        throw new Error('Failed to upload to storage');
      }
      
      // 3. Store the file ID for further processing
      setUploadedFileIds(prev => [...prev, fileId]);
      
      return fileId;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      throw err;
    } finally {
      setIsUploading(false);
    }
  };

  const onSubmit = async (data: UploadFormValues) => {
    // Here you would normally handle the form submission,
    // possibly triggering extraction or other processing
    console.log('Form submitted:', data);
    console.log('Uploaded file IDs:', uploadedFileIds);
  };

  if (!session) {
    return (
      <div className="p-6 text-center">
        <p>Please sign in to upload documents</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Upload Documents</h1>
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Document Type
          </label>
          <select
            {...register('fileType')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value={FileType.CV}>CV / Resume</option>
            <option value={FileType.JD}>Job Description</option>
          </select>
          {errors.fileType && (
            <p className="mt-1 text-sm text-red-600">{errors.fileType.message}</p>
          )}
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {selectedFileType === FileType.CV ? 'Candidate Name' : 'Job Title'}
          </label>
          <input
            type="text"
            {...register('title')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder={selectedFileType === FileType.CV ? 'Enter candidate name' : 'Enter job title'}
          />
          {errors.title && (
            <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
          )}
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Upload File
          </label>
          <FileUpload 
            fileType={selectedFileType} 
            onFileUpload={handleFileUpload}
            isUploading={isUploading}
          />
          {error && (
            <p className="mt-1 text-sm text-red-600">{error}</p>
          )}
        </div>
        
        <div className="pt-4">
          <button
            type="submit"
            disabled={uploadedFileIds.length === 0 || isUploading}
            className={`w-full px-4 py-2 text-white font-medium rounded-md ${
              uploadedFileIds.length === 0 || isUploading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            Process Document
          </button>
        </div>
      </form>
    </div>
  );
}
