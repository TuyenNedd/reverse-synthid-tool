import { Eraser, Loader2 } from 'lucide-react';

interface RemovalPanelProps {
  mode: 'fast' | 'full';
  onModeChange: (mode: 'fast' | 'full') => void;
  strength: string;
  onStrengthChange: (strength: string) => void;
  onRemove: () => void;
  isProcessing: boolean;
  disabled: boolean;
}

// Strength options per mode. Fast mode uses V3 bypass which supports
// gentle/moderate/aggressive/maximum. Full mode uses V4 which supports
// final/nuke.
const STRENGTH_OPTIONS: Record<string, { value: string; label: string }[]> = {
  fast: [
    { value: 'default', label: 'Default' },
    { value: 'gentle', label: 'Gentle' },
    { value: 'moderate', label: 'Moderate' },
    { value: 'aggressive', label: 'Aggressive' },
    { value: 'maximum', label: 'Maximum' },
  ],
  full: [
    { value: 'default', label: 'Default' },
    { value: 'final', label: 'Final' },
    { value: 'nuke', label: 'Maximum (Nuke)' },
  ],
};

export default function RemovalPanel({
  mode,
  onModeChange,
  strength,
  onStrengthChange,
  onRemove,
  isProcessing,
  disabled,
}: RemovalPanelProps) {
  const strengthOptions = STRENGTH_OPTIONS[mode] || STRENGTH_OPTIONS.fast;

  // Reset strength to default when mode changes and current value is invalid
  const handleModeChange = (newMode: 'fast' | 'full') => {
    onModeChange(newMode);
    const validValues = (STRENGTH_OPTIONS[newMode] || []).map((o) => o.value);
    if (!validValues.includes(strength)) {
      onStrengthChange('default');
    }
  };
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Remove Watermark
      </h3>

      {/* Mode Selector */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Mode
        </label>
        <div className="space-y-2">
          <label
            className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
              mode === 'fast'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
            }`}
          >
            <input
              type="radio"
              name="mode"
              value="fast"
              checked={mode === 'fast'}
              onChange={() => handleModeChange('fast')}
              className="mt-0.5"
            />
            <div>
              <span className="font-medium text-gray-900 dark:text-white">Fast</span>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Spectral subtraction, PSNR 43dB+, seconds
              </p>
            </div>
          </label>
          <label
            className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
              mode === 'full'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
            }`}
          >
            <input
              type="radio"
              name="mode"
              value="full"
              checked={mode === 'full'}
              onChange={() => handleModeChange('full')}
              className="mt-0.5"
            />
            <div>
              <span className="font-medium text-gray-900 dark:text-white">Full</span>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                7-stage pipeline, maximum removal, slower
              </p>
            </div>
          </label>
        </div>
      </div>

      {/* Strength Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Strength
        </label>
        <select
          value={strength}
          onChange={(e) => onStrengthChange(e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {strengthOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Remove Button */}
      <button
        onClick={onRemove}
        disabled={disabled || isProcessing}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isProcessing ? (
          <>
            <Loader2 size={18} className="animate-spin" />
            Processing...
          </>
        ) : (
          <>
            <Eraser size={18} />
            Remove Watermark
          </>
        )}
      </button>
    </div>
  );
}
