/**
 * Google Docs HTML to Semantic HTML Converter
 *
 * Converts Google Docs exported HTML (with CSS classes) to semantic HTML
 * that TipTap can understand (strong, em, blockquote, etc.).
 */

/**
 * Parse CSS from <style> block and extract class→properties mapping.
 *
 * @param {string} styleContent - CSS string from <style> tag
 * @returns {Object} Dict mapping class names to their CSS properties
 */
function parseCssRules(styleContent) {
  const classMap = {}

  // Regex to match CSS rules: .className { property: value; }
  const rulePattern = /\.([a-zA-Z0-9_-]+)\s*\{([^}]+)\}/g
  let match

  while ((match = rulePattern.exec(styleContent)) !== null) {
    const className = match[1]
    const propertiesBlock = match[2]

    // Parse properties: "font-weight: 700; color: red;"
    const props = {}
    const propPattern = /([a-zA-Z-]+)\s*:\s*([^;]+);?/g
    let propMatch

    while ((propMatch = propPattern.exec(propertiesBlock)) !== null) {
      const propName = propMatch[1].trim()
      const propValue = propMatch[2].trim()
      props[propName] = propValue
    }

    if (Object.keys(props).length > 0) {
      classMap[className] = props
    }
  }

  return classMap
}

/**
 * Identify which CSS classes should map to semantic HTML tags.
 *
 * @param {Object} classMap - Dict from parseCssRules()
 * @returns {Object} Dict mapping class names to semantic tags
 */
function identifySemanticClasses(classMap) {
  const semanticMap = {}

  for (const [className, props] of Object.entries(classMap)) {
    // Check for bold (font-weight: 700 or "bold")
    const fontWeight = props['font-weight'] || ''
    if (['700', 'bold', '800', '900'].includes(fontWeight)) {
      semanticMap[className] = 'strong'
      continue
    }

    // Check for italic (font-style: italic)
    const fontStyle = props['font-style'] || ''
    if (fontStyle === 'italic') {
      semanticMap[className] = 'em'
      continue
    }

    // Check for blockquote (border-left + padding)
    const borderLeft = props['border-left'] || ''
    const paddingLeft = props['padding-left'] || ''
    if (borderLeft && paddingLeft) {
      semanticMap[className] = 'blockquote'
      continue
    }
  }

  return semanticMap
}

/**
 * Process HTML element and convert classes to semantic tags.
 *
 * @param {HTMLElement} element - DOM element to process
 * @param {Object} semanticMap - Dict from identifySemanticClasses()
 */
function processElement(element, semanticMap) {
  if (element.nodeType !== Node.ELEMENT_NODE) return

  // Process children first (depth-first)
  const children = Array.from(element.children)
  for (const child of children) {
    processElement(child, semanticMap)
  }

  // Get classes on this element
  const classes = Array.from(element.classList || [])

  // Handle blockquote (p tags with blockquote class)
  const blockquoteClasses = classes.filter((c) => semanticMap[c] === 'blockquote')
  if (
    blockquoteClasses.length > 0 &&
    (element.tagName === 'P' || element.tagName === 'DIV')
  ) {
    // Create blockquote element
    const blockquote = document.createElement('blockquote')
    blockquote.innerHTML = element.innerHTML

    // Replace element with blockquote
    element.replaceWith(blockquote)
    element = blockquote

    // Remove blockquote classes
    for (const bc of blockquoteClasses) {
      element.classList.remove(bc)
    }
  }

  // Find semantic tags to apply (strong, em)
  const tagsToApply = []
  for (const className of classes) {
    if (semanticMap[className] && ['strong', 'em'].includes(semanticMap[className])) {
      tagsToApply.push(semanticMap[className])
    }
  }

  // Apply semantic tags (wrap content)
  if (tagsToApply.length > 0) {
    let currentElement = element

    // Wrap content in semantic tags (innermost first)
    for (const tagName of tagsToApply) {
      const wrapper = document.createElement(tagName)
      wrapper.innerHTML = currentElement.innerHTML
      currentElement.innerHTML = ''
      currentElement.appendChild(wrapper)
    }
  }

  // Remove class attribute
  element.removeAttribute('class')

  // Remove style attribute
  element.removeAttribute('style')

  // If this is a <span> with no attributes left, unwrap it
  if (element.tagName === 'SPAN' && element.attributes.length === 0) {
    // Replace span with its contents
    const parent = element.parentNode
    if (parent) {
      while (element.firstChild) {
        parent.insertBefore(element.firstChild, element)
      }
      parent.removeChild(element)
    }
  }
}

/**
 * Convert Google Docs HTML to semantic HTML for TipTap.
 *
 * @param {string} html - Google Docs exported HTML string
 * @returns {string} Clean semantic HTML string
 */
export function convertGoogleDocsHtml(html) {
  // Create a temporary DOM to parse HTML
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')

  // Find and parse <style> block
  const styleTag = doc.querySelector('style')
  let semanticMap = {}

  if (styleTag) {
    const styleContent = styleTag.textContent || ''
    const classMap = parseCssRules(styleContent)
    semanticMap = identifySemanticClasses(classMap)

    // Remove <style> tag
    styleTag.remove()
  }

  // Remove Google Docs meta tags
  const metaTags = doc.querySelectorAll('meta')
  metaTags.forEach((meta) => meta.remove())

  // Get body content
  const body = doc.body || doc.documentElement

  // Process all elements to convert classes to semantic tags
  const allElements = body.querySelectorAll('*')
  for (const element of allElements) {
    processElement(element, semanticMap)
  }

  // Clean up empty elements
  const emptyElements = body.querySelectorAll('span:empty, div:empty')
  emptyElements.forEach((el) => {
    if (el.children.length === 0 && !el.textContent.trim()) {
      el.remove()
    }
  })

  // Extract body HTML
  let result = body.innerHTML

  // Clean up extra whitespace
  result = result.replace(/\n\s*\n/g, '\n').trim()

  return result
}

/**
 * Check if HTML looks like it came from Google Docs export.
 *
 * @param {string} html - HTML string to check
 * @returns {boolean} True if HTML appears to be from Google Docs
 */
export function isGoogleDocsHtml(html) {
  const markers = [
    'docs-internal-guid',
    'id="docs-internal-guid',
    '<meta charset="utf-8">',
    '<style type="text/css">',
  ]

  return markers.some((marker) => html.includes(marker))
}
