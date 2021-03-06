from django.utils.translation import gettext_lazy as _


iso_639_choices = [
    ('ab', _('Abkhaz')),
    ('aa', _('Afar')),
    ('af', _('Afrikaans')),
    ('ak', _('Akan')),
    ('sq', _('Albanian')),
    ('am', _('Amharic')),
    ('ar', _('Arabic')),
    ('an', _('Aragonese')),
    ('hy', _('Armenian')),
    ('as', _('Assamese')),
    ('av', _('Avaric')),
    ('ae', _('Avestan')),
    ('ay', _('Aymara')),
    ('az', _('Azerbaijani')),
    ('bm', _('Bambara')),
    ('ba', _('Bashkir')),
    ('eu', _('Basque')),
    ('be', _('Belarusian')),
    ('bn', _('Bengali')),
    ('bh', _('Bihari')),
    ('bi', _('Bislama')),
    ('bs', _('Bosnian')),
    ('br', _('Breton')),
    ('bg', _('Bulgarian')),
    ('my', _('Burmese')),
    ('ca', _('Catalan; Valencian')),
    ('ch', _('Chamorro')),
    ('ce', _('Chechen')),
    ('ny', _('Chichewa; Chewa; Nyanja')),
    ('zh', _('Chinese')),
    ('cv', _('Chuvash')),
    ('kw', _('Cornish')),
    ('co', _('Corsican')),
    ('cr', _('Cree')),
    ('hr', _('Croatian')),
    ('cs', _('Czech')),
    ('da', _('Danish')),
    ('dv', _('Divehi; Maldivian;')),
    ('nl', _('Dutch')),
    ('dz', _('Dzongkha')),
    ('en', _('English')),
    ('eo', _('Esperanto')),
    ('et', _('Estonian')),
    ('ee', _('Ewe')),
    ('fo', _('Faroese')),
    ('fj', _('Fijian')),
    ('fi', _('Finnish')),
    ('fr', _('French')),
    ('ff', _('Fula')),
    ('gl', _('Galician')),
    ('ka', _('Georgian')),
    ('de', _('German')),
    ('el', _('Greek, Modern')),
    ('gn', _('Guaraní')),
    ('gu', _('Gujarati')),
    ('ht', _('Haitian')),
    ('ha', _('Hausa')),
    ('he', _('Hebrew (modern)')),
    ('hz', _('Herero')),
    ('hi', _('Hindi')),
    ('ho', _('Hiri Motu')),
    ('hu', _('Hungarian')),
    ('ia', _('Interlingua')),
    ('id', _('Indonesian')),
    ('ie', _('Interlingue')),
    ('ga', _('Irish')),
    ('ig', _('Igbo')),
    ('ik', _('Inupiaq')),
    ('io', _('Ido')),
    ('is', _('Icelandic')),
    ('it', _('Italian')),
    ('iu', _('Inuktitut')),
    ('ja', _('Japanese')),
    ('jv', _('Javanese')),
    ('kl', _('Kalaallisut')),
    ('kn', _('Kannada')),
    ('kr', _('Kanuri')),
    ('ks', _('Kashmiri')),
    ('kk', _('Kazakh')),
    ('km', _('Khmer')),
    ('ki', _('Kikuyu, Gikuyu')),
    ('rw', _('Kinyarwanda')),
    ('ky', _('Kirghiz, Kyrgyz')),
    ('kv', _('Komi')),
    ('kg', _('Kongo')),
    ('ko', _('Korean')),
    ('ku', _('Kurdish')),
    ('kj', _('Kwanyama, Kuanyama')),
    ('la', _('Latin')),
    ('lb', _('Luxembourgish')),
    ('lg', _('Luganda')),
    ('li', _('Limburgish')),
    ('ln', _('Lingala')),
    ('lo', _('Lao')),
    ('lt', _('Lithuanian')),
    ('lu', _('Luba-Katanga')),
    ('lv', _('Latvian')),
    ('gv', _('Manx')),
    ('mk', _('Macedonian')),
    ('mg', _('Malagasy')),
    ('ms', _('Malay')),
    ('ml', _('Malayalam')),
    ('mt', _('Maltese')),
    ('mi', _('Māori')),
    ('mr', _('Marathi (Marāṭhī)')),
    ('mh', _('Marshallese')),
    ('mn', _('Mongolian')),
    ('na', _('Nauru')),
    ('nv', _('Navajo, Navaho')),
    ('nb', _('Norwegian Bokmål')),
    ('nd', _('North Ndebele')),
    ('ne', _('Nepali')),
    ('ng', _('Ndonga')),
    ('nn', _('Norwegian Nynorsk')),
    ('no', _('Norwegian')),
    ('ii', _('Nuosu')),
    ('nr', _('South Ndebele')),
    ('oc', _('Occitan')),
    ('oj', _('Ojibwe, Ojibwa')),
    ('cu', _('Old Church Slavonic')),
    ('om', _('Oromo')),
    ('or', _('Oriya')),
    ('os', _('Ossetian, Ossetic')),
    ('pa', _('Panjabi, Punjabi')),
    ('pi', _('Pāli')),
    ('fa', _('Persian')),
    ('pl', _('Polish')),
    ('ps', _('Pashto, Pushto')),
    ('pt', _('Portuguese')),
    ('qu', _('Quechua')),
    ('rm', _('Romansh')),
    ('rn', _('Kirundi')),
    ('ro', _('Romanian, Moldavan')),
    ('ru', _('Russian')),
    ('sa', _('Sanskrit (Saṁskṛta)')),
    ('sc', _('Sardinian')),
    ('sd', _('Sindhi')),
    ('se', _('Northern Sami')),
    ('sm', _('Samoan')),
    ('sg', _('Sango')),
    ('sr', _('Serbian')),
    ('gd', _('Scottish Gaelic')),
    ('sn', _('Shona')),
    ('si', _('Sinhala, Sinhalese')),
    ('sk', _('Slovak')),
    ('sl', _('Slovene')),
    ('so', _('Somali')),
    ('st', _('Southern Sotho')),
    ('es', _('Spanish; Castilian')),
    ('su', _('Sundanese')),
    ('sw', _('Swahili')),
    ('ss', _('Swati')),
    ('sv', _('Swedish')),
    ('ta', _('Tamil')),
    ('te', _('Telugu')),
    ('tg', _('Tajik')),
    ('th', _('Thai')),
    ('ti', _('Tigrinya')),
    ('bo', _('Tibetan')),
    ('tk', _('Turkmen')),
    ('tl', _('Tagalog')),
    ('tn', _('Tswana')),
    ('to', _('Tonga')),
    ('tr', _('Turkish')),
    ('ts', _('Tsonga')),
    ('tt', _('Tatar')),
    ('tw', _('Twi')),
    ('ty', _('Tahitian')),
    ('ug', _('Uighur, Uyghur')),
    ('uk', _('Ukrainian')),
    ('ur', _('Urdu')),
    ('uz', _('Uzbek')),
    ('ve', _('Venda')),
    ('vi', _('Vietnamese')),
    ('vo', _('Volapük')),
    ('wa', _('Walloon')),
    ('cy', _('Welsh')),
    ('wo', _('Wolof')),
    ('fy', _('Western Frisian')),
    ('xh', _('Xhosa')),
    ('yi', _('Yiddish')),
    ('yo', _('Yoruba')),
    ('za', _('Zhuang, Chuang')),
    ('zu', _('Zulu'))
]
