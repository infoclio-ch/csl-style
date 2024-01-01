#!/usr/bin/env python3

import os
import glob
from itertools import chain

def get_styles():
    styles = [
        (os.path.splitext(os.path.basename(style))[0].split('-'), style)
        for style
        in glob.iglob("src/*.csl")
    ]
    ids = {}
    if len(styles) == 1:
        _, filename = styles.pop()
        ids = {'any': filename}
    else:
        # start with longest filenames
        for i, style in enumerate(sorted(styles, key=len, reverse=True)):
            tokens, filename = style
            # get the first part of the filename that is not present in any of
            # the other filenames
            identifier = set(tokens) - set(chain.from_iterable([s[0] for s in styles[:i] + styles[i+1:]]))
            if len(identifier) >= 1:
                ids[[t for t in tokens if t in identifier][0]] = filename
            else:
                # if all parts are in other filenames, get the first one that
                # is not in *all* other filenames
                t = next(tok
                         for tok
                         in tokens
                         if not all([tok in style[0] for style in styles[:i] + styles[i+1:]]))
                ids[t] = filename
    return ids
