# Markdown Documentation Guidelines

Self-contained reference for writing Markdown documentation in ClickNBack. Follow every rule here when creating or editing any `.md` file so that files pass `markdownlint` with zero issues.

---

## 1. Document Structure

### One Top-Level Heading Per File (MD025)

Every file begins with exactly one `#` heading. Using more than one `#` heading in a file is a lint error.

```markdown
# My Document Title

Intro paragraph.
```

### Heading Levels Must Increment by One (MD001)

Never skip a level — jump from `##` to `####` triggers a warning.

```markdown
<!-- ✅ correct -->
## Section
### Subsection
#### Detail

<!-- ❌ wrong — skips a level -->
## Section
#### Detail
```

### Headings Must Be Surrounded by Blank Lines (MD022)

Always leave one blank line before and after every heading.

```markdown
<!-- ✅ correct -->
Some paragraph.

## Next Section

More content.

<!-- ❌ wrong — no blank lines around heading -->
Some paragraph.
## Next Section
More content.
```

### No Trailing Punctuation in Headings (MD026)

```markdown
<!-- ✅ correct -->
## Error Handling

<!-- ❌ wrong -->
## Error Handling:
```

---

## 2. Code Blocks

### Always Specify a Language (MD040)

Every fenced code block must declare its language. For plain text, use `text`. For shell commands, use `bash` or `shell`.

| Content | Fence language |
| --- | --- |
| Python code | `python` |
| Shell commands | `bash` |
| SQL | `sql` |
| JSON | `json` |
| YAML | `yaml` |
| TOML | `toml` |
| Plain text / output | `text` |
| Markdown examples | `markdown` |

```text
<!-- ✅ correct -->
    ```python
    def hello() -> None:
        print("hi")
    ```

<!-- ❌ wrong — no language tag -->
    ```
    def hello() -> None:
        print("hi")
    ```
```

### Code Blocks Must Be Surrounded by Blank Lines (MD031)

Leave one blank line before the opening fence and one blank line after the closing fence.

````markdown
Some prose.

```python
x = 1
```

More prose.
````

### Use Consistent Fence Style (MD048)

Use triple backticks ` ``` ` exclusively. Do not mix with `~~~`.

### No Dollar Signs on Commands Without Output (MD014)

When showing a shell command that has no accompanying output, omit the `$` prefix. Include `$` only when the example shows both input and output together.

```bash
# ✅ command only — no dollar sign
make test

# ✅ command + output together — dollar sign acceptable
$ make test
...collected 42 items...
```

---

## 3. Tables

### Separator Row Must Have Spaces Around Each Set of Dashes (MD055 / style)

The header separator cells must be written as `| --- |`, not `|---|`. Omitting spaces is flagged by markdownlint's pipe table rules.

```markdown
<!-- ✅ correct -->
| Column A | Column B | Column C |
| --- | --- | --- |
| value | value | value |

<!-- ❌ wrong — no spaces around dashes -->
| Column A | Column B | Column C |
|---|---|---|
| value | value | value |
```

### Every Table Needs a Header Row

All Markdown pipe tables must start with a header row followed by a separator row.

### Keep Tables Readable

- Align pipes vertically when the content length is similar — it is not required but aids readability.
- Avoid embedding complex Markdown (nested lists, multi-line content) inside table cells.
- Prefer prose or a list if content does not fit naturally in a table.

---

## 4. Lists

### Lists Must Be Surrounded by Blank Lines (MD032)

```markdown
Paragraph before the list.

- Item one
- Item two
- Item three

Paragraph after the list.
```

### One Space After List Marker (MD030)

```markdown
<!-- ✅ correct -->
- Item
* Item
1. Item

<!-- ❌ wrong — two spaces -->
-  Item
```

### Consistent Unordered List Marker Style (MD004)

Pick one marker (`-`) and use it throughout the file. Do not mix `-`, `*`, and `+`.

### Nested List Indentation (MD007)

Use **2 spaces** per indent level for unordered lists.

```markdown
- Top level
  - Second level
    - Third level
```

### Ordered Lists Must Use Consistent Prefix (MD029)

Use `1.` for every ordered list item (the renderer numbers them automatically), or increment normally. Never mix styles.

```markdown
1. First step
1. Second step
1. Third step
```

---

## 5. Whitespace and Formatting

### No Trailing Spaces (MD009)

Do not leave spaces at the end of any line. Hard line breaks use a backslash `\` or HTML `<br>` instead.

### No Hard Tabs (MD010)

Use spaces only. Configure your editor to expand tabs.

### One Line Per Paragraph — No Manual Wrapping

Write each paragraph as a single unbroken line regardless of its length. Never insert a hard line break in the middle of a paragraph to keep it within a visual column limit.

Editors and renderers wrap lines automatically. Manual wraps create misleading diffs and break paragraph-level search.

```markdown
<!-- ✅ correct — full paragraph on one line -->
Application secrets live in a static `.env` file on the VPS, placed once by an operator with `chmod 600`. The CD pipeline never reads or writes this file.

<!-- ❌ wrong — manual wrap mid-paragraph -->
Application secrets live in a static `.env` file on the VPS, placed once by an
operator with `chmod 600`. The CD pipeline never reads or writes this file.
```

The same rule applies to list items: each item is a single line.

```markdown
<!-- ✅ correct -->
- CI secrets rotate independently of the VPS; keeping them in sync adds operational risk.

