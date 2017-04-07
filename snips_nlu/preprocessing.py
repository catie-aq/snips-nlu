import glob
import io
import os

from snips_nlu.utils import RESOURCES_PATH

_LANGUAGE_STEMS = dict()


def verbs_stems(language):
    stems_paths = glob.glob(os.path.join(RESOURCES_PATH, language.iso_code,
                                         "top_*_verbs_conjugated.txt"))
    if len(stems_paths) == 0:
        return dict()

    verb_stemmings = dict()
    lines = [l.strip() for l in io.open(stems_paths[0], encoding="utf8")]
    for line in lines:
        elements = line.split(';')
        verb_stemmings.update(
            {inflection.split(',')[1]: elements[0] for inflection in
             elements[1:]})
    return verb_stemmings


def language_stems(language):
    global _LANGUAGE_STEMS
    if language.iso_code not in _LANGUAGE_STEMS:
        _LANGUAGE_STEMS[language.iso_code] = verbs_stems(language)
    return _LANGUAGE_STEMS[language.iso_code]


def stem_sentence(string, language):
    tokens = string.split()
    stemmed_tokens = [stem(token, language) for token in tokens]
    return ' '.join(stemmed_tokens)


def stem(string, language):
    return language_stems(language).get(string, string)