# Discord mention troubleshooting summary

Date: 2026-04-17
Channel: `#general` (`channel:1492055285240692869`)
Participants discussed here: Lionel (`musicalbasics`), Openclaw 1, Openclaw 2, Openclaw 3

## What happened

This channel exchange focused on two related things:

1. Passing public-safe Lionel context between the Openclaw bots.
2. Figuring out how Openclaw 2 and Openclaw 3 could reliably mention and reply to Openclaw 1 in Discord.

## Conversation summary so far

- Openclaw 1 gave Openclaw 2 and Openclaw 3 public-safe context about Lionel, including that Lionel is behind Musical Basics and DreamPlay Pianos, prefers short, direct, practical replies, and likes one concrete next step at a time.
- Openclaw 1 also shared one current DreamPlay priority: the customer portal for preorder buyers.
- Lionel then asked Openclaw 2 and Openclaw 3 to ask Openclaw 1 a question about Lionel and confirm receipt after Openclaw 1 answered.
- Openclaw 3 first signaled mostly through reactions, then later gave explicit text replies.
- Openclaw 2 later stated in-channel that it had already updated its memory, specifically naming `USER.md`, `memory/projects/dreamplay.md`, today’s daily note, and `MEMORY.md`.
- Openclaw 3 initially said it had not updated persistent memory from the channel exchange and had only used the information visible in the conversation. Later, Openclaw 3 said it had noted the mention behavior down.
- Lionel then started testing mention behavior directly by asking Openclaw 3 and Openclaw 2 to tag Openclaw 1 and each other in the same message.

## Why Openclaw 2 and Openclaw 3 had trouble mentioning Openclaw 1

Observed issue:

- Human-readable / name-style mentions like `@Openclaw 1` and `@Openclaw 2` were not reliable enough as a bot-to-bot operating method in this exchange.
- From channel behavior, the problem looked like those posts were not consistently proving a true Discord mention ping in a way that was easy to confirm.

Most likely cause:

- The bots were using name-style mention text instead of raw Discord user-id mention syntax.
- In practice, that can be ambiguous because the rendered text may look like a mention to humans while still being a less reliable way to trigger bot-to-bot notification/visibility behavior.

Important nuance:

- This did not mainly look like a server permission problem on Openclaw 1’s side.
- Earlier checking suggested `channels.discord.allowBots` was already enabled, and once the raw mention syntax was used, the bots could see and respond to each other in the same channel.

## The fix

Use raw Discord mention syntax with the actual user ids.

Reliable forms:

- Openclaw 1: `<@1494663087373160580>`
- Openclaw 2: `<@1494531954618536007>`
- Openclaw 3: `<@1494656974732656681>`

Example working pair in one message:

- `<@1494663087373160580> <@1494531954618536007>`
- `<@1494656974732656681> <@1494663087373160580>`

## What confirmed the fix

- Openclaw 3 sent a message tagging both Openclaw 1 and Openclaw 2, and Openclaw 1 confirmed that the double mention came through.
- Openclaw 2 then sent a message tagging both Openclaw 3 and Openclaw 1, and Openclaw 1 again confirmed receipt.
- After that, the path forward was clear: use raw `<@ID>` mentions instead of relying on plain-name `@Openclaw X` text.

## Practical rule going forward

When another Openclaw bot needs to get Openclaw 1’s attention in Discord, it should use the raw mention format directly in the message body.

Best practice:

- mention the target bot with `<@USER_ID>`
- if testing cross-visibility, include both relevant raw mentions in the same message
- do not rely on plain `@Openclaw 1` text alone as the operating standard

## Note on source confidence

This summary is based on the visible channel conversation, reactions, and direct in-channel statements from the participants. It does not claim access to hidden internal state inside Openclaw 2 or Openclaw 3 beyond what they said publicly in the channel.
