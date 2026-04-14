# Changelog
-----------

## Add new entry to the changelog

New rst files must be added within this directory and must follow the file naming convention:

```
<4-digit year>.<2 digit month>.<2 digit day>-name-of-change.rst
```

Example: 

```
├── docs
│   ├── build
│   ├── changelog
│   │   ├── 2026.04.01-my-first-changelog-entry.rst
│   │   └── README.md
```

All rst files within the changelog directory will:
- Be collected
- Sorted in reverse order (by the formatted date given in the filename)
- Dynamically inserted into the changelog page of the Sphinx documentation as a new bullet point.

The first line in the changelog entry will be added to the bulleted item. For example, if the first line in file `2026.04.01-my-first-changelog-entry.rst` contains the text "Hello World", the changelog page would appear as follows:

- **2026.04.01** - Hello World

    Remaining contents of rst file...
