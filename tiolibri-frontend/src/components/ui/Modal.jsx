/*
================================================================================
USAGE EXAMPLES
================================================================================

import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';

// Basic usage
const [isOpen, setIsOpen] = useState(false);

<Button onClick={() => setIsOpen(true)}>Open Modal</Button>

<Modal isOpen={isOpen} onClose={() => setIsOpen(false)}>
  <h2 className="text-xl font-semibold mb-4">Modal Title</h2>
  <p className="text-gray-600 mb-6">Modal content goes here.</p>
  <div className="flex justify-end gap-3">
    <Button variant="secondary" onClick={() => setIsOpen(false)}>
      Cancel
    </Button>
    <Button variant="primary">Confirm</Button>
  </div>
</Modal>

// Without close button
<Modal isOpen={isOpen} onClose={() => setIsOpen(false)} showClose={false}>
  <p>Content without X button</p>
</Modal>

// Custom width
<Modal isOpen={isOpen} onClose={() => setIsOpen(false)} className="max-w-2xl">
  <p>Wider modal</p>
</Modal>

// Confirmation dialog
<Modal isOpen={showDelete} onClose={() => setShowDelete(false)}>
  <h2 className="text-xl font-semibold mb-2">Delete Project?</h2>
  <p className="text-gray-600 mb-6">
    This action cannot be undone. All chapters and generated files will be deleted.
  </p>
  <div className="flex justify-end gap-3">
    <Button variant="secondary" onClick={() => setShowDelete(false)}>
      Cancel
    </Button>
    <Button variant="danger" onClick={handleDelete}>
      Delete
    </Button>
  </div>
</Modal>

================================================================================
*/

import { useEffect } from 'react';

export default function Modal({
  isOpen,
  onClose,
  children,
  showClose = true,
  className = '',
}) {
  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal content */}
      <div
        className={`relative bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4 animate-in fade-in zoom-in-95 duration-200 ${className}`}
      >
        {/* Close button */}
        {showClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        )}

        {children}
      </div>
    </div>
  );
}
