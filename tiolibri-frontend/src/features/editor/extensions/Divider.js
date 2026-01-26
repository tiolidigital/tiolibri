import { Node, mergeAttributes } from '@tiptap/core';

export const Divider = Node.create({
  name: 'divider',

  group: 'block',

  atom: true,

  addAttributes() {
    return {
      style: {
        default: 'stars',
        parseHTML: element => element.getAttribute('data-divider-style'),
        renderHTML: attributes => {
          return {
            'data-divider-style': attributes.style,
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-divider]',
      },
    ];
  },

  renderHTML({ node, HTMLAttributes }) {
    const style = node.attrs.style || 'stars';

    // Define SVG elements as DOM structure (not innerHTML string)
    const svgElements = {
      stars: [
        'svg',
        {
          width: '120',
          height: '20',
          viewBox: '0 0 120 20',
          fill: 'none',
          xmlns: 'http://www.w3.org/2000/svg'
        },
        ['circle', { cx: '40', cy: '10', r: '2', fill: 'currentColor' }],
        ['circle', { cx: '60', cy: '10', r: '2', fill: 'currentColor' }],
        ['circle', { cx: '80', cy: '10', r: '2', fill: 'currentColor' }],
      ],

      line: [
        'svg',
        {
          width: '200',
          height: '20',
          viewBox: '0 0 200 20',
          fill: 'none',
          xmlns: 'http://www.w3.org/2000/svg'
        },
        ['line', { x1: '20', y1: '10', x2: '90', y2: '10', stroke: 'currentColor', 'stroke-width': '1' }],
        ['circle', { cx: '100', cy: '10', r: '3', fill: 'currentColor' }],
        ['line', { x1: '110', y1: '10', x2: '180', y2: '10', stroke: 'currentColor', 'stroke-width': '1' }],
      ],

      dots: [
        'svg',
        {
          width: '100',
          height: '20',
          viewBox: '0 0 100 20',
          fill: 'none',
          xmlns: 'http://www.w3.org/2000/svg'
        },
        ['circle', { cx: '35', cy: '10', r: '1.5', fill: 'currentColor' }],
        ['circle', { cx: '50', cy: '10', r: '1.5', fill: 'currentColor' }],
        ['circle', { cx: '65', cy: '10', r: '1.5', fill: 'currentColor' }],
      ],
    };

    return [
      'div',
      mergeAttributes(HTMLAttributes, {
        'data-divider': '',
        'data-divider-style': style,
        style: 'text-align: center; margin: 2em 0; user-select: none;',
      }),
      [
        'div',
        { style: 'display: inline-block;' },
        svgElements[style] || svgElements.stars,
      ],
    ];
  },

  addCommands() {
    return {
      setDivider: (style = 'stars') => ({ commands }) => {
        return commands.insertContent({
          type: this.name,
          attrs: { style },
        });
      },
    };
  },
});
