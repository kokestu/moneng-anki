# https://www.biblical.ie/page.php?fl=NRSV/Mark

import re

def get_mark():
    with open("/home/jasutton/code/other/marks-gospel/mark.txt", "r") as f:
        data = f.read()
    return data

def format_book(raw, max_len = 12):
    chapters = re.split(r"Chapter ", raw)
    res = ""
    for chapter in chapters[1:]:
        chap_no = chapter.split("\n")[0]
        res += format_chapter(chapter, chap_no, max_len)
        res += "\n"
    return res

def format_chapter(raw_text, chapter, max_len_w = 10):
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
        v_no = f"<sup>{chapter}:{i+1}</sup>"
        # If the verse is too long, split on punctuation.
        if len(v.split()) > max_len_w:
            #Find the approx middle punctuation of the verse.
            chunks = split_punc(v)
            # Split there and append, starting with the verse number.
            res.append(v_no)
            for chunk in chunks:
                res.append(chunk)
                if chunk:
                    res.append("\n")
        else:
            # Otherwise, use the whole verse without splitting.
            res.append(v_no)
            res.append(v)
            res.append("\n")
    return "".join(res)


# Cut the verse into sections that do not exceed the max length. Prioritise splitting
# on punctuation, but use spaces if necessary.
def split_punc(x, punc = r"\.'\"|,'\"|,'|\.\"|\?\"|!\"|,|;|:|\.|\?|!", target_len_c = 40, tol = 15):
    # How many splits do we need to make based on the max length?
    splits = len(x) // target_len_c
    # Make the chunks roughly equal sizes.
    target = len(x) // splits
    res = []
    # Look for punctuation and spaces.
    ps = [p.end() for p in re.finditer(punc, x)]
    sps = [sp.end() for sp in re.finditer(r" ", x)]
    cands = ps + sps
    for i in range(splits):
        # Find the first candidate that falls within the tolerance of the desired
        # splitting point. Prioritise punctuation by checking them first.
        cut = None
        for cand in cands:
            # If there is no cut within the tolerance, take the first cut
            # after the target.
            if abs(cand - target) < tol:
                cut = cand
                break
        # If we didn't find a cut within the tolerance, find the value that minimises
        # the distance to the target.
        if cut == None:
            cut = min(cands, key = lambda cand: abs(cand - target))
        # Cut and add it to the result.
        res.append(x[0:cut])
        # Trim the string and adjust the candidates.
        x = x[cut:]
        cands = [cand - cut for cand in cands if cand - cut >= 0]
    # Add the rest.
    res.append(x)
    # return.
    return res