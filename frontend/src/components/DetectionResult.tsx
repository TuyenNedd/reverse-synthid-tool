import { ShieldCheck, ShieldAlert, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import type { DetectionResult as DetectionResultType } from '../api/client';

interface DetectionResultProps {
  result: DetectionResultType;
}

export default function DetectionResult({ result }: DetectionResultProps) {
  const [showDetails, setShowDetails] = useState(false);
  const confidencePercent = Math.round(result.confidence * 100);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Detection Result
      </h3>

      {/* Status Badge */}
      <div className="flex items-center gap-3 mb-4">
        {result.is_watermarked ? (
          <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
            <ShieldAlert size={16} />
            Watermarked
          </span>
        ) : (
          <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
            <ShieldCheck size={16} />
            Clean
          </span>
        )}
      </div>

      {/* Confidence Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600 dark:text-gray-400">Confidence</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {confidencePercent}%
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full transition-all ${
              result.is_watermarked ? 'bg-red-500' : 'bg-green-500'
            }`}
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      {/* Phase Match */}
      <div className="mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Phase Match</span>
          <span className="font-mono text-gray-900 dark:text-white">
            {result.phase_match.toFixed(4)}
          </span>
        </div>
      </div>

      {/* Collapsible Details */}
      {result.details && Object.keys(result.details).length > 0 && (
        <div>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            {showDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {showDetails ? 'Hide details' : 'Show details'}
          </button>
          {showDetails && (
            <pre className="mt-2 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-xs text-gray-700 dark:text-gray-300 overflow-auto max-h-48">
              {JSON.stringify(result.details, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
