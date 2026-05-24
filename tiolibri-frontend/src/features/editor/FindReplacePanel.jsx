import { useState, useEffect, useRef, useCallback, useReducer } from 'react'

const QUICK_FIXES = [
  {
    label: '-- → —',
    title: 'Zamień -- na em-dash (—)',
    find: '--',
    replace: '—',
    useRegex: false,
    confirm: (n) => `Zamienić ${n} wystąpień "--" na "—"?`,
  },
  {
    label: '- → –',
    title: 'Zamień dywiz między liczbami na półpauze (–) — pomija nazwy jak KB-3-1, MCF-7',
    find: '(?<![A-Za-z\\-])(\\d+)\\s*-\\s*(\\d+)(?![A-Za-z])',
    replace: '$1–$2',
    useRegex: true,
    confirm: (n) => `Zamienić ${n} zakresów liczbowych z dywizem na półpauze (–)?`,
  },
  {
    label: 'rok-rok → –',
    title: 'Zamień dywiz między latami (np. 2020-2025) na półpauze (–)',
    find: '(\\b\\d{4})\\s*-\\s*(\\d{4}\\b)',
    replace: '$1–$2',
    useRegex: true,
    confirm: (n) => `Zamienić ${n} zakresów lat z dywizem na półpauze (–)?`,
  },
  {
    label: ' - → –',
    title: 'Zamień dywiz otoczony spacjami na półpauze (–) — dla wtrąceń i pauz narracyjnych',
    find: ' - ',
    replace: ' – ',
    useRegex: false,
    confirm: (n) => `Zamienić ${n} wystąpień " - " (dywiz ze spacjami) na " – " (półpauza)?`,
  },
  {
    label: 'biało–czerwony → -',
    title: 'Zamień półpauze bez spacji (złożenia przymiotnikowe) na dywiz (–→-)',
    find: '([^\\s\\d])–([^\\s\\d])',
    replace: '$1-$2',
    useRegex: true,
    confirm: (n) => `Zamienić ${n} półpauz w złożeniach (bez spacji, np. "biało–czerwony") na dywiz?`,
  },
  {
    label: '... → …',
    title: 'Zamień ... na wielokropek (…)',
    find: '\\.\\.\\.',
    replace: '…',
    useRegex: true,
    confirm: (n) => `Zamienić ${n} wystąpień "..." na "…"?`,
  },
  {
    label: '" " → „ ”',
    title: 'Zamień cudzysłowy na polskie (Polish quotes)',
    find: null, // handled specially
    replace: null,
    useRegex: false,
    special: 'polish-quotes',
    confirm: (n) => `Zamienić ${n} par cudzysłowów na polskie „…”?`,
  },
  {
    label: '  → ␣',
    title: 'Usuń podwójne spacje',
    find: ' {2,}',
    replace: ' ',
    useRegex: true,
    confirm: (n) => `Usunąć ${n} wystąpień podwójnych spacji?`,
  },
  {
    label: '⎵→∅',
    title: 'Usuń spacje na końcu wierszy',
    find: ' +$',
    replace: '',
    useRegex: true,
    confirm: (n) => `Usunąć spacje na końcu ${n} wierszy?`,
  },
]

// Apply Polish quotes transformation — only in text nodes, never in HTML attributes.
function applyPolishQuotes(html) {
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')
  let pairCount = 0

  const walk = (node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      const replaced = node.textContent.replace(/(["“„])([^"”]*?)(["”])/g, (match, _open, inner) => {
        const normalized = `„${inner}”`
        if (match !== normalized) pairCount++
        return normalized
      })
      if (replaced !== node.textContent) node.textContent = replaced
    } else {
      node.childNodes.forEach(walk)
    }
  }
  walk(doc.body)

  return { html: doc.body.innerHTML, count: pairCount }
}

// Build a RegExp that matches the editor extension's semantics for search.
function buildHtmlSearchRegex(find, useRegex, matchCase, wholeWord) {
  try {
    let pattern = useRegex ? find : find.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    if (wholeWord) pattern = `\\b${pattern}\\b`
    return new RegExp(pattern, matchCase ? 'g' : 'gi')
  } catch {
    return null
  }
}

// Count regex matches in an HTML string (strips tags first)
function countMatchesInHtml(html, find, useRegex, matchCase, wholeWord) {
  const text = html.replace(/<[^>]+>/g, ' ')
  const re = buildHtmlSearchRegex(find, useRegex, matchCase, wholeWord)
  if (!re) return 0
  return (text.match(re) || []).length
}

const FORMAT_TAG = { italic: 'em', bold: 'strong', boldItalic: 'strong', plain: null, none: null }
const FORMAT_WRAP = { boldItalic: 'em' }

