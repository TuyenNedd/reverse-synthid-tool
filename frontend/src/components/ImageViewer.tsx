import { useCallback, useEffect, useRef, useState } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, X } from 'lucide-react';

interface ImageViewerProps {
  /** Image source URL to display. */
  src: string;
  /** Accessible label / alt text for the image. */
  alt: string;
  /** Whether the viewer modal is open. */
  isOpen: boolean;
  /** Called when the viewer requests to close (X, backdrop, Escape). */
  onClose: () => void;
}

const MIN_ZOOM = 1;
const MAX_ZOOM = 5;
const ZOOM_STEP = 0.25;

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

/**
 * A lightweight, accessible lightbox modal for viewing an image with
 * zoom (buttons + mouse wheel) and pan (drag when zoomed) support.
 */
export default function ImageViewer({ src, alt, isOpen, onClose }: ImageViewerProps) {
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragState = useRef<{ startX: number; startY: number; originX: number; originY: number } | null>(
    null
  );
  const [isDragging, setIsDragging] = useState(false);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);

  const resetView = useCallback(() => {
    setZoom(1);
    setOffset({ x: 0, y: 0 });
  }, []);

  // Reset zoom/pan whenever a new image opens (src change) or the modal opens.
  useEffect(() => {
    if (isOpen) {
      resetView();
    }
  }, [isOpen, src, resetView]);

  // Prevent body scroll while open, and restore on close.
  useEffect(() => {
    if (!isOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  // Manage focus: move focus into the dialog when opening, restore on close.
  useEffect(() => {
    if (isOpen) {
      previouslyFocused.current = document.activeElement as HTMLElement | null;
      // Focus the close button once the dialog is rendered.
      const id = window.setTimeout(() => closeButtonRef.current?.focus(), 0);
      return () => window.clearTimeout(id);
    }
    // On close, restore focus to the element that opened the viewer.
    previouslyFocused.current?.focus?.();
  }, [isOpen]);

  // Keyboard handling: Escape to close, +/- to zoom, 0 to reset.
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        setZoom((z) => clamp(z + ZOOM_STEP, MIN_ZOOM, MAX_ZOOM));
      } else if (e.key === '-' || e.key === '_') {
        e.preventDefault();
        setZoom((z) => clamp(z - ZOOM_STEP, MIN_ZOOM, MAX_ZOOM));
      } else if (e.key === '0') {
        e.preventDefault();
        resetView();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, resetView]);

  const zoomIn = useCallback(() => {
    setZoom((z) => clamp(z + ZOOM_STEP, MIN_ZOOM, MAX_ZOOM));
  }, []);

  const zoomOut = useCallback(() => {
    setZoom((z) => {
      const next = clamp(z - ZOOM_STEP, MIN_ZOOM, MAX_ZOOM);
      if (next === MIN_ZOOM) {
        // Re-center when fully zoomed out.
        setOffset({ x: 0, y: 0 });
      }
      return next;
    });
  }, []);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const direction = e.deltaY < 0 ? 1 : -1;
    setZoom((z) => {
      const next = clamp(z + direction * ZOOM_STEP, MIN_ZOOM, MAX_ZOOM);
      if (next === MIN_ZOOM) {
        setOffset({ x: 0, y: 0 });
      }
      return next;
    });
  }, []);

  // Drag-to-pan handlers (only meaningful when zoomed in).
  const handlePointerDown = useCallback(
    (e: React.PointerEvent) => {
      if (zoom <= 1) return;
      e.preventDefault();
      (e.target as Element).setPointerCapture?.(e.pointerId);
      dragState.current = {
        startX: e.clientX,
        startY: e.clientY,
        originX: offset.x,
        originY: offset.y,
      };
      setIsDragging(true);
    },
    [zoom, offset]
  );

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    const state = dragState.current;
    if (!state) return;
    setOffset({
      x: state.originX + (e.clientX - state.startX),
      y: state.originY + (e.clientY - state.startY),
    });
  }, []);

  const endDrag = useCallback(() => {
    dragState.current = null;
    setIsDragging(false);
  }, []);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Image viewer: ${alt}`}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onMouseDown={(e) => {
        // Close only when the backdrop itself (not a child) is clicked.
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      {/* Toolbar */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <button
          type="button"
          onClick={zoomOut}
          disabled={zoom <= MIN_ZOOM}
          aria-label="Zoom out"
          title="Zoom out (-)"
          className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-gray-800/80 text-white hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
        >
          <ZoomOut size={20} />
        </button>
        <button
          type="button"
          onClick={zoomIn}
          disabled={zoom >= MAX_ZOOM}
          aria-label="Zoom in"
          title="Zoom in (+)"
          className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-gray-800/80 text-white hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
        >
          <ZoomIn size={20} />
        </button>
        <button
          type="button"
          onClick={resetView}
          disabled={zoom === MIN_ZOOM && offset.x === 0 && offset.y === 0}
          aria-label="Reset zoom"
          title="Reset zoom (0)"
          className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-gray-800/80 text-white hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
        >
          <RotateCcw size={20} />
        </button>
        <button
          ref={closeButtonRef}
          type="button"
          onClick={onClose}
          aria-label="Close image viewer"
          title="Close (Esc)"
          className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-gray-800/80 text-white hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      {/* Zoom indicator */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-gray-800/80 text-white text-xs font-medium select-none">
        {Math.round(zoom * 100)}%
      </div>

      {/* Image container */}
      <div
        className="max-w-[90vw] max-h-[90vh] overflow-hidden flex items-center justify-center"
        onWheel={handleWheel}
      >
        <img
          src={src}
          alt={alt}
          draggable={false}
          onMouseDown={(e) => e.stopPropagation()}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={endDrag}
          onPointerCancel={endDrag}
          onPointerLeave={endDrag}
          style={{
            transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})`,
            transition: isDragging ? 'none' : 'transform 0.15s ease-out',
            cursor: zoom > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default',
          }}
          className="max-w-[90vw] max-h-[90vh] object-contain select-none"
        />
      </div>
    </div>
  );
}
