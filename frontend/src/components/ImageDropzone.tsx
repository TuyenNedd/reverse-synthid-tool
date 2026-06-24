import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Image as ImageIcon } from 'lucide-react';

interface ImageDropzoneProps {
  onImageDrop: (file: File) => void;
  preview: string | null;
  fileName: string | null;
}

export default function ImageDropzone({ onImageDrop, preview, fileName }: ImageDropzoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onImageDrop(acceptedFiles[0]);
      }
    },
    [onImageDrop]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/webp': ['.webp'],
    },
    multiple: false,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
        isDragActive
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
      }`}
    >
      <input {...getInputProps()} />
      {preview ? (
        <div className="space-y-4">
          <img
            src={preview}
            alt="Preview"
            className="max-h-64 mx-auto rounded-lg shadow-md"
          />
          <div className="flex items-center justify-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <ImageIcon size={16} />
            <span>{fileName}</span>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-500">
            Drop a new image to replace
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <Upload className="mx-auto text-gray-400 dark:text-gray-500" size={48} />
          <div>
            <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
              {isDragActive ? 'Drop your image here' : 'Drag & drop an image'}
            </p>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-500">
              or click to browse. Accepts PNG, JPEG, WebP.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
