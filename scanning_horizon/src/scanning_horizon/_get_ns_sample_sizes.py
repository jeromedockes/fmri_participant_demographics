# https://github.com/poldracklab/ScanningTheHorizon/blob/09b9f64eda5fc5c82e64679aa33d4c3c2685928b/SampleSize/get_ns_sample_sizes.py
# get_ns_sample_sizes.py - extract estimated sample size data from neurosynth
# Tal Yarkoni, 2016

import re

def text2int(textnum, numwords={}):
    if not numwords:
        units = [
            "zero", "one", "two", "three", "four", "five", "six", "seven",
            "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
            "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
        ]

        tens = ["", "", "twenty", "thirty", "forty",
                "fifty", "sixty", "seventy", "eighty", "ninety"]
        scales = ["hundred", "thousand", "million", "billion", "trillion"]

        # numwords["and"] = (1, 0)
        for idx, word in enumerate(units):
            numwords[word] = (1, idx)
        for idx, word in enumerate(tens):
            numwords[word] = (1, idx * 10)
        for idx, word in enumerate(scales):
            numwords[word] = (
                10 ** (idx * 3 or 2), 0)

    ordinal_words = {'first': 1, 'second': 2, 'third': 3,
                     'fifth': 5, 'eighth': 8, 'ninth': 9, 'twelfth': 12}
    ordinal_endings = [('ieth', 'y'), ('th', '')]

    textnum = textnum.replace('-', ' ')

    current = result = 0
    for word in textnum.split():
        if word in ordinal_words:
            scale, increment = (1, ordinal_words[word])
        else:
            for ending, replacement in ordinal_endings:
                if word.endswith(ending):
                    word = "%s%s" % (word[:-len(ending)], replacement)

            if word not in numwords:
                raise Exception("Illegal word: " + word)

            scale, increment = numwords[word]

        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current


def estimate_n(text):
    text = text.lower()
    populations = [
        'volunteers', 'subjects', 'individuals', 'participants', 'students',
        'patients', 'outpatients', 'undergraduates', 'adults', 'control',
        'people', 'stroke', 'children'
    ]
    pops = '|'.join(populations)
    patt = '([a-zA-Z0-9\-]+)\s+([^\s]+\s+)?(%s)' % pops
    matches = re.finditer(patt, text)
    n = []
    for m in matches:
        try:
            # print(m)
            m0 = m.group(1)
            if m0.isnumeric():
                n_ = int(m0)
            else:
                n_ = text2int(m0)
            n.append((re.sub('\s+', ' ', m.group(0)), n_, m.start(), m.end()))
        except:
            pass

    more = re.finditer('[\(\s]+n\s*=\s*(\d+)', text)
    n.extend([('n = %d' % int(m.group(1)), int(m.group(1)), m.start(), m.end()) for m in more])
    return n
