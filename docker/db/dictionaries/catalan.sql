--
-- Run this on the database
--

DROP TEXT SEARCH CONFIGURATION IF EXISTS catalan;
DROP TEXT SEARCH DICTIONARY IF EXISTS catalan_hunspell;

CREATE TEXT SEARCH DICTIONARY catalan_hunspell (
	TEMPLATE  = ispell,
	DictFile  = ca,
	AffFile   = ca,
	StopWords = catalan
);
COMMENT ON TEXT SEARCH DICTIONARY catalan_hunspell
	IS '[USER ADDED] Hunspell dictionary for catalan';
CREATE TEXT SEARCH CONFIGURATION catalan (
	COPY = pg_catalog.english
);
ALTER TEXT SEARCH CONFIGURATION catalan
	ALTER MAPPING
	FOR
		asciiword, asciihword, hword_asciipart,  word, hword, hword_part
	WITH
		catalan_hunspell, simple;
COMMENT ON TEXT SEARCH CONFIGURATION catalan
	IS '[USER ADDED] configuration for catalan';
