#!/usr/bin/env python3
"""
Quick test - polskie znaki w PDF
Uruchom: python test_polish_pdf.py
"""

from weasyprint import HTML, CSS

html = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<h1>Zażółć gęślą jaźń - wszystkie polskie znaki:</h1>
<p><strong>ą ę ć ł ń ó ś ź ż</strong></p>
<p><strong>Ą Ę Ć Ł Ń Ó Ś Ź Ż</strong></p>
<p>Prof. Bożena Muszyńska pisze o grzybach.</p>
<p>Żółć to nie żółw, a gęś to nie gąska.</p>
</body>
</html>
"""

css = """
body {
    font-family: "DejaVu Serif", "Liberation Serif", Georgia, serif;
    font-size: 14pt;
    line-height: 1.8;
}
h1 {
    font-family: "DejaVu Sans", Arial, sans-serif;
}
"""

output = "/tmp/test_polish.pdf"
HTML(string=html).write_pdf(output, stylesheets=[CSS(string=css)])
print(f"✅ PDF wygenerowany: {output}")
print("   Otwórz i sprawdź czy polskie znaki są OK")
