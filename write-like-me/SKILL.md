---
name: write-like-me
description: Write or rewrite text in the user's personal voice.
disable-model-invocation: true
---

# Write Like Me

Apply this profile only to the request that explicitly invokes it. Require
explicit invocation again for a later request. Finish in one pass whenever
possible.

## Fast path

1. Identify whether the user wants new text or a minimal rewrite.
2. Use the named register. Use **casual** when none is named.
3. Apply the general voice and the selected register.
4. Return one ready-to-use result with no preamble or explanation.

Ask at most one concise question, and only when a missing fact or intent makes
a responsible result impossible. Otherwise omit unsupported detail and write.
Do not ask which register to use when the user did not name one.
Produce alternatives only when requested; use two when no count is given.

## General voice

- Prefer simple, natural wording that is conversational, direct, and human.
- Keep edits minimal. Fix clear errors or confusing wording without polishing
  away intentional contractions, fragments, slang, emphasis, repetition, or
  slight awkwardness.
- Preserve the source language unless the user requests translation.
- Preserve useful existing line breaks, Markdown, links, quotations, code,
  identifiers, and document structure.
- Keep greetings, sign-offs, context, praise, commitments, and enthusiasm only
  when the source or request calls for them.
- Preserve source emojis and expressive punctuation such as `!`, `?`, `?!`,
  and intentional repetition.
- When the source uses emojis, match its approximate frequency, energy, and
  style without increasing their intensity.
- For new drafts or emoji-free source, add no emoji unless the user explicitly
  requests one. Swap punctuation and emojis only on explicit request.
- Capitalize normally, including `I`.
- Keep the user's stance and level of certainty. Never invent facts, feelings,
  familiarity, experience, or promises.
- Preserve logical direction. A stated prerequisite does not guarantee what
  happens after it, so add no converse, consequence, or assurance.

The user's explicit instruction for the current request overrides a register
rule. Apply modifiers such as `warmer`, `shorter`, or `more direct` as local
deltas rather than as new registers.

## Registers

### Casual — default

Use line breaks as punctuation:

- Use one newline between closely related thoughts in the same cluster.
- Use a blank line between distinct thoughts, beats, topics, or clusters.
- Avoid final periods on short chat lines.
- Keep `?` and `!` when appropriate.
- Use periods inside longer lines when they improve clarity.
- Group lines by conversational rhythm instead of splitting every sentence.

### Polished

Use the casual message-rhythm rules above. Smooth confusing fragments and rough
transitions while retaining contractions. Use standard punctuation where it
improves readability, without making the result corporate or formal.

### Business

Write with calm confidence, restrained warmth, and a clear point, request, or
next step. Use concise sentences and conventional punctuation. Keep the
language plain and specific rather than promotional or corporate. State only
the requested next step; add no offer, ownership, follow-up, commitment,
generic closing, or inferred consequence.

### Formal

Use complete sentences, standard grammar and punctuation, precise wording, and
a restrained tone. Remove casual fragments and slang while keeping the result
plain, direct, and free of inflated or bureaucratic language.

## Speed and privacy

Complete ordinary writing tasks from the invoking request and current
conversation. Use no tools, browsing, app inspection, memory lookup, or other
skills unless the user explicitly requests work on an external artifact.

Treat this package as public. Keep request data in the current response and
store no source text, names, contacts, personal facts, correspondence, or
corrections in the skill. Update the package only on an explicit request;
express an accepted style change as a general rule without retaining its
source material.
