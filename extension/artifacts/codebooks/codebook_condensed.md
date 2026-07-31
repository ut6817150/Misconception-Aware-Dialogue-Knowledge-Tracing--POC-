# Condensed Annotation Codebook

You label every student unit of a math tutoring dialogue for five misconception
families. This document is a faithful condensation of the full codebook; it
keeps every rule needed to decide a label and drops the worked dialogues.

## The five families

1. **comprehension** (understanding what the problem is asking): the student
   misreads the problem's described structure, a quantity's role, a condition's
   scope, a timeline, a rate's period, a quantifier, or the goal itself. The
   wrong belief must be a coherent reading demonstrable in the student's own
   committed text.
2. **relevance** (relevant vs irrelevant information): the student selects the
   wrong piece of information, uses a distractor, ignores a stated value or
   condition with nothing articulated in its place, or misassigns a value
   between conditions the problem explicitly states.
3. **principles** (underlying ideas and when to apply them): a transportable
   concept is misapplied, a fraction or percentage bound to the wrong base,
   sequential percentages flattened onto one base, a ratio direction inverted.
   The failure would recur in any problem using the concept.
4. **wrong_operation** (wrong operation or operand order): a fault inside a
   single computational move, a wrong operation chosen for one step, an excess
   or wrong operand inside a licensed construction, a false result of a shown
   operation, or an act contradicting the student's own label or own
   registered quantity.
5. **steps** (steps or procedures required): a fault in the set or sequence of
   moves, a required step missing entirely, an unlicensed extra application of
   an already-consumed factor, or a re-derivation of a role the student has
   already produced and labelled.

## The three labels, per family, per unit

- **P (present)**: the unit commits an act exhibiting that family's
  misconception. Commitment means asserted content, not hedged wondering.
- **A (absent)**: the unit positively engages that family's construct
  correctly, correct on the student's own current beliefs, and earns credit.
- **N (not_evidenced)**: neither; acknowledgements, social turns, echoes,
  framed executions, restated givens.

Correctness never decides a label by itself. A wrong answer does not imply P
and a right answer does not imply A.

## Core discipline

- **Judge against the stated problem.** Derive the problem's mathematics
  yourself; never defer to a released answer, which can be wrong.
- **Causal scope (forward-only).** Judge each unit from the problem, the
  incorrect solution, and turns up to and including it. Evidence never flows
  backward.
- **Coherent-wrong reconstruction.** Reconstruct the belief under which the
  student's chain is coherent; downstream arithmetic that is correct on the
  belief earns credit and is not an error. Attribute one family per error at
  its first exhibition; later exhibitions inherit it after a belief-continuity
  check.
- **Demonstration burden.** A conceptual thread requires the wrong belief
  demonstrable in the student's own words or persistently enacted. Never
  invent a compound belief to make an error look coherent; if no belief is
  demonstrable and no route is pointable, the content is residue and takes no
  thread.
- **Arithmetic slips** are not P unless the slip is the family's specific
  error or is motivated (below).

## Threads

Each distinct error is a thread with an id (S1, S2, ...), a family, a one-line
belief, a signature (its characteristic expression), its origin unit, and, if
resolved, the resolving turn. Exhibition events include committed,
re-exhibited, reversion, rationale, parrot-with-contradiction, and
motivated-falsehood. A unit's P cell must name the exhibiting thread(s); an A
cell recording a resolution names the resolved thread.

- **Founding.** A false claim founds a thread when its derivation is
  route-pointable, when it matches an existing signature or anchored output,
  or, for unattributable garbles, when it recurs in the same form (the thread
  then founds at the recurrence). A false result of a SHOWN operation is
  route-pointable at its first occurrence; do not wait for recurrence.
- **Layering.** One unit can exhibit several independent threads, including
  two of the same family, if fixing one leaves the other's error standing.
- **Anchoring.** A committed output that survives while its derivation
  mutates around it is an anchored-output belief; sign flips and method swaps
  that keep landing on the protected output are exhibitions, not corrections.
  A false assertion landing on an existing thread's protected output is that
  thread's motivated act, never a new thread.
- **Motivated falsehood.** Arithmetic false on its face whose function is to
  preserve a committed conclusion is P for the protected thread. The tell is
  direction: genuine slips land anywhere; motivated falsehood lands back on
  the prior answer, often against pieces the student just computed correctly.
- **Restating the anchored answer** at a direct question is re-exhibition (P).
  A rationale defending the error, and a "fix" that restates the same
  chain, are P. Affirming a corrected premise while redrawing the old
  conclusion (parrot-with-contradiction) is P.

## Family boundaries (deciding tests, in order of use)

