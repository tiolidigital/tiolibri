import { Extension } from '@tiptap/core'
import { Plugin, PluginKey } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'

export const searchAndReplaceKey = new PluginKey('searchAndReplace')

// replaceFormat: 'none' | 'italic' | 'bold' | 'boldItalic' | 'plain'
// Returns { marks, plain } where plain=true means strip all marks after insert
function buildReplaceSpec(schema, replaceFormat) {
  if (!replaceFormat || replaceFormat === 'none') return { marks: null, plain: false }
  if (replaceFormat === 'plain') return { marks: null, plain: true }
  const marks = []
  if (replaceFormat === 'italic' || replaceFormat === 'boldItalic') {
    if (schema.marks.em) marks.push(schema.marks.em.create())
  }
  if (replaceFormat === 'bold' || replaceFormat === 'boldItalic') {
    if (schema.marks.strong) marks.push(schema.marks.strong.create())
  }
  return { marks: marks.length > 0 ? marks : null, plain: false }
}

function buildSearchRegex(term, matchCase, wholeWord, useRegex) {
  if (!term) return null
  try {
    let pattern = useRegex ? term : term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    if (wholeWord) pattern = `\\b${pattern}\\b`
    return new RegExp(pattern, matchCase ? 'g' : 'gi')
  } catch {
    return null
  }
}

function findMatches(doc, regex) {
  if (!regex) return []
  const matches = []
  doc.descendants((node, pos) => {
    if (!node.isText) return
    let m
    regex.lastIndex = 0
    while ((m = regex.exec(node.text)) !== null) {
      matches.push({ from: pos + m.index, to: pos + m.index + m[0].length })
    }
  })
  return matches
}

function buildDecorations(doc, matches, currentIndex) {
  if (matches.length === 0) return DecorationSet.empty
  const decorations = matches.map((match, i) =>
    Decoration.inline(match.from, match.to, {
      class: i === currentIndex ? 'search-match-current' : 'search-match',
    })
  )
  return DecorationSet.create(doc, decorations)
}

function recomputeMatches(editor) {
  const s = editor.storage.searchAndReplace
  const regex = buildSearchRegex(s.searchTerm, s.matchCase, s.wholeWord, s.useRegex)

  if (s.useRegex && s.searchTerm && !regex) {
    s.regexError = true
  }

  const matches = findMatches(editor.state.doc, regex)
  s.matches = matches
  if (matches.length === 0) {
    s.currentIndex = 0
  } else if (s.currentIndex >= matches.length) {
    s.currentIndex = 0
  }

  // Dispatch a no-op meta transaction so the plugin re-derives decorations.
  const { tr } = editor.state
  tr.setMeta(searchAndReplaceKey, { forceUpdate: true })
  editor.view.dispatch(tr)
}

function scrollToMatch(editor) {
  const s = editor.storage.searchAndReplace
  const match = s.matches[s.currentIndex]
  if (!match) return

  const coords = editor.view.coordsAtPos(match.from)
  // Walk up from the editor DOM to find the scrollable container.
  let scrollEl = editor.view.dom.parentElement
  while (scrollEl && scrollEl.scrollHeight <= scrollEl.clientHeight) {
    scrollEl = scrollEl.parentElement
  }
  if (!scrollEl) return

  const rect = scrollEl.getBoundingClientRect()
  if (coords.top < rect.top + 80 || coords.bottom > rect.bottom - 40) {
    scrollEl.scrollBy({ top: coords.top - rect.top - 120, behavior: 'smooth' })
  }
}

