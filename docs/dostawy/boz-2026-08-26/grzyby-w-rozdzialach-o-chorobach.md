# Grzyby w rozdziałach o chorobach — mapa gatunków i poziomów nagłówków

Bożena Muszyńska, „Grzyby lecznicze" · projekt TIOLIBRI `fe9cba47` · stan bazy 2026-09-08.
Dotyczy CZĘŚCI II (rozdziały `sort_order` 22–26).

---

## 1. Odpowiedź na pytanie o poziomy

Fragment, o który pytałeś, jest w rozdziale **„Wsparcie w terapii nowotworów – grzyby jako sojusznicy"** i to są **prawdziwe nagłówki H2/H3/H4**, nie bold:

| Tekst | Poziom |
|---|---|
| Grzyby – najskuteczniejsi sojusznicy w walce z chorobami nowotworowymi | **H2** |
| Najlepiej udokumentowane gatunki w badaniach klinicznych | **H3** |
| Twardnik japoński (Lentinula edodes) | **H4** |

W bazie w H4 jest „Najlepiej udokumentowane gatunki **w** badaniach klinicznych" — ze spacją; w Twoim cytacie się skleiła, ale w treści jest OK.

**Zero pseudo-nagłówków bold** we wszystkich pięciu rozdziałach o chorobach — sprawdzone: 0 akapitów i 0 pozycji listy złożonych wyłącznie z `<strong>`. Cała hierarchia to H1–H4.

Rozkład nagłówków:

| Rozdział | H2 | H3 | H4 | bold-pseudo |
|---|---:|---:|---:|---:|
| Choroby układu immunologicznego | 7 | 23 | 45 | 0 |
| Serce i naczynia | 7 | 22 | 19 | 0 |
| Cukrzyca i metabolizm | 7 | 27 | 32 | 0 |
| Mózg i układ nerwowy | 7 | 26 | 39 | 0 |
| Wsparcie w terapii nowotworów | 7 | 21 | 48 | 0 |

---

## 2. Ważne: gatunki NIE siedzą wszędzie na tym samym poziomie

To jest sedno sprawy, jeśli chcesz je wyciągnąć automatycznie. Każdy z pięciu rozdziałów trzyma gatunki gdzie indziej:

