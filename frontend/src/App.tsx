import { useState, useCallback, useRef, useEffect } from 'react';
import { Search, Loader2 } from 'lucide-react';
import Header from './components/Header';
import ImageDropzone from './components/ImageDropzone';
import DetectionResult from './components/DetectionResult';
import RemovalPanel from './components/RemovalPanel';
import ImageComparison from './components/ImageComparison';
import {
  detectWatermark,
  removeWatermark,
  type DetectionResult as DetectionResultType,
} from './api/client';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [detectionResult, setDetectionResult] = useState<DetectionResultType | null>(null);
  const [removalResult, setRemovalResult] = useState<string | null>(null);
  const removalUrlRef = useRef<string | null>(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);
  const [mode, setMode] = useState<'fast' | 'full'>('fast');
  const [strength, setStrength] = useState('default');
  const [error, setError] = useState<string | null>(null);

  // Revoke previous object URL when a new one is created or on unmount
  useEffect(() => {
    return () => {
      if (removalUrlRef.current) {
        URL.revokeObjectURL(removalUrlRef.current);
      }
    };
  }, []);

  const handleImageDrop = useCallback((droppedFile: File) => {
    setFile(droppedFile);
    setDetectionResult(null);
    setRemovalResult(null);
    setError(null);

    const reader = new FileReader();
    reader.onload = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(droppedFile);
  }, []);

  const handleDetect = async () => {
    if (!file) return;
    setIsDetecting(true);
    setError(null);
    try {
      const result = await detectWatermark(file);
      setDetectionResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Detection failed. Is the backend running?');
    } finally {
      setIsDetecting(false);
    }
  };

  const handleRemove = async () => {
    if (!file) return;
    setIsRemoving(true);
    setError(null);
    try {
      const blob = await removeWatermark(file, mode, strength === 'default' ? undefined : strength);
      // Revoke previous object URL to avoid memory leak
      if (removalUrlRef.current) {
        URL.revokeObjectURL(removalUrlRef.current);
      }
      const url = URL.createObjectURL(blob);
      removalUrlRef.current = url;
      setRemovalResult(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Removal failed. Is the backend running?');
    } finally {
      setIsRemoving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-5xl mx-auto px-4 pb-12">
        <Header />

        {/* Main Content */}
        <main className="mt-8 space-y-8">
          {/* Dropzone */}
          <ImageDropzone
            onImageDrop={handleImageDrop}
            preview={imagePreview}
            fileName={file?.name ?? null}
          />

          {/* Action Buttons */}
          {file && (
            <div className="flex flex-wrap gap-4 justify-center">
              <button
                onClick={handleDetect}
                disabled={isDetecting}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isDetecting ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Detecting...
                  </>
                ) : (
                  <>
                    <Search size={18} />
                    Detect Watermark
                  </>
                )}
              </button>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Results Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Detection Results */}
            {detectionResult && <DetectionResult result={detectionResult} />}

            {/* Removal Panel */}
            {file && (
              <RemovalPanel
                mode={mode}
                onModeChange={setMode}
                strength={strength}
                onStrengthChange={setStrength}
                onRemove={handleRemove}
                isProcessing={isRemoving}
                disabled={!file}
              />
            )}
          </div>

          {/* Image Comparison */}
          {removalResult && imagePreview && (
            <ImageComparison
              originalUrl={imagePreview}
              cleanedUrl={removalResult}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
