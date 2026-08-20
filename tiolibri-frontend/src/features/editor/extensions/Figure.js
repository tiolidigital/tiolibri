import { Node, mergeAttributes } from '@tiptap/core';

/**
 * Obraz z podpisem: <figure><img><figcaption>…</figcaption></figure>.
 *
 * Podpis jest treścią węzła (`content: 'inline*'`), a nie atrybutem — dzięki temu
 * da się w nim zaznaczyć fragment i włączyć kursywę (Ctrl+I), np. nazwę łacińską,
 * bez pochylania całej linijki. Grafika i podpis są jednym blokiem, więc łamanie
 * strony w PDF ich nie rozdzieli (`break-inside: avoid` po stronie generatora).
 *
 * `fullPage` robi z figury planszę: cała strona dla grafiki, bez numeru strony.
 *
 * Stary sposób wstawiania obrazów (goły <img> w akapicie) zostaje nietknięty —
 * rozdziały napisane wcześniej otwierają się bez zmian.
 */
export const Figure = Node.create({
  name: 'figure',

  group: 'block',

  content: 'inline*',

  draggable: true,

  isolating: true,

  addAttributes() {
    return {
      src: {
        default: null,
        parseHTML: element => element.querySelector('img')?.getAttribute('src') || null,
        renderHTML: () => ({}),
      },
      alt: {
        default: null,
        parseHTML: element => element.querySelector('img')?.getAttribute('alt') || null,
        renderHTML: () => ({}),
      },
      fullPage: {
        default: false,
        parseHTML: element => element.hasAttribute('data-full-page'),
        renderHTML: attributes =>
          attributes.fullPage ? { 'data-full-page': '' } : {},
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'figure',
        // Bez obrazka to nie jest nasza figura — niech leci normalnym parserem.
        getAttrs: element => (element.querySelector('img') ? {} : false),
        // Treścią węzła jest wyłącznie podpis; obrazek siedzi w atrybucie `src`.
        contentElement: element =>
          element.querySelector('figcaption') || document.createElement('figcaption'),
      },
    ];
  },

  renderHTML({ node, HTMLAttributes }) {
    const { src, alt } = node.attrs;

    // Zapisany HTML ma zostać czysty i przenośny — sam <figure><img><figcaption>,
    // bez atrybutów pod edytor. To ten HTML ląduje w bazie, w PDF i w EPUB-ie.
    return [
      'figure',
      mergeAttributes(HTMLAttributes),
      ['img', { src: src || '', ...(alt ? { alt } : {}) }],
      ['figcaption', {}, 0],
    ];
  },

  addCommands() {
    return {
      setFigure:
        ({ src, alt = null, caption = '' } = {}) =>
        ({ chain }) =>
          chain()
            .insertContent({
              type: this.name,
              attrs: { src, alt, fullPage: false },
              content: caption ? [{ type: 'text', text: caption }] : [],
            })
            // Kursor sam nie wchodzi do podpisu — insertContent zostawia go za
            // figurą. Cofamy się do świeżo wstawionego węzła i siadamy w środku.
            .command(({ tr, commands }) => {
              const { from } = tr.selection;
              let figurePos = null;

              tr.doc.nodesBetween(Math.max(0, from - 500), from, (node, pos) => {
                if (node.type.name === this.name) figurePos = pos;
              });

              return figurePos === null ? true : commands.setTextSelection(figurePos + 1);
            })
            .run(),

      toggleFigureFullPage:
        () =>
        ({ editor, commands }) =>
          commands.updateAttributes(this.name, {
            fullPage: !editor.getAttributes(this.name).fullPage,
          }),
    };
  },

  addKeyboardShortcuts() {
    return {
      // Enter w podpisie kończy figurę i otwiera akapit pod nią — inaczej
      // `isolating` zamyka autora w podpisie i nie ma czym wyjść niżej.
      Enter: () => {
        const { state } = this.editor;
        const { $from, empty } = state.selection;

        if (!empty || $from.parent.type.name !== this.name) return false;

        const after = $from.after();

        return this.editor
          .chain()
          .insertContentAt(after, { type: 'paragraph' })
          .setTextSelection(after + 1)
          .focus()
          .run();
      },
    };
  },
});
