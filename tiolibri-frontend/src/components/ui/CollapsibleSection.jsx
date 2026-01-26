export default function CollapsibleSection({ title, isOpen, onToggle, children, defaultOpen = false }) {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        className="w-full p-4 flex items-center justify-between bg-white hover:bg-gray-50 transition-colors"
        onClick={onToggle}
      >
        <span className="font-medium text-sm text-gray-900">{title}</span>
        <svg
          className={`w-4 h-4 transition-transform duration-200 ${
            isOpen ? 'rotate-180 text-[#e3704a]' : 'text-gray-400'
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="p-4 pt-0 bg-gray-50">
          {children}
        </div>
      )}
    </div>
  )
}
