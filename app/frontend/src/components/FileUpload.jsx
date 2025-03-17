import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { FiUploadCloud, FiFile, FiAlertCircle } from 'react-icons/fi';
import { useLanguage } from '../contexts/LanguageContext';

const FileUpload = ({ onFileUpload, acceptedFileTypes = { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'], 'text/plain': ['.txt'] } }) => {
  const { language } = useLanguage();
  
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      onFileUpload(acceptedFiles[0]);
    }
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive, isDragReject, fileRejections } = useDropzone({
    onDrop,
    accept: acceptedFileTypes,
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  // Format file size
  const formatFileSize = (size) => {
    if (size < 1024) return size + (language === 'ja' ? ' バイト' : ' bytes');
    else if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB';
    else return (size / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // Get error message
  const getErrorMessage = (fileRejection) => {
    const { errors } = fileRejection;
    if (errors[0]?.code === 'file-too-large') {
      return language === 'ja' 
        ? `ファイルサイズが大きすぎます。最大サイズは10MBです。`
        : `File is too large. Max size is 10MB.`;
    } else if (errors[0]?.code === 'file-invalid-type') {
      return language === 'ja'
        ? `無効なファイル形式です。PDF、DOCX、またはTXTをアップロードしてください。`
        : `Invalid file type. Please upload PDF, DOCX, or TXT.`;
    }
    return errors[0]?.message || (language === 'ja' ? '無効なファイル' : 'Invalid file');
  };

  return (
    <div className="mb-6">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'dropzone-active' : ''} ${
          isDragReject ? 'border-red-500 bg-red-50' : ''
        }`}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <div className="flex flex-col items-center">
            <FiUploadCloud className="h-12 w-12 text-primary-500 mb-2" />
            <p className="text-primary-500">
              {language === 'ja' ? 'ここにファイルをドロップ...' : 'Drop the file here...'}
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <FiUploadCloud className="h-12 w-12 text-gray-400 mb-2" />
            <p className="text-gray-600 mb-1">
              {language === 'ja' 
                ? 'ファイルをここにドラッグ＆ドロップ、またはクリックして選択' 
                : 'Drag & drop a file here, or click to select a file'}
            </p>
            <p className="text-xs text-gray-500">
              {language === 'ja' 
                ? 'PDF、DOCX、TXTに対応（最大10MB）' 
                : 'Supports PDF, DOCX, and TXT (max 10MB)'}
            </p>
          </div>
        )}
      </div>

      {fileRejections.length > 0 && (
        <div className="mt-2 text-red-500 text-sm flex items-start">
          <FiAlertCircle className="h-4 w-4 mr-1 mt-0.5" />
          <span>{getErrorMessage(fileRejections[0])}</span>
        </div>
      )}
    </div>
  );
};

export default FileUpload; 