// Usage: VSC_NM=<VS Code node_modules> node check_jinja.js
// Tokenizes Jinja samples with VS Code's built-in grammars plus syntaxes/jinja.injection and asserts the scopes.
const fs = require("fs"), assert = require("assert");
const NM = process.env.VSC_NM, SYN = "/usr/share/code/resources/app/extensions/";
const tm = require(NM + "/vscode-textmate"), onig = require(NM + "/vscode-oniguruma");
const pkg = JSON.parse(fs.readFileSync(__dirname + "/package.json", "utf8")).contributes.grammars[0];

const files = {};  // scopeName -> grammar file, for every built-in grammar
for (const ext of fs.readdirSync(SYN)) {
  const dir = SYN + ext + "/syntaxes/";
  if (fs.existsSync(dir)) for (const f of fs.readdirSync(dir)) if (f.endsWith(".json"))
    files[JSON.parse(fs.readFileSync(dir + f, "utf8")).scopeName] = dir + f;
}
files[pkg.scopeName] = __dirname + "/" + pkg.path;

(async () => {
  await onig.loadWASM(fs.readFileSync(NM + "/vscode-oniguruma/release/onig.wasm").buffer);
  const reg = new tm.Registry({
    onigLib: Promise.resolve({ createOnigScanner: s => new onig.OnigScanner(s), createOnigString: s => new onig.OnigString(s) }),
    loadGrammar: async sc => files[sc] ? tm.parseRawGrammar(fs.readFileSync(files[sc], "utf8"), files[sc]) : null,
    getInjections: sc => pkg.injectTo.includes(sc) ? [pkg.scopeName] : undefined,
  });
  // innermost scope of the first occurrence of `text` in `line`
  const scopeOf = async (root, line, text) => {
    const g = await reg.loadGrammar(root), at = line.indexOf(text);
    const t = g.tokenizeLine(line, tm.INITIAL).tokens.find(t => t.startIndex <= at && at < t.endIndex);
    return t.scopes.at(-1);
  };
  const cases = [
    ["source.python", 'Template("Hi {{ user.name | title }}")', "user", "variable.other.jinja"],
    ["source.python", 'Template("Hi {{ user.name | title }}")', "title", "support.function.filter.jinja"],
    ["source.python", 'Template("Hi {{ user.name | title }}")', "{{", "punctuation.definition.tag.begin.jinja"],
    ["source.python", "t = '{% for x in items -%}'", "for", "keyword.control.jinja"],
    ["source.python", "t = '{% for x in items -%}'", "in", "keyword.other.jinja"],
    ["source.python", "t = '{% for x in items -%}'", "-%}", "punctuation.definition.tag.end.jinja"],
    ["source.python", 'f"{{ x }}"', "x", "!jinja"],           // f-string: {{ is an escaped brace
    ["source.python", "x = {1: 2}  # {{ y }}", "y", "!jinja"],  // only inside strings
    ["source.yaml", "msg: Hello {{ name }}", "name", "variable.other.jinja"],
    ["source.yaml", 'n: "{{ 42 }}"', "42", "constant.numeric.jinja"],
    ["source.yaml", "# {{ off }}", "off", "!jinja"],            // not in comments
    ["text.html.basic", '<a href="{{ url_for(\'home\') }}">', "url_for", "entity.name.function.jinja"],
    ["text.html.basic", "<p>{# note #}</p>", "note", "comment.block.jinja"],
    ["text.xml", '<item id="{{ i }}">{{ none }}</item>', "none", "constant.language.jinja"],
    ["source.json", '{"k": "{{ v | default(\'x\') }}"}', "default", "support.function.filter.jinja"],
  ];
  for (const [root, line, text, want] of cases) {
    const got = await scopeOf(root, line, text);
    if (want === "!jinja") assert(!got.endsWith(".jinja"), `${root} ${line}: ${text} -> ${got}`);
    else assert.strictEqual(got, want, `${root} ${line}: ${text}`);
  }
  // every Jinja scope the grammar emits (comments aside) gets the theme's Jinja colour
  const theme = JSON.parse(fs.readFileSync(__dirname + "/themes/paper-frost-color-theme.json", "utf8").replace(/,(\s*[}\]])/g, "$1"));
  const jr = theme.tokenColors.filter(r => r.name?.startsWith("Jinja"));
  assert(jr.every(r => r.settings.fontStyle === "italic"), "every Jinja rule is italic");
  const colored = new Set(jr.flatMap(r => r.scope));
  const all = `x = "{% if a.b > 1 and c[0] %}{{ f('s', \\"t\\") | upper ~ none }}{% endif %}"`;
  const leaves = (await reg.loadGrammar("source.python")).tokenizeLine(all, tm.INITIAL).tokens
    .map(t => t.scopes.at(-1)).filter(s => s.endsWith(".jinja"));
  for (const s of new Set(leaves)) assert(colored.has(s), `theme has no Jinja colour for ${s}`);
  console.log(`ok: ${cases.length} cases, ${new Set(leaves).size} Jinja scopes coloured`);
})().catch(e => { console.error(e.message); process.exit(1); });