| Rozdział | Gdzie są gatunki | Da się wyciąć po nagłówku? |
|---|---|---|
| Choroby układu immunologicznego | w tytułach **H3**, po kilka gatunków w jednym nagłówku | częściowo — nie ma sekcji per gatunek |
| Serce i naczynia | **tylko w akapitach**, H3 to nazwy funkcji („Mistrzowie w profilaktyce hipercholesterolemii") | **nie** — trzeba po treści |
| Cukrzyca i metabolizm | **H4** per gatunek, z nazwą łacińską | **tak** |
| Mózg i układ nerwowy | **H3** per gatunek, H4 to podsekcje wewnątrz | **tak**, ale na H3 |
| Wsparcie w terapii nowotworów | **H4** per gatunek | **tak** |

Dodatkowo: rozdział o odporności jako jedyny **w ogóle nie podaje nazw łacińskich** — same nazwy polskie. Więc regexp na `(Rodzaj gatunek)` pominie go w całości.

---

## 3. Gatunki wyjęte z każdego rozdziału

### Choroby układu immunologicznego i grzyby, które pomogą
H2 „Grzyby – sprzymierzeńcy odporności" → trzy H3, każdy zbiorczy:

- **Pierwsza linia obrony** — twardnik japoński, wrośniak różnobarwny, żagwica listkowata, rozszczepka pospolita
- **Regulatorzy równowagi** — lakownica żółtawa, maczużnik bojowy
- **Intensywne wsparcie** — pieczarka migdałowa, błyskoporek podkorowy

### Serce i naczynia – grzyby dla zdrowia kardiologicznego
H2 „Grzyby wspierające układ sercowo-naczyniowy" → trzy H3 funkcjonalne, gatunki dopiero w akapitach:

- **Mistrzowie w profilaktyce hipercholesterolemii** — boczniak ostrygowaty (*Pleurotus ostreatus*), twardnik japoński (*Lentinula edodes*)
- **Działanie hipotensyjne** — lakownica żółtawa (*Ganoderma lucidum*), żagwica listkowata (*Grifola frondosa*)
- **Modulatorzy metaboliczni** — pieczarka migdałowa (*Agaricus blazei*), uszak bzowy (*Auricularia auricula-judae*), wrośniak różnobarwny (*Trametes versicolor*)

### Cukrzyca i metabolizm – grzybowa pomoc w kontroli cukru
H2 „Gatunki grzybów o działaniu przeciwcukrzycowym" → trzy H3 kategorie → H4 per gatunek:

- **Gatunki o udowodnionej skuteczności klinicznej**
  - Błyskoporek podkorowy (*Inonotus obliquus*)
  - Czyreń (*Phellinus linteus*) – specjalista od ochrony trzustki
- **Kategoria wsparcia metabolicznego – wszechstronni pomocnicy**
  - Soplówka jeżowata (*Hericium erinaceus*) – alternatywa dla metforminy w badaniach z udziałem zwierząt
  - Maczużnik bojowy (*Cordyceps militaris*) – regulator poziomu glukozy i lipidów
  - Lakownica żółtawa (*Ganoderma lucidum*) – modulator mikrobioty
- **Kategoria dostępnej profilaktyki – codzienni sprzymierzeńcy**
  - Twardnik japoński (*Lentinula edodes*) – fundament zdrowej diety
  - Pieczarka dwuzarodnikowa (*Agaricus bisporus*) – powszechnie dostępny gatunek

Poza nagłówkami w treści rozdziału pojawiają się jeszcze: żagwica listkowata, pieczarka migdałowa (*Agaricus subrufescens*), wrośniak różnobarwny.

### Mózg i układ nerwowy – neuroprotekcja z natury
H2 „Ranking grzybów wspierających równowagę psychiczną" → gatunki **na poziomie H3**:

- **Lider spośród grzybów** — soplówka jeżowata (*Hericium erinaceus*)
- **Wsparcie dla neurotransmisji** — boczniaki (*Pleurotus* spp.)
- **Modulator stresu** — lakownica żółtawa (*Ganoderma lucidum*)
- **Gatunki ergogeniczne** — maczużnik bojowy i maczużniczek chiński (*Cordyceps militaris* i *Ophiocordyceps sinensis*)

W treści dodatkowo boczniak różowy (*Pleurotus djamor*).

### Wsparcie w terapii nowotworów – grzyby jako sojusznicy
H2 „Grzyby – najskuteczniejsi sojusznicy w walce z chorobami nowotworowymi" → dwa H3 → H4 per gatunek:

- **Najlepiej udokumentowane gatunki w badaniach klinicznych**
  - Twardnik japoński (*Lentinula edodes*)
  - Wrośniak różnobarwny (*Trametes versicolor*)
  - Żagwica listkowata (*Grifola frondosa*)
  - Rozszczepka pospolita (*Schizophyllum commune*)
  - Pieczarka migdałowa (*Agaricus blazei*)
- **Specjalistyczne zastosowania**
  - Pieczarka dwuzarodnikowa (*Agaricus bisporus*)
  - Boczniak ostrygowaty (*Pleurotus ostreatus*)
  - Soplówka jeżowata (*Hericium erinaceus*)
  - Maczużnik bojowy (*Cordyceps militaris*)

Trzeci H3 — **„Dobór grzybów według typów nowotworów"** — nie ma H4, tylko akapity wiążące gatunek z lokalizacją:

| Nowotwór | Pierwszy wybór | Wsparcie | Mechanizm |
|---|---|---|---|
| żołądek | twardnik japoński | wrośniak różnobarwny | immunostymulacja |
| jelito grube | wrośniak różnobarwny | boczniak ostrygowaty, soplówka jeżowata | immunomodulacja, apoptoza |
| pierś | pieczarka dwuzarodnikowa | żagwica listkowata | hamowanie aromatazy |
| prostata | pornatka kokosowa lub pieczarka migdałowa | żagwica listkowata | apoptoza, hamowanie aromatazy |
| płuca | twardnik japoński | żagwica listkowata | immunostymulacja |
| wątroba | żagwica listkowata | twardnik japoński | zapobieganie przerzutom |

---

## 4. Tabela krzyżowa: gatunek × rozdział o chorobach

`H3` / `H4` = gatunek ma własny nagłówek na tym poziomie · `tekst` = tylko w akapitach · `–` = nieobecny

| Gatunek | Odporność | Serce | Cukrzyca | Mózg | Nowotwory |
|---|---|---|---|---|---|
| Twardnik japoński (*Lentinula edodes*) | H3 (zbiorczy) | tekst | H4 | – | H4 |
| Wrośniak różnobarwny (*Trametes versicolor*) | H3 (zbiorczy) | tekst | tekst | – | H4 |
| Żagwica listkowata (*Grifola frondosa*) | H3 (zbiorczy) | tekst | tekst | – | H4 |
| Rozszczepka pospolita (*Schizophyllum commune*) | H3 (zbiorczy) | – | – | – | H4 |
| Lakownica żółtawa (*Ganoderma lucidum*) | H3 (zbiorczy) | tekst | H4 | H3 | – |
| Maczużnik bojowy (*Cordyceps militaris*) | H3 (zbiorczy) | – | H4 | H3 | H4 |
| Pieczarka migdałowa (*Agaricus blazei* / *subrufescens*) | H3 (zbiorczy) | tekst | tekst | – | H4 |
| Błyskoporek podkorowy (*Inonotus obliquus*) | H3 (zbiorczy) | – | H4 | – | – |
| Soplówka jeżowata (*Hericium erinaceus*) | – | – | H4 | H3 | H4 |
| Boczniak ostrygowaty (*Pleurotus ostreatus*) | – | tekst | – | H3 (jako *Pleurotus* spp.) | H4 |
| Pieczarka dwuzarodnikowa (*Agaricus bisporus*) | – | – | H4 | – | H4 |
| Czyreń (*Phellinus linteus*) | – | – | H4 | – | – |
| Uszak bzowy (*Auricularia auricula-judae*) | – | tekst | – | – | – |
| Maczużniczek chiński (*Ophiocordyceps sinensis*) | – | – | – | H3 (wspólny) | tekst |
| Boczniak różowy (*Pleurotus djamor*) | – | – | – | tekst | – |
| Pornatka kokosowa (*Wolfiporia extensa*) | – | – | – | – | tekst |

**Gatunki spoza monografii CZĘŚCI I**, które pojawiają się dopiero w rozdziałach o chorobach: rozszczepka pospolita, maczużnik bojowy, maczużniczek chiński, czyreń, uszak bzowy, boczniak różowy, pieczarka migdałowa.
