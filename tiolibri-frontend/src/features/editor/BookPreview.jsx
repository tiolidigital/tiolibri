import { useState, useEffect, useMemo } from 'react';
import { getPreset } from '../../lib/presets';

// Split HTML content into pages based on word count
function splitContentIntoPages(htmlContent, wordsPerPage = 400) {
  if (!htmlContent) return [];

  const parser = new DOMParser();
  const doc = parser.parseFromString(htmlContent, 'text/html');
  const elements = Array.from(doc.body.childNodes);

  const pages = [];
  let currentPage = [];
  let currentWordCount = 0;

  for (const element of elements) {
    if (element.nodeType === Node.TEXT_NODE && !element.textContent.trim()) {
      continue;
    }

    const clone = element.cloneNode(true);
    const elementText = clone.textContent || '';
    const elementWordCount = elementText.split(/\s+/).filter(w => w.length > 0).length;

    if (currentWordCount + elementWordCount > wordsPerPage && currentPage.length > 0) {
      pages.push(currentPage);
      currentPage = [clone];
      currentWordCount = elementWordCount;
    } else {
      currentPage.push(clone);
      currentWordCount += elementWordCount;
    }
  }

  if (currentPage.length > 0) {
    pages.push(currentPage);
  }

  return pages.map(pageElements => {
    const div = document.createElement('div');
    pageElements.forEach(el => div.appendChild(el));
    return div.innerHTML;
  });
}

// Pagination navigation component
function PaginationNav({ currentPage, totalPages, onPageChange, disabled }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '1rem',
      padding: '0.75rem',
      borderBottom: '1px solid #e5e7eb',
      backgroundColor: '#f9fafb',
    }}>
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={disabled || currentPage === 1}
        style={{
          padding: '0.5rem 1rem',
          border: '1px solid #d1d5db',
          borderRadius: '0.375rem',
          backgroundColor: currentPage === 1 || disabled ? '#f3f4f6' : 'white',
          color: currentPage === 1 || disabled ? '#9ca3af' : '#374151',
          cursor: currentPage === 1 || disabled ? 'not-allowed' : 'pointer',
          fontWeight: '500',
        }}
      >
        ← Previous
      </button>

      <span style={{
        fontSize: '0.875rem',
        color: '#6b7280',
        minWidth: '120px',
        textAlign: 'center',
      }}>
        Page {currentPage} of {totalPages}
      </span>

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={disabled || currentPage === totalPages}
        style={{
          padding: '0.5rem 1rem',
          border: '1px solid #d1d5db',
          borderRadius: '0.375rem',
          backgroundColor: currentPage === totalPages || disabled ? '#f3f4f6' : 'white',
          color: currentPage === totalPages || disabled ? '#9ca3af' : '#374151',
          cursor: currentPage === totalPages || disabled ? 'not-allowed' : 'pointer',
          fontWeight: '500',
        }}
      >
        Next →
      </button>
    </div>
  );
}

