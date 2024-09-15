#!/usr/bin/env python3

import sys
import json


def compare_refs(path_old, path_new):
    with open(path_old) as f:
        refs_old = json.load(f)

    with open(path_new) as f:
        refs_new = json.load(f)

    refs_old_dict = {ref['id']: ref for ref in refs_old}
    refs_new_dict = {ref['id']: ref for ref in refs_new}

    added_refs = []
    removed_refs = []
    changed_refs = []

    for key in refs_new_dict:
        if key not in refs_old_dict:
            added_refs.append(refs_new_dict[key])
            continue

        all_fields = set(refs_new_dict[key].keys()) | set(refs_old_dict[key].keys())
        for field in all_fields:
            if field not in refs_old_dict[key] or \
               field not in refs_new_dict[key] or \
               refs_old_dict[key][field] != refs_new_dict[key][field]:
                changed_refs.append((refs_old_dict[key], refs_new_dict[key]))
                # no need to add this again to changed_refs
                break

    for key in refs_old_dict:
        if key not in refs_new_dict:
            removed_refs.append(refs_old_dict[key])

    return added_refs, removed_refs, changed_refs, refs_old


def simple_format_reference(ref):
    formatted = []
    # creator
    creators = []
    if 'author' in ref:
        creators = ref['author']
    elif 'editor' in ref:
        creators = ref['editor']
    elif 'director' in ref:
        creators = ref['director']
    if creators and len(creators) < 3:
        names = []
        for name in creators:
            try:
                names.append(f"{name['given']} {name['family']}")
            except KeyError:
                names.append(name['literal'])
            formatted.append(' '.join(names))
    elif len(creators):
        formatted.append(f"{creators[0]['given']} {creators[0]['family']} et al.")
    # title
    if 'title' in ref:
        if ref['type'] in ['article-journal', 'article-newspaper', 'entry-encyclopedia']:
            formatted.append(f"«{ref['title']}»")
        else:
            formatted.append(ref['title'])
    # date
    if 'issued' in ref:
        formatted.append(ref['issued']['date-parts'][0][0])
    else:
        formatted.append('(no date)')
    return f"({ref['type']}) " + ', '.join(formatted)


def confirm():
    while True:
        choice = input().lower()
        if choice in ['yes', 'y']:
            return True
        elif choice in ['no', 'n']:
            return False
        else:
            sys.stdout.write("  Please answer by “yes”, “y”, “no” or “n”: ")


def save_references(references):
    with open('tests/references.json', 'w') as f:
        json.dump(
            references,
            f,
            indent=2,
            ensure_ascii=False
        )
        f.write("\n")


if __name__ == '__main__':
    added, missing, changed, master = compare_refs(
        path_old='tests/references.json',
        path_new='tests/references-in.json'
    )

    if changed:
        print("Some references have been changed:")
        for old, new in changed:
            old_formatted = simple_format_reference(old)
            new_formatted = simple_format_reference(new)
            formatted = old_formatted
            if old_formatted != new_formatted:
                formatted += ' ⇒ ' + new_formatted
            print(f"#{old['id']}: {formatted}")
            for field, value in new.items():
                if field not in old:
                    print(f"  New field: '{field}' with value '{value}'")
                    sys.stdout.write("  Adopt this new field? (y/n) ")
                    try:
                        if confirm():
                            # note that this changes the value in the `master' variable as well
                            old[field] = value
                            save_references(master)
                    except KeyboardInterrupt:
                        print()
                        sys.exit(1)
                    continue

                if old[field] != value:
                    print(f"  Changed value of {field}: {old[field]} -> {value}")
                    sys.stdout.write(f"  Change value to {value}? (y/n) ")
                    try:
                        if confirm():
                            # note that this changes the value in the `master' variable as well
                            old[field] = value
                            save_references(master)
                    except KeyboardInterrupt:
                        print()
                        sys.exit(1)
            fields_to_remove = []
            for field, value in old.items():
                if field not in new:
                    print(f"  Field '{field}' with value '{value}' removed")
                    sys.stdout.write("  Remove this old field? (y/n) ")
                    try:
                        if confirm():
                            fields_to_remove.append(field)
                    except KeyboardInterrupt:
                        print()
                        sys.exit(1)
            if fields_to_remove:
                for field in fields_to_remove:
                    del old[field]
                    save_references(master)

    if added:
        if changed:
            print()
        print("Following references appear to be new:")
        for ref in added:
            formatted = simple_format_reference(ref)
            print(f"#{ref['id']}: {formatted}")
            sys.stdout.write("  Import this new reference? (y/n) ")
            try:
                if confirm():
                    master.append(ref)
                    save_references(master)
            except KeyboardInterrupt:
                print()
                sys.exit(1)

    if missing:
        if changed or added:
            print()
        print("Following old references are missing in the new file:")
        for ref in missing:
            formatted = simple_format_reference(ref)
            print(f"#{ref['id']}: {formatted}")
            sys.stdout.write("  Remove this old reference? (y/n) ")
            try:
                if confirm():
                    master = [r for r in master if r['id'] != ref['id']]
                    save_references(master)
            except KeyboardInterrupt:
                print()
                sys.exit(1)