// Apply regex replace to an HTML string (replaces in text nodes only via DOM)
function applyReplaceInHtml(html, find, replace, useRegex, matchCase, wholeWord, replaceFormat = 'none') {
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')
  const re = buildHtmlSearchRegex(find, useRegex, matchCase, wholeWord)
  if (!re) return html

  const wrapWithFormat = (text) => {
    if (!replaceFormat || replaceFormat === 'none') return doc.createTextNode(text)
    if (replaceFormat === 'plain') return doc.createTextNode(text)
    const outer = FORMAT_TAG[replaceFormat] ? doc.createElement(FORMAT_TAG[replaceFormat]) : null
    const inner = FORMAT_WRAP[replaceFormat] ? doc.createElement(FORMAT_WRAP[replaceFormat]) : null
    const textNode = doc.createTextNode(text)
    if (outer && inner) {
      inner.appendChild(textNode)
      outer.appendChild(inner)
      return outer
    }
    if (outer) {
      outer.appendChild(textNode)
      return outer
    }
    return textNode
  }

  const walk = (node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      if (replaceFormat === 'none') {
        node.textContent = node.textContent.replace(re, replace)
      } else {
        // Need to split text node and wrap matches
        const text = node.textContent
        const parts = []
        let lastIndex = 0
        re.lastIndex = 0
        let m
        while ((m = re.exec(text)) !== null) {
          if (m.index > lastIndex) parts.push(doc.createTextNode(text.slice(lastIndex, m.index)))
          const replacement = replace.replace(/\$(\d+)/g, (_, g) => m[parseInt(g)] ?? '')
          parts.push(wrapWithFormat(replacement))
          lastIndex = m.index + m[0].length
          if (m[0].length === 0) re.lastIndex++
        }
        if (lastIndex < text.length) parts.push(doc.createTextNode(text.slice(lastIndex)))
        if (parts.length > 0 && parts.length !== 1) {
          const frag = doc.createDocumentFragment()
          parts.forEach((p) => frag.appendChild(p))
          node.parentNode?.replaceChild(frag, node)
          return
        }
        if (parts.length === 1 && parts[0].nodeType !== Node.TEXT_NODE) {
          node.parentNode?.replaceChild(parts[0], node)
          return
        }
        node.textContent = text.replace(re, replace)
      }
    } else {
      // Walk children in reverse so we can safely replace nodes
      const children = [...node.childNodes]
      children.forEach(walk)
    }
  }
  walk(doc.body)
  return doc.body.innerHTML
}

