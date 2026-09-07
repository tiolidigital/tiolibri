-- ISBN-y w danych wydawniczych.
--
-- Bez zmiany schematu: `projects.imprint` to jsonb, dochodzą tylko dwa
-- opcjonalne klucze. Aktualizujemy komentarz, żeby opis kolumny nie kłamał.
-- ISBN jest osobny dla każdego formatu (tak nadaje je Biblioteka Narodowa),
-- generatory wpisują go w metadane pliku: EPUB `dc:identifier`, PDF metadane
-- dokumentu.

comment on column projects.imprint is
    'Dane wydawnicze: {"publisher", "place_year", "rights_note", "isbn_pdf", "isbn_epub"}. Pusty obiekt = generator drukuje samą nazwę, podtytuł i autora, jak dotąd; bez ISBN-u identyfikatorem EPUB-a zostaje UUID projektu.';
