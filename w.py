from whoosh.analysis import CharsetFilter, StemmingAnalyzer
from whoosh.support.charset import accent_map
# more complete:
# from whoosh.support.charset import default_charset, charset_table_to_dict
# charmap = charset_table_to_dict(default_charset)
# ...
# CharsetFilter(charmap)

# Sources
# accent folding: https://gist.github.com/gregplaysguitar/1727204

STOPWORDS = ["a", "abans", "ací", "ah", "així", "això", "al", "als", "aleshores", "algun", "alguna", "algunes",
             "alguns", "alhora", "allà", "allí", "allò", "altra", "altre", "altres", "amb", "ambdós", "ambdues",
             "apa", "aquell", "aquella", "aquelles", "aquells", "aquest", "aquesta", "aquestes", "aquests", "aquí",
             "baix", "cada", "cadascú", "cadascuna", "cadascunes", "cadascuns", "com", "contra", "d'un", "d'una",
             "d'unes", "d'uns", "dalt", "de", "del", "dels", "des", "després", "dins", "dintre", "donat", "doncs",
             "durant", "e", "eh", "el", "els", "em", "en", "encara", "ens", "entre", "érem", "eren", "éreu", "es",
             "és", "esta", "està", "estàvem", "estaven", "estàveu", "esteu", "et", "etc", "ets",
             "fins", "fora", "gairebé", "ha", "han", "has", "havia", "he", "hem", "heu", "hi ", "ho", "i", "igual",
             "iguals", "ja", "l'hi", "la", "les", "li", "li'n", "llavors", "m'he", "ma", "mal", "malgrat", "mateix",
             "mateixa", "mateixes", "mateixos", "me", "mentre", "més", "meu", "meus", "meva", "meves", "molt",
             "molta", "moltes", "molts", "mon", "mons", "n'he", "n'hi", "ne", "ni", "no", "nogensmenys", "només",
             "nosaltres", "nostra", "nostre", "nostres", "o", "oh", "oi", "on", "pas", "pel", "pels", "per", "però",
             "perquè", "poc ", "poca", "pocs", "poques", "potser", "propi", "qual", "quals", "quan", "quant ", "que",
             "què", "quelcom", "qui", "quin", "quina", "quines", "quins", "s'ha", "s'han", "sa", "semblant",
             "semblants", "ses", "seu ", "seus", "seva", "seva", "seves", "si", "sobre", "sobretot", "sóc",
             "solament", "sols", "son ", "són", "sons ", "sota", "sou", "t'ha", "t'han", "t'he", "ta", "tal",
             "també", "tampoc", "tan", "tant", "tanta", "tantes", "teu", "teus", "teva", "teves", "ton", "tons",
             "tot", "tota", "totes", "tots", "un", "una", "unes", "uns", "us", "va", "vaig", "vam", "van", "vas",
             "veu", "vosaltres", "vostra", "vostre", "vostres"]


# class CustomSearchBackend(WhooshSearchBackend):
#     def build_schema(self, fields):
#         schema = super(CustomSearchBackend, self).build_schema(fields)
#
#         for name, field in list(schema[1].items()):
#             if isinstance(field, TEXT):
#                 field.analyzer = (StemmingAnalyzer(minsize=1, stoplist=frozenset(STOPWORDS)) |
#                                   CharsetFilter(accent_map))

ana = StemmingAnalyzer(minsize=1, stoplist=frozenset(STOPWORDS))
print([token.text for token in ana("Avui em compraré un avió")])
