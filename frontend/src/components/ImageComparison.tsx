interface ImageComparisonProps {
  originalUrl: string;
  cleanedUrl: string;
  psnr?: number;
}

export default function ImageComparison({
  originalUrl,
  cleanedUrl,
  psnr,
}: ImageComparisonProps) {
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
          <div className="rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
            <img
              src={originalUrl}
              alt="Original"
              className="w-full h-auto object-contain max-h-80"
            />
          </div>
        </div>

        {/* Cleaned */}
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
            Cleaned
          </p>
          <div className="rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
            <img
              src={cleanedUrl}
              alt="Cleaned"
              className="w-full h-auto object-contain max-h-80"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
