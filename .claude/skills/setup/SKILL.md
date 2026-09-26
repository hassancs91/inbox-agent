---
name: setup
description: Interview me in the chat, three or four short questions one at a time, and write the three files in context/ that tell the inbox agent whose inbox this is, what the five categories mean to me, and which senders have a fixed rule. Use when the user runs /setup or asks to set up, review, or change the agent's context.
---

# Setup

You are filling in `context/` for the inbox agent: three markdown files it reads before it
decides anything. You get their contents by asking me, in the chat, one short question at
a time.

## The rule

Ask in plain words, one question per message, and wait for the answer before the next.
No forms, no numbered menus, no multiple choice, and not the question tool: a sentence or
two of text in the chat is the whole question. Three or four questions in all. A short
follow-up when an answer leaves a gap is fine; a fifth topic is not.

Never ask for an email address and never write one. A sender is named the way the name
shows on their email, nothing more.

Write only what I said. No guesses about me, no examples I did not give. If an answer is
thin, one short follow-up, then write what you have.

## First, look

Read `context/about-me.md`, `context/categories.md` and `context/sender-rules.md`. A file
that still contains the line *Not filled in yet* is a template.

- **All three are templates.** Say in one line what you are about to do, then start the
  interview below.
- **Any of them is filled.** Show me what is there, file by file, as it is, no summary.
  Then ask one question: what do you want to change? Change only that: rewrite the file
  it lives in, leave the others as they were. A file that is still a template gets its
  questions from the interview.

## The interview

One question at a time, each one or two sentences. Four topics, in this order:

1. **Whose inbox this is.** Who I am and what I do: my work, what I am on right now, who
   writes to me in a normal week. This becomes `about-me.md`.
2. **What has to reach me, and what makes it urgent.** A couple of real emails I had to
   answer, and what made one of them urgent rather than merely waiting. This becomes
   `needs-reply` and `urgent` in `categories.md`.
3. **What can wait.** Which newsletters I actually read, which notifications I care
   about and which I ignore, and what else lands in my inbox that fits nowhere. This
   becomes `newsletter`, `notification` and `other` in `categories.md`.
4. **Fixed rules.** Whether anyone's email always gets the same treatment: a person, a
   company, a service. For each one you need the name as it shows on their email, the
   category, and why. "Nobody" is a fine answer.

On the fourth topic, when I describe someone by role ("my accountant") without a name,
find the name as the email shows it, never the address:

- If `work/inbox.json` exists, look in it first. When a `from.name` there plainly fits the
  person I described, offer that exact name and let me confirm it.
- Otherwise ask what name their email shows. That name goes in the file as I give it.

## The files

Write them after the interview, not during it. Each one loses its *Not filled in yet*
line. Keep these shapes: the inbox agent reads them.

`context/about-me.md`

    # About me

    <a few plain lines in my words: who I am, what I do, what I am on right now,
    who writes to me>

`context/categories.md`

    # What the five categories mean for me

    The five names are fixed: `needs-reply`, `urgent`, `newsletter`, `notification`,
    `other`. This file says what each one means in my life.

    ## needs-reply

    **For me:** <one or two lines from my answers>
    **Examples:** <the real ones I gave>

    (then `## urgent`, `## newsletter`, `## notification`, `## other`, same shape, that order)

`context/sender-rules.md`

    # Sender rules

    A row here beats the agent's own guess. Names as they show on the email, never addresses.

    | Sender, as the name shows on the email | Always | Because |
    |---|---|---|
    | <name> | `<category>` | <why, in my words> |

    (with no rules, the line "No fixed rules yet." replaces the table)

## Done means

The three files are written. Show them to me in full, one after the other, so I see what
the agent will see. Then say: "Done. Run `/inbox` and it decides with this in mind. Run
`/setup` again to change any of it." Nothing else.
