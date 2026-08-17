// Nazwy pobieranych plików: polskie znaki mają się transliterować, a nie znikać.
//
// Odpowiednik `slugify()` z tiolibri-api/app/services/md_exporter.py — ta sama
// kolejność kroków (mapa liter bez diakrytyku rozkładalnego → NFKD → zdjęcie
// znaków łączących), żeby backend i front nazywały pliki tak samo.

// Litery, których NFKD NIE rozłoży, bo nie są "baza + diakrytyk" tylko osobnym
// znakiem. Bez tej mapy "ł" wypadłoby z nazwy: "całe" → "cae".
const LATIN_MAP = {
  ł: 'l', Ł: 'L', đ: 'd', Đ: 'D', ø: 'o', Ø: 'O',
  æ: 'ae', Æ: 'AE', œ: 'oe', Œ: 'OE', ß: 'ss', þ: 'th', Þ: 'TH',
}

/** Sprowadza tekst do ASCII z zachowaniem liter: "Kości na całe życie" → "Kosci na cale zycie". */
export function transliterate(text) {
  return (text || '')
    .normalize('NFC')
    .replace(/[łŁđĐøØæÆœŒßþÞ]/g, (c) => LATIN_MAP[c])
    .normalize('NFKD')
    .replace(/\p{M}/gu, '')
}

/** Nazwa pliku książki: "Kości na całe życie" + "pdf" → "kosci-na-cale-zycie.pdf". */
export function bookFilename(title, extension, fallback = 'ksiazka') {
  const stem = transliterate(title)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return `${stem || fallback}.${extension}`
}
