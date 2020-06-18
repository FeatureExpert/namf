#!/usr/bin/env python3

import glob
import sys
import csv
import os
import re
import string
import shutil
import pprint
import filecmp
import tempfile

translations = {}
keys_index = {}
for filepath in glob.iglob(r'./src/lang/intl_*.h'):
    name = os.path.basename(filepath)
    m = re.search('_(\w\w).h', name)
    lang = m.group(1)
    translations[lang] = {}
    locations = ('./src/sensors/*_{l}.lang', './src/lang/*_{l}.lang')
    print("Looking for language files for {l}".format(l=lang.upper()))
    files = []
    for i in locations:
        files.extend(glob.glob(i.format(l=m.group(1))))
    for lang_file in files:
        print(lang_file)
        with open(lang_file) as f:
            for row in f:
                if re.match("^\W*[$#]", row):
                    continue
                entries = row.rstrip().partition(" ")
                if len(entries[0]) == 0:
                    continue
                # print(entries[0])
                translations[lang][entries[0]] = {"body": entries[2], "src": lang_file}
                keys_index[entries[0]] = True

# pp = pprint.PrettyPrinter(indent=4)
# pprint.pprint(translations)

for lang in translations:
    unprocessed_keys = list(keys_index.keys())
    f, temp_file = tempfile.mkstemp()

    os.write(f, str.encode("""
/*
(c) Nettigo

Language translation file for Nettigo Air Monitor 

*** THIS IS AUTOGENERATED FILE ****
For changes in translations do them in corresponding .lang file. Files with translations has format:

KEY[SPACE]translation string

So entry in file:
INTL_DS18B20 Sensor DS18B20 ({t}) 
Will become 
const char INTL_DS18B20[] PROGMEM = "Sensor DS18B20 ({t})";
in this file.

Generator will add before each line .lang source from which file was generated. For .lang files are searched in 
following directories:

./src/lang/
./src/sensors/
*/ 

"""))

    for key in sorted(translations[lang]):
        os.write(f, str.encode('/* {src} */ const char {key}[] PROGMEM = "{body}";\n'.format(
            body=translations[lang][key]['body'],
            src=translations[lang][key]['src'],
            key=key)))
        unprocessed_keys.remove(key)
    if len(unprocessed_keys) > 0:
        print("UNTRANSLATED ENTRIES for lang {l}".format(l=lang))
        for key in unprocessed_keys:
            print(key)
            os.write(f, str.encode(' const char {key}[] PROGMEM = "TRANSLATE ME PLIZ &#x1F431;";\n'.format(
                key=key)))

    os.close(f)
    final_file = "./src/lang/intl_{lang}.h".format(lang=lang)
    if not (filecmp.cmp(final_file, temp_file, shallow=True)):
        print('Changes detected, generating new {f}'.format(f=final_file))
        shutil.copy(temp_file, final_file)
    else:
        print('identyczne {f} i {t}'.format(t=temp_file,f=final_file))
        pass

    os.remove(temp_file)
