"""
Google Docs HTML to Semantic HTML Converter

Converts Google Docs exported HTML (with CSS classes) to semantic HTML
that TipTap can understand (strong, em, blockquote, etc.).

Usage:
    from app.utils.html_converter import convert_google_docs_html

    clean_html = convert_google_docs_html(google_docs_html)
"""

import re
from typing import Dict, Set
from bs4 import BeautifulSoup, NavigableString, Tag


def parse_css_rules(style_content: str) -> Dict[str, Dict[str, str]]:
    """
    Parse CSS from <style> block and extract class→properties mapping.

    Args:
        style_content: CSS string from <style> tag

    Returns:
        Dict mapping class names to their CSS properties
        Example: {'c8': {'font-weight': '700'}, 'c5': {'font-style': 'italic'}}
    """
    class_map = {}

    # Regex to match CSS rules: .className { property: value; }
    # Handles multi-line rules and multiple properties
    rule_pattern = r'\.([a-zA-Z0-9_-]+)\s*\{([^}]+)\}'

    for match in re.finditer(rule_pattern, style_content):
        class_name = match.group(1)
        properties_block = match.group(2)

        # Parse properties: "font-weight: 700; color: red;"
        props = {}
        prop_pattern = r'([a-zA-Z-]+)\s*:\s*([^;]+);?'

        for prop_match in re.finditer(prop_pattern, properties_block):
            prop_name = prop_match.group(1).strip()
            prop_value = prop_match.group(2).strip()
            props[prop_name] = prop_value

        if props:
            class_map[class_name] = props

    return class_map


def identify_semantic_classes(class_map: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    """
    Identify which CSS classes should map to semantic HTML tags.

    Args:
        class_map: Dict from parse_css_rules()

    Returns:
        Dict mapping class names to semantic tags
        Example: {'c8': 'strong', 'c5': 'em', 'c0': 'blockquote'}
    """
    semantic_map = {}

    for class_name, props in class_map.items():
        # Check for bold (font-weight: 700 or "bold")
        font_weight = props.get('font-weight', '')
        if font_weight in ('700', 'bold', '800', '900'):
            semantic_map[class_name] = 'strong'
            continue

        # Check for italic (font-style: italic)
        font_style = props.get('font-style', '')
        if font_style == 'italic':
            semantic_map[class_name] = 'em'
            continue

        # Check for blockquote (border-left + padding)
        border_left = props.get('border-left', '')
        padding_left = props.get('padding-left', '')
        if border_left and padding_left:
            semantic_map[class_name] = 'blockquote'
            continue

    return semantic_map


def wrap_with_tag(element: Tag, tag_name: str) -> Tag:
    """
    Wrap element's contents with a semantic tag.

    Args:
        element: BeautifulSoup Tag to wrap
        tag_name: Semantic tag name (strong, em, etc.)

    Returns:
        New tag wrapping the content
    """
    new_tag = element.new_tag(tag_name)

    # Move all children to new tag
    for child in list(element.children):
        new_tag.append(child.extract())

    return new_tag


def process_element(element: Tag, semantic_map: Dict[str, str], soup: BeautifulSoup) -> None:
    """
    Recursively process HTML element and convert classes to semantic tags.

    Args:
        element: BeautifulSoup Tag to process
        semantic_map: Dict from identify_semantic_classes()
        soup: BeautifulSoup object for creating new tags
    """
    if isinstance(element, NavigableString):
        return

    # Process children first (depth-first)
    for child in list(element.children):
        if isinstance(child, Tag):
            process_element(child, semantic_map, soup)

    # Get classes on this element
    classes = element.get('class', [])

    # Find semantic tags to apply (in order: strong, em)
    tags_to_apply = []
    for class_name in classes:
        if class_name in semantic_map:
            tag_name = semantic_map[class_name]
            if tag_name in ('strong', 'em'):
                tags_to_apply.append(tag_name)

    # Apply semantic tags (wrap content)
    if tags_to_apply:
        # Sort to ensure consistent nesting (strong outer, em inner)
        # Actually, let's keep order as is from classes
        for tag_name in reversed(tags_to_apply):  # Reverse to wrap from innermost
            new_tag = soup.new_tag(tag_name)

            # Move all children to new tag
            for child in list(element.children):
                new_tag.append(child.extract())

            # Add wrapped content back
            element.append(new_tag)

    # Remove class attribute
    if 'class' in element.attrs:
        del element.attrs['class']

    # Remove style attribute (inline styles)
    if 'style' in element.attrs:
        del element.attrs['style']

    # If this is a <span> with no attributes left, unwrap it
    if element.name == 'span' and not element.attrs:
        element.unwrap()


def convert_google_docs_html(html: str) -> str:
    """
    Convert Google Docs HTML to semantic HTML for TipTap.

    Steps:
    1. Parse <style> block and extract CSS rules
    2. Build map: class_name → CSS properties
    3. Identify semantic classes (bold, italic, blockquote)
    4. Replace <span class="cX"> with semantic tags
    5. Remove <style> block and artifacts
    6. Return clean semantic HTML

    Args:
        html: Google Docs exported HTML string

    Returns:
        Clean semantic HTML string

    Example:
        Input:
            <style>.c8 { font-weight: 700; }</style>
            <p><span class="c8">Bold text</span></p>

        Output:
            <p><strong>Bold text</strong></p>
    """
    # Parse HTML
    soup = BeautifulSoup(html, 'lxml')

    # Find and parse <style> block
    style_tag = soup.find('style')
    class_map = {}
    semantic_map = {}

    if style_tag:
        style_content = style_tag.string or ''
        class_map = parse_css_rules(style_content)
        semantic_map = identify_semantic_classes(class_map)

        # Remove <style> tag
        style_tag.decompose()

    # Remove Google Docs meta tags
    for meta in soup.find_all('meta'):
        meta.decompose()

    # Get body content (or entire soup if no body)
    body = soup.find('body')
    if not body:
        body = soup

    # Process all elements to convert classes to semantic tags
    for element in body.find_all(True):  # True = all tags
        if isinstance(element, Tag):
            # Handle blockquote (p tags with blockquote class)
            classes = element.get('class', [])
            blockquote_classes = [c for c in classes if semantic_map.get(c) == 'blockquote']

            if blockquote_classes and element.name in ('p', 'div'):
                # Convert to blockquote
                element.name = 'blockquote'
                # Remove the blockquote class
                for bc in blockquote_classes:
                    if bc in element.get('class', []):
                        element['class'].remove(bc)
                if not element.get('class'):
                    del element['class']

            # Process inline formatting (strong, em)
            process_element(element, semantic_map, soup)

    # Clean up empty tags
    for tag in body.find_all(True):
        if isinstance(tag, Tag):
            # Remove empty spans, divs (but keep structural tags like p, br)
            if tag.name in ('span', 'div') and not tag.get_text(strip=True) and not tag.find_all(True):
                tag.decompose()

    # Extract body HTML
    if body.name == 'body':
        # Get inner HTML of body
        result = ''.join(str(child) for child in body.children)
    else:
        result = str(body)

    # Clean up extra whitespace
    result = re.sub(r'\n\s*\n', '\n', result)
    result = result.strip()

    return result


def is_google_docs_html(html: str) -> bool:
    """
    Check if HTML looks like it came from Google Docs export.

    Args:
        html: HTML string to check

    Returns:
        True if HTML appears to be from Google Docs
    """
    # Google Docs typically includes these markers
    markers = [
        'docs-internal-guid',
        'id="docs-internal-guid',
        '<meta charset="utf-8">',
        '<style type="text/css">',
    ]

    return any(marker in html for marker in markers)
