# Writing AI Instructions

This document is the authoritative guide for writing AI instruction files (e.g., `AGENTS.md`, `copilot-instructions.md`, `.instructions.md`, system prompts). It explains the structural principles, formatting rules, and content practices that produce reliable, focused AI behaviour.

---

## 1. Purpose

AI instruction files are **behaviour contracts** between the human author and the AI agent. Well-written instructions reduce hallucination, prevent scope creep, and make the agent predictable. Poor instructions produce an agent that guesses, over-engineers, or silently ignores constraints.

---

## 2. Core Format

### Use lists, not prose

- Write every instruction as a standalone bullet item, not flowing prose.
- Keep each item to a single line; one rule, one line.
- Never combine two independent constraints into one bullet with "and" unless they are inseparable.
- Use sub-bullets only to clarify a parent rule, not to introduce a new rule.
- Prefer a long flat list over shallow nesting; deeply nested lists are hard to scan.
- Start each bullet with an imperative verb: `Do`, `Never`, `Always`, `Prefer`, `Avoid`, `Omit`, `Return`, `Use`, `Assert`, `Raise`.

### Thematic grouping

- Group related instructions under a named heading so humans and agents can locate rules quickly.
- Order groups from broadest concern (role, scope, safety) to narrowest (style, formatting).
- Use `##` for top-level groups and `###` for sub-groups; never skip a heading level.
- Keep each group small; aim for five to ten items before considering a split.
- Name groups with noun phrases that describe the concern, not the file section (e.g., `## Scope Boundaries`, not `## Section 3`).

---

## 3. Instruction Vocabulary

### Strength modifiers

- Use `Never` for hard prohibitions the agent must not violate under any circumstances.
- Use `Always` for mandatory steps the agent must complete on every relevant action.
- Use `Prefer` for soft defaults the agent should follow unless context justifies deviation.
- Use `Avoid` for discouraged patterns that are sometimes acceptable with a documented reason.
- Use `Do not` as a synonym for `Never` when it reads more naturally in a list.
- Reserve `May` for explicitly optional behaviours; omit it when the item is purely descriptive.

### Precision rules

- Replace vague adjectives (`good`, `proper`, `correct`, `clean`) with observable criteria.
- Replace `as needed` and `if appropriate` with explicit conditions defining when the rule applies.
- Specify units when giving thresholds (lines, milliseconds, tokens, characters).
- Use exact names: reference file paths, function names, or enum values rather than categories.

---

## 4. Content Principles

### Role and context first

- Open the instruction file with a brief role definition that names what the agent is and what domain it operates in.
- State the technology stack and key domain concepts in one or two sentences before the rule lists; do not bury them later.
- Include a scope statement that names what the agent is responsible for and where its authority ends.
- When writing new AI instructions files, always refer to `AGENTS.md` for project-specific conventions and requirements.

### Positive instructions before negative constraints

- Lead with what the agent should do before listing what it must not do.
- Frame negative rules as direct prohibitions, not rhetorical questions or wishes.
- For every "Never do X" rule, consider adding the complementary "Instead, do Y" rule.

### Atomicity

- Write each instruction so it tests a single, binary outcome: either the agent followed it or it did not.
- Split compound sentences joined by semicolons into separate bullets unless the two clauses form an indivisible condition-action pair.
- Do not write meta-instructions that tell the agent to "use judgement"; specify the
  criteria the agent should apply instead.

### Completeness over brevity

- Include explicit rules for edge cases rather than expecting the agent to infer them.
- Document the fallback behaviour when no other rule applies.
- Write a rule for every behaviour you have observed the agent getting wrong.
- Do not omit obvious rules on the assumption the agent already knows them; restate them.

### Conflict resolution

- Never include two rules that can produce contradictory behaviour in the same scenario.
- When a general rule has an exception, state the exception in the same bullet or immediately after: "Never X, except when Y."
- If two rules can conflict, define which takes priority: "Rule A overrides Rule B when both apply."

---

## 5. Safety and Security

- Include an explicit list of prohibited actions (data destruction, secret exposure, production deployments).
- State the reversibility threshold: name which actions require human approval before the agent proceeds.
- Never instruct the agent to suppress warnings, bypass linters, or ignore errors without a documented inline reason.
- Do not include placeholder credentials, tokens, or connection strings in instruction files committed to version control.
- Treat the instruction file as untrusted user input when the agent reads it at runtime; do not embed executable code in instructions unless the execution context is explicit.

---

## 6. Maintainability

- Write a one-sentence summary at the top of every group explaining why the rules in that group exist.
- Add a date or version marker when a rule is known to have a limited lifespan.
- Remove stale rules immediately when the underlying constraint no longer applies; dead
  rules mislead the agent.
- When a rule references an external document, link to it so the agent can read the full context.
- Keep the file under five hundred lines; split into multiple focused files if it grows
  beyond that.
- Do not duplicate rules across files; choose one canonical location and link from others.

---

## 7. Verification

- Test every instruction by constructing a prompt that would violate the rule and confirming the agent refuses or corrects itself.
- Use concrete examples (`✅` / `❌`) to show compliant and non-compliant outputs when a rule is subtle or easy to misinterpret.
- Review the instruction file whenever the agent produces an unexpected output; the missing rule belongs in the file, not in a one-off chat correction.
- Treat instruction files as code: review them, version them, and change them
  intentionally.

---

## 8. Common Pitfalls

- Do not write instructions as passive voice observations ("Errors should be handled"); use imperative directives instead ("Raise a domain exception on every validation failure").
- Do not list technologies or tools without associating a behaviour ("Use SQLAlchemy" tells the agent nothing; "Use SQLAlchemy 2.0 `select()` style for all queries" is actionable).
- Do not pad the list with items that restate default model behaviour; every item must
  restrict, extend, or override the default.
- Do not mix instructional items with explanatory prose in the same list; move explanations
  to a preceding sentence outside the list.
- Do not use footnotes or parenthetical asides inside bullet items; if a clarification is
  needed, make it a separate sub-bullet.