<!-- ❌ wrong -->
- CI secrets rotate independently of the VPS; keeping them in sync adds
  operational risk.
```

### No More Than One Consecutive Blank Line (MD012)

```markdown
<!-- ✅ correct — one blank line between paragraphs -->
Paragraph one.

Paragraph two.

<!-- ❌ wrong — two consecutive blank lines -->
Paragraph one.


Paragraph two.
```

### File Must End with a Single Newline (MD047)

Ensure the last line of every file is followed by exactly one newline character.

---

## 6. Links and References

### No Bare URLs (MD034)

Always wrap standalone URLs in angle brackets or use a link label.

```markdown
<!-- ✅ correct -->
<https://example.com>
[Example](https://example.com)

<!-- ❌ wrong -->
https://example.com
```

### No Reversed Link Syntax (MD011)

```markdown
<!-- ✅ correct -->
[link text](url)

<!-- ❌ wrong -->
(link text)[url]
```

### Images Must Have Alt Text (MD045)

```markdown
<!-- ✅ correct -->
![Architecture diagram](docs/design/architecture.png)

<!-- ❌ wrong -->
![](docs/design/architecture.png)
```

---

## 7. Horizontal Rules

### Use Consistent Horizontal Rule Style (MD035)

Use three dashes on their own line: `---`. Do not use `***`, `___`, or variations with spaces.

---

## 8. Emphasis and Strong

### No Emphasis as a Substitute for a Heading (MD036)

Use a real heading (`##`), not bold or italic text on its own line.

```markdown
<!-- ✅ correct -->
## Configuration

...

<!-- ❌ wrong — bold used as a pseudo-heading -->
**Configuration**

...
```

### Consistent Emphasis Style (MD049 / MD050)

Use `_word_` for italic and `**word**` for bold throughout the file. Do not mix `*word*` and `_word_` for italic.

---

## 9. Blockquotes

### One Space After Blockquote Symbol (MD027)

```markdown
<!-- ✅ correct -->
> This is a note.

<!-- ❌ wrong — two spaces -->
>  This is a note.
```

### No Blank Line Inside a Blockquote (MD028)

```markdown
<!-- ✅ correct — single continuous blockquote -->
> First line.
> Second line.

<!-- ❌ wrong — blank line splits the blockquote into two -->
> First line.

> Second line.
```

---

## 10. Content Conventions for Technical Docs

### Lead with Context, Not Procedure

Open every document and major section with a one-sentence statement of *what* the subject is and *why* it matters, before any how-to steps.

### AAA Structure for Example Workflows

When documenting a multi-step process, mirror the three-block pattern: context (what you need), action (the steps), outcome (what to verify).

### Use Tables for Structured Comparisons

Prefer a table over prose whenever you are comparing two or more options across the same set of attributes.

### Use Code Blocks for All Commands and File Paths

Never write a shell command, file path, function name, or config key as plain text mid-sentence. Inline code or a fenced block must be used.

```markdown
<!-- ✅ correct -->
Run `make test` before pushing.

<!-- ❌ wrong -->
Run make test before pushing.
```

### Heading Hierarchy Mirrors Document Purpose

```text
# Document title          ← one per file
## Major section          ← primary topics
### Subsection            ← details within a topic
#### Sub-subsection       ← use sparingly; restructure if you need more levels
```

### Checklists for Procedural Steps

When capturing a repeatable process (e.g., a release procedure, a review checklist), use a Markdown task list.

```markdown
- [ ] Run `make lint`
- [ ] Run `make test`
- [ ] Update `CHANGELOG.md`
- [ ] Open a pull request
```

### Callout Convention

Use blockquotes with a bold label when flagging important notes or warnings.

```markdown
> **Note:** This only applies when `DEBUG=true` is set.

> **Warning:** Running this in production will truncate the table.
```

---

## 11. Quick Reference — Common Lint Errors

| Rule | What triggers it | Fix |
| --- | --- | --- |
| MD001 | Heading level skipped (e.g. `##` → `####`) | Use consecutive levels only |
| MD010 | Hard tab character in file | Replace with spaces |
| MD012 | Two or more consecutive blank lines | Remove extra blank lines |
| MD014 | `$` before a command with no output shown | Remove `$` prefix |
| MD022 | No blank line before/after a heading | Add blank lines around headings |
| MD025 | More than one `#` heading in the file | Keep exactly one top-level heading |
| MD026 | Heading ends with `:` or other punctuation | Remove trailing punctuation |
| MD029 | Ordered list item numbers inconsistent | Use `1.` for every item |
| MD031 | No blank line before/after fenced code block | Add blank lines around code blocks |
| MD032 | No blank line before/after a list | Add blank lines around lists |
| MD034 | Bare URL in text | Wrap in `<…>` or `[text](url)` |
| MD040 | Fenced code block has no language tag | Add a language tag after the opening fence: `python`, `text`, `bash`, etc. |
| MD045 | Image has no alt text | Add descriptive alt text inside `![…]` |
| MD047 | File does not end with newline | Ensure a final newline character |
| MD055 | Table separator row uses `&#124;---&#124;` without spaces | Use `&#124; --- &#124;` in every separator cell |