export default function FindReplacePanel({
  editor,
  showReplace: initialShowReplace = false,
  scope,
  onScopeChange,
  chapters,
  onSaveChapter,
  onClose,
}) {
  const [searchTerm, setSearchTerm] = useState('')
  const [replaceTerm, setReplaceTerm] = useState('')
  const [showReplace, setShowReplace] = useState(initialShowReplace)
  const [matchCase, setMatchCase] = useState(false)
  const [wholeWord, setWholeWord] = useState(false)
  const [useRegex, setUseRegex] = useState(false)
  const [replaceFormat, setReplaceFormat] = useState('none')
  const [bookProgress, setBookProgress] = useState(null) // { current, total } or null
  const [confirmState, setConfirmState] = useState(null) // { message, onConfirm }
  const searchInputRef = useRef(null)
  // Trigger re-renders when the editor dispatches transactions (match count changes etc.)
  const [, forceUpdate] = useReducer((x) => x + 1, 0)

  // Focus search input on mount
  useEffect(() => {
    searchInputRef.current?.focus()
  }, [])

  // Re-render whenever the editor processes a transaction so match counts stay fresh.
  useEffect(() => {
    if (!editor) return
    editor.on('transaction', forceUpdate)
    return () => editor.off('transaction', forceUpdate)
  }, [editor])

  // Sync search term to editor extension
  useEffect(() => {
    if (!editor) return
    editor.commands.setSearchTerm(searchTerm)
  }, [editor, searchTerm])

  useEffect(() => {
    if (!editor) return
    editor.commands.setMatchCase(matchCase)
  }, [editor, matchCase])

  useEffect(() => {
    if (!editor) return
    editor.commands.setWholeWord(wholeWord)
  }, [editor, wholeWord])

  useEffect(() => {
    if (!editor) return
    editor.commands.setUseRegex(useRegex)
  }, [editor, useRegex])

  useEffect(() => {
    if (!editor) return
    editor.commands.setReplaceTerm(replaceTerm)
  }, [editor, replaceTerm])

  useEffect(() => {
    if (!editor) return
    editor.commands.setReplaceFormat(replaceFormat)
  }, [editor, replaceFormat])

  const storage = editor?.storage?.searchAndReplace
  const matchCount = storage?.matches?.length ?? 0
  const currentIndex = storage?.currentIndex ?? 0
  const regexError = storage?.regexError ?? false

  const handleFindNext = useCallback(() => {
    editor?.commands.findNext()
  }, [editor])

  const handleFindPrev = useCallback(() => {
    editor?.commands.findPrev()
  }, [editor])

  const handleReplaceOne = useCallback(() => {
    if (!editor || matchCount === 0) return
    editor.commands.replaceOne()
  }, [editor, matchCount])

  // "Entire book" replace: iterate chapters, update their processed_html, save via callback
  const runBookReplaceAll = useCallback(async () => {
    if (!chapters || chapters.length === 0 || !searchTerm) return

    let total = 0
    let skipped = 0
    for (const ch of chapters) {
      if (!ch.processed_html) {
        skipped++
        continue
      }
      total += countMatchesInHtml(ch.processed_html, searchTerm, useRegex, matchCase, wholeWord)
    }
    total += matchCount

    if (total === 0) return

    let message = `Zamienić ${total} wystąpień w całej książce (${chapters.length} rozdziałów)?`
    if (skipped > 0) {
      message += `\n\nUwaga: ${skipped} ${skipped === 1 ? 'rozdział nie ma' : 'rozdziałów nie ma'} jeszcze przetworzonej zawartości i ${skipped === 1 ? 'zostanie' : 'zostaną'} pominięte. Otwórz je najpierw w edytorze, aby uwzględnić w zamianie.`
    }

    const confirmed = window.confirm(message)
    if (!confirmed) return

    setBookProgress({ current: 0, total: chapters.length })

    for (let i = 0; i < chapters.length; i++) {
      const ch = chapters[i]
      setBookProgress({ current: i + 1, total: chapters.length })
      if (!ch.processed_html) continue
      const newHtml = applyReplaceInHtml(
        ch.processed_html,
        searchTerm,
        replaceTerm,
        useRegex,
        matchCase,
        wholeWord,
        replaceFormat
      )
      if (newHtml !== ch.processed_html) {
        await onSaveChapter(ch.id, newHtml)
      }
    }

    if (matchCount > 0) {
      editor.commands.replaceAll()
    }

    setBookProgress(null)
  }, [
    chapters,
    searchTerm,
    replaceTerm,
    replaceFormat,
    useRegex,
    matchCase,
    wholeWord,
    matchCount,
    editor,
    onSaveChapter,
  ])

  const handleReplaceAll = useCallback(() => {
    if (!editor || !searchTerm) return
    if (scope === 'book') {
      runBookReplaceAll()
      return
    }
    if (matchCount === 0) return
    const confirmed = window.confirm(`Zamienić ${matchCount} wystąpień?`)
    if (confirmed) editor.commands.replaceAll()
  }, [editor, searchTerm, scope, matchCount, runBookReplaceAll])

  const runPolishQuotesQuickFix = useCallback(async () => {
    if (scope === 'chapter') {
      const html = editor.getHTML()
      const { html: newHtml, count } = applyPolishQuotes(html)
      if (count === 0) {
        alert('Brak cudzysłowów do zamiany.')
        return
      }
      setConfirmState({
        message: `Zamienić ${count} par cudzysłowów na polskie „…”?`,
        onConfirm: () => {
          editor.commands.setContent(newHtml, false)
          setConfirmState(null)
        },
      })
    } else {
      let total = 0
      const replacements = []
      for (const ch of chapters) {
        if (!ch.processed_html) continue
        const { html: newHtml, count } = applyPolishQuotes(ch.processed_html)
        total += count
        replacements.push({ id: ch.id, newHtml, changed: newHtml !== ch.processed_html })
      }
      if (total === 0) {
        alert('Brak cudzysłowów w żadnym rozdziale.')
        return
      }
      setConfirmState({
        message: `Zamienić ${total} par cudzysłowów na polskie „…”? (${chapters.length} rozdziałów)`,
        onConfirm: async () => {
          setConfirmState(null)
          setBookProgress({ current: 0, total: replacements.length })
          for (let i = 0; i < replacements.length; i++) {
            setBookProgress({ current: i + 1, total: replacements.length })
            const r = replacements[i]
            if (r.changed) await onSaveChapter(r.id, r.newHtml)
          }
          setBookProgress(null)
        },
      })
    }
  }, [editor, scope, chapters, onSaveChapter])

  // Quick fix: runs a preset replace (current chapter or whole book)
  const runQuickFix = useCallback(
    async (fix) => {
      if (fix.special === 'polish-quotes') {
        await runPolishQuotesQuickFix()
        return
      }

      if (scope === 'chapter') {
        const count = countMatchesInHtml(editor.getHTML(), fix.find, fix.useRegex, false, false)
        if (count === 0) {
          alert('Brak wystąpień.')
          return
        }
        setConfirmState({
          message: fix.confirm(count),
          onConfirm: () => {
            // Apply directly to the editor HTML so we don't clobber the user's
            // search-term/regex/case state in the panel storage.
            const currentHtml = editor.getHTML()
            const newHtml = applyReplaceInHtml(
              currentHtml,
              fix.find,
              fix.replace,
              fix.useRegex,
              false,
              false
            )
            if (newHtml !== currentHtml) {
              editor.commands.setContent(newHtml, false)
            }
            setConfirmState(null)
          },
        })
      } else {
        let total = 0
        for (const ch of chapters) {
          if (!ch.processed_html) continue
          total += countMatchesInHtml(ch.processed_html, fix.find, fix.useRegex, false, false)
        }
        if (total === 0) {
          alert('Brak wystąpień w żadnym rozdziale.')
          return
        }
        setConfirmState({
          message: fix.confirm(total) + ` (${chapters.length} rozdziałów)`,
          onConfirm: async () => {
            setConfirmState(null)
            setBookProgress({ current: 0, total: chapters.length })
            for (let i = 0; i < chapters.length; i++) {
              const ch = chapters[i]
              setBookProgress({ current: i + 1, total: chapters.length })
              if (!ch.processed_html) continue
              const newHtml = applyReplaceInHtml(
                ch.processed_html,
                fix.find,
                fix.replace,
                fix.useRegex,
                false,
                false
              )
              if (newHtml !== ch.processed_html) {
                await onSaveChapter(ch.id, newHtml)
              }
            }
            setBookProgress(null)
          },
        })
      }
    },
    [editor, scope, chapters, onSaveChapter, runPolishQuotesQuickFix]
  )

  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (e.shiftKey) handleFindPrev()
      else handleFindNext()
    }
    if (e.key === 'Escape') {
      e.preventDefault()
      onClose()
    }
  }

  return (
    <div
      className="bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden"
      role="search"
      aria-label="Znajdź i zamień"
    >
      {/* Confirmation overlay */}
      {confirmState && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/20 rounded-lg">
          <div className="bg-white border border-gray-200 rounded-lg shadow-xl p-4 max-w-xs mx-4">
            <p className="text-sm text-gray-700 mb-3">{confirmState.message}</p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setConfirmState(null)}
                className="px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900 border border-gray-200 rounded"
              >
                Nie
              </button>
              <button
                onClick={confirmState.onConfirm}
                className="px-3 py-1.5 text-xs bg-[#e3704a] text-white rounded hover:bg-[#c9613d]"
              >
                Tak
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="px-3 py-2.5 space-y-2">
        {/* Row 1: Search */}
        <div className="flex items-center gap-2">
          <div className="flex-1 relative">
            <input
              ref={searchInputRef}
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              placeholder="Znajdź…"
              className={`w-full text-sm px-2.5 py-1.5 border rounded focus:outline-none focus:ring-1 ${
                regexError
                  ? 'border-red-400 focus:ring-red-300 bg-red-50'
                  : 'border-gray-300 focus:ring-[#e3704a] focus:border-[#e3704a]'
              }`}
              aria-label="Szukaj"
            />
          </div>

          {/* Match counter */}
          <span className="text-xs text-gray-500 whitespace-nowrap min-w-[60px] text-center">
            {regexError ? (
              <span className="text-red-500">błąd regex</span>
            ) : searchTerm ? (
              matchCount === 0 ? (
                'Brak'
              ) : (
                `${currentIndex + 1} z ${matchCount}`
              )
            ) : (
              ''
            )}
          </span>

          {/* Prev / Next */}
          <button
            onClick={handleFindPrev}
            disabled={matchCount === 0}
            title="Poprzednie (Shift+Enter)"
            className="p-1 text-gray-500 hover:text-gray-900 disabled:opacity-30 rounded"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <path d="M10 9L7 6l-3 3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          <button
            onClick={handleFindNext}
            disabled={matchCount === 0}
            title="Następne (Enter)"
            className="p-1 text-gray-500 hover:text-gray-900 disabled:opacity-30 rounded"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <path d="M4 5l3 3 3-3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          {/* Toggle replace */}
          <button
            onClick={() => setShowReplace((v) => !v)}
            title="Pokaż/ukryj zamień"
            className={`p-1 rounded transition-colors ${showReplace ? 'text-[#e3704a] bg-orange-50' : 'text-gray-400 hover:text-gray-700'}`}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
            >
              <path
                d="M1 4h9M8 2l2 2-2 2M13 10H4m2 2l-2-2 2-2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>

          {/* Close */}
          <button
            onClick={onClose}
            title="Zamknij (Esc)"
            className="p-1 text-gray-400 hover:text-gray-700 rounded"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <path d="M3 3l8 8M11 3l-8 8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>

        {/* Row 2: Replace (conditional) */}
        {showReplace && (
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={replaceTerm}
                onChange={(e) => setReplaceTerm(e.target.value)}
                onKeyDown={(e) => e.key === 'Escape' && onClose()}
                placeholder="Zamień na…"
                className="flex-1 text-sm px-2.5 py-1.5 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-[#e3704a] focus:border-[#e3704a]"
                aria-label="Zamień na"
              />
              <button
                onClick={handleReplaceOne}
                disabled={matchCount === 0}
                className="px-2.5 py-1.5 text-xs text-gray-700 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40 whitespace-nowrap"
              >
                Zamień
              </button>
              <button
                onClick={handleReplaceAll}
                disabled={matchCount === 0 && scope === 'chapter'}
                className="px-2.5 py-1.5 text-xs bg-[#e3704a] text-white rounded hover:bg-[#c9613d] disabled:opacity-40 whitespace-nowrap"
              >
                Zamień wszystko
              </button>
            </div>
            {/* Format of replaced text */}
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-xs text-gray-400 shrink-0">Format zamiany:</span>
              {[
                { value: 'none', label: 'Bez zmian' },
                { value: 'italic', label: 'Kursywa' },
                { value: 'bold', label: 'Pogrubienie' },
                { value: 'boldItalic', label: 'Pogrubiona kursywa' },
                { value: 'plain', label: 'Zwykły tekst' },
              ].map((opt) => (
                <label key={opt.value} className="flex items-center gap-1 text-xs text-gray-600 cursor-pointer">
                  <input
                    type="radio"
                    name="replaceFormat"
                    value={opt.value}
                    checked={replaceFormat === opt.value}
                    onChange={() => setReplaceFormat(opt.value)}
                    className="accent-[#e3704a] w-3 h-3"
                  />
                  {opt.label}
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Row 3: Options + Scope */}
        <div className="flex items-center gap-4 flex-wrap">
          <label className="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={matchCase}
              onChange={(e) => setMatchCase(e.target.checked)}
              className="accent-[#e3704a] w-3 h-3"
            />
            Wielkość liter
          </label>
          <label className="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={wholeWord}
              onChange={(e) => setWholeWord(e.target.checked)}
              className="accent-[#e3704a] w-3 h-3"
            />
            Całe słowo
          </label>
          <label className="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={useRegex}
              onChange={(e) => setUseRegex(e.target.checked)}
              className="accent-[#e3704a] w-3 h-3"
            />
            Regex
          </label>

          <div className="ml-auto flex items-center gap-1.5">
            <span className="text-xs text-gray-500">Zakres:</span>
            <select
              value={scope}
              onChange={(e) => onScopeChange(e.target.value)}
              className="text-xs border border-gray-300 rounded px-1.5 py-1 focus:outline-none focus:ring-1 focus:ring-[#e3704a]"
            >
              <option value="chapter">Bieżący rozdział</option>
              <option value="book">Cała książka</option>
            </select>
          </div>
        </div>

        {/* Row 4: Quick fixes */}
        <div className="flex items-center gap-2 pt-1 border-t border-gray-100 flex-wrap">
          <span className="text-xs text-gray-400 shrink-0">Szybkie korekty:</span>
          {QUICK_FIXES.map((fix) => (
            <button
              key={fix.label}
              onClick={() => runQuickFix(fix)}
              title={fix.title}
              className="px-2 py-0.5 text-xs font-mono border border-gray-200 rounded hover:border-[#e3704a] hover:text-[#e3704a] transition-colors whitespace-nowrap"
            >
              {fix.label}
            </button>
          ))}
        </div>

        {/* Book-scope progress */}
        {bookProgress && (
          <div className="text-xs text-gray-500 flex items-center gap-2 pt-0.5">
            <div className="animate-spin h-3 w-3 border border-[#e3704a] border-t-transparent rounded-full shrink-0" />
            Zastępuję w rozdziale {bookProgress.current} z {bookProgress.total}…
          </div>
        )}
      </div>
    </div>
  )
}
