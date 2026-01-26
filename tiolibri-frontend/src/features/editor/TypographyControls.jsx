export default function TypographyControls({ value, onChange }) {
  const settings = value || {
    textAlign: 'left',
    fontSize: 16,
    lineHeight: 1.7,
    marginTop: 2,
    marginBottom: 2,
    marginLeft: 1.5,
    marginRight: 1.5,
    chapterSpacing: 2
  }

  const handleChange = (key, newValue) => {
    const updated = { ...settings, [key]: newValue }
    onChange(updated)
  }

  return (
    <div className="space-y-6">
      {/* Text Alignment */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-2">
          Text Alignment
        </label>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => handleChange('textAlign', 'left')}
            className={`flex-1 px-3 py-2 text-sm rounded-lg border transition-colors ${
              settings.textAlign === 'left'
                ? 'bg-gray-200 text-gray-900 border-gray-300'
                : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
            }`}
          >
            Left
          </button>
          <button
            type="button"
            onClick={() => handleChange('textAlign', 'justify')}
            className={`flex-1 px-3 py-2 text-sm rounded-lg border transition-colors ${
              settings.textAlign === 'justify'
                ? 'bg-gray-200 text-gray-900 border-gray-300'
                : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
            }`}
          >
            Justify
          </button>
        </div>
      </div>

      {/* Font Size */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-2">
          Font Size: <span className="font-mono text-gray-700">{settings.fontSize}px</span>
        </label>
        <input
          type="range"
          min="12"
          max="24"
          step="2"
          value={settings.fontSize}
          onChange={(e) => handleChange('fontSize', parseInt(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-400"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>12px</span>
          <span>24px</span>
        </div>
      </div>

      {/* Line Height */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-2">
          Line Height: <span className="font-mono text-gray-700">{settings.lineHeight.toFixed(2)}</span>
        </label>
        <input
          type="range"
          min="1.2"
          max="2.5"
          step="0.05"
          value={settings.lineHeight}
          onChange={(e) => handleChange('lineHeight', parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-400"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>1.2</span>
          <span>2.5</span>
        </div>
      </div>

      {/* Margins */}
      <div className="space-y-3">
        <h4 className="text-xs font-medium text-gray-600">Margins (em)</h4>

        {/* Top */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">
            Top: <span className="font-mono text-gray-700">{settings.marginTop}em</span>
          </label>
          <input
            type="range"
            min="0"
            max="4"
            step="0.5"
            value={settings.marginTop}
            onChange={(e) => handleChange('marginTop', parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-400"
          />
        </div>

        {/* Bottom */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">
            Bottom: <span className="font-mono text-gray-700">{settings.marginBottom}em</span>
          </label>
          <input
            type="range"
            min="0"
            max="4"
            step="0.5"
            value={settings.marginBottom}
            onChange={(e) => handleChange('marginBottom', parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-400"
          />
        </div>

        {/* Left */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">
            Left: <span className="font-mono text-gray-700">{settings.marginLeft}em</span>
          </label>
          <input
            type="range"
            min="0"
            max="3"
            step="0.25"
            value={settings.marginLeft}
            onChange={(e) => handleChange('marginLeft', parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-400"
          />
        </div>

        {/* Right */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">
            Right: <span className="font-mono text-gray-700">{settings.marginRight}em</span>
          </label>
          <input
            type="range"
            min="0"
            max="3"
            step="0.25"
            value={settings.marginRight}
            onChange={(e) => handleChange('marginRight', parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-400"
          />
        </div>
      </div>

      {/* Chapter Spacing */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-2">
          Chapter Spacing: <span className="font-mono text-gray-700">{settings.chapterSpacing}em</span>
        </label>
        <input
          type="range"
          min="0.5"
          max="4"
          step="0.5"
          value={settings.chapterSpacing}
          onChange={(e) => handleChange('chapterSpacing', parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-400"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>Compact (0.5em)</span>
          <span>Spacious (4em)</span>
        </div>
      </div>
    </div>
  )
}