export const SearchAndReplace = Extension.create({
  name: 'searchAndReplace',

  addStorage() {
    return {
      searchTerm: '',
      replaceTerm: '',
      replaceFormat: 'none',
      matchCase: false,
      wholeWord: false,
      useRegex: false,
      currentIndex: 0,
      matches: [],
      regexError: false,
    }
  },

  addCommands() {
    return {
      setSearchTerm:
        (term) =>
        ({ editor }) => {
          const s = editor.storage.searchAndReplace
          s.searchTerm = term
          s.currentIndex = 0
          s.regexError = false
          recomputeMatches(editor)
          return true
        },
      setReplaceTerm:
        (term) =>
        ({ editor }) => {
          editor.storage.searchAndReplace.replaceTerm = term
          return true
        },
      setMatchCase:
        (val) =>
        ({ editor }) => {
          const s = editor.storage.searchAndReplace
          s.matchCase = val
          s.currentIndex = 0
          recomputeMatches(editor)
          return true
        },
      setWholeWord:
        (val) =>
        ({ editor }) => {
          const s = editor.storage.searchAndReplace
          s.wholeWord = val
          s.currentIndex = 0
          recomputeMatches(editor)
          return true
        },
      setUseRegex:
        (val) =>
        ({ editor }) => {
          const s = editor.storage.searchAndReplace
          s.useRegex = val
          s.currentIndex = 0
          s.regexError = false
          recomputeMatches(editor)
          return true
        },
      findNext:
        () =>
        ({ editor }) => {
          const s = editor.storage.searchAndReplace
          if (s.matches.length === 0) return false
          s.currentIndex = (s.currentIndex + 1) % s.matches.length
          recomputeMatches(editor)
          scrollToMatch(editor)
          return true
        },
      findPrev:
        () =>
        ({ editor }) => {
          const s = editor.storage.searchAndReplace
          if (s.matches.length === 0) return false
          s.currentIndex = (s.currentIndex - 1 + s.matches.length) % s.matches.length
          recomputeMatches(editor)
          scrollToMatch(editor)
          return true
        },
      setReplaceFormat:
        (val) =>
        ({ editor }) => {
          editor.storage.searchAndReplace.replaceFormat = val
          return true
        },
      replaceOne:
        () =>
        ({ editor, tr, dispatch }) => {
          const s = editor.storage.searchAndReplace
          if (s.matches.length === 0) return false
          const match = s.matches[s.currentIndex]
          if (!match) return false
          if (dispatch) {
            const schema = editor.schema
            const { marks, plain } = buildReplaceSpec(schema, s.replaceFormat)
            const replacement = s.replaceTerm || ''
            if (plain) {
              // Insert as plain text; strip marks from the inserted range afterward.
              tr.insertText(replacement, match.from, match.to)
              const to = match.from + replacement.length
              Object.values(schema.marks).forEach((markType) => {
                tr.removeMark(match.from, to, markType)
              })
            } else if (marks) {
              const node = schema.text(replacement, marks)
              tr.replaceWith(match.from, match.to, node)
            } else {
              tr.insertText(replacement, match.from, match.to)
            }
            dispatch(tr)
            setTimeout(() => {
              recomputeMatches(editor)
              scrollToMatch(editor)
            }, 0)
          }
          return true
        },
      replaceAll:
        () =>
        ({ editor, tr, dispatch }) => {
          const s = editor.storage.searchAndReplace
          if (s.matches.length === 0) return false
          if (dispatch) {
            const schema = editor.schema
            const { marks, plain } = buildReplaceSpec(schema, s.replaceFormat)
            const replacement = s.replaceTerm || ''
            // Replace from end to start so earlier positions don't shift.
            const sorted = [...s.matches].sort((a, b) => b.from - a.from)
            sorted.forEach((match) => {
              if (plain) {
                tr.insertText(replacement, match.from, match.to)
                const to = match.from + replacement.length
                Object.values(schema.marks).forEach((markType) => {
                  tr.removeMark(match.from, to, markType)
                })
              } else if (marks) {
                const node = schema.text(replacement, marks)
                tr.replaceWith(match.from, match.to, node)
              } else {
                tr.insertText(replacement, match.from, match.to)
              }
            })
            dispatch(tr)
            setTimeout(() => recomputeMatches(editor), 0)
          }
          return true
        },
      clearSearch:
        () =>
        ({ editor }) => {
          const s = editor.storage.searchAndReplace
          s.searchTerm = ''
          s.replaceTerm = ''
          s.currentIndex = 0
          s.matches = []
          s.regexError = false
          recomputeMatches(editor)
          return true
        },
    }
  },

  addProseMirrorPlugins() {
    const extension = this
    return [
      new Plugin({
        key: searchAndReplaceKey,
        state: {
          init: () => DecorationSet.empty,
          apply(tr, _old, _oldState, newState) {
            const s = extension.editor?.storage?.searchAndReplace
            if (!s || !s.searchTerm) return DecorationSet.empty
            const regex = buildSearchRegex(s.searchTerm, s.matchCase, s.wholeWord, s.useRegex)
            if (!regex) return DecorationSet.empty
            const matches = findMatches(newState.doc, regex)
            if (s.currentIndex >= matches.length) s.currentIndex = 0
            return buildDecorations(newState.doc, matches, s.currentIndex)
          },
        },
        props: {
          decorations(state) {
            return this.getState(state)
          },
        },
      }),
    ]
  },
})
