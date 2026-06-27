import { useState } from 'react';
import { Download } from 'lucide-react';
import ImageViewer from './ImageViewer';

interface ImageComparisonProps {
  originalUrl: string;
  cleanedUrl: string;
  psnr?: number;
  /** Original file name, used to derive the downloaded file name. */
  originalFileName?: string | null;
}

/** Build a sensible download filename from the original file name. */
function buildDownloadName(originalFileName?: string | null): string {
  if (!originalFileName) return 'cleaned.png';
  // Strip the extension from the original name and append "-cleaned.png".
  const dotIndex = originalFileName.lastIndexOf('.');
  const baseName = dotIndex > 0 ? originalFileName.slice(0, dotIndex) : originalFileName;
  return `${baseName}-cleaned.png`;
}

type ViewerImage = { src: string; alt: string } | null;

export default function ImageComparison({
  originalUrl,
  cleanedUrl,
  psnr,
  originalFileName,
}: ImageComparisonProps) {
  const downloadName = buildDownloadName(originalFileName);
  const [viewerImage, setViewerImage] = useState<ViewerImage>(null);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Comparison
        </h3>
        {psnr !== undefined && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
            PSNR: {psnr.toFixed(1)} dB
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Original */}
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
            Original
          </p>
          <button
            type="button"
            onClick={() => setViewerImage({ src: originalUrl, alt: 'Original' })}
            aria-label="View original image"
            title="Click to enlarge"
            className="block w-full rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <img
              src={originalUrl}
              alt="Original"
              className="w-full h-auto object-contain max-h-80"
            />
          </button>
        </div>

        {/* Cleaned */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Cleaned
            </p>
            <a
              href={cleanedUrl}
              download={downloadName}
              aria-label="Download cleaned image"
              title="Download cleaned image"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded transition-colors"
            >
              <Download size={16} />
              Download
            </a>
          </div>
          <button
            type="button"
            onClick={() => setViewerImage({ src: cleanedUrl, alt: 'Cleaned' })}
            aria-label="View cleaned image"
            title="Click to enlarge"
            className="block w-full rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <img
              src={cleanedUrl}
              alt="Cleaned"
              className="w-full h-auto object-contain max-h-80"
            />
          </button>
        </div>
      </div>

      <ImageViewer
        isOpen={viewerImage !== null}
        src={viewerImage?.src ?? ''}
        alt={viewerImage?.alt ?? ''}
        onClose={() => setViewerImage(null)}
      />
    </div>
  );
}
