"""Generate python_demo.ipynb: every Python element with its Paper Frost color.

Colors are not typed in: tokenize.js runs VS Code's Python grammar and resolves each char against the theme.
Pylance only runs inside VS Code, so its semantic tokens are written in below, one type per row
(check them with Developer: Inspect Editor Tokens and Scopes); the theme's semantic rules then color them.
Each snippet must appear in its section's code; the build fails otherwise. Needs what make_rust_demo.py needs, plus Pylance.
"""
import ast
import json
import re
import tempfile
from pathlib import Path

from make_rust_demo import Lookup, extension, find, legend, tokenize, write_notebook

# (legend title, [(Pylance semantic token or None, [snippets])], code)
SECTIONS = [
    ("Imports & modules", [
        (None, ["import", "from", "as"]),
        ("namespace", ["os", "re", "collections", "dataclasses"]),
        ("class", ["Counter", "Enum"]),
        ("function", ["dataclass,", "field"]),
    ], '''import os
import re as regex
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum, auto
from warnings import deprecated'''),

    ("Constants, numbers & operators", [
        ("variable.readonly", ["MAX_SIZE"]),
        (None, ["1_000", "3.14", "0xFF", "0o755", "0b1010", "2j", "None", "True", "False", "..."]),
        ("variable.declaration", ["ratio", "mask", "flags"]),
        (None, ["=", "*", "**", "//", "%", ">", "and", "not", " or ", " is ", " in ", "(", ")", "[", "]", ","]),
    ], '''MAX_SIZE = 1_000
ratio = 3.14 * 2 ** 3 // 1 % 7
mask, octal, binary, imaginary = 0xFF, 0o755, 0b1010, 2j
flags = [None, True, False, ...]
ok = ratio > 1 and not (mask is None) or 3 in [1, 2, 3]'''),

    ("Strings", [
        (None, ['"Tokyo"', 'b"', '"done"', "\\x41"]),
        (None, ['f"', "Hello", "{", "!r", ":>10", "letters", "\\n"]),
        ("variable", ["{name"]),
        (None, ['r"', "C:#1", 'R"', "C:#2", "[A-Z]", "\\w", "\\d{2,4}"]),
    ], '''name = "Tokyo"
greeting = f"Hello {name!r:>10}, {len(name)} letters\\n"
raw_regex_scoped = r"C:\\Users\\night"
raw_plain = R"C:\\Users\\night"
data = b"\\x41\\x42"
pattern = regex.compile(r"^(?P<word>[A-Z]\\w+)\\s+\\d{2,4}$")
print(greeting, raw_regex_scoped == raw_plain, data, pattern.match("Tokyo 2026"), "done")'''),

    ("Comments & docstrings", [
        (None, ["# A regular comment", "TODO", "FIXME", "XXX", "# type: int"]),
        (None, ['"""Triple-quoted docstring.', 'r"""', "Raw docstring", "'Single-quoted docstring."]),
    ], '''# A regular comment
# TODO: tag inside a comment; FIXME and XXX too


def documented():
    """Triple-quoted docstring."""


def raw_documented():
    r"""Raw docstring with \\d."""


def single_documented():
    'Single-quoted docstring.'


x = 1  # type: int'''),

    ("Functions & parameters", [
        (None, ["def", "lambda", "return", "->", ":"]),
        ("function.declaration", ["greet"]),
        ("function", ["greet#2"]),
        ("parameter.declaration", ["who:", "*args", "mark:", "**kwargs"]),
        ("parameter", ["{who}", "{mark}"]),
        ("parameter.keywordArgument", ["mark=", "sep="]),
        ("variable.declaration", ["result"]),
        ("variable", ["result#2"]),
        ("function.builtin", ["len", "print", "sorted"]),
        ("class.builtin", ["str", "int", "object"]),
    ], '''def greet(who: str, *args: int, mark: str = "!", **kwargs: object) -> str:
    result = f"Hi {who}{mark}"
    return result


square = lambda n: n * n
print(greet("Tokyo", 1, 2, mark="?"), len("abc"), sorted([3, 1, 2]), square(4), sep=" | ")'''),

    ("Classes, methods & decorators", [
        (None, ["class "]),
        ("class.declaration", ["City", "Megacity"]),
        ("function.decorator", ["@dataclass"]),
        ("class.decorator.builtin", ["@property", "@classmethod"]),
        ("selfParameter.declaration", ["(self)"]),
        ("clsParameter.declaration", ["(cls)"]),
        ("selfParameter", ["self.name"]),
        ("clsParameter", ["cls("]),
        ("property.declaration", [".visits ="]),
        ("property", [".name", ".population"]),
        ("method.declaration", ["rename", "tokyo"]),
        ("magicFunction.declaration", ["__init__", "__repr__"]),
        ("class.builtin", ["super", "list"]),
    ], '''@dataclass
class City:
    name: str
    population: int = 0
    tags: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.name} ({self.population:,})"

    @classmethod
    def tokyo(cls) -> "City":
        return cls("Tokyo", 14_000_000)

    def rename(self, new_name: str) -> None:
        self.name = new_name

    def __repr__(self) -> str:
        return self.label


class Megacity(City):
    def __init__(self, name: str) -> None:
        super().__init__(name, 10_000_000)
        self.visits = 0


osaka = Megacity("Osaka")
osaka.rename("Ōsaka")
print(City.tokyo(), osaka, osaka.visits)'''),

    ("Enums", [
        ("enum.declaration", ["Weather"]),
        ("enumMember.declaration", ["CLEAR", "RAIN", "SNOW"]),
        ("enumMember", ["CLEAR#2"]),
        ("class", ["auto"]),
    ], '''class Weather(Enum):
    CLEAR = auto()
    RAIN = auto()
    SNOW = auto()


tonight = Weather.CLEAR
print(tonight, tonight is Weather.RAIN)'''),

    ("Type hints & generics", [
        ("keyword", ["type"]),
        ("type.declaration", ["Pair"]),
        ("typeParameter.declaration", ["K", "V", "T"]),
        ("class.builtin", ["tuple", "list"]),
    ], '''type Pair[K, V] = tuple[K, V]


def first[T](items: list[T]) -> T | None:
    return items[0] if items else None


counts: Counter[str] = Counter("tokyo")
pair: Pair[str, int] = ("night", 1)
print(first([1, 2, 3]), counts.most_common(1), pair)'''),

    ("Control flow, exceptions & async", [
        (None, ["if", "for", "match", "case", "try", "except", "finally", "raise", "global", "async", "await", ":="]),
        ("class.builtin", ["ValueError", "KeyError"]),
    ], '''counter = 0


def bump() -> None:
    global counter
    counter += 1


def describe(value: object) -> str:
    match value:
        case int(n) if n > 0:
            return "positive int"
        case [first_item, *rest]:
            return f"list starting with {first_item}"
        case _:
            return "something else"


try:
    if (n := len(os.sep)) > 0:
        raise ValueError(f"separator length {n}")
except (ValueError, KeyError) as err:
    print("caught:", err)
finally:
    for _ in range(2):
        bump()


async def fetch() -> str:
    return "done"

print(describe(5), describe([1, 2]), await fetch(), counter)'''),

    ("Deprecated", [
        ("function.decorator", ["@deprecated"]),
        ("function.declaration", ["old_api"]),
        ("function.deprecated", ["old_api#2"]),
    ], '''@deprecated("Use greet() instead")
def old_api() -> None: ...


old_api()'''),
]


