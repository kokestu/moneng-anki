# https://www.biblical.ie/page.php?fl=NRSV/Mark

import re

def format_chapter(raw_text, max_len = 12):
    # Remove headings
    x1 = re.sub(r"\n\n((\w| |,|')+)\n\n", "", raw_text)
    # Remove line breaks
    x2 = re.sub(r"\n", "", x1)
    # Split into verses.
    x3 = [x for x in re.split(r" ?\d+ ", x2) if x != '']
    # Build the verses with proper numbers and split into shortish lines
    res = []
    for (i, v) in enumerate(x3):
        # Superscript verse number.
        v = f"<sup>{i+1}</sup>" + v
        # If the verse is too long, split on punctuation.
        if len(v.split()) > max_len:
            # Find the approx middle punctuation of the verse.
            a, b = split_punc(v)
            # Split there and append.
            res.append(a)
            res.append("\n")
            if b:
                res.append(b)
                res.append("\n")
        else:
            # Otherwise, use the whole verse without splitting.
            res.append(v)
            res.append("\n")
    return "".join(res)


# Find the punctuation mark closest to the middle, and split.
def split_punc(x, punc = r",|;|\.|\?|!"):
    mid = len(x) // 2
    a = re.search(punc, x).start()
    while True:
        if not re.search(punc, x[a+1:]):
            break
        b = a + re.search(punc, x[a+1:]).start() + 1
        if b < mid:
            a = b
            continue
        else:
            if b - mid < abs(a - mid):
                a = b
            break
    return x[0:a+1], x[a+1:]
