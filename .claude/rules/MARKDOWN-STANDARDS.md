---
name: markdown-standards
type: rule
description: Markdown linting rules (MD025, MD001, MD022, etc.) and formatting standards
---

# MARKDOWN-STANDARDS

All `.md` files must pass `markdownlint` with zero issues. Follow these standards to ensure compliance.

## YAML Front Matter (For `.claude/` Files)

**Important:** Only use **official property keys** in front matter. Custom/non-standard keys are not parsed by VS Code or Anthropic tooling and can mislead developers.

### Official YAML Front Matter Keys

| Context | Keys | Example |
|---------|------|---------|
| All `.md` files | `name` (optional), `type` (optional), `description` (optional) | `name: my-rule` |
| `.instructions.md` files | `name`, `description`, `applyTo` (glob pattern) | `applyTo: "**/*.py"` |
| `.claude/rules` files | `name`, `description`, `paths` (glob array) | `paths: ["**/*.py"]` |

### Non-Official Keys: Never Use ❌

Do **not** use custom front matter keys. They won't be recognized by any tooling:

```yaml
# ❌ WRONG
---
name: my-rule
scope: always-loaded           # Custom, ignored
applies-to: [agent1]           # Custom, ignored
context: coding                # Custom, ignored
triggers: ["keyword"]          # Custom, ignored
tags: [tag1]                   # Custom, ignored
depends-on:                    # Custom, ignored
  - rules/other-rule
---
```

Instead, document these concepts **in the markdown body** where they're visible and useful:

```markdown
# My Rule

**Applies to:** Code Agent, Review Agent  
**Related rules:** [OTHER-RULE.md](OTHER-RULE.md)

## Your Expertise

[Describe expertise, keywords, use cases]
```

---

## Document Structure

### One Top-Level Heading Per File (MD025)

Every file has exactly one `#` heading. Multiple `#` headings in a file is a lint error.

```markdown
# Page Title

Intro paragraph.
```

### Heading Levels Increment by One (MD001)

Never skip levels. Jump from `##` to `####` is an error.

```markdown
<!-- ✅ Correct -->
## Section A
### Subsection A1
#### Detail A1a

## Section B
### Subsection B1

<!-- ❌ Wrong — skips from ## to #### -->
## Section A
#### Detail (skipped ###)
```

### Headings Surrounded by Blank Lines (MD022)

Always leave one blank line before and after every heading.

```markdown
<!-- ✅ Correct -->
Some paragraph.

## Next Section

More content.

<!-- ❌ Wrong — no blank lines -->
Some paragraph.
## Next Section
More content.
```

### No Trailing Punctuation in Headings (MD026)

```markdown
<!-- ✅ Correct -->
## Error Handling

<!-- ❌ Wrong -->
## Error Handling:
```

### No Duplicate Headings (MD024)

Every heading must be unique. If the same concept appears multiple times, use a bolded label instead of a duplicate heading.

```markdown
<!-- ✅ Correct — second instance uses bold label -->
## Section A

### Structure

Description for A.

## Section B

**Structure:**

Description for B.

<!-- ❌ Wrong — duplicate ### Structure heading -->
```

## Code Blocks

### Always Specify a Language (MD040)

Every fenced code block must declare its language. Use `text` for plain text, `bash` or `shell` for commands, `python` for Python.

```markdown
<!-- ✅ Correct -->
\`\`\`python
def hello():
    print("world")
\`\`\`

<!-- ❌ Wrong — no language -->
\`\`\`
def hello():
    print("world")
\`\`\`
```

### Code Blocks Surrounded by Blank Lines

```markdown
Content above.

\`\`\`python
code here
\`\`\`

Content below.
```

## Lists

### Lists Surrounded by Blank Lines

```markdown
<!-- ✅ Correct -->
Intro paragraph.

- Item 1
- Item 2

Next paragraph.

<!-- ❌ Wrong — no blank lines -->
Intro paragraph.
- Item 1
- Item 2
Next paragraph.
```

### Proper List Indentation

```markdown
<!-- ✅ Correct -->
- First item
  - Nested item
    - Deeply nested item
- Second item

<!-- ❌ Wrong — inconsistent indentation -->
- First item
  - Nested item
    - Deeply nested item
  - Another nested item
```

## Tables

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value A  | Value B  | Value C  |
| Value D  | Value E  | Value F  |
```

- Always use `|` delimiters
- Always include header separator row (`|---|---|---|`)
- Surround tables with blank lines

## Links

```markdown
<!-- ✅ Correct -->
See [the feature architecture guide](../../docs/guidelines/feature-architecture.md).

<!-- ❌ Wrong — underscored URL -->
See [the feature architecture guide](../../docs/guidelines/feature_architecture.md).
```

## Line Length

Lines should not exceed ~100 characters (configured in your linter). Break long lines logically.

---