function BookPreview({ content, typography, preset: presetName, isFullScreen = false, onClose }) {
  const [currentPage, setCurrentPage] = useState(1);

  const settings = {
    fontSize: typography?.fontSize || 18,
    lineHeight: typography?.lineHeight || 1.6,
    textAlign: typography?.textAlign || 'left',
    marginTop: typography?.marginTop || 1.5,
    marginBottom: typography?.marginBottom || 1.5,
    marginLeft: typography?.marginLeft || 1,
    marginRight: typography?.marginRight || 1,
  };

  // Convert preset string to preset object with fontFamily
  const preset = getPreset(presetName);

  console.log('🔍 Preview content HTML:', content?.substring(0, 500));
  console.log('🔍 Full content length:', content?.length);
  console.log('🔍 Preset name:', presetName, '→ fontFamily:', preset.fontFamily);

  // A5 dimensions in cm
  const A5_WIDTH_CM = 14.8;
  const A5_HEIGHT_CM = 21.0;

  // Preview scale: 700px = 14.8cm (A5 width)
  const PREVIEW_WIDTH_PX = 700;
  const PX_PER_CM = PREVIEW_WIDTH_PX / A5_WIDTH_CM; // ~47.3px per cm

  // Calculate preview height to match A5 proportions
  const PREVIEW_HEIGHT_PX = A5_HEIGHT_CM * PX_PER_CM; // ~994px

  // Calculate content margins in px
  const marginTopPx = settings.marginTop * PX_PER_CM;
  const marginBottomPx = settings.marginBottom * PX_PER_CM;
  const marginLeftPx = settings.marginLeft * PX_PER_CM;
  const marginRightPx = settings.marginRight * PX_PER_CM;

  // Split content into pages (memoized)
  const pages = useMemo(() => {
    if (!content) return ['<p style="color: #9ca3af; text-align: center; padding: 2rem;">No content yet. Start writing!</p>'];
    return splitContentIntoPages(content, 400);
  }, [content]);

  const totalPages = pages.length;

  // Reset to page 1 when content changes
  useEffect(() => {
    setCurrentPage(1);
  }, [content]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowLeft' && currentPage > 1) {
        setCurrentPage(p => p - 1);
      } else if (e.key === 'ArrowRight' && currentPage < totalPages) {
        setCurrentPage(p => p + 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentPage, totalPages]);

  const currentPageContent = pages[currentPage - 1] || '';

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: '#f3f4f6',
    }}>
      {/* Header - only in full-screen mode */}
      {isFullScreen && (
        <div style={{
          padding: '12px 16px',
          borderBottom: '1px solid #e5e7eb',
          backgroundColor: 'white',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
            📖 Preview
          </span>

          <button
            onClick={onClose}
            style={{
              padding: '6px 12px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              backgroundColor: 'white',
              color: '#374151',
              fontSize: '14px',
              cursor: 'pointer',
              fontWeight: '500',
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#f9fafb'}
            onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
          >
            ← Back to Editor
          </button>
        </div>
      )}

      <PaginationNav
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
        disabled={!content}
      />

      <div style={{
        padding: '0.5rem 1rem',
        backgroundColor: '#fef3c7',
        borderBottom: '1px solid #fcd34d',
        fontSize: '0.75rem',
        color: '#92400e',
        textAlign: 'center',
      }}>
        ℹ️ Approximate page count - actual PDF layout may differ
      </div>

      <div style={{
        flex: 1,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-start',
        padding: '2rem',
        overflowY: 'auto',
      }}>
        <div style={{
          width: `${PREVIEW_WIDTH_PX}px`,
          height: `${PREVIEW_HEIGHT_PX}px`,
          backgroundColor: 'white',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}>
          {/* 1. TOP MARGIN - empty spacer div */}
          <div style={{
            height: `${marginTopPx}px`,
            flexShrink: 0,
          }} />

          {/* 2. CONTENT - constrained height */}
          <div
            className="book-content"
            style={{
              flex: 1,
              overflow: 'hidden',
              paddingLeft: `${marginLeftPx}px`,
              paddingRight: `${marginRightPx}px`,
              fontFamily: preset?.fontFamily || 'Georgia, serif',
              fontSize: `${settings.fontSize}px`,
              lineHeight: settings.lineHeight,
              textAlign: settings.textAlign,
            }}
            dangerouslySetInnerHTML={{ __html: currentPageContent }}
          />

          {/* 3. BOTTOM MARGIN - empty spacer div with page number */}
          <div style={{
            height: `${marginBottomPx}px`,
            flexShrink: 0,
            position: 'relative',
          }}>
            <div style={{
              position: 'absolute',
              bottom: '14px',
              left: '0',
              right: '0',
              textAlign: 'center',
              fontSize: '0.75rem',
              color: '#6b7280',
            }}>
              {currentPage}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BookPreview;