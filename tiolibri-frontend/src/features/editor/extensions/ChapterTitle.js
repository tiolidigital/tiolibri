import { Extension } from '@tiptap/core';

/**
 * Wyjątek per rozdział dla tytułu spod grafiki otwierającej.
 *
 * Rozdział otwarty grafiką trzyma ją w nagłówku: `<h1><img ...>Rozdział 1: …</h1>`.
 * Grafika u Ewy ma tytuł w sobie, więc generator domyślnie chowa ten nagłówek —
 * inaczej tytuł stoi w książce dwa razy. Bywa jednak, że grafika niesie co innego
 * (inny tytuł, sam obraz, podtytuł) i nagłówek ma zostać widoczny.
 *
 * Ten atrybut jest właśnie takim wyjątkiem: `data-chapter-title="visible"` albo
 * `"hidden"` na `<h1>`. Gdy go nie ma, decyduje ustawienie książki
 * (`hideOpenerTitle` w typografii). Nagłówek ZAWSZE zostaje w treści — bez niego
 * spis treści nie miałby dokąd skoczyć, a EPUB nie miałby skąd wziąć nazwy rozdziału.
 *
 * Zapisany HTML zostaje czysty: bez kliknięcia w guzik żaden atrybut nie dochodzi.
 */
export const ChapterTitle = Extension.create({
  name: 'chapterTitle',

  addGlobalAttributes() {
    return [
      {
        types: ['heading'],
        attributes: {
          chapterTitle: {
            default: null,
            parseHTML: element => element.getAttribute('data-chapter-title'),
            renderHTML: attributes =>
              attributes.chapterTitle
                ? { 'data-chapter-title': attributes.chapterTitle }
                : {},
          },
        },
      },
    ];
  },

  addCommands() {
    return {
      // 'visible' | 'hidden' | null (null = wróć do ustawienia książki)
      setChapterTitleVisibility:
        value =>
        ({ commands }) =>
          commands.updateAttributes('heading', { chapterTitle: value }),
    };
  },
});

/**
 * Czy kursor stoi w nagłówku otwierającym rozdział grafiką.
 *
 * Generator patrzy wyłącznie na PIERWSZY nagłówek rozdziału, więc guzik pokazujemy
 * tylko tam — gdziekolwiek indziej atrybut niczego by nie zmienił.
 *
 * Zwraca `{ setting }` (wartość atrybutu albo null) albo `null`, gdy to nie ten nagłówek.
 */
export function openerTitleState(editor) {
  if (!editor) return null;

  const { $from } = editor.state.selection;
  if ($from.depth < 1 || $from.before(1) !== 0) return null;

  const first = editor.state.doc.firstChild;
  if (!first || first.type.name !== 'heading' || first.attrs.level !== 1) return null;

  let hasImage = false;
  first.forEach(child => {
    if (child.type.name === 'image') hasImage = true;
  });
  if (!hasImage) return null;

  return { setting: first.attrs.chapterTitle || null };
}
