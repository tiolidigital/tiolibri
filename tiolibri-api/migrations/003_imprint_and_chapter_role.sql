-- Dane wydawnicze na stronę tytułową + rola rozdziału.
--
-- Oba pola są opcjonalne i mają bezpieczne wartości domyślne: projekt bez
-- `imprint` i rozdział bez `role` renderują się dokładnie tak jak przed tą
-- zmianą, więc migracja nie rusza istniejących książek.

alter table projects
    add column if not exists imprint jsonb not null default '{}'::jsonb;

comment on column projects.imprint is
    'Dane na stronę tytułową: {"publisher", "place_year", "rights_note"}. Pusty obiekt = generator drukuje samą nazwę, podtytuł i autora, jak dotąd.';

alter table chapters
    add column if not exists role text;

alter table chapters
    drop constraint if exists chapters_role_check;

alter table chapters
    add constraint chapters_role_check
    check (role is null or role in ('colophon'));

comment on column chapters.role is
    'Rola rozdziału. ''colophon'' = strona redakcyjna: mniejszy stopień pisma, poza spisem treści w obu formatach.';