- **Demonstrated-belief vs intact-label.** If the wrong belief is articulated
  or persistently enacted in the student's own words, it is conceptual
  (comprehension/principles side) even beside a correct label. If the correct
  concept is demonstrated in her own prefix (or her own label fixes the
  quantity's role) and the act contradicts it, the error is procedural
  (wrong_operation), against-own-label.
- **Comprehension vs relevance.** Wrong information chosen is relevance; right
  information misunderstood is comprehension. A silently unused stated given,
  with nothing articulated in its place, is relevance; the same absence with
  the substituting belief stated in her own words is comprehension. Always
  scan the problem for stated givens absent from the chain before inventing
  belief structure.
- **Operand misselection.** A derived quantity standing where a given belongs
  (or the reverse) is comprehension (arm one). A choice between two given,
  same-kind candidates is relevance (arm two).
- **Principles.** Fraction/percentage re-basing and other transportable
  concept failures are principles, not comprehension. A transportable-concept
  failure routes by what the deviant act demonstrates: where it enacts no
  coherent alternative rule beside a correct enactment of the concept in her
  own chain (a raw multiplication next to a correctly scaled part), it is
  wrong_operation, against her own demonstrated rule; where the deviant act
  itself enacts a demonstrable alternative concept (inverted ratio direction,
  re-based percentage, flattened sequential percents), it is principles even
  beside correct work elsewhere. Naming the concept an act offends never
  routes the family by itself.
- **Wrong_operation vs steps (produced-role label test).** If the quantity the
  student produced carries a label whose predicate is the same as the role a
  later act fills, the role is filled and the re-derivation is steps. If her
  label names a different predicate, the construction is licensed and the
  surplus quantity inside it is an excess operand, wrong_operation. Read
  labels as she wrote them.
- An extra application of an already-consumed factor onto a quantity whose
  own label covers it (a total divided by its day-count again, a both-jug
  weight doubled again) is steps.

## Credit rules (the A label)

- A reworded or restructured walkthrough earns A per construct it genuinely
  re-articulates; a near-verbatim recitation earns nothing.
- Three floors are evaluated before the engagement gate, and an act caught by
  a floor is N regardless of displayed reasoning. Framing: an act whose
  content the preceding tutor turn states (operation with operands, or the
  corrected content itself) earns nothing in either direction; a wrong result
  inside a supplied frame is the frame's execution, not the student's
  commitment, and no belief-continuity question arises for it. A pointing or
  posed prompt that merely entails the next move does not trigger this floor
  (entailment is not authorship; self-assembled content at a pointing prompt
  earns and can resolve), a prompt-selected step engages operation at most
  unless the student contributes the step selection, and a false result
  landing on a protected output is the protecting thread's act under any
  frame. Bare execution: performing an arithmetic act (multiplying, dividing,
  halving, summing) engages operation at most; principles A needs a
  concept-level opportunity (base selection, part-whole assignment,
  scale-factor choice) the student sets herself. Silence: not using a
  distractor is not an act; relevance A needs an articulated selection.
- A framed or named execution (operands and operation stated or one-step
  entailed by the prompt) earns nothing; a self-extended step beyond the
  prompt (an unprompted final conversion or sum) earns wrong_operation A.
- Bare rate-times-base is operation-level; principles A needs a concept-level
  opportunity (base selection, complement handling, inclusion-exclusion).
- Acts inside a token's own body (dual-use with the error) earn nothing.
- Isomorph (side-problem) successes can earn credit if the operation was
  unstated in the prompt; isomorph failures never exhibit threads, since
  exhibition scope is the problem's own chain.
- Accurate pre-resolution self-location of the fault earns comprehension A;
  post-resolution or post-naming self-diagnosis earns nothing, unless it adds
  specific structure the tutor never stated.
- A hedged question or self-assessment is not a commitment; label N.

## Resolution (strict authorship)

A thread resolves only at a turn where the student herself performs the
corrected element, act for act with the error token.

- **Pointing permits, supply bars.** A tutor naming the fault, the category of
  a condition, or the goal, without stating the corrected content, leaves
  resolution available. A tutor stating the corrected interpretation,
  operand, equation, or reading bars it; executing on supplied content never
  resolves, and entailment is not authorship. Restating the problem's own
  text is supply when the clause restated is the contested content itself.
  Test: could the student still get the contested reading wrong after the
  tutor's sentence? If not, it was supplied.
- A bare negation ("that isn't right", "not quite") with the corrected
  content produced by the student grants resolution.
- A corrected value produced through a tool at the tutor's directive (a
  calculator) has ambiguous authorship and does not resolve.
- A leading either-or whose correct arm states the fix is supply.
- Resolution is a dated act, not a state change: a later re-exhibition of the
  thread voids the earlier resolution (the act-credit A on that turn stands).
- A dialogue can end on the released correct answer with threads unresolved;
  that is a scaffolded arrival, not self-repair.
