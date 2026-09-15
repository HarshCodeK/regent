# Ownership

This project is built with AI assistance, and that is stated openly rather than hidden.
The rule is not "never use AI"; the rule is that **every module has an owner who can
defend it line by line** under questioning.

## The three states a module can be in

| State | Meaning |
|---|---|
| `owned` | Written by hand, or generated and then rewritten until every line is defensible |
| `assisted` | Scaffolded with AI help, reviewed line by line, not yet rewritten |
| `pending` | Not reviewed yet - **must not be claimed as mine in an interview** |

## Module status

| Module | State | Notes |
|---|---|---|
| `src/ledger.py` | owned | Integer money arithmetic and schema were written to be defended |
| `src/providers.py` | owned | The protocol seam; stub behaviour is deliberate |
| `src/models.py` | owned | Schema shape and validation rules |
| `src/config.py` | owned | Environment handling, no secret fallbacks |
| `src/app.py` | assisted | Wiring reviewed; routing/error mapping to be rewritten on Day 5 |
| `tests/*` | owned | Every test states the behaviour it protects and why it matters |

## The rule for every future module

1. Write it (with or without AI help), then read it out loud and delete anything you cannot explain.
2. Answer the twelve questions in `docs/QA.md` for that module, in writing, without the AI.
3. Only then set the state to `owned`.

A module that is `pending` does not count as mine, so it does not go in the README,
the resume, or the interview story.
