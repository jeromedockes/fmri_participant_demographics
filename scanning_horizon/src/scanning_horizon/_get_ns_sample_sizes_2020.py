# https://github.com/poldracklab/ScanningTheHorizon/blob/09b9f64eda5fc5c82e64679aa33d4c3c2685928b/SampleSize/2020/get_ns_sample_sizes.py
# get_ns_sample_sizes.py - extract estimated sample size data from neurosynth
# Tal Yarkoni, 2016

import re

def estimate_n(text):
    text = text.lower()
    matches = re.finditer('[\(\s]+n\s*=\s*(\d+)', text)
    res = []
    for m in matches:
        n = int(m.group(1))
        res.append((f"n = {n}", n, m.start(), m.end()))
    return res