def semantic_tokens(code):
    """One token per snippet whose row names a Pylance token, spanning the identifier the snippet points at."""
    toks = []
    for _, rows, section in SECTIONS:
        start = code.index(section)
        for sem, snippets in rows:
            for s in snippets if sem else []:
                pos = find(code, s, start, start + len(section))
                while pos > 0 and (code[pos - 1].isalnum() or code[pos - 1] == "_"):
                    pos -= 1
                kind, *mods = sem.split(".")
                toks.append({"start": pos, "len": re.match(r"\w+", code[pos:]).end(), "type": kind, "mods": mods})
    return toks


def main():
    for title, _, section in SECTIONS:
        compile(section, title, "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    code = "\n\n".join(c for _, _, c in SECTIONS) + "\n"
    with tempfile.TemporaryDirectory() as tmp:
        src, sem = Path(tmp, "demo.py"), Path(tmp, "sem.json")
        src.write_text(code)
        sem.write_text(json.dumps(semantic_tokens(code)))
        lk = Lookup(tokenize(src, extension("ms-python.vscode-pylance"), str(sem)), "python")

    cells = [("markdown",
              "# Paper Frost: Python colors\n\n"
              "Every Python element and the color the theme gives it (<code>semanticHighlighting</code> is on). "
              "Colors are resolved from VS Code's Python grammar and the theme's rules; the semantic token types are the ones "
              "Pylance assigns, written into `make_python_demo.py` because Pylance only runs inside VS Code. "
              "Check any token with **Developer: Inspect Editor Tokens and Scopes**.")]
    for title, rows, section in SECTIONS:
        snippets = [s for _, snips in rows for s in snips]
        cells += [("markdown", legend(lk, title, snippets, section, code.index(section))), ("code", section)]
    write_notebook(cells, "python", "python_demo.ipynb",
                   {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                    "language_info": {"name": "python"}})


if __name__ == "__main__":
    main()
