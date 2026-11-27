# Paper Frost

Warm paper-white background with ink-dark text and crisp teal, blue and violet accents. A light VS Code colour theme, made for [rich-struct](https://github.com/wiertmir/rich-struct), where it is one of the built-in themes.

Markdown gets its own colours while editing: each heading level, bold, italic, inline code, links, list bullets and quotes.
With the themed-markdown-notebook-render extension the same colours show in notebook Markdown cells.

Python and Rust get extra colours from semantic highlighting (Pylance, rust-analyzer): classes vs. other types, docstrings, f-strings and raw strings, `self`/`cls`, decorators and attributes, traits, macros, and bold methods that consume `self`. Log files have coloured errors, warnings and stack traces. Notebooks show white cells on a grey-blue page.

JSON, YAML and XML have muted punctuation, so keys, values and tags stand out. JSON and YAML keys are coloured by depth, in five blues that repeat from the sixth level on. Jinja templates (`{{ }}`, `{% %}`, `{# #}`) are highlighted inside YAML, HTML, XML, JSON and Python strings, with no extra extension. f-strings are left alone, since `{{` there is an escaped brace. Only single-line tags are recognised.

## Install

```sh
npm run package                          # builds paper-frost-theme-0.1.0.vsix
code --install-extension paper-frost-theme-0.1.0.vsix
```

Then pick **Paper Frost** with *Preferences: Color Theme*.
