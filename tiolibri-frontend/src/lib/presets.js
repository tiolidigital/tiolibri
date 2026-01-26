/**
 * Style Presets - Font family mappings
 * These match the font-family definitions in tiolibri-api/app/presets/*.css
 */

export const STYLE_PRESETS = {
  classic: {
    name: 'Classic',
    description: 'Crimson Text, traditional typography',
    fontFamily: '"Crimson Text", "Georgia", "Times New Roman", serif',
  },
  modern: {
    name: 'Modern',
    description: 'Inter, clean and minimal',
    fontFamily: '"Inter", "Helvetica Neue", Arial, sans-serif',
  },
  minimal: {
    name: 'Minimal',
    description: 'System font, no frills',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif',
  },
}

/**
 * Get preset object from preset name string
 * @param {string} presetName - "classic" | "modern" | "minimal"
 * @returns {Object} Preset object with fontFamily
 */
export function getPreset(presetName) {
  return STYLE_PRESETS[presetName] || STYLE_PRESETS.classic
}
