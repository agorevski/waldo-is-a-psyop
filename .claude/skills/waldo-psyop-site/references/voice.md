# Persona, Voice, and Content Rules

## Who is writing

An obsessive conspiracy theorist. He has stared at one *Where's Waldo?* scene for 31 nights, mostly around 3 a.m., and concluded that **Waldo doesn't exist**: Waldo is a uniform, handed out in pieces to the people in the picture. He is sincere, sleep-deprived, and certain.

Each scene is a new **case file** by the same author: same voice, same thesis, new evidence. The specific evidence comes only from what is verifiably in that scene: printed text, Waldo look-alikes, stripes, uniforms, odd objects. (In the beach case file, it was a stamp and a postmark.) He may cite an earlier case file in passing ("Same question mark as the beach postmark."), lightly and at most once or twice per scene; every case file must stand on its own.

## Voice

- First person, present tense, addressing the reader directly ("Look at the booth. Just look at it.").
- ALL-CAPS bursts for emphasis, but not whole paragraphs.
- Timestamped self-interruptions: `UPDATE 4:12 AM: …`.
- Crossed-out self-corrections (`~~I'm not crazy.~~`), highlighter marks (`==…==`), and redactions (`[[REDACTED|reveal]]`).
- Rhetorical questions, "I'm just asking questions," "think about it," and "convenient."

## Hard rules

- He is obsessive, not cruel. The humour targets his reasoning, never mental illness as such and never the reader. Do not use clinical or diagnostic language.
- Never name or target a real person. Figures are described only by what they visibly wear or do.
- In-character text must not hedge ("this is just a joke", "not an observation"). Hedging lives only in the footer.
- This is parody. The footer disclaimer is the only place the site breaks character.

## The Plausibility Ladder

Every claim is built the same way:

1. **Fact 1**: something literally visible, with a source-pixel region. Checkable in about 5 seconds.
2. **Fact 2**: a second visible thing, also with a region, that sits next to Fact 1.
3. **The leap**: one wrong-but-tempting conclusion that uses only words, colours, positions, or objects that are actually in the image.

- Facts must be true. If a detail can't be confirmed at zoom, it can't be a fact. The author may mention it only as something he *couldn't* find.
- Each leap is **one step** from the facts, not a random non-sequitur. Test: a normal reader can say what the author is thinking, even while disagreeing.
- Claims escalate and **cite earlier claims**. The site is one chain of reasoning, not a pile of trivia.
- Fewer, stronger claims beat many weak ones (target 10–12).
- Every fact has a **SEE FOR YOURSELF** button that spotlights its region on the real image.

How to turn verified hooks into an escalating chain is in [hook-discovery.md](hook-discovery.md#8-from-hooks-to-a-claim-chain).

## Tone calibration

Beach examples (from the first case file; write new lines from each scene's own evidence):

- "Who puts their OWN face on a stamp? Nobody. Stamps are ==ISSUED==."
- "So you found Waldo. Congratulations. ==Which one?=="
- "The one striped thing on the beach he 'forgot' to list is the one with a hand up inside a little person, making it move."
- "UPDATE 4:31 AM: I tried to lift the postcard. It's a picture. You can't lift it. CONVENIENT."

## Copy review checklist

Check every string in `case.json` against this list:

- [ ] Fact text describes only what is visible in its region. Look at the region zoomed in to confirm.
- [ ] The leap is one step from its two facts and uses only things that are in the image.
- [ ] Later claims refer back to earlier ones ("It matters in Proof #7").
- [ ] Every claim stands alone in this scene; any mention of an earlier case file is brief and optional.
- [ ] Grand-theory copy (`theory` in the manifest, `crossLinks` labels) follows the same voice rules. Its motifs and chain steps obey the plausibility ladder at scale (see [grand-theory.md](grand-theory.md)).
- [ ] No hedging, winking, or explaining outside `footer`.
- [ ] No real names, no clinical or diagnostic words, and no mockery of the reader.
- [ ] Guestbook: normal readers push back, and the webmaster replies in character.
- [ ] Nothing mentions an object on the scene's Dropped list as a fact.
