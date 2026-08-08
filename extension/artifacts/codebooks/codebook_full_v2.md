# Misconception Annotation Codebook

Rules for labelling each student turn as **present**, **absent**, or
**not_evidenced** for **each of the five misconception families**. Every turn
receives five labels, one per family, each judged by that family's own construct.

The codebook has three parts, applied in order. The **general rules** govern how
any label is decided. The **cross-family adjudication** section fixes which
family owns an error when more than one could claim it, so that one underlying
error triggers exactly one family. The **family sections** define each family's
construct and its present, absent, and not_evidenced conditions.

The label always tracks the **family's specific misconception**, not whether
the turn is correct overall.

---

## General rules (apply to all)

These rules apply to every family and every turn. They are grouped for
navigation; every rule binds regardless of its group.

### The universal question (the three labels)

- **The universal question (engagement decides the label):** every turn is
  labelled by two steps in order, an engagement gate and then a correctness
  judgment.
  - **Step 1, the engagement gate:** does the turn contain reasoning that bears
    on the family's specific construct, that is, the target reasoning the family
    is about (for the principles family, reasoning that applies or should apply
    the underlying principle; for comprehension, reasoning about what the
    problem is asking; and so on). If the family's target reasoning is not in
    play in the turn, the turn is **not_evidenced**, and you stop here. A bare
    fact, a social remark, or a sub-step the tutor fully dictated does not pass
    the gate. This step is decided before correctness is ever considered, so a
    correct-looking turn that does not engage the construct is still
    not_evidenced, not absent.
  - **Step 2, the correctness judgment (only if the gate is passed):** does that
    reasoning handle the construct without exhibiting the misconception. If the
    reasoning handles the family's target soundly, the turn is **absent**. If
    the reasoning is in play but exhibits the misconception, the turn is
    **present**.
  - **The credit default.** Credit is act-based and per-construct: an absent
    label requires a self-authored act this turn that engages the family's
    own decision and comes out right. Ambient correctness, carried figures,
    and correctness downstream of another family's fault earn nothing, and
    where it is unclear whether a family was engaged at all, the label is
    not_evidenced: the default for an unengaged family is never absent.
  - **Floors evaluated before the gate (order of operations):** the engagement
    gate is assessed only after three floors, and an act caught by a floor is
    **not_evidenced** regardless of how much reasoning it displays.
    - *The framing floor:* an act whose content the immediately preceding
      tutor turn states, the operation named together with its operands, or
      the corrected content itself, earns nothing, whichever label direction
      is at issue: executing a stated move never passes the gate, and a wrong
      result inside a supplied frame is judged as the frame's execution, not
      as the student's own commitment. A pointing or posed prompt that merely
      entails what to do next does not trigger this floor, in harmony with
      the supply-versus-pointing boundary: entailment is not authorship, and
      self-assembled content at a pointing prompt earns and can resolve. For
      the steps family specifically, a prompt that itself selects the step or
      names the target leaves steps unengaged unless the student contributes
      step selection beyond the prompt, assembling which components enter, so
      executing a prompt-selected step with self-carried operands engages
      operation at most. And the floor never shields a motivated falsehood: a
      false result inside any frame that lands on a protected output is the
      protecting thread's act, the motivated-falsehood machinery outranking
      the frame.
    - *The bare-execution floor (principles):* bare execution of an arithmetic
      act, multiplying, dividing, halving, summing, engages the operation
      construct at most. Principles engagement requires a concept-level
      opportunity, a base selection, a part-whole assignment, a scale-factor
      choice, that the student sets herself beyond what the prompt supplies;
      correctly performing division does not engage the equal-sharing concept
      where the only conceptual choice in play, such as who belongs in the
      group, is elsewhere or is itself the error. The earn side, for
      calibration: a scale factor the student derives herself and applies
      correctly in her own chain is a self-set concept-level choice and earns
      principles credit despite being arithmetic in form, and a unit rate she
      derives herself at a posed question is likewise self-set, posed prompts
      leaving the concept choice hers.
    - *The silence floor (relevance):* silently not using a distractor or an
      irrelevant given is not an act and earns nothing; relevance engagement
      requires an articulated selection, naming which information matters or
      explicitly setting a piece aside. Silence is never a positive act, in
      symmetry with the silent-omission rule on the present side.
  Put as a one-liner, absent means the student engaged the family's target
  reasoning and handled it correctly, present means they engaged it but
  exhibited the misconception, and not_evidenced means the turn did not engage
  that reasoning at all. This is the top-level decision, and every rule below is
  a way of answering it for a particular situation. The gate is judged against
  both the main problem and the latest tutor turn, so if the preceding tutor
  turn supplied the construct-relevant content, the student reproducing it does
  not pass the engagement gate on its own (see the tutor-supplied rule).

### Reconstructing the student's error

- **Reconstruct the student's mistake before labelling ambiguous turns
  (annotator guidance, for human and LLM annotators alike):** some turns can
  only be labelled correctly once you have worked out what the student's
  underlying mistake actually is across the dialogue up to and including the
  turn being labelled (its prefix), because the same surface
  turn means different things under different error models. For example, a
  student who reports a wrong count may be making a shallow arithmetic slip, or
  may hold a coherent but wrong interpretation of what a quantity represents,
  and the label differs between the two. Before labelling an ambiguous turn, form
  an account of the student's error from the dialogue as a whole (the incorrect
  solution, the turns, and the tutor's corrections), then read each turn against
  that account. *Illustration (ice-cream free-cones dialogue):* the student
  keeps landing on 8 free cones. The reconstruction is that she believes the 50
  cones already include the free ones, so she treats each group of six as five
  paid plus one free within the 50, which is why dividing by six seems right to
  her. Only with that model in view does it become clear that turn 6 (accepting
  "one free per five" while still reporting 8) is present, since she is holding a
  coherent wrong interpretation rather than merely parroting.
  **Two guards on this practice.**
  - **Judge each turn on its own content.** The reconstruction is *evidence that
    informs* the per-turn judgment; it does not override what a turn actually
    shows, and it does not license copying one inferred model onto every turn
    regardless of content. A turn that does not engage the construct is still
    not_evidenced even if the student's error model is clear from elsewhere.
  - **A wrong reconstruction propagates.** Inferring the student's mistake wrong
    would mislabel every turn read against it, which is more systematically
    damaging than an occasional per-turn slip. Treat the reconstruction as a
    hypothesis to be checked against each turn, not as a fixed premise, and
    revise it if a turn contradicts it.
  - **Incoherent turns (the three-limb boundary).** Where a turn's content is
    semantically broken rather than wrong, apply three tests in order. First,
    the route test: a committed false claim whose derivation is recoverable
    from the prefix, even as a wrong one (a total whose value equals the sum
    with one component dropped), has a reconstructable belief and founds or
    exhibits a thread as usual; recoverability means a pointable derivation,
    not a story that merely could be told. Second, where no route is
    recoverable, run the step-2 matchers of the ledger, per the residual
    discriminator of step 4: a result landing on a protected output within a
    continuing defence, or a construction instantiating a live thread's
    structural signature, is an exhibition of that thread
    (motivated-falsehood or splice), not incoherence. Third, where neither
    test fires, the turn is incoherent residue, not_evidenced for the
    constructs it does not coherently engage, recorded in the note and
    founding nothing: incoherence is not evidence of any family's
    misconception, and a label should not be assigned by vibe. Recurrence
    upgrades residue causally: an unattributable garble that recurs in the
    same form establishes a route-shaped belief by the repetition itself,
    and the thread is founded at the recurrence, whose prefix contains the
    first occurrence; the earlier occurrence stays residue, never
    relabelled, per causal scope.
  - **A false result of a shown operation is pointable at first occurrence.**
    The recurrence upgrade above exists for garbles whose derivation cannot be
    recovered. It is not needed, and must not be waited for, where the
    operation producing the false result is written on the page: there the
    derivation is route-pointable immediately, the first limb fires, and the
    thread founds at the first occurrence. *Illustration:* where a student
    writes the subtraction 84 - 27 and asserts 67, the thread founds at that
    first assertion, because the subtraction is shown; the annotator does not
    wait for any re-checked repetition. Deciding question: is the operation visible? If
    yes, found now; if the number arrives with no visible route, hold it as
    residue and let recurrence decide.
  - **Stated-versus-enacted conflicts within a turn (self-originated).** Where a
    turn's own stated operation or narration conflicts with its enacted result,
    and no tutor echo is involved, the reconstructed belief governs, judged from
    what the student's results enact across the dialogue up to and including the
    turn being judged. A student who writes
    one multiplication and reports a product corresponding to another, or lists
    a sum whose terms do not produce the total she asserts, or asserts two
    claims that cannot both hold in one sentence, is judged on the belief her
    results enact, not on the written surface. Where no coherent belief is
    reconstructable, judge the committed final claim of the turn. The priority
    order is belief first, committed claim second, written surface last. Where
    the conflicting stated content is reproduced from the tutor, this clause
    does not apply, and the parroting-versus-comprehending test governs instead
    (its third outcome, reproduced content with reasoning still exhibiting the
    misconception, is present).

**Narration versus data assertion.** A false statement about one's *own
computation*, the operation named, the operand recited, is forgiven when the
enacted result shows the belief intact: the student who says she multiplied
0.2 by 0.7 while her result enacts 0.2 x 0.3 is judged on the enacted belief
(the probability dialogue, 929). A false claim about the *problem's given
data* is a committed claim judged on its content, and it is comprehension
present even when the arithmetic built on it is internally correct: the
student who reaches the right difference by asserting that sixty biscuits
were baked in the morning has replaced the given facts with invented ones
(the biscuits dialogue, 1143, turn 5). The line is what the falsehood is
about, the student's own process versus the problem's facts.

**Restating is not resolving.** Accurately restating the problem, the plan,
or one's prior work while omitting the disputed element does not engage the
disputed construct and earns nothing for it: the turn that recites the ribbon
plan without the leftover deduction is not_evidenced for steps (1745, turn
3). Resolution requires the turn's own content to perform the corrected
element, per the resolution step of the ledger.

### Label stability and belief tracking (causal scope)

**Scope of evidence is causal.** A unit is annotated from the problem, the
incorrect solution, and the dialogue up to and including that unit (its prefix).
The incorrect solution is annotated from the problem and the solution alone.
Later turns never inform earlier labels: the annotation describes the evidence
state at the time, like any online estimate, and may be wrong in hindsight by
design. This is deliberate, since the deployed grader runs live, turn by turn,
and a gold standard built with hindsight could not be matched by any online
system.

**Presence is per-turn; family attribution is tracked over the prefix.**
Judging each turn on its own content decides whether the turn exhibits an error
(engagement, presence). Which family a persisting error carries is decided by
tracking the belief behind it:

- **Origin attribution:** at an error's first exhibition, reconstruct the
  belief behind it from the prefix available there and fix the family by the
  usual machinery, defaults included. If that prefix cannot positively
  establish an intact belief, the procedural labels are unavailable at the
  origin, per burden of establishment.
- **Belief-continuity check at every later exhibition:** run the framing test
  first: if the act this turn performs has its content stated by the
  immediately preceding tutor turn, the operation with its operands, or the
  corrected content itself, the unit is not_evidenced for that family
  regardless of whether the result is true, and no continuity question
  arises, since a framed execution is the frame's act, not the student's. A
  pointing or posed prompt leaves the act self-authored and the continuity
  question live, and a false result landing on a protected output is the
  protecting thread's act under any frame. Only for a
  self-authored act: when a turn exhibits
  an error already attributed earlier (identity test: the same wrong quantity,
  operand, or omission in the same role), reconstruct the belief this turn's
  act enacts and compare it with the origin belief. If it is the same wrong
  belief, the exhibition **inherits** the origin family and is recorded as
  inherited. An act reproduced in the same form is presumed to enact the same
  belief (parsimony): prefer the single belief that accounts for every
  exhibition so far over readings that fragment them into repeated independent
  slips.
- **Root-cause re-investigation:** if the enacted belief has genuinely changed,
  because the act itself changes form, the student volunteers a rationale that
  re-identifies the error, or the prefix shows the origin belief corrected and
  the error re-emerging under a different driver, investigate the root cause
  afresh from this turn's prefix and attribute the family anew from this turn
  forward. Earlier labels stand; re-attribution never flows backward. (This is
  the forward-scoped version of "revise the reconstruction if a turn
  contradicts it" in the general reconstruction rule.)
- **Echo discount:** assent to, or repetition of, content the tutor has just
  supplied is not evidence of the student's own belief. This mirrors the
  statement-supplies principle: just as an echoed figure earns no correctness
  credit, an echoed fact does not establish an intact belief for the purpose of
  re-familying a persisting error. Enacted computation and spontaneous
  self-generated statements are strong belief evidence.
- **Persistence phenomena inherit:** post-correction reversions, splices that
  graft supplied figures onto retained wrong structure, motivated falsehoods,
  and parrot-with-contradiction turns protect the origin error and inherit its
  family, as the parroting and motivated-arithmetic rules already provide.

A genuinely different error, a different wrong quantity, operand, omission, or
belief such that the account of the prefix requires two errors rather than one,
is attributed independently from its own prefix.

**Recording:** thread-level facts (belief, signature, origin, history) are
recorded once in the thread table of the source-ledger schema (see
"Annotation procedure: the source ledger"); turn cells carry only status and
source attribution.

**No label propagation; no anchoring.** Labels attach to acts, and only the
family attribution of a persisting error flows forward. Presence is never
inherited by a turn that does not re-exhibit the error, and it is never
blocked by earlier labels: a construct marked absent in one turn is marked
present in a later turn the moment that turn commits the error (the
defence-expiry cases are the standard instance). Symmetrically, a family
already present from one belief does not monopolise itself: a new error in
the same family that fails the identity test against the existing thread is a
fresh origin, attributed independently from its own prefix and recorded with
its own enacted belief (a dialogue can carry two comprehension threads with
distinct beliefs). Absent labels never propagate at all, since a passed trial
is a dated event, not a state; the persistence of demonstrated skill between
acts is the tracer's job, carried by its latent state through the
not_evidenced no-update turns, and copying absents forward would count one
event many times.

*Worked poles.* *Fish dialogue (163):* the solution labels the derived 28 as
the three-person total at its creation, comprehension at origin; the next turn
states the correct two-person label yet writes the identical three-person
equation, and the identical act enacts the identical belief, so the turn
inherits comprehension, the in-turn correct label notwithstanding. *Candle-box
dialogue (547):* the operand-pairing error is operation at origin; the student
then defends the anchored product for seven turns, latterly writing the correct
expression beside it, and every reassertion inherits operation, since a
corrected surface does not change what the defended error is. *Beads dialogue
(308):* the solution uses the stated total 40 as an addend while its own final
step uses 40 correctly as the total constraint, so the belief is intact within
the origin prefix and the error is operation there; the student's next turn
volunteers "I added 40 because that is the total", a spontaneous rationale
re-identifying the error as part-whole concept confusion, so root-cause
re-investigation fires and the error is principles from that turn forward. The
solution's label stands.

*Reading demonstrability off the student's own labels.* Whether a concept
failure is demonstrable at origin is decided by testing the candidate wrong
belief against the labels the student herself wrote. Labels consistent with
the candidate belief demonstrate it and route the thread conceptual: in the
race dialogue (1075) the 60 is labelled the start-phase count, the 80 the
after-halfway count, and their sum offered as the race total, every label
agreeing with the phase-sum composition concept, which later transports to
the tutor's invented scenario, so principles is earned. A move against the
student's own label refutes the candidate belief and routes procedural under
burden of establishment: in the wall dialogue (1036) the solution names the
2000 as the five-course total of the wall and then adds the 1200 subtotal to
it anyway, so the part-whole belief the surface shape suggests is
contradicted by her own adjacent assertion, no wrong belief is demonstrable,
and the error files as operation, vanishing at the first clean rebuild as
execution faults do. The routing stays evidence-driven in both directions:
a later rationale articulating the concept re-attributes the thread forward
(the beads pattern above), and transport to structurally new material is
behavioural evidence of a concept where the origin text was silent.

### Labelling the other families on an erroneous unit

When a unit's error has been attributed to one family, the remaining families
are still judged by their own engagement gates and constructs, relative to the
student's belief (per the execution-relative-to-belief standard and the harvest
worked pole). Downstream work that genuinely engages a construct and handles it
soundly on her belief is **absent** for that construct: operating inside a
wrong frame still presents real opportunities for operational, procedural, and
conceptual errors, and passing them is evidence the tracer should receive. Two
guards apply:

- **Dual-use exclusion:** the token that constitutes the attributed error
  cannot double as engagement evidence for another family. One behaviour
  cannot serve as both the error and another family's credit. The exclusion
  cuts only that way: a single act may earn absent in every family whose
  construct it genuinely engages and handles soundly, as the walkthrough of
  the credit-card dialogue 280 earns principles, operation, and steps in one
  utterance. The move that expresses a comprehension misread (subtracting a
  time from a distance) is not also an operation-selection trial passed; that
  column is not_evidenced unless the unit contains operational work distinct
  from the error.
- **Carried figures stay not_evidenced:** restating earlier outputs without
  fresh reasoning passes no gate, as elsewhere.

### The error token: definition and localisation

The **error token** is the specific act in the student's chain that first
departs from truth, by committing a false value, a false label on a true
value, or a false claim. It is a single, pointable act, and it is what the
thread's identity signature names, what dual-use excludes from credit, and
what later turns must re-commit in order to re-exhibit the thread. The token
dates the thread's origin; it does not bound its recurrence. Each later
re-commitment of the same wrong content is a fresh act, recorded as an
exhibition event of the same thread and judged as an act in its own turn
(including for dual-use there), so the error reappears through new acts while
the origin token stays fixed as the point where the thread began.

**The baseline the token is measured against.** "Departs from truth" is
relative to the prevailing judged baseline, not always the stated problem
directly. By default the baseline is the stated problem's mathematics. Once a
thread's belief governs downstream work, the correct-on-belief rule makes the
belief-conditional chain the baseline for that stretch, and where the
accepted-premise machinery applies, the accepted premise plays the same role.
A second error committed inside an already-wrong chain is therefore localised
at its own first departure from its baseline and founds its own thread, which
is what lets a procedural token sit on top of a conceptual thread (1827's
false 3 x 3 = 27 beside the deduction-threshold belief; 1538's inverted
back-projection at turn 1 beside the timeframe thread) without the earlier
thread's falsity swallowing the later token's location.

Two consequences fix how the token is located:

- **Everything before the token is not the error.** Acts earlier in the chain
  whose outputs are true under the problem commit nothing wrong. They cannot
  exhibit the thread, they cannot carry a present label, and where they
  genuinely engage a construct they remain creditable distinct work. Being
  causally necessary for a later error does not make a true act part of it.
- **Repeated application localises to the excess act.** When any operation is
  applied more times than the situation licenses, scaling by a factor,
  deducting a quantity, including a component in an aggregate, converting a
  unit, or otherwise, the earlier applications are typically each valid in
  isolation and leave the chain's content true, so the token is the excess
  application, the one whose output is the first false content. It is never
  the earlier valid application, even though removing either application would
  repair the chain: the question is not which acts the error depends on, but
  where false content first exists. Re-exhibition accordingly requires the
  excess application or its duplicated outcome to be re-committed; a later
  turn that restates or defends only a valid earlier application alone
  exhibits nothing. Applying an operation fewer times than licensed is the
  separate omission shape, handled under the steps family's machinery.

*Worked pointer (jug dialogue, 2152).* Doubling for the two jugs is licensed
exactly once, and either placement would be valid: double the volume then
weigh (1.4 x 2 = 2.8, then 2.8 x 5 = 14), or weigh one jug then double (7 x 2
= 14). The student does both. Her initial 1.4 x 2 = 2.8 produces the true
both-jug volume, is not the token, and earns as distinct work; her closing 14
x 2 = 28 produces the chain's first false quantity and is the token. A later
turn defending the initial doubling alone (turn 2) exhibits nothing; a turn
defending the closing doubling (turn 1) re-exhibits the thread.

### Walkthrough and narration turns (the re-articulation standard)

Most dialogues open with the tutor asking the student to walk through the
solution. Such turns are judged, like any turn, on what their own content
demonstrably engages, and the deciding question is whether the turn
re-articulates the reasoning or merely lists its outputs. The standard is
position-independent: it governs any turn in which the student re-derives her
own work, opening walkthroughs, mid-dialogue re-runs under challenge, reworks
at re-check prompts, and re-derivations embedded in rationales alike, since
the opportunity to fail that grounds the credit does not depend on where in
the dialogue the re-derivation occurs. This includes re-derivations inside
reversions and defences, where the three poles alone decide the credit
columns (a reversion that replays verbatim earns nothing as recitation; one
that freshly re-derives with operands and order earns for what it engages, as
at the sporting-goods dialogue 37, turn 3), while the error side and the
motivated-falsehood machinery govern as usual, so a re-derivation whose
arithmetic is bent to protect an anchored output remains a falsehood, not a
trial passed.

- **Reasoned re-articulation earns absent.** Accurately re-deriving one's own
  work, with the operands, the relations, and the order intact, is a genuine
  trial of the constructs it engages: it can fail, and in this corpus it does
  (narrations that garble the student's own chain, stated operations that
  contradict the enacted result, broken equations produced while describing
  correct work). A walkthrough that re-articulates the reasoning therefore
  earns absent for each construct it engages correctly on the student's
  belief, exactly as the original performance did. Solving and accurately
  re-explaining are two acts and two trials; their correlation is no different
  from that of any adjacent-turn labels.
- **Bare figure-listing is a carried account.** A walkthrough that only lists
  outcomes ("I figured out X, then I got Y") re-articulates no reasoning,
  contains no opportunity to fail at any construct, and is not_evidenced for
  the non-error columns, per the carried-figures rule.
- **Verbatim replay is recitation, not re-articulation.** Reproducing one's
  own prior text verbatim or near-verbatim, with only trivial connective
  changes, contains no opportunity to fail at any construct and is therefore
  not a trial, exactly as bare figure-listing is not, whatever operands and
  order the copied text happens to contain. Credit requires a fresh
  formulation, reworded into new sentences, reordered, or shaped to answer
  the specific question asked, which restores the opportunity to fail. The
  operational test: where each content sentence maps one-to-one onto a prior
  sentence with only person, tense, or connective changes, the turn is
  recitation and earns nothing, whatever its length; rewording means fresh
  sentence structure or a reshaped derivation, not pronoun conversion (the
  games dialogue, 2233, turn 1 earns as a reworded first-person
  re-derivation; the bunny dialogue, 1064, turn 2 repeats the previous turn
  nearly unchanged and earns nothing). The two endorsement effects are
  unaffected, since they are acts rather than trials: a verbatim replay of a
  wrong chain still re-exhibits the thread, and a verbatim replay of a
  defended solution still re-enacts the defence in the comprehension column.
  Dual-use applies on top as usual, so a replay whose only computation is the
  error token's own derivation earns nothing on that ground independently
  (the trails dialogue, 2063, turn 1).
- **The error side is unchanged.** Re-committing the wrong chain in a
  walkthrough is a live act of endorsement: the error inherits present as the
  stability section provides, whichever way the non-error columns fall.
- **Defended readings.** For a solution whose reading is a live ambiguity
  defence, the walkthrough re-enacts the defence, so the comprehension column
  is absent; this is the same principle, the turn's content re-exhibits the
  (defensible) reading.
- **Dual-use still applies.** A named computation that is the error's own
  token earns nothing by being narrated.

*Worked pair.* Credit-card dialogue (280), turn 1: "I calculated that the
interest charged would be 20% of $150.00 = $30.00. Then, I added the interest
to the balance... Finally, I subtracted the payment..." re-articulates the
percentage application, the operand choices, and the sequence, so principles,
operation, and steps are absent, while the recommitted timing chain keeps
comprehension present. Turtle-race dialogue (96), turn 1: "I figured out that
the hare would run the race in 2 seconds, and then I figured out that the
turtle would need 18 seconds... so I divided 18 by 2" lists outcomes, and the
one operation it names is the error's own token (dual-use), so the non-error
columns stay not_evidenced.

### One error, one family (exclusivity and layering)

- **A turn can genuinely exhibit more than one misconception, and they can
  layer.** This rule concerns turns that *genuinely* exhibit several
  misconceptions at once, which is different from a turn that merely *looks like*
  it could belong to one family or another. For the latter, telling two
  confusable families apart, use the cross-family adjudication rules below; a
  turn that is really one misconception dressed to look like another is resolved
  there, not here.

  **The governing principle is that the families are mutually exclusive at the
  level of a single underlying error.** One underlying error triggers exactly
  one family, attributed at the *root* of its causal chain; the downstream
  shadows it casts (a wrong strategy that follows from a misreading, a wrong
  step that follows from a wrong strategy) trigger nothing. Multiple present
  labels on one turn are legitimate only when the turn carries multiple
  *independent* errors, never because one error is describable in two families'
  vocabularies. Crossover (one error, two labels) is a boundary failure the
  adjudication rules exist to eliminate; layering (two errors, two labels) is
  real and expected.

  **The independence test.** Two candidate errors are independent, and may each
  trigger a family, only if fixing one would leave the other standing. If
  correcting error A would dissolve error B, then B is A's shadow and only A's
  family is labelled. If B survives the correction of A, they are separate
  errors and both families are legitimately present. Apply this counterfactually
  from the reconstructed belief, and when annotating more than one family as
  present on a turn, note briefly which error triggers each label, so that
  co-occurrence can later be audited as layering rather than crossover.

  This rule applies once genuine co-occurrence is established: a
  single turn may exhibit more than one misconception, sometimes from different
  families, and these can build on top of one another. The label for each
  family is decided only by whether that family's specific misconception
  is exhibited, judged by that family's own construct, independent of whether
  other misconceptions are present. This has two directions, and both matter.
  - **Another misconception does not create a present.** If the student exhibits
    an error from a different family but not the judged family's specific
    misconception, the judged family's label is not present just because something went
    wrong. Do not let a salient error from another family bleed into the label.
  - **Another misconception does not hide the judged one.** If the student
    exhibits both another misconception and the judged family's, the judged one is
    still present, and a more salient error from another family must not draw
    attention away from it.
  **Evaluating a layered misconception (relative to the student's own
  understanding).** When one misconception sits on top of another, evaluate the
  upper-layer judged misconception relative to the student's own understanding
  of the lower layer, not relative to the objectively correct values. If the
  student correctly executes the judged family's construct given her own
  (possibly wrong) understanding, the judged misconception is absent even
  though the lower-layer misconception is present. This is the same principle as
  the equation-correct-under-own-logic test in the wrong-operation family,
  applied to layered errors. *Worked example (harvest dialogue, judging the wrong-operation
  family):* the lower layer is a comprehension error, the student compounds
  forward and believes her two harvest figures are 24 and 28.8. The question asks
  for the total, so on her own understanding she should sum 24 and 28.8, and she
  fails to, reporting only 28.8. Because she does not sum even her own two
  figures, the wrong-operation misconception is present, layered on top of the
  comprehension error. Had she summed 24 + 28.8 = 52.8, she would have correctly
  applied the summing operation to the figures she believed were her harvests, so
  the wrong-operation misconception would be absent while the comprehension error
  remained.
  **When the judged misconception is on the lower layer.** If the judged
  misconception sits at the base of the reasoning and a different family's error
  sits on top, the judged misconception is judged directly on its own content,
  because there is nothing beneath it to evaluate it against. The
  relative-to-own-understanding step applies only to an upper-layer judged
  misconception, so for a lower-layer one the rule collapses to reading the
  misconception directly. This produces an asymmetry worth holding in view.
  - **Judged family on the upper layer:** correcting the upper layer makes the
    judged misconception absent, as in the harvest example where summing her
    own figures would have removed the wrong-operation error.
  - **Judged family on the lower layer:** correcting an upper-layer error in a
    different family does not make the lower-layer judged misconception absent,
    because fixing something built on top of the foundation does not repair the
    foundation.
  *Constructed example (judging the comprehension family):* the problem asks for the change
  from a $20 bill after buying 5 apples at $2 each. Lower layer, the student
  misreads the question as asking for the total cost of the apples rather than
  the change, which is the judged comprehension misconception. Upper layer, she
  then computes 5 + 2 = 7, a wrong-operation error. The comprehension turn is
  present because she misread what the problem asks, and even if she had
  correctly computed the total cost as 5 x 2 = 10, the comprehension
  misconception would still be present, because she is still answering the wrong
  question. Correcting the upper-layer operation does not rescue the lower-layer
  judged misconception. **Scoping guard:** the judged misconception must be
  independently present in the turn by its own family's test. The existence of
  another misconception is neither evidence for nor against the judged one, and
  this rule does not license reframing another family's error as the judged one
  to manufacture a present. The family boundary notes still decide which family
  an error belongs to.

### What engages a construct

- **Either the tutor's prompt or the student's response can trigger the
  construct:** the engagement gate is passed if either side brings the family's
  target reasoning into play. The tutor's prompt can invite the relevant
  reasoning, for example by asking for the quantity the construct produces, and
  the student's response can volunteer the relevant reasoning even when the
  tutor's turn did not invite it, for example by committing to an answer about
  what the problem asks when the tutor only said to refocus. If either holds, the
  turn engages the construct and is judged present or absent on its content.
  **Guard on the student-side trigger:** a student-side trigger requires a
  committed assertion about what the problem asks or the quantity the construct
  produces, not an incidental echo. A purely mechanical repetition with no fresh
  commitment does not self-trigger the construct and remains not_evidenced, which
  is the same line the bare figure rule below draws. *Worked example
  (comprehension, cake dialogue, turn 6):* the tutor only says to forget the
  original answer and refocus, which does not invite the construct, but the
  student volunteers "the cake must have had 48 pieces" as her committed answer
  to the problem. The 48 is the wrong output of her misinterpretation, and she
  commits to it as her answer, so she self-triggers the construct and the turn is
  present.

- **Bare figure versus re-asserted result (when a number is not "bare"):** a
  number stated by the student is not always a bare answer. Distinguish two
  cases, judged on the turn's own content.
  - **Bare figure, not_evidenced:** the student states a number with no
    engagement, such as reading a given value off the problem, or repeating a
    figure while the construct is not in question.
  - **Re-asserted result, present or absent:** the student states a number in
    direct answer to a question about the quantity the construct is supposed to
    produce, so the number is the student's committed output of the family's
    principle or procedure. If that committed output is wrong (it embodies the
    misconception), the turn is present; if right, absent.
  The test for which case applies is whether the construct is in play, from
  either side per the rule above. If the tutor asks for the quantity the
  construct produces and the student commits to a value, that value is a
  re-asserted result. A value the student volunteers as her committed answer to
  the problem is also a re-asserted result, even when the tutor did not ask for
  it, provided it is a committed assertion and not an incidental echo. *Worked
  example (principles, ice-cream free-cones dialogue, turn 3):* asked "how many
  free ones were there", the student answers "8". The 8 is the wrong output of
  the grouping principle (it comes from dividing the total by six rather than
  counting one free per five paid), and the student commits to it in direct
  answer to a question about that quantity, so the turn is present. **Guard
  against inheriting a label:** this rule stays within the turn. It does not
  license reaching back to an earlier turn and copying its label onto a later
  bare number. The present judgment here rests on the student committing to a
  wrong output *in this turn* when asked for it, not on the fact that the
  misconception appeared earlier. A number repeated while the construct is not in
  question remains not_evidenced. This keeps the rule consistent with the
  forward-only rule below.

- **Answering a tutor analogy engages the construct only if the analogy could
  elicit the misconception:** tutors often pose an analogy that is not about the
  problem itself, such as a simple worked example meant to prompt insight. To
  label a turn that answers such an analogy, ask whether the analogy is capable
  of eliciting the student's specific misconception.
  - **If the analogy could elicit the misconception:** the turn engages the
    construct, so a correct answer is absent and a mistaken answer is present,
    judged the same as any other turn.
  - **If the analogy is too simple or too far from the misconception to elicit
    it:** answering it does not engage the construct and is not_evidenced, even
    when the answer is correct.
  The test is the same engagement gate applied to the analogy, does answering it
  bear on the family's specific construct. *Worked example (principles, Todd
  snow-cone dialogue, turns 2 and 4):* the misconception is about ordering and
  double-counting cash flows. The tutor asks whether $10 can buy a $50 toy
  (turn 2) and what $200 minus $50 is (turn 4). Neither analogy tests ordering or
  double-counting, they test whether you can overspend and basic subtraction, so
  answering them could not have elicited the misconception, and both turns are
  not_evidenced despite being correct. Had the tutor posed an analogy mirroring
  the double-counting structure and the student double-counted in it, that would
  be present.

- **One act, several floors (credit-side engagement).** For any single act,
  credit is decided per family by that family's own engagement floor, run
  independently: comprehension's resolving-versus-restating line, the
  principles family's operation-selection and component-figure rules, the
  operation family's selecting-versus-executing and assembling-versus-describing
  lines, and the steps family's advancing-a-step requirement. One decision may
  pass several floors at once and earns absent in each, as the walkthrough of
  the credit-card dialogue 280 earns principles, operation, and steps in one
  utterance; the dual-use exclusion cuts only the error-and-credit pairing,
  per its own clause. The common test behind every floor is the
  re-articulation standard's: the act must contain an opportunity to fail
  that construct specifically, so a floor is passed only where the act's
  content could have gone wrong at that construct and did not. Where an act
  passes no floor beyond the one it plainly engages, credit stays in that
  single column; breadth is earned at the floors, never by generosity.

- **Social turns:** pure acknowledgement or thanks with no task reasoning is
  **not_evidenced**.
- **Claimed verification is not evidence:** a student's claim to have checked,
  re-read, or verified (including claims of calculator checks) is not evidence
  for any family, whether or not the claim is credible. Judge the turn on its
  mathematical content alone; a claimed check that accompanies a wrong
  assertion does not soften the assertion, and a claimed consistency that does
  not hold is judged on the actual content, not the claim. Whether such a turn
  is present or not_evidenced is decided by the ordinary commitment standard
  applied to the assertion the claim accompanies, with the verification
  component ignored entirely. A confident reassertion of the wrong content
  under challenge is a committed claim and re-exhibits the thread ("Yes, I am
  confident that this is the correct answer. I have double checked my work",
  the fruit dialogue 1462; the calculator-backed reassertions of the boxes
  dialogue 547). A hedged self-assessment withholds commitment and is meta,
  hence not_evidenced ("I think my answer is correct but I'm not sure", the
  eggs dialogue 1744). The hedge shields only the bare self-assessment: a
  hedged turn that goes on to enact or defend the error substantively is
  present on that enacted content as usual.

- **Correct sub-steps that do not engage the construct are not_evidenced:**
  a turn that correctly executes an arithmetic or procedural sub-step the tutor
  has dictated, but that does not engage the family's specific construct, is
  **not_evidenced**, not absent. Absent is reserved for turns that genuinely
  engage the misconception's target reasoning and handle it correctly, not for
  any turn that happens to contain correct arithmetic. For example, computing
  $10 \times 0.5 = 5$ when the tutor asks for that product engages none of
  the families' constructs in itself, so it is not_evidenced even
  though it is correct. This narrows absent to a meaningful label and keeps
  correct-but-incidental computation from inflating the absent rate.

- **Judge each turn on its own content (no hindsight):** label a student turn
  using only that turn's reasoning and the dialogue *up to and including* it. Do
  **not** use the tutor's reaction in the *following* turn (including
  acknowledgments like "you identified the correct steps" or corrections), or
  any later turns, to inform the label.
  - A turn with no mistake in its own content is not present just because a
    later tutor turn reveals a problem.
  - A turn is not made absent by a later tutor acknowledgment of an earlier
    turn.
  - The *preceding* tutor turn is part of the context and is used (e.g. for the
    tutor-supplied-answer rule, which concerns an answer given *before* the
    student turn). The distinction is: preceding context counts, the following
    reaction does not.

### Tutor-supplied content

- **Tutor supplied the construct-relevant content (all families):** when the
  preceding tutor turn has supplied the content the construct is about (the
  answer, the principle, a statement of what the problem is asking, or the
  operation and operands), do not credit the student merely for reproducing it.
  Judge the student's turn by *what it adds beyond the echo*:
  - If the student only echoes the supplied content or acknowledges it, with no
    reasoning of their own, it is **not_evidenced** (the correctness is the
    tutor's, not the student's).
  - If the student adds reasoning that demonstrates they now understand,
    including restating the corrected idea in their own terms or correctly
    characterising what was wrong before, it is **absent**.
  - If the student reproduces the supplied content but their reasoning still
    exhibits the misconception (a contradictory wrong value or explanation
    remains), it is **present**. This third outcome is the
    **parrot-with-contradiction rule**, referenced by that name elsewhere in
    this codebook.
  This is the parroting-versus-comprehending test, and it applies whatever the
  tutor supplied.
  - **Fluency is not comprehension (referent and application, not wording):**
    do not treat fluent reasoning or phrases like "I understand now" as evidence
    of comprehension by themselves. Check whether the restatement actually
    resolves the *specific* error under correction, in particular whether the
    student attaches the corrected value to the **correct referent** and applies
    it to the **correct quantity**. If the student reproduces the supplied value
    but keeps the wrong referent, the wrong role, or re-introduces the original
    conflation, the misconception is still operative and the turn is
    **present**, even though it sounds like understanding. Tie this to the
    family's construct: an unrelated slip does not make the turn present, only a
    restatement that re-exhibits the family's specific error does. *Worked
    example (principles, dialogue 188):* after the tutor corrects the student,
    the student repeatedly says "I understand now, each video was 120 seconds".
    The value 120 is correct as the combined length of the two equal videos, but
    the student attaches it to the wrong referent (each single video, rather than
    the two together), so the halving principle is still not applied and the turn
    is present, not absent, despite the fluent "I understand now". Only when the
    student finally states that each video is 60 seconds (two videos summing to
    120) is the principle resolved and the turn absent. *Second worked example
    (comprehension, dialogue with the barking dogs):* the student first gives the
    correct answer (terrier barked 12, poodle barked 24), then in a later turn
    says "Yes, I see where I went wrong... the terrier actually barked 6 times,
    so the poodle barked 2 x 6 = 12", regressing to a wrong answer. The turn is
    fluent and retrospectively framed ("I see where I went wrong"), all the
    surface cues of comprehension, but the referent is wrong: the student
    attaches "6" to the terrier's total barks when 6 is the hush count and the
    terrier actually barked twice that. By the referent test this is present, not
    absent, even though it sounds like a correction and even though a (mistaken)
    tutor accepted it. Do not be moved by the confident framing or the tutor's
    approval; check the referent.
  - **Executing a fully dictated correction:** when the tutor has named both the
    error and the fix, a turn that only applies the named fix and reports the
    result, without adding reasoning that demonstrates grasp, is not_evidenced
    rather than absent. A clean, corrected answer is not by itself evidence of
    understanding when the correction was handed over in full. Absent still
    requires the student to add something, restating the corrected idea in their
    own terms, explaining why the fix is right, or applying it beyond the literal
    instruction. Added reasoning means content the student supplies that the
    tutor did not state, so to decide whether the student added something, compare
    the content of the student's turn against the content of the tutor's turn. If
    the student articulates reasoning the tutor did not spell out, such as why the
    corrected quantity is the right one, that is added reasoning and the turn is
    absent. If the student only restates the tutor's stated conclusion, that is
    not added reasoning and the turn is not_evidenced. *Worked example
    (comprehension, Alejandra kombucha dialogue, turn 2):* the tutor says 6 is the
    answer and the last step is unnecessary, and the student replies that Henry
    can buy 6 bottles with the refund money. The tutor stated the figure but did
    not spell out that the 6 is specifically what the refund funds, so the
    student's refund-funded reasoning is content she supplied beyond the tutor's
    statement, which is added reasoning, so the turn is absent. *Worked example (principles, Alejandra overtime dialogue):* the
    tutor says the overtime is 4 hours in total and not times 5 days, naming both
    the error and the fix, and the student removes the times-5 and reports $770
    with no explanation of why the overtime is a total. The clean corrected
    answer is not evidence of grasp here, since the student only executed the
    named fix, so the turn is not_evidenced, not absent.
    - **The clause applies only when the student actually applies the fix.** If
      the student verbally accepts the correction but her working still
      reproduces the misconception, the turn is present under the
      parrot-with-contradiction rule, not not_evidenced. Verbal acceptance is not
      application, so check the working, not the acknowledgement. The test is
      whether the working adopts the fix or re-exhibits the error, and only a
      turn that adopts the fix qualifies for not_evidenced. *Worked example
      (steps, Pirate Rick dialogue, turn 6):* the tutor spells out the full
      correct procedure, that 8 minus 4 plus 2 gives 6 feet and that 6 divided by
      2 gives 3 hours. The student says "that's correct", then reproduces her own
      wrong procedure, still adding the original 8 to reach 14 feet and still
      arriving at 6 hours rather than 3. She accepted the correction verbally but
      did not apply it, so the turn is present, not not_evidenced.
  - **Supplying a figure is not supplying the correction to the misconception:**
    distinguish the tutor supplying a figure from the tutor supplying the
    correction to the misconception itself. When the tutor states a figure but
    the student independently drops the specific error that defines the
    misconception, the turn is absent, because the student corrected the
    misconception through her own reasoning. This is distinct from the
    fully-dictated-correction case above, where the tutor names the error and the
    fix and the student only applies them. The test is whether the tutor named
    the defining error and its fix, which is not_evidenced, or only supplied a
    figure while the student herself abandoned the error, which is absent.
    *Worked example (principles, Todd snow-cone dialogue, turn 9):* for eight
    turns the student double-counts the $75 ingredient cost, subtracting it a
    second time at the end. The tutor states that Todd has $175, but never names
    the double-counting error or tells the student to stop doing it. In turn 9
    the student assembles $25 + $150 = $175 and subtracts only the $110,
    dropping the double count for the first time. The tutor supplied the figure
    $175, but the correction of the double-counting misconception came from the
    student, so the turn is absent.
  The two rules that follow are named instances of the test.
  - *Instance, tutor-supplied answer:* the three-way test above applied to a
    supplied numeric answer (parrot-with-contradiction present, clean
    integration absent, bare acknowledgement not_evidenced).
  - *Instance, retrospective acknowledgement of one's own error:* a student
    correctly characterising their earlier error in a way that shows they now
    understand (e.g. "I should have subtracted 7, not 21") is absent; only
    admitting a mistake without showing the correct understanding is
    not_evidenced. This is distinct from a pure social acknowledgement that
    carries no reasoning at all, which is not_evidenced for that reason.
    A *wrong* self-diagnosis is judged as content like any other reasoning: a
    diagnosis that misdescribes the student's own error and in doing so
    exhibits a family's misconception (for example, re-attaching a corrected
    value to the wrong referent while explaining the mistake) is present for
    that family, while an inaccurate but construct-irrelevant diagnosis is
    not_evidenced.

- **When the tutor is wrong (wrong premises, endorsements, and models).** The
  rules above assume the tutor's supplied content is correct. Tutors are
  sometimes materially wrong, and three situations need their own judgments.
  - **Accepted wrong premises enter the belief state.** When the tutor asserts
    content and the student accepts it, her subsequent working is judged
    against a belief state that includes the accepted premise, per the cluster
    test and the reconstruction rule. Valid reasoning from a wrong tutor
    premise is not present for any family, since the working is right on the
    belief and the wrong belief is the tutor's contribution, not the student's
    misconception. Invalid reasoning on the incorporated premise is judged
    normally, wrong on the updated own-belief state is procedural. Conceptual
    families are judged only on content the student herself contributes beyond
    the accepted premise, since accepting what the tutor stated is an echo
    under the parroting test and evidences nothing about the student's own
    model. *Worked example (hare-and-turtle dialogue, final turn):* the tutor
    garbles the summary, stating the hare will take 20 seconds and the turtle
    18. The student is not present for believing those supplied numbers. Her
    own contribution is subtracting them to report a 2 second head start, and
    on the supplied premise the turtle is the faster animal and needs no head
    start at all, so her handling of the premise is wrong on the belief state
    she accepted, and that contribution is judged normally.
  - **A tutor endorsing the student's own error does not convert it into
    tutor-supplied content.** Endorsement is not supply. An error that
    originated with the student remains hers, and it stays present when
    re-exhibited after the endorsement. The fluency rule's barking-dogs
    example already applies this, do not be moved by a mistaken tutor's
    approval. *Worked example (Mariana ribbon dialogue, turn 4):* the student
    has been dividing the full 4.5 feet without deducting the leftover foot,
    an error of her own making, and the tutor wrongly endorses it by saying
    the leftover is not needed. The student then repeats the division of 4.5
    by 0.7. The endorsement does not convert her error into supplied content,
    so the turn is still present.
  - **A correct result reached through a tutor's wrong model evidences
    nothing.** Where the tutor's wrong model happens to produce the correct
    number and the student executes within it, the execution is judged under
    the dictation rules, typically not_evidenced, and the correct result is
    not evidence that the student's own model is right. Conceptual families
    remain judged on the student's own contributions, and the mismatch is
    noted rather than credited as absent. *Worked example (race-cars
    dialogue):* the problem says each car gains one passenger at the halfway
    point, but the tutor instead asserts that twenty new cars join with one
    occupant each, which happens to reach the same correct total of 80. The
    student computes 60 plus 20 equals 80 inside the tutor's wrong model. The
    execution is not_evidenced under the dictation rules, and the correct 80
    does not make her earlier start-state-plus-end-state double-count absent.

- **What counts as dictating (the boundary for the tutor-supplied rule):** the
  test for whether the tutor supplied the content is whether the
  construct-relevant content itself appears in the tutor's turn, or only in the
  student's. The construct-relevant content is the thing the family is about,
  the operation or operand arrangement for the operation families, the
  interpretation or the identification of what to do for comprehension. If that
  content appears in the tutor's words and the student reproduces it, the tutor
  dictated it and the turn is not_evidenced. If the tutor points at where work is
  needed but does not state the content, and the student supplies it, the tutor
  only prompted and correct work is absent. The line is not how strongly the
  tutor hinted, it is whether the content was stated. A strong hint that stops
  short of naming the content still leaves the content for the student to
  produce, so it is prompting, and some strongly telegraphed turns will be absent
  under this test. This keeps the label reproducible, since one can point to the
  tutor's words and check whether the operation, the step, or the interpretation
  is literally there. This boundary generalises the selecting-versus-executing
  line and the fully-dictated-correction clause, which both turn on whether the
  tutor named the content. For operands, "literally there" means the value, not
  merely the referent. A tutor turn that names an operation and points at an
  operand by description ("add on the slices Tony used on Saturday") while
  leaving its value for the student to retrieve from her own work leaves real
  content for the student to produce, since retrieval can fail and in this
  corpus does (anchored outputs fetched in place of the intended figure), so a
  correct execution with any self-retrieved operand value earns for what it
  engages (the sandwich dialogue 748, turn 8; the sink dialogue 977, turn 5).
  Where every operand value is stated in the recent exchange alongside the
  operation, only execution remains and the turn is not_evidenced (the bunny
  dialogue 1064, turn 3; the apples dialogue 1926, turn 8). This clause reads
  the stated-content test, it does not soften the resolution step: a value the
  tutor stated remains supplied content there even when the student retrieves
  and deploys it competently.

- **A tutor statement supplies content just as a question does:** a tutor turn
  supplies construct-relevant content whether it is phrased as a question or as
  a bare statement or correction. A student who merely confirms a tutor's stated
  figure or assertion, without adding reasoning of their own, is not_evidenced,
  the same as if the tutor had asked and the student had answered. For example,
  when the tutor states "they bought 15 kg in week one" and the student replies
  "yes, in week one they bought 10 + 5 = 15 kg", the student is confirming
  content the tutor supplied, so the turn is not_evidenced. Do not treat a
  tutor statement as leaving the content for the student to produce simply
  because it was not a question.

- **Content can be supplied across the recent exchange, not only the immediately
  preceding turn:** construct-relevant content counts as dictated when the recent
  tutor turns together fully specify the step, even if no single turn does. If
  the tutor supplies the operand in one turn and the operation in the next, and
  the student then executes the fully specified calculation, the turn is
  not_evidenced. For example, when the tutor states the week-one amount is 15 in
  one turn and says week two was twice that in the next, a student computing
  2 x 15 = 30 is executing a calculation the tutor fully specified across the two
  turns, so the turn is not_evidenced. Scope this concretely to the current and
  immediately preceding tutor turn, the window the example above spans, not
  content scattered anywhere earlier in the dialogue, so it does not let
  almost anything be treated as dictated. Two neighbouring scopes are
  governed elsewhere and are wider by design: a corrected figure supplied
  upstream stays the tutor's contribution for credit purposes, per the
  not-re-committing clause of the comprehension family, and element-supply
  for the resolution step is thread-scoped, per the supply rule of ledger
  step 3.

- **The incorrect solution can establish who owns the content (provenance for
  the dictating boundary):** the student's initial incorrect solution is
  evidence of what the student already possessed before the dialogue. Use it to
  decide whether the tutor supplied the construct-relevant content or only
  corrected an operand around content the student already had. If the student's
  own incorrect solution already displays the strategy, operation, or
  interpretation, then a tutor who later states a corrected number is correcting
  an operand, not supplying the construct-relevant content, so the student
  applying that strategy with the fixed operand is engaging the construct and is
  absent, not not_evidenced. Two guards keep this within the per-turn rule.
  - **The turn must still display the reasoning:** the incorrect solution
    establishes provenance, that the student is the source of the content, but
    the turn being labelled must itself restate or apply that content. Do not
    credit a turn that contains no reasoning just because the incorrect solution
    had it.
  - **Provenance does not override a fresh error:** if the student's turn departs
    from the strategy shown in the incorrect solution and exhibits the
    misconception, that turn is present on its own content, regardless of what
    the incorrect solution showed earlier.
  *Worked example (Tanya fruit dialogue, turn 3):* the student's
  incorrect solution already sets up the work-backwards strategy (total minus
  known fruit gives the plums), erring only by miscounting the known fruit. When
  the tutor later states that the known fruit is 12 and asks for the plums, the
  tutor is correcting an operand, not supplying the work-backwards strategy the
  student already owned. The student restates that strategy in turn 3 and applies
  it correctly, so the turn is absent.

### Correctness independence

- **Label the reasoning, not the answer (the channel reads what the student
  said):** the misconception label is evidenced by the *content of the
  student's stated reasoning*, not by whether their answer is numerically
  correct. The correctness of the answer is already captured by the separate
  correctness channel; the misconception channel exists to carry information
  correctness does not, so it must be able to diverge from correctness. A turn
  that states reasoning can be present (the reasoning shows the misconception),
  absent (the reasoning correctly engages the misconception's target), or
  not_evidenced (the reasoning does not bear on the misconception). A turn that
  gives only a bare answer with no reasoning is **not_evidenced** for the
  misconception channel: the answer being right or wrong is the correctness
  channel's job, and a bare number reveals no reasoning to diagnose. Do not
  infer present from a wrong number or absent from a right number; that would
  make the misconception label a copy of correctness, which is precisely the
  redundancy the channel is meant to avoid. (Exception: whether a bare answer
  is nonetheless labelled is decided by the
  bare-figure-versus-reasserted-result rule under "What engages a construct",
  bounded at the far end by the no-attributable-route limit of ledger step 4.
  Compressed, a committed output of a construct in play is a re-asserted
  result and takes a label, a bare figure otherwise.) In
  short, a wrong answer does not imply present and a right answer does not imply
  absent; the label tracks whether the family's specific misconception is
  operative in the stated reasoning.

- **Downstream/arithmetic errors:** calculation and arithmetic slips are not
  present unless the error itself reflects the family's specific misconception.
- **Motivated false arithmetic is perseveration, not a slip (answer-anchoring).**
  The downstream-arithmetic exclusion above covers genuine slips, which are
  directionless. It does not cover an arithmetic assertion that is false on its
  face and whose function is to preserve a previously committed conclusion,
  such as asserting 3 + 10 = 11 to keep an answer of 11 (juggling dialogue,
  turns 2 and 3), asserting a product still equals the old total against the
  student's own claimed calculator check, or asserting that six is less than
  three to keep a no-deduction reading (Winnie deduction dialogue, later
  turns). The tell is direction. A genuine slip lands anywhere, while motivated
  falsehood systematically lands back on the prior answer, often against
  pieces the student herself has just computed correctly. Such a turn is
  **present** for the family whose belief the falsehood protects, reconstructed
  per the reconstruction rule, because the falsehood is the surviving
  misconception defending itself, not noise. Five companion judgments keep
  this consistent with the rules above.
  - **Splice turns.** A turn that bolts a supplied answer onto an otherwise
    unchanged wrong chain is judged on what the student still asserts of her
    own. The echoed fragment falls under the parroting test and earns no
    credit, and the retained chain is judged normally, which typically makes
    the turn present.
  - **Post-reveal contradiction is a re-asserted result.** A bare wrong
    assertion that contradicts a just-supplied answer is a committed
    re-asserted result under the bare-figure rule, not a bare figure, so it is
    present for the family the reconstruction attributes, even when the turn
    contains no reasoning of its own.
  - **Premise-conclusion decoupling.** When a turn affirms a corrected premise
    and immediately redraws the old conclusion, the affirmed premise is judged
    under the parroting test, where it is usually an uncredited echo, and the
    conclusion is the student's committed output, so the label follows the
    conclusion. Where every premise is demonstrably the student's own and
    correct and only the assembly fails, the working is wrong on her own
    beliefs, and the cluster boundary test routes the error procedural.
  - **The anchored composition can itself be the belief.** Where a committed
    output survives while its own derivation mutates around it, the thread's
    belief is the anchored composition, not any one derivation. Sign, operand,
    or method changes are exhibitions of that belief rather than corrections
    of it, because each variant is selected for landing on the protected
    output. *Illustration:* a student committed to a total of 90
    first derives it as 120 - 30; when the 30 is corrected to a gain, she
    re-derives 60 + 30 = 90. The sign flip is not a repaired step; the
    composition rule enacted is "the 30 combines with whatever sign keeps
    90", and the turn is present.
  - **Anchor identity binds a false claim to the existing thread.** A false
    assertion whose result lands on an existing thread's protected or anchored
    output is that thread's motivated act, not the founding commitment of a
    new thread, even where the assertion is route-pointable on its own.
    Founding a separate thread would double-count one belief defending
    itself. *Illustration:* where a thread's protected total is 1600,
    a later product 40 x 45 asserted equal to 1600 inside the corrected
    frame is that output invading the new frame, present for the original
    thread, no fresh thread founded. *Contrast:* a false product landing on
    a fresh value that matches no anchored output founds its own thread
    correctly.

- **Partial correctness does not rescue a turn:** a turn may correctly handle
  one part of the task's structure while failing another. Correct handling of
  one sub-relationship does **not** make the turn absent if the family's
  misconception is exhibited in another load-bearing part of the reasoning.
  Judge the turn by whether the misconception appears anywhere in the reasoning
  the task requires at that point, not by whether some part was handled
  correctly. A useful discriminator sits alongside this: asserting a wrong
  quantity because the student misunderstands what it refers to is the
  misconception (for a comprehension family, this is present), whereas
  miscomputing a correctly understood quantity is an arithmetic slip and is not
  present unless the slip itself is the family's misconception. *Worked example
  (comprehension, barking dogs, turn 3):* the student correctly applies the
  poodle-doubling relationship ("poodle barks twice per terrier bark, so
  $2 \times 6 = 12$") but asserts the terrier barked 6 times, mistaking the
  hush count for the bark count. The correct poodle-doubling logic does not
  rescue the turn, because the comprehension misconception is exhibited in the
  hush-to-bark relationship, which is load-bearing here. The turn is present.

- **Ambiguity defence (a defensible reading of an ambiguous problem is not the
  misconception):** when a problem genuinely supports more than one reading, a
  student who applies one defensible reading coherently has not exhibited the
  misconception, even if the resulting answer differs from the dataset's
  expected answer. This is a hard case of the correctness-independence rule
  above, and it applies in any family, since a problem can be ambiguous about a
  rate, an operation, a step sequence, or what is being asked. The defence
  applies only when all three conditions hold.
  - **Genuine ambiguity:** the problem text itself supports more than one
    reading, not merely that the student reached a different answer. A reading
    is genuinely available only if it yields a physically and semantically
    possible model of the described situation; internal consistency of the
    execution does not by itself establish availability, since a chain can be
    run flawlessly on an impossible model. The granted defences all pass this
    test on both arms (both timelines of the lateness dialogue 634, both work
    weeks of the overtime dialogue 1050, both schedules of the juggling
    dialogue 1334 are real situations), while the ladder dialogue 2142 fails
    it: reading the rungs' stated 18-inch length as vertical extent requires
    18-inch-thick rungs, which no sense of "long" licenses, so the reading is
    unavailable and the solution is a committed misreading, not a defence. The
    bar is impossibility, not implausibility or non-preference: a reading that
    describes a strange but possible situation remains available, and
    availability is never defeated merely because the other arm is more
    natural.
  - **Internal coherence:** the turn applies a single reading consistently, with
    no contradiction inside the turn between something the student endorses and
    what the student then does with it.
  - **Not yet expired:** the defence holds only until the intended reading is
    made explicit in the dialogue. Once the tutor has stated the intended
    reading, the ambiguity is resolved for this dialogue, and persistence in
    the alternative reading from that point is present, judged normally. This
    route is distinct from the internal-coherence disqualifier below, which
    catches the student who *endorses* the clarification and then contradicts
    it; expiry catches the student who never endorses the clarification at
    all and simply carries on, whose turns stay internally coherent and would
    otherwise hold the defence indefinitely.
  **Disqualifier.** If the turn endorses construct-relevant content and then acts
  inconsistently with it, whether that is reporting a total the endorsed
  structure does not produce, or naming an operation that conflicts with one just
  accepted, the turn is not a clean application of a defensible reading. It is a
  self-contradiction, the defence does not apply, and the turn is judged normally
  (under the parrot-with-contradiction rule when the endorsed content came from
  the tutor, or under the stated-versus-enacted clause above when the conflict
  is self-originated). Failing any
  condition removes the defence, and the internal-coherence test is checked
  before ambiguity is even considered. *Worked example (comprehension, juggling
  dialogue):* the problem says Jeanette starts at 3 objects, gains 2 a week, and
  practises 5 weeks, which is genuinely ambiguous about whether 5 weeks means
  five increments or four. In turn 1 the student applies the four-increment
  reading coherently to reach 11, passing all three conditions (no clarification
has yet been given, so the defence has not expired), so the turn is absent
  despite the dataset expecting 13. In turn 2 the student verbally accepts the
  tutor's ten-additional-objects structure yet still reports 11 (which
  contradicts 10 + 3 = 13), failing the internal-coherence test, so the defence
  is disqualified and the turn is present. *Worked example for expiry (Alejandra
  overtime dialogue, turn 3):* the problem's four hours of overtime is genuinely
  ambiguous between a total and a per-day amount, so the student's per-day
  reading is defensible at turn 1 and the defence holds there. The tutor then
  states explicitly that the overtime was not worked every day, making the
  intended total reading explicit. At turn 3 the student repeats the times-five
  computation without endorsing the correction. Her turn is internally coherent,
  so the disqualifier does not bite, but the defence has expired, and the turn
  is present.

### Endpoint note

- **Endpoint interaction:** a present final label on a reveal-assisted dialogue
  is coherent and maps to the endpoint check's reveal stratum. Where the final
  turn is not_evidenced, the dialogue's substantive endpoint comes from the
  last substantive (present/absent) turn.

---


## Annotation procedure: the source ledger

The rules above are applied through an explicit per-dialogue state, the source
ledger, which tracks every misconception thread from its origin to the end of
the dialogue. The ledger is procedure, not new logic: every step below names a
rule defined elsewhere in this codebook, and its purpose is to make the
stability machinery mechanical for a sequential annotator (human or LLM)
working under causal scope.

**The output schema (misconception metadata).** The annotation of a dialogue
is two linked tables. The **thread table** holds one row per misconception
source with the fields: `source_id` (S1, S2, ... in order of first
appearance); `family` (one of the five; re-attributions are events, the field
is not edited); `enacted_belief` (one line); `identity_signature` (the wrong
quantity, operand, or omission and the role it sits in; re-emergence matching
runs on this, never on the belief prose. For threads whose persistence becomes
output-anchored, where later exhibitions defend, falsely re-derive, or migrate
the original output rather than re-committing the originating act, the
signature also names the protected output, and re-emergence matching may run
on it: the boxes dialogue 547, whose 32,000 survives its own pairing; the eggs
dialogue 1744, whose pooled 9 migrates from the cracked slot to the perfect
slot. The output binds as a matcher only where the persistence is motivated,
falsehoods landing on it or the quantity relocating within a continuing
defence, never by numerical coincidence alone, and this does not disturb the
anchored-recombination rule of ledger step 4, whose division with this
matcher is by order: where the output matcher or the structural signature
claims the turn, it is an exhibition of the existing thread, and step 4
founds a new thread only for the residual case where neither fires and the
old output sits as a mere ingredient in an otherwise unattributable
committed claim); `origin_unit` (SOL or a turn);
`origin_kind` (*initial*, *re-attribution* out of an existing thread with a
changed root cause, or *post-expiry* of an ambiguity defence);
`exhibitions` (the event history as turn and event-tag pairs, tags drawn
from the fixed vocabulary and defined as follows. *committed*: the origin
event, the token's first commitment. *re-exhibited*: a recurrence with no
intervening correction event. *reversion*: a re-exhibition immediately
following the corrected content being named, adopted, or performed.
*splice*: a supplied figure bolted onto retained wrong structure, per the
motivated-arithmetic companions. *parrot-with-contradiction*: supplied
content accepted while the working re-exhibits the error, per the
tutor-supplied rule. *motivated-falsehood*: a facially false assertion whose
function is to preserve the committed conclusion, per the
motivated-arithmetic rule. *rationale*: a spontaneous articulation of the
belief behind the error, per the root-cause trigger. *resolved*: the
resolution act of step 3. Where several apply to one event, record the most
specific, in the precedence resolved, motivated-falsehood,
parrot-with-contradiction, splice, reversion, rationale, re-exhibited, with
committed reserved for origins. Tags are analysis metadata: the model
consumes only the collapsed statuses, and the reopening rule of step 3 keys
on any presence event of the thread regardless of tag);
`resolved_at` (the turn of the terminal resolution event, present iff
resolved_by_end is true: a resolution event later voided by re-exhibition
remains in the exhibitions list, tagged resolved, and in the turn grid as an
absent cell with its source, but carries no resolved_at); and
`resolved_by_end` (true iff the last event is a resolution as defined in the
thread-linked resolution step of the ledger procedure, with no later
re-exhibition; the conjunction over threads is the
dialogue-level resolution verdict checked against the dataset's resolution
field). The **turn grid** keeps one row per unit and five family cells, each
a status plus attribution: present cells list the exhibiting source ids
(multiplicity is the list length); absent cells list resolved source ids or
the marker *independent* for thread-free credit (the symmetric and
re-articulation standards, where most absents arise); not_evidenced is bare.
A resolution event may fall at a turn whose cell for that family is present,
when the presence is attributed entirely to different source ids: the
resolving thread's family-mate is exhibiting in the same turn, the letter
records that exhibition, and the resolution is recorded in the thread table
alone (the sandwich dialogue 98, turn 6, where S1's corrected composition and
S2's live error share one sentence, the cell reading P for S2 with S1's
resolution at that turn in its thread row). A single source never appears on
both sides of one cell, since one thread contributes one event per turn.
Consistency checking must therefore verify resolutions against the thread
table, never by scanning for absent cells alone, which is exactly the
inference that fails on these dialogues.
A slim per-turn note remains for genuine residue only.

**Invariants (mechanically checked).** Every present cell's sources carry
that unit in their exhibition list, and every exhibition appears as a present
cell of the thread's family; any mismatch is an annotation bug, not a
judgment call. Three further invariants govern resolution recording: a
thread's resolved_at must coincide with an absent cell of the thread's
family carrying that thread as source at that turn; no presence of the
thread may follow its resolved_at; and a voided resolution event, an
absent-with-source cell followed by a later re-exhibition, carries no
resolved_at, which is how a voided event is told from an annotation bug. The model consumes only the collapsed three-value statuses;
ids, tags, kinds, and terminal statuses are metadata for validation, the
endpoint check, and persistence analysis.

**Per-turn procedure.**

1. Read the turn within its prefix (problem, incorrect solution, turns so
   far).
2. **Re-emergence check.** For each thread, run the identity test against the
   turn's content. On a match, run the belief-continuity check: same enacted
   belief, the thread re-exhibits and the turn is present for the thread's
   family; genuinely changed belief (the act changes form, a spontaneous
   rationale re-identifies the error, or the corrected belief re-emerges under
   a different driver), root-cause re-investigation fires and the family is
   re-attributed from this turn forward, logged.
3. **Thread-linked resolution.** A resolution is the student's own act
   committing the corrected counterpart of the thread's token: the corrected
   element itself, performed by her, at the token's structural position,
   act-for-act with the token. Correct content arriving by other routes does
   not resolve, however correct: executing a fix whose content the tutor
   named; performing her own operation on a supplied operand where that
   operand was the corrected element (the tears dialogue, 680, the stated 90
   inside her division); and self-performed work downstream of a supplied or
   revealed correction, aggregating or extending its outputs (the desserts
   dialogue, 59, summing the instructed divisions; the bakery dialogue, 1626,
   completing the revealed integration). A pointing prompt that locates the
   area while supplying no content does not block resolution (852, 609, 1966,
   2223), and a named frame within which the student produces the corrected
   element herself resolves (the beads dialogue, 308, her own 40 - 30 with
   the silver binding) while a named element executed does not (328). Between
   these poles sit the diagnosis-led closes, assigned by authorship of the
   corrected content rather than by the surface form of the tutor's
   utterance. A named fault, the wrong element identified without its
   corrected content being stated, functions as a pointing prompt:
   resolution is available where the corrected assembly and its content are
   the student's own, even where dropping the named fault one-step-entails
   the fix, since entailment is not authorship. A supplied corrected
   interpretation functions as a named element, including one carried inside
   a leading either-or whose correct arm states it: selecting that arm
   echoes supplied content, and execution within the fixed relationship
   afterward does not resolve. Two boundary judgments sharpen this. First,
   restating the problem's own text is supply, not pointing, when the clause
   restated is the contested content itself: "the question tells us the
   total is for both weeks together" states the disputed period reading and
   bars resolution, while "check the question again, it tells us about the
   time period" names only the category of the condition and leaves the
   content to the student, so resolution is available. The test is whether the student
   could still get the contested reading wrong after the tutor's sentence;
   if not, the content was supplied. Second, a corrected value produced
   through a tool at the tutor's directive has ambiguous authorship and does
   not resolve: "use a calculator to work out 3 x 3" yields a corrected nine
   whose provenance cannot be assigned to the student, so the thread stays
   open; contrast a corrected sum that is the student's own mental
   re-evaluation at a bare add-up prompt, which resolves. Surface form decides nothing here, a
   statement can point and a question can name. An act
   for this purpose includes an accurately committed articulation, not only a
   performed computation: a self-diagnosis that identifies the error and
   commits the corrected content is a resolution where that content is
   self-supplied (the fabric dialogue 609, "I had subtracted 21 instead of
   7", an identification no tutor turn had stated), and is not where it
   restates content the tutor established in the recent exchange (the tears
   dialogue 680, turn 7, accurate at the value level but mirroring the stated
   90 and the corrected division). The stated-content discipline governs
   articulations exactly as it governs performances. Supply for this step is
   thread-scoped, not a sliding window: once the corrected element's content
   has been stated in the thread's correction sequence, later performances of
   it execute named content and do not resolve, however many turns intervene.
   An intervening re-exhibition of the thread reopens resolvability, since it
   shows the naming did not take and a subsequent self-performed correction
   is then the student's own act; content re-stated in the current exchange
   closes it again. The two poles: a corrected element named early,
   re-exhibited through the middle turns, and self-performed at the close
   resolves; an adopted correction that never re-exhibits leaves its later
   deployment executing named content, resolving nothing. Such
   executions still earn ordinary absent credit where the engagement gates
   pass; the resolution status is the stronger claim and is what this step
   withholds. One act can resolve more than one thread: where a single
   self-performed act commits the corrected counterpart of two threads'
   tokens, each thread records its own resolution event at that turn (the
   games dialogue 1538, turn 4, where 7 - 5 = 2 corrects both the inverted
   direction and the timeframe binding; the beads dialogue 308, turn 4),
   judged thread by thread exactly as presence is. A self-performed correct
   execution on a tutor-posed isomorph can constitute a resolution, since it
   is the student's own act committing the corrected element in structural
   form on material nobody solved for her (the ages analogy of the fishing
   dialogue 163, where both planted errors are caught and the corrected total
   structure assembled). No analogy-specific rule follows from this: the
   dated-resolution design discriminates the outcomes as usual, so 163's
   resolution stands because the belief never re-exhibits, while the pennies
   analogy of the walking dialogue 44, an equally clean isomorph performance,
   is voided by the target-side re-exhibition one turn later. An analogy the
   tutor works and the student merely endorses is echo and resolves nothing,
   and the stated-content discipline applies to the isomorph's materials
   exactly as to the target's. Exhibition runs narrower than resolution
   here: a failure on a tutor-posed isomorph does not exhibit any thread,
   because exhibition scope is the problem's own chain, while a success can
   earn credit floors and, per the above, can resolve. The asymmetry is
   deliberate, credit measures competence wherever shown, presence tracks
   commitments inside the task (*illustration:* a failed
   side-problem about a sibling's age, posed by the tutor away from the task
   chain, is noted, not present). Isomorph credit also
   respects the framing standard: an isomorph whose operation is unstated in
   the prompt can earn (a comparison of two heights the prompt leaves
   unoperationalised), while one whose operation is named earns nothing
   ("double that"). Resolution is a dated act,
   not a state transition: the thread stays live, and a later re-exhibition
   makes a later turn present again (no anchoring).
4. **New threads.** Scan the remaining content for errors matching no thread;
   each gets a fresh origin attribution from its own prefix, including a
   same-family second thread when the identity test separates it from the
   existing one. Two limits govern creation. A bare committed answer with no
   attributable route and no engagement creates no thread and is
   not_evidenced, since a present label requires a reconstructable family. An
   anchored recombination, an old output recombined with a newly supplied
   figure into a committed claim, does engage the problem within the existing
   error context and is present, comprehension by the burden default, with
   the anchor as its signature. The recombination rule is a residual,
   reachable only for content the step-2 scan leaves unattributed. At any
   turn where an old output or a supplied figure appears inside a fresh
   committed construction, two questions are asked in order. First, does the
   result land on a protected output within a continuing defence, or does
   the construction instantiate a live thread's structural signature? If
   either, the turn is an exhibition of that thread, motivated-falsehood or
   splice, and creation is closed. Second, only where neither matcher fires
   and an old output sits as a mere ingredient in an otherwise
   unattributable claim does this rule found the new thread.
5. **Thread-independent credit.** Apply the ordinary engagement gates for
   absent credit unrelated to any thread (the symmetric standard, the
   re-articulation standard, dual-use). Most absent labels arise here, not in
   step 3.
5b. **Individuation and the residual scan.** Threads are individuated by
   belief, not by family or by turn: distinct wrong beliefs get distinct
   threads even in the same family, and a single unit may commit or exhibit
   several. After attributing a unit's most salient error, re-scan its
   remaining wrong content; whatever no attributed belief explains founds or
   exhibits its own thread rather than being absorbed into the dominant
   story.
6. **Emit the five labels.** A family is present if any of its threads
   re-exhibits or newly originates in the turn; otherwise absent if the turn
   correctly engages the family's construct on the student's belief;
   otherwise not_evidenced. Layering across families is unchanged.
7. **Record.** Emit the turn's grid row (statuses with source attributions)
   and update the thread table (new rows, appended exhibitions with event
   tags, re-attribution entries stating what changed).

**Validation use.** Human and LLM annotations compare at the thread level as
well as the cell level: same sources found, same origins, same re-emergence
patterns. Thread-level disagreement localises failures that cell agreement
averages away.

**Worked rendering (video-game hours dialogue, 1159).** Thread table: S1,
comprehension, belief "the derived 6 is hours per game-day, the mislabelled
4+2", signature "the 6 in the per-day slot of 6 x 3", origin SOL, initial,
exhibitions (SOL, committed), (T5, re-exhibited), (T7,
parrot-with-contradiction), (T8, re-exhibited), (T9, re-exhibited), (T10,
splice), resolved_by_end false. S2, relevance, belief "the given 4, the TV
hours, fills the games slot", signature "4 in the per-day games slot", origin
T6, initial, exhibitions (T6, committed), resolved_by_end false. Turn grid
highlights: SOL reads comprehension present [S1] with operation and steps
absent [independent]; T6 reads relevance present [S2]; T10 reads
comprehension present [S1], the dictated 2 x 3 earning nothing.

## Cross-family adjudication

This section is for a single decision: when a turn *looks like* it could belong
to one of two families, which family does it belong to. It is distinct from the
genuine-co-occurrence rule in the general rules above, which handles turns that
really do exhibit several misconceptions at once. Here the turn exhibits one
misconception that is easy to misfile as another; the rules below fix which
family owns it.

**The families fall into two clusters, and confusion lives within a cluster.**
Crossover is a within-cluster phenomenon, so this is a map of where the hard
calls are.

- **Conceptual-understanding cluster:** comprehension (understanding what the
  problem asks), relevance (which information matters), and principles (which
  underlying idea applies). These turn on *understanding something* about the
  problem, so one misreading can plausibly be described by more than one of
  them. Strategy selection is also a conceptual judgement about the problem's
  structure, but it is not a separate family: a wrong strategy is the symptom
  of one of these failures and is routed to its source (see "Strategy errors
  route to their conceptual source").
- **Procedural-execution cluster:** wrong operation or operand order (which
  operation, in which order) and steps or procedures (the set and sequence of
  steps). These turn on *executing* an already-chosen approach, so one wrong move
  can be framed as an operation or a step error.

A turn that seems to sit in *different* clusters is usually a misread turn rather
than a true cross-cluster case; re-read it before splitting the difference, since
a genuine cross-cluster crossover is rare. The exceptions are the surface-form
cases, where a conceptual error surfaces as an arithmetic move or a broken
procedure (comprehension versus operation, comprehension versus steps); these are
real and recurring cross-cluster calls and are adjudicated below.

### The cluster boundary (the governing test)

Before any pairwise question, one test separates the two clusters, and every
across-cluster boundary below inherits it. The test is **execution under the
student's own belief**.

- A **conceptual** error is a wrong belief about the problem: what it asks, which
  information matters, or which idea applies. The
  student's later working may be *correct for that wrong belief*.
- A **procedural** error is a wrong execution given a correct belief: the student
  understood the problem correctly but combined the quantities with the wrong
  move or in the wrong set or order of steps. The working is *wrong on the
  student's own belief*.

So the governing question is: **is the working wrong given what the student
believes, or correct given what she believes but built on a wrong belief?** Wrong
on her own belief is procedural; correct on her own belief but the belief is
wrong is conceptual. Reconstruct the belief from the dialogue up to the turn
being judged (per the general reconstruction rule and its causal scope)
whenever the reading is unclear.

This is why the surface-form cases are the only genuine cross-cluster confusions:
a conceptual error can produce working that *looks* procedural (a wrong-looking
arithmetic step or a broken procedure) while being correct for the student's
wrong belief. The test resolves them by asking whose logic the error is wrong on.
Every across-cluster pair below is an application of this one test; the pair
entries add only what is specific to the two families in question.

**Equation construction routes the same way.** A wrongly built equation is not a
family of its own; it routes by what the mismatch reflects. A side or operand
that misrepresents what a quantity refers to falls under the misassignment
rules (the dimensional-slot clause for given quantities, the derived-quantity
clause for derived ones). A variable bound to the wrong timeframe is
comprehension, temporal structure. Algebraic garbling with demonstrably intact
beliefs is procedural, per this test.

### Derived and intermediate quantities (route by the cluster test)

The family constructs speak of the problem's stated information and described
structure, but the most frequent error mechanism in the development data involves
quantities the *student herself derived*: an intermediate re-enters the
computation in the wrong role, a factor or component is applied twice, or a
derived total is relabelled as one of its parts. Examples include re-multiplying
an already-aggregated total by the same factor, adding a subtotal into the total
that contains it, and treating a combined quantity as an individual one. No
single construct owns these, so this clause routes them explicitly, by the
cluster boundary test.

**Reconstruct what the student believes the derived quantity is, then route by
execution under that belief.**

- **Wrong belief about the quantity (conceptual).** If the student demonstrably
  holds a wrong model of what the derived quantity represents, the working that
  follows is correct *for that wrong belief*, and the error is conceptual. It is
  **comprehension** in most cases (the role or meaning of the quantity is
  misread), and **principles** where the failure is part-whole or inclusion as a
  concept. *Worked pole (bricks, courses dialogue):* the student states the first
  three courses hold 1200 bricks, states all five courses hold 2000, and adds
  them. Her turns show she treats these as disjoint piles, a wrong part-whole
  model, so the belief itself is wrong and the error is conceptual.
- **Intact belief, duplicated bookkeeping (procedural).** If the student's
  beliefs about the quantities are demonstrably correct and the computation
  still duplicates or misplaces them, the working is wrong *on her own belief*,
  and the error is procedural. It is **steps** for a duplicated or extra step,
  **wrong operation** for operand construction within a step. *Worked pole
  (sand-jugs dialogue):* the student knows there are exactly two jugs, computes
  the per-jug volume correctly, doubles for the two jugs, and doubles again at
  the end, justifying both doublings by the same fact she plainly knows. The
  belief inventory is correct, so the duplication is an execution lapse.

**Default for unreconstructable cases.** Sometimes the prefix never reveals
what the student thinks the derived quantity is, and both stories fit everything
she wrote. *Worked case (video-game hours dialogue):* the student writes 2
hours x 3 days = 6 hours and, in the same turn, 6 x 3 = 18. Read in isolation
this looks unresolvable: the first half suggests she knows the 6 is the weekly
total (procedural), while the persistence of the re-multiplication under
correction suggests a stuck belief (conceptual). Belief tracking (see "Label
stability and belief tracking") resolves it without the default: the sentence
"he spends 6 x 3 = 18 hours playing video games in a week" is reproduced
verbatim from her solution in five separate turns; when challenged she
substitutes the other per-day quantity (the TV hours, 4) into the same slot,
showing the slot itself is per-day times days; her statements of the correct
2-hours-and-3-days assent to content the tutor had just supplied (echo
discount); and the 2 x 3 = 6 itself fills in a formula the tutor dictated in
the preceding turn. The single belief explaining every exhibition is that the 6
is a per-day quantity, her solution's mislabelled 4 + 2, so the origin is a
wrong belief about a derived quantity, comprehension, and every exhibition
inherits it. Where even prefix-scoped reconstruction genuinely fails (no stable
act, no rationale, no consistent enactment),
**default to the conceptual side (comprehension)**. The rationale is burden of
establishment: the procedural label requires positively establishing that the
belief is intact, since a demonstrably intact belief is what makes the error
bookkeeping rather than misconception, and where the belief cannot be
reconstructed that requirement fails. This mirrors the logic of the other
default clauses in this section, where the side carrying the
positive-establishment burden loses ties.

**Relation to the independence test.** If granting the student her wrong belief
about the derived quantity would make the computation correct, there is one
error, the belief, and one conceptual label. If her beliefs are all correct and
the computation still duplicates, there is one error, the bookkeeping, and one
procedural label. Only when a wrong belief *and* an independent execution fault
both survive the counterfactual fix of the other is layering present.

**Remit.** Relevance is about selection among the problem's *given* information,
so derived and intermediate quantities do not take relevance labels. A same-kind
confusion involving a derived quantity (an earlier derived count migrating into
a same-kind slot) routes under this clause, not under the dimensional-slot
clause's same-kind arm, which governs the problem's stated quantities only.

**Referent-to-derived-base errors are comprehension (the ordered provenance
test).** When a stated relation's referent binds to the wrong base, the
routing is fixed by an ordered test on the provenance of the two candidate
quantities, checked before any mechanism reading.

- **A derived quantity on either side routes here, comprehension.** Where a
  derived quantity stands where a given belongs, or a given stands where a
  derived belongs, the error is a wrong belief about what the phrase refers
  to, comprehension, even though the arithmetic performed on the misbound
  base is locally correct.
- **Two given candidates route to relevance.** Where both candidates are the
  problem's stated quantities, the case is same-kind misassignment under the
  same-kind arm of the comprehension-relevance entry, whether or not the
  misselection travels through a relational or anaphoric phrase ("twice
  that", "half as many as she had lost" between two givens). A relational
  wording does not lift a two-given misselection out of the same-kind arm;
  provenance, not the presence of a relational phrase, is what moves a case
  into this rule.
- **Two derived candidates route by belief.** Where both candidates are
  derived, relevance is unavailable by the remit above, and the case routes
  by the belief test of this clause, conceptual or procedural.

The signature at origin is the misbound referent and its base. Worked
instances, each with a derived quantity on one side:
half-as-many-as-she-lost computed on the derived given-away eight
rather than the lost four (746); twice-as-many-as-week-one bound to the given
ten rather than the derived fifteen (1598); the stated half-apple rate
overridden by the derived per-pie rate (1830); originally-had bound to the
post-give-away amount (1471). The procedural reading, correct referent with
an operand slip, requires the intact referent belief to be demonstrated in
the prefix, per burden of establishment; repeated identical binding under
correction is a stable wrong belief, per parsimony. Contrast slot-filling
among same-kind given candidates, the 30-minute gap placed in the lateness
slot (634, turn 3): a candidate quantity is simply misselected for a role,
which is relevance under the same-kind arm, and the routing is the same when
the misselection is carried by a relational phrase over two givens, per the
ordered test above.

### Strategy errors route to their conceptual source (there is no strategy-selection family)

Earlier drafts carried a sixth family, problem-type recognition, defined
residually: present only when the strategy was wrong despite intact
comprehension, relevance, and principles. The category has been dropped, for a
structural reason confirmed empirically. To assert that a chosen strategy does
not fit the problem, the annotator must say what makes it not fit, and every
completion of that sentence lands in another family. A strategy-fit belief is
not a primitive belief type; it reduces to beliefs about the situation, the
information, and the mathematics, so the residual was unreachable by any
specifiable route. The full six-way annotation pass bore this out: zero present
labels in 516 units, including all thirteen dialogues the dataset itself
profiled as problem-type errors (the historical annotation file
sixway_annotations.csv retains the column as the record of this result, and the
findings report gives the argument in full).

**Routing rule for wrong strategies.** When a student's overall approach does
not fit the problem, route by the source of the misfit:

- the strategy serves a misread situation or goal, so it is the shadow of that
  misreading: **comprehension**;
- it operates on the wrong information or roles: **relevance**;
- it presumes a mathematical relationship that does not hold (pooled division
  treated as equivalent to per-type division, demands summed where the peak
  governs): **principles**;
- no false belief licenses it, she selected against what she demonstrably
  knows: **procedural** (wrong operation or steps, by grain).

Two principles survive from the old boundary entries. An execution slip within
a fitting strategy is procedural, never conceptual. And a wrong strategy is not
rescued by correct arithmetic inside it: judge the model the strategy
presupposes, not whether intermediate numbers come out right along the way.
When a wrong-information error and a wrong-looking strategy coincide, the wrong
information is usually the cause, so relevance. When it is unclear whether the
reading behind a strategy was intact, the burden defaults apply as usual
(comprehension).

**Validation note.** The thirteen problem-type-profiled dialogues remain in the
development set; their profiled errors annotate under the five families via
this routing rule, and the thirteen-per-profiled-family sampling stratification
stands as provenance.

**How to read the entries.** Each boundary is written once, under one pair, in a
uniform shape: the cluster relationship, the deciding question, a compressed
one-line form, a tie-breaker for the hard case, and a pointer to any worked
example. A family's full set of boundaries can be traced through the pair
entries; a boundary is not repeated from the other family's side.

### Comprehension versus relevance (conceptual cluster)

**Deciding question: did the student use the wrong piece of information, or
misunderstand what a correctly chosen piece represents?**

- If the error is in the *selection* of information, choosing a distractor,
  ignoring a stated value or quantity, or attaching a value to the wrong
  condition among those the problem states, it is **relevance**. Relevance
  owns which of the problem's information enters the model: a stated given
  left unused, displaced by an invented quantity or an assumed value, or a
  foreign quantity imported, is a relevance fault even where it yields a
  false model of the situation, and even where the problem contains no
  distractor at all. Comprehension owns what the text is taken to state or
  ask. The silence floor governs credit only and never blocks a presence: a
  given silently omitted or displaced, with visible effect in the model, is
  an act on the present side under the silent-omission rule. *Worked
  example (egg-collection dialogue, 1420):* the one-hour collection duration is
  a stated quantity with no role in any correct chain; multiplying it into the
  egg count (270 x 60) is the inclusion face of the same selection failure whose
  exclusion face is the ignored blue chips of 1639, and both route to relevance.
- If the error is in the *interpretation* of a correctly selected piece,
  misreading what role it plays in the problem's described structure, it is
  **comprehension**.

Compressed: relevance is about *which* information; comprehension is about *what
the information means*. Wrong information chosen is relevance; right information
misunderstood is comprehension.

**Tie-breaker for the hard case (misassignment).** Attaching a value to the
wrong condition sits close to the line, since the student understood the value
but misread which condition it applies to. Resolve it by scope: if the confusion
is between two conditions the problem *explicitly states*, it is relevance
misassignment; if the confusion is about the overall situation the problem
*describes*, not a choice between stated conditions, it is comprehension. So
misassignment is picking wrong among stated options; role-misreading is
misunderstanding the frame itself. *Worked example (James running dialogue):*
the student uses the 100 miles figure, which is relevant, but misreads it as the
starting level rather than the pre-injury level from which the goal is derived.
That role misreading is comprehension, so it does not make the relevance turns
present, and the student's correct days-to-weeks judgment is the relevance
engagement, which is absent.

**Tie-breaker (silent omission versus articulated substitute).** An unused
stated given can arrive at this boundary two ways, and the presence or absence
of a stated substitute belief decides the family. Where the given is simply
absent from the chain and no line of the student's articulates what stands in
its place, the failure is one of selection and routes to **relevance**; the
evidence is textual absence, verifiable by scanning the chain for the given.
Where the student's own words state the substituting belief, the demonstrated
belief outranks the absence framing and the thread is **comprehension**, since
the given is not merely unselected but displaced by a stated wrong model.
*Illustration pair:* where a stated half-of-them condition never appears in
the chain and nothing is said in its place, relevance; where a stated
group-size given is equally absent but the student's own "each group uses 1"
states the substituting rate, comprehension.
Procedure note: before founding either thread, scan the problem statement for
stated givens absent from the chain; an unused given found this way is
evidence, and inventing an undemonstrated compound belief in place of this
scan is the documented failure mode.

**The ignored-condition test (value versus rule).** When a stated condition
never enters the student's model at all (never registered anywhere in the
dialogue), route by what kind of thing was ignored. If it can be stated as a
standalone value or quantity (the 3 blue chips, a $5 fee, a 4-day absence),
ignoring it is a selection failure and is **relevance**: the student's structure
is sound and was starved of a datum. If it can only be stated as a rule,
relation, or conditional clause (a discount tier, an every-third-day deduction,
an in-three-years qualifier), failing to incorporate it means the student's
model of the described scheme is itself wrong, which is a **comprehension**
structure misread (see "Misreading a described structure is comprehension" in
the comprehension family entry). Contrast: in the chips dialogue (1639) the
blue chips never enter the remainder account, and the ignored thing is a
quantity, so relevance; in the discount dialogue (927) the 50% second-shirt
tier never enters the pricing account, and the ignored thing is a rule of the
scheme, so comprehension. This test applies only to never-registered
conditions; if the condition was registered and then dropped, the
coincident-case tie-breaker routes the error to the procedural families before
this question arises.
Registration is not purpose-relative: a value used anywhere in the unit's working counts as registered, whatever role it served there, so a quantity employed as one computation's base and omitted from another's aggregation is registered-then-dropped, procedural, not never-registered (the phone dialogue, 1095, where the 1000 serves as the percentage base and is dropped from the sum; the cake dialogue, 1900, where the snack 1 derives the 2 and is dropped from the add-back).
Where a never-registered given's role is occupied by a mislabelled derived quantity, the derived-mislabel account governs and the thread files comprehension, by parsimony: one belief, that the derived quantity is that thing, explains both the occupation and the ignoring at once (the sandwich dialogue 98, the derived 40 in the eaten slot with the given 28 absent; the terrier dialogue 990, the structure-derived 3 with the six hushes absent). The relevance arm applies where the ignored given's role is simply unfilled, nothing standing in it (the chips dialogue 1639).

**The dimensional-slot clause.** The two constructs overlap on
misassignment (attaching a value to the wrong condition versus
"misunderstanding what role a quantity plays" describe the same act), and the
scope tie-breaker above does not cover the case where a *single* quantity lands
in the wrong slot, which is neither a choice between two stated conditions nor a
whole-frame misreading. Split that space by *kind*, and **check kind first**: the
stated-conditions tie-breaker above applies only *within* same-kind confusions,
so if the kinds differ, the error is comprehension regardless of whether both
quantities are explicitly stated (subtracting a stated time from a stated
distance is comprehension, not a choice between stated conditions).

- **Wrong-kind slot is comprehension.** A quantity placed in a slot of the wrong
  kind, a count where a time belongs (adding 6 cups into an hours total), a
  length where a height belongs (a rung's horizontal length treated as vertical
  extent), seconds subtracted from feet, is **comprehension**. The failure is
  about *what the quantity is*, its dimensional identity within the problem's
  structure.
- **Same-kind confusion is relevance.** A confusion between two quantities of
  the same kind, made versus eaten, lost versus given away, this timeframe
  versus that, is **relevance** misassignment. The student knows what kind of
  thing the slot needs and picks the wrong instance of that kind.
- **Referent and anaphora errors route by the referent rule.** Where a
  relational or anaphoric phrase like "twice that" or "half as many as she had
  lost" is attached to the wrong candidate quantity, the routing is fixed by
  the referent-to-derived-base rule in the derived-and-intermediate-quantities
  clause, which orders the test by the provenance of the two candidates. The
  boundary is stated once, there.

**Kind is judged by the problem's own text.** Kind is a level of description,
and two quantities can be the same kind coarsely and different kinds finely
(pieces versus whole sandwiches are both counts of food items, yet sit at
different part-whole depths). To keep the routing stable across annotators, kind
is fixed by the problem's own dimensional distinctions, the units, object types,
and measured dimensions the problem text itself separates. If the problem's text
draws the distinction (the sandwich problem explicitly cuts sandwiches into
pieces, so pieces and sandwiches are different kinds by its own lights, and a
piece-versus-sandwich confusion is comprehension), the quantities are different
kinds; if the text does not draw it, the annotator does not invent it, and the
confusion is same-kind, relevance. Disagreements then resolve by pointing at the
text.

### Comprehension versus wrong operation (cross-cluster, but common)

This pair crosses the two clusters, so by the general expectation it should be
rare. It is not, because a comprehension error frequently *surfaces as an
arithmetic step*, which looks procedural. The deciding question exists precisely
to stop that surface form from pulling a comprehension error into the operation
family.

**Deciding question: is the arithmetic wrong given what the student believes, or
is it correct given what she believes but built on a wrong belief about the
problem?**

- If the student correctly understood the quantities and the structure but
  combined them with the wrong operation or in the wrong order, the arithmetic is
  wrong on her own logic, and it is **wrong operation**.
- If the student's arithmetic is correct for the problem as she understood it,
  but her understanding of the problem is wrong, the error is upstream, and it is
  **comprehension**.

Compressed: wrong operation is a correct understanding wrongly executed;
comprehension is a wrong understanding correctly executed. Ask whether the
equation is right or wrong under the student's own beliefs. Wrong under her own
beliefs is operation; right under her own beliefs, but the beliefs are wrong, is
comprehension. This unifies the two family-level rules that already govern this
boundary: the wrong-structural-level rule in the comprehension family (deducting
per crate is correct arithmetic for the wrong belief that the rot is per crate,
so comprehension) and the operand-omission rule in the wrong-operation family (a
term is only an operand omission if the student's own model included it; the
Winnie deduction, correct for her belief that the threshold was not reached, is
comprehension, while the Heidi phone omission, wrong on her own logic, is
operation).

**Tie-breaker (unclear belief).** The question depends on knowing what the
student believed, which is not always visible in a single turn. Reconstruct the
belief from the dialogue up to the turn being judged, per the general
reconstruction rule
("Reconstruct the student's mistake before labelling ambiguous turns"), then
judge the turn against that reconstructed belief. If after reconstruction the
belief is still genuinely ambiguous, the turn is not an operation-family
error, since operation requires a demonstrated wrong execution under a clear
belief. The error then routes conceptual, comprehension by the burden
default: the procedural labels require the intact belief positively
established, and where reconstruction cannot establish it that requirement
fails, per the origin-attribution rule of the stability section and the
default of the derived-and-intermediate-quantities clause.

**Both can be present, but only as genuine co-occurrence.** This note is bounded,
because this pair is exactly where an annotator is tempted to mark both. Two
situations must be kept apart.

- **Confusion (one misconception, resolved above):** a comprehension error that
  merely *surfaces as* arithmetic, such as the per-crate deduction, is
  comprehension *alone*. Do not also mark operation present just because the
  error appears in an arithmetic step; the deciding question routes it to
  comprehension.
- **Genuine co-occurrence (both present, per the layering rule):** a turn in
  which the student *both* misunderstands the problem *and*, independently,
  combines her correctly understood quantities with the wrong operation, exhibits
  both, because each family's construct is independently satisfied. This is the
  layering rule of the general rules, not the confusion case.

The test for the second situation is independence: operation is present only if,
setting the comprehension error aside, the student *still* mis-executes
quantities as she understands them. The execution is judged on her own belief
state, per the layered-evaluation standard of the one-error-one-family rule
and the judged-baseline clause of the error-token section, so an operation
owed and withheld on her own wrong figures is an independent op error (the
harvest pole, where failing to sum her own 24 and 28.8 is op present layered
on the comprehension error). If the only operation-looking error is the
downstream shadow of the comprehension error, it is the confusion case and
operation is not present.

### Wrong operation versus steps (procedural cluster)

These two are close cousins, since a procedure is built out of operations. The
clean separation is *grain*: wrong operation is a fault inside a single
computational move, while steps is a fault in the set and sequence of moves the
procedure requires. Fix the grain of the error before asking which family, since
an annotator who does not will oscillate between the two.

**Deciding question: is the error in a single computational move, or in the set
and sequence of steps the procedure requires?**

- If the student chose the wrong operation for one step, or arranged the operands
  wrongly within a step, while the overall procedure is otherwise right, it is
  **wrong operation**.
- If the student omitted a required step, included a step the procedure does not
  need, or sequenced the steps in a way that is not valid, it is **steps**.

Compressed: wrong operation is a wrong move *within* a step; steps is a wrong set
or order *of* steps. Ask whether the fault is inside one operation or in the
scaffolding of operations. Inside one operation is wrong operation; in the
scaffolding is steps.

**Tie-breaker (a missing operation).** A missing operation can look like either a
missing step or a wrong operation. Resolve it by presence versus correctness of
the step: if a required step is entirely absent, so a whole operation the
procedure needs is not there, it is **steps** (a missing step); if the step is
present but performed with the wrong operation or operand order, it is **wrong
operation**. A different but *valid* ordering is neither, it is absent for both,
per the valid-reordering rule in the steps family: a reordering counts as a steps
error only if the new order is invalid, not merely non-standard.

**Tie-breaker (an excess application).** When an operation is applied more
times than the situation licenses (see the error-token section for
localisation), the token can be described both ways, a malformed move and a
duplicated stage. Where the excess application involves a derived quantity,
this tie-breaker carries a precondition: the belief test of the
derived-and-intermediate-quantities clause runs first, and the tie-breaker
is reached only on that clause's procedural side, with the belief about the
derived quantity demonstrably intact in the prefix, typically through the
student's own label contradicted by the act. A wrong model of the derived
quantity never reaches this test, since the working is then correct for the
wrong belief and the router files it conceptually; likewise an excess that
exists only against the true reading, and not on the student's own chain
under her demonstrated belief, is not an excess for this test at all. Where
no derived quantity is involved, entry is governed by the ordinary cluster
test as before. Once reached, route by whether the target quantity still
needed constructing at the token's position in the student's own chain (her
true prefix). If the construction was needed there and the excess enters as an
operand within it, the step is licensed but badly built, and it is **wrong
operation**: the men-factor inside 2 x 10 x 66 (329), the duplicated pair
totals inside the five-term sum (1967), the re-added subtotal inside the
final sum (1036). If the quantity's role was already produced and the act
re-derives it, the step itself is unlicensed and its existence is the fault,
individual arithmetic notwithstanding, and it is **steps**: the closing 14 x
2 after the weight already covered both jugs (2152), the second eating
deduction after the daily rate already charged it (1825). An entirely
unlicensed act files as steps regardless of its internal operands, and a
chained continuation that takes a just-produced result as its input is its
own act for this test.

**Tie-breaker (the produced-role label test).** Whether a re-derivation is an
unlicensed act on a filled role (steps) or a licensed construction carrying an
excess operand (wrong operation) turns on the student's own labels, matched at
the level of the predicate. If the quantity she produced carries a label whose
predicate is the same as the role the later act fills, the role is filled, the
later act is unlicensed, and the error is **steps**. If her label names a
different predicate, the role is unfilled, the construction is licensed on her
model, and the surplus quantity inside it is an excess operand, **wrong
operation**. *Illustration pair:* where the student has produced "30 did not finish" and
the question asks how many dropped before finishing, the predicates are the
same, the role is filled, and a closing re-derivation of it is steps; where
she has produced a quantity labelled "still to be done" and the asked role is
"done last month", the predicates differ, the role is unfilled, the
construction is licensed, and the surplus quantity re-deducted inside it is
an excess operand, wrong operation. The same test separates a label naming
one person's share, which does not fill a differently-labelled joint role,
from a total whose own label is simply re-derived. Labels are read as she wrote them, not as the problem
would have them.

### Comprehension versus steps (cross-cluster, same trap as operation)

This pair is the procedure-grain version of the comprehension-versus-operation
case above, and it is governed by the *same* principle. A comprehension error
can surface as a broken procedure (a missing or wrong step) just as it can
surface as a wrong arithmetic move, so the surface form again risks pulling a
comprehension error into a procedural family.

**Deciding question: is the procedure wrong given what the student believes the
problem asks, or correct given her understanding but built on a wrong
understanding of the problem?**

- If a missing or wrong step follows *correctly* from a misreading of what the
  problem asks, so the procedure is right for the problem as she understood it,
  it is **comprehension**.
- If a missing or wrong step is procedurally wrong *even under her own correct
  understanding* of what the problem asks, it is **steps**.

This is the execution-under-belief test of the comprehension-versus-operation
entry, applied at the procedure grain rather than the single move. Compressed: a
broken procedure that is the downstream shadow of a misread problem is
comprehension; a broken procedure that is wrong on the student's own correct
reading is steps. Reconstruct the belief first (per the general reconstruction
rule) when the reading is unclear, and apply the same independence test for
genuine co-occurrence: steps is present only if, setting any comprehension error
aside, the procedure is *still* wrong under the student's own reading.

### Comprehension versus principles (conceptual cluster)

Comprehension is about *this specific problem*, what it asks and what its
quantities mean. Principles is about the *general mathematical idea* the problem
rests on (proportionality, conservation, and so on), independent of this
particular wording.

**Deciding question: did the student misread what this specific problem asks, or
fail to grasp the general idea the problem relies on?**

- If she has the wrong picture of *this situation*, it is **comprehension**.
- If she reads the situation correctly but does not understand or apply the
  underlying principle it tests, it is **principles**.

Compressed: comprehension is misunderstanding *this problem*; principles is not
grasping *the idea behind it*.

**Tie-breaker.** When the idea is essentially what the problem is about, so
grasping the principle is inseparable from reading the problem correctly, default
to **comprehension**; principles requires a failure of the general idea that
would show up beyond this one problem's wording, not merely a misreading of this
problem.

### Relevance versus principles (conceptual cluster)

Relevance is about *which pieces of information* the student uses. Principles is
about *the idea that governs how the pieces combine*.

**Deciding question: did the student use the wrong piece of information, or
misunderstand the principle that determines how the pieces combine?**

- If the error is in *selecting* which information to use, it is **relevance**.
- If the error is in understanding the *idea that relates* the information, it is
  **principles**.

Compressed: relevance is *which* information; principles is *the idea relating*
the information.

**Tie-breaker.** If the student chose the right pieces but combined them under a
wrong concept, it is principles; if she grasped the concept but fed it the wrong
pieces, it is relevance.

**Rate and ratio bases.** A misapplied percentage, ratio, or rate often turns on
its *base*, what the stated fraction or rate attaches to. Misunderstanding what
a base is, as a concept, such as not grasping that every sixth customer means
five paid per group of six, is **principles**. Misassigning the base between
stated same-kind candidates, applying a stated rate to the wrong one of two
given quantities, is **relevance** misassignment, per the dimensional-slot
clause. The full routing for a rate applied to the wrong base is ordered, and
is stated once here for landing. First, a failure of the base concept itself,
as above, is principles. Otherwise the ordered provenance test of the
referent-to-derived-base rule governs: two given same-kind candidates are
relevance, as above, and derived involvement on either side routes into the
referent rule's belief arms, comprehension by default and burden of
establishment, or wrong operation where the intact referent belief is
demonstrated in the prefix and the act is an operand pairing slip against it,
the white part scaled on the green amount while the student's own blue
derivation shows the scale grasped (2150).

**The principles-versus-wrong-operation tie-breaker (own-chain demonstration).**
A transportable-concept failure routes by what the deviant act itself
demonstrates. Where the concept is enacted correctly on one component and the
deviant application enacts no coherent alternative rule, a raw multiplication
beside a correctly scaled part, an operand pairing that follows no statable
concept, the act is wrong operation, against her own demonstrated rule, and
the demonstrability burden for a principles belief is unmet. Where the
deviant application itself enacts a demonstrable alternative concept, a ratio
direction inverted, a percentage re-based, sequential percentages flattened
onto one base, the demonstrated-belief pole governs and the thread is
principles even beside correct enactments of the neighbouring concept
elsewhere in the chain: correct work nearby does not immunise a coherent
wrong rule. An alternative concept is demonstrated only where the deviant
act retains the concept's own structure with one component set contrary, the
fraction inverted inside an otherwise intact scaling, the percentage applied
with its structure intact to a re-chosen base, successive percentages
composed with the base held fixed. Mere statability never suffices: any
operand mispairing can be phrased as a rule ("multiply by the ratio
number"), and phrasing an act as a rule is redescription, not demonstration.
An act that abandons the demonstrated concept's structure for a flat
operation, a raw multiplication standing beside a two-step
find-the-factor-then-apply scaling, demonstrates no alternative concept and
is wrong operation. Naming the underlying concept the act offends ("this is really
about proportionality") never routes the family by itself; the route runs
through what the student's own act demonstrates.

**The family routing principle (own-chain demonstration).** The same logic
governs the comprehension boundary. A comprehension thread's belief misstates
what the text says or asks, and the student's acts follow that wrong reading
coherently. Where the student's own labels, definitions, or prefix work
demonstrate the correct reading, an idle correct line computing the very
quantity later mishandled, a component derived correctly and then dropped or
contradicted, the deviant act is an operational fault against her own chain,
however easily a hypothetical misreading could rationalise it. Routing runs
through what her own chain demonstrates, never through what a misreading
could explain: nearly every operational fault can be redescribed as a belief
about the problem, and that redescription is not evidence. Within the
operational cluster the licensed-step discriminator completes the routing:
an excess or misplaced operand inside a licensed construction (a total that
must be formed, a difference that must be taken) is wrong operation, while
an act with no license at all, including any further derivation performed
after the asked quantity already stands produced in her own chain, is steps
unless the act enacts a statable belief of its own.

### Across-cluster pairs (conceptual versus procedural)

The four remaining pairs each set a conceptual family against a procedural one.
All are governed by the cluster boundary test above: **is the working wrong given
what the student believes (procedural), or correct given her belief but built on a
wrong belief (conceptual)?** The entries below add only what is specific to each
pair; the surface-form trap (a conceptual error that *looks* procedural) is the
only reason any of these confuse, and it is handled the same way each time, by
asking whose logic the error is wrong on.

#### Relevance versus wrong operation

Relevance is using the wrong piece of information; wrong operation is combining
correctly chosen quantities with the wrong move or order.

**Deciding question: is the fault in *which* quantity was used, or in *how*
correctly chosen quantities were combined?** Wrong quantity selected is
**relevance**; right quantities combined with the wrong operation is **wrong
operation**. Tie-breaker: if the student used the wrong number but operated on it
correctly, it is relevance; if she used the right numbers but mis-operated, it is
wrong operation. The wrong-number arm is confined to the problem's stated
quantities, per the remit of the dimensional-slot clause; a derived wrong
number routes by the referent-to-derived-base rule and the
derived-and-intermediate-quantities clause, never to relevance. A wrong number that is then mis-operated is relevance for this
family's purposes (the selection error is the cause), with the operation judged
separately only if it is independently wrong under her own reading.

#### Relevance versus steps

Relevance is using the wrong information; steps is a wrong set or order of steps
within a fitting procedure.

**Deciding question: is the fault in *which* information was used, or in the *set
and sequence of steps*?** Wrong information is **relevance**; missing, extra, or
invalidly ordered steps is **steps**. Tie-breaker: a procedure that is complete
and validly ordered but fed the wrong information is relevance, not steps; a
procedure missing a required step is steps even if the information used was
correct.

**The coincident case (which failed first).** The tie-breaker above assumes the
wrong information and the broken procedure are separable, but they can be the
same event: ignoring a piece of information manifests exactly as the step that
would have handled it going missing. Resolve by reconstruction, asking which
failed first.

- **Never registered the information (relevance).** Where the dialogue shows the
  student never registered the piece of information as relevant, the missing
  step is the downstream shadow of the relevance failure, one error, relevance.
  *Worked example (chips dialogue):* asked for the green chips when the rest
  after white and blue are green, the student computes total minus white
  throughout, and the blue chips never enter her account of the remainder. The
  missing subtraction follows from the unregistered information, so the turn is
  relevance, not steps.
- **Registered but omitted (procedural).** Where the student demonstrably has
  the information in her model and the procedure simply omits handling it, the
  omission is procedural. It lands in **steps** when a whole step is absent,
  and in **wrong operation** when the step is present with a term dropped, per
  the missing-operation tie-breaker in the wrong-operation-versus-steps entry.
  *Worked example (Heidi phone dialogue):* asked to inventory the costs, the
  student lists all four items including the phone, then builds a sum with
  three. The information is registered and the term is dropped inside the
  present summing step, which is the operand-omission case, wrong operation.

**Default.** Where reconstruction cannot establish whether the information was
registered, default to **relevance**. The procedural label requires the
demonstrably registered information, per the burden-of-establishment logic of
this section's other defaults, and where registration cannot be shown that
requirement fails.

#### Principles versus wrong operation

Principles is not grasping the governing idea; wrong operation is mis-executing a
single move with the idea intact. The codebook already treats unit conversion and
similar as execution, not principle, which is this boundary.

**Deciding question: does the error show a failure to understand the idea, or a
correct idea wrongly executed in one move?** A misunderstood concept is
**principles**; a understood concept let down by a wrong operation is **wrong
operation**. Tie-breaker: if the student's move is correct *for the principle she
is applying* but the principle is wrong, it is principles; if the principle is
right and only the arithmetic move is wrong, it is wrong operation (per the
cluster test, wrong on her own logic is procedural).

#### Principles versus steps

Principles is not grasping the governing idea; steps is a wrong set or order of
steps with the idea intact.

**Deciding question: does the error show a failure to understand the idea, or a
correct idea carried out with a wrong or missing step?** Misunderstood concept is
**principles**; understood concept with a broken procedure is **steps**.
Tie-breaker: if each step is individually sound but the procedure omits or
misorders steps, it is steps; if the procedure faithfully executes a *wrong*
concept, it is principles (the steps are correct for the wrong idea).




## Specific rules: Family: relevant vs irrelevant information

*Profile wording: difficulty determining which pieces of information are
relevant and which are irrelevant to solving the problem.*

**Boundary index (see Cross-family adjudication):** versus comprehension ("Comprehension versus relevance"); versus principles ("Relevance versus principles"); versus wrong operation ("Relevance versus wrong operation"); versus steps ("Relevance versus steps").

**Wider reading.** The misconception is about relevance in use, not just in
reading, and it concerns pieces of *information*, not only numeric quantities.
A piece of information may be a number, but it may equally be a qualitative
condition, label, relationship, or constraint (for example "works days",
"per dozen", "round trip"). Failing to register which stated condition a
piece of information is attached to is a relevance failure even when a number
is used arithmetically correctly.

- **present:** the student brings in or relies on an irrelevant piece of
  information, ignores a relevant one, or misassigns which stated condition
  or same-kind given a value attaches to, whether the information is a
  numeric quantity or a qualitative condition. This includes using a value attached to one condition
  as if it applied to another (for example treating "70% work days" as the
  fraction who work nights), not only misreading which numbers to pick.
- **absent:** the student correctly identifies which pieces of information are
  relevant, sets aside the irrelevant ones, and uses each in its correct role,
  including registering the conditions a value is attached to.
- **not_evidenced:** the turn does not engage relevance reasoning.

**Key test:** does the turn show a failure to identify which information is
relevant, ignore a relevant piece of information, or misassign which stated
condition or same-kind given a value attaches to, including a qualitative
condition and not only a number?
If yes, present, even if the individual numbers were read and computed
correctly.

**Choosing which form of a quantity to use is a relevance judgment.** Deciding
which form of a given quantity to bring to bear, such as converting 280 days
into 40 weeks before using it, is a relevance judgment about how a piece of
information should enter the problem. A correct such choice engages the
construct and is absent, and using the wrong form (for example dividing by 280
days when the problem is framed in weeks) is present. This applies only when the
choice is substantive, that is when using the wrong form would change which
information is correctly brought to bear. A routine unit conversion with no
bearing on which information matters does not engage the construct and is
not_evidenced, so this note does not turn every arithmetic conversion into a
relevance turn. This rule concerns the problem's *given* quantities; derived
quantities route via the derived-and-intermediate-quantities clause.

**Units and dimensional tracking route via the adjudication clauses.** A failure
to track what a quantity represents dimensionally is no longer labelled here by
default, because the adjudication clauses now own this space. For the problem's
*given* quantities, a quantity placed in a wrong-kind slot is comprehension and
a same-kind confusion is relevance, per the dimensional-slot clause. For
quantities the student *derived*, the derived-and-intermediate-quantities clause
governs, and derived quantities do not take relevance labels at all. The guard
from the older version of this rule still holds and is worth restating: a wrong
operation that incidentally produces bad units stays in the operation or steps
family, since the error there is the move, not the tracking. *Worked example
(Mariana ribbon dialogue, turn 9), re-routed:* the student writes the used
ribbon as 0.7x and then multiplies by x again, giving 0.7x squared. The quantity
0.7x is the student's own derived total in feet, so it falls under the
derived-quantity clause, not this family. Her failure to register what 0.7x
already stands for is a wrong belief about a derived quantity, so the turn
routes to **comprehension**, not relevance. This example was labelled relevance
under the earlier single-family scheme; the routing above supersedes that
labelling for the five-way annotation.

**Boundary with comprehension.** The full treatment of this boundary, including
the misassignment tie-breaker, the dimensional-slot clause, and the James
running worked example, lives in the cross-family adjudication section under
"Comprehension versus relevance". In brief, wrong selection among the problem's
given information is relevance, misreading what a correctly selected piece
represents is comprehension, and kind is checked first, a quantity in a
wrong-kind slot is comprehension while same-kind confusion is relevance
misassignment.

---

## Specific rules: Family: understanding what the problem is asking

*Profile wording: struggles most with understanding what the problem is asking
them to do.*

**Boundary index (see Cross-family adjudication):** versus relevance ("Comprehension versus relevance"); versus principles ("Comprehension versus principles"); versus wrong operation ("Comprehension versus wrong operation"); versus steps ("Comprehension versus steps").

**Wider reading.** Comprehension includes the task's structure as it unfolds,
not just the initial overall goal.

- **present:** the turn shows the student failing to grasp what the task is
  asking, including what to compute now, which quantity represents what, or
  what the question wants at this step.
- **absent:** the student correctly grasps what is being asked, including on a
  decomposed sub-question.
- **not_evidenced:** the turn does not bear on task comprehension. In
  particular, a correct arithmetic sub-step the tutor has walked the student
  through (computing a product or difference the tutor asked for) does not
  engage task comprehension and is not_evidenced, not absent, per the general
  rule above.

**Key test:** does the student misunderstand the task or its structure at this
point? Computing the wrong thing (e.g. what was made instead of what was
consumed, conflating pieces with sandwiches) is present.

**Misreading a described structure is comprehension.** When the problem
describes a structure, such as a tiered discount scheme or a rate relationship,
misreading that structure is a comprehension failure and is present. This is
distinct from errors in executing a correctly understood structure, which belong
to the operation or steps families. The test is whether the student misread what
the problem describes, which is comprehension, or correctly read it and then
mis-executed, which is not. *Worked example (discount dialogue, dialogue 927,
turn 1):* the student frames the saving correctly as original cost minus
discounted cost, and handles the third shirt correctly (computing the $6 as a
discount and pricing the shirt at $4), but her scheme has no second-shirt tier
at all: she pays full price for the first two shirts, so the stated 50%
condition never enters her pricing model. An ignored rule of a described scheme
is a structure misread, not an information-selection failure (see the
ignored-condition test under "Comprehension versus relevance"), so the turn is
present. The correct savings framing and correct third-shirt arithmetic do not
rescue the turn, since the misread scheme is the thing the problem asks the
student to understand. (Her separate percent-complement error, reading $10 x
0.6 as the price rather than the discount, first appears at turn 5 and is
covered by the rate-and-ratio-bases note.)
*Second worked example (tomato dialogue, Brenda profile, turn 1):* the problem
says 3 kilograms of tomatoes were rotten out of a total across three crates, so
the 3 kilograms is a single whole-batch quantity deducted once. The student
deducts 3 kilograms from each crate, computing 20 minus 3 equals 17 per crate
and then 17 times 3 equals 51, which misreads the 3 rotten kilograms as a
per-crate quantity rather than a single total. She grasps the profit goal, but
the per-crate deduction misreads what the problem describes about the rotten
tomatoes, so the turn is present. **A quantity applied at the wrong structural
level is a comprehension misreading, not an operation error.** Applying a
subtraction (or any operation) at the wrong structural level, such as per item
when the problem describes it once for the whole, is a misreading of the
described structure and is comprehension, not a mere operation or steps slip. The
tell is that the student has misunderstood how the quantity relates to the
structure, per crate versus per total, rather than choosing a wrong operation
between correctly understood quantities. Do not misfile this as an operation
error because the surface form is an arithmetic step; the error is in what the
student thinks the quantity applies to.

**Goal misreading is comprehension (scope errors).** Misreading *which quantity
the problem asks for* is a comprehension failure, and it includes carrying the
solution beyond the asked for quantity and presenting an out of scope quantity
as the goal. A student who computes the asked for quantity and treats it as the
answer has read the goal correctly and is absent, even if she then mentions a
further figure she clearly marks as incidental. A student who presents an out of
scope quantity as her answer has misread what the problem asks her to produce,
so the turn is present. This rule originated as scope misrecognition under the earlier six-family
scheme's problem-type category; it belongs here because presenting an out of
scope quantity as the answer is a failure to read what the problem asks.
*Worked example (Alejandra kombucha dialogue, turn 1):* the question asks how
many bottles the refund money buys, which is 6, and the student correctly
derives the 6 but then carries on to compute the year's total of 186 and
presents 186 as her answer. Presenting the out of scope total as the goal
reveals she misread the asked for quantity, a total bottles reading of a refund
funded bottles question, so the turn is present, judged on the misread goal and
not on the wrongness of 186. The same pattern covers reporting a remaining
amount where the taken amount is asked, leftovers where consumed is asked, and a
final state where a sum of stages is asked.

**Resolving versus restating a stated relationship.** Absent requires the
student to resolve an interpretation the problem did not already spell out, such
as deciding what an ambiguous quantity refers to, choosing what to compute at a
step, or recognising how a relationship applies when the problem did not state
it plainly. Restating a relationship the problem gives directly and then
computing it is execution, not comprehension, and is not_evidenced even when the
restatement is correct. This mirrors the selecting-versus-executing line in the
operation families. *Worked example (Mariana TV dialogue, turn 4):* asked how
long Mike plays on a video game day, the student restates the problem's own
wording that he plays half as long as he watches TV and computes 4/2 = 2. The
student resolved no unstated interpretation, so the turn is not_evidenced, not
absent.

**Not re-committing an error is not comprehension.** A turn that applies a
stated rate or operation to an already-corrected figure, and simply does not
reintroduce the misconception, has not thereby engaged the construct. This is
especially so when the correcting figure was supplied by the tutor upstream
rather than derived by the student. Producing a result free of the error is not
the same as demonstrating the understanding that avoids it, so such a turn is
not_evidenced unless the student performs the comprehension step themselves in
that turn. *Worked example (Emberly walking dialogue, dialogue 44, turn 7):*
the tutor supplied the corrected figure of 27 days, and the student then
computes 27 hours times the stated 4 miles per hour to reach 108. The
comprehension step, excluding the missed days, happened upstream in the tutor's
question, so turn 7 executes a stated rate on a corrected input without
demonstrating the understanding itself, and is not_evidenced.

---

- **Fabricated scenario assumptions are comprehension.** Assumptions invented
  with no textual basis, a slower second half where the problem states none,
  a rate imported from the other trail, are wrong beliefs about the situation
  and label comprehension when enacted (the trails dialogue, 2063, turn 6).
- **Unit conversions applied to quantities already in the target unit default
  to comprehension.** The intact-unit belief that would make the conversion a
  mere momentum slip is rarely demonstrable in the prefix, so burden of
  establishment governs (the fabric dialogue, 609).

## Specific rules: Family: underlying ideas and principles, and recognition of when to apply them

*Profile wording: problem with understanding of underlying ideas and principles
and a recognition of when to apply them.*

**Boundary index (see Cross-family adjudication):** versus comprehension ("Comprehension versus principles"); versus relevance ("Relevance versus principles"); versus wrong operation ("Principles versus wrong operation"); versus steps ("Principles versus steps").

**Conceptual construct.** Tracks grasp of the principle at work and knowing
when to apply it.

- **present:** the turn shows the student failing to grasp or apply the
  relevant underlying principle (e.g. not recognising that "equal length" plus
  "sum is 120" requires halving).
- **absent:** the student correctly grasps and applies the principle.
- **not_evidenced:** the turn does not engage a principle.

**Notes:** unit conversion is treated as execution, not principle (so
forgetting to convert is not this misconception). The tutor-supplied-answer
rule is central for this family.

**Selecting the operation when the tutor names only a rate or operand.**
Recognising which operation to apply, when the tutor has stated a rate or an
operand but has not named the operation, is applying the principle and is
**absent**, not not_evidenced. Stating a quantity is not the same as dictating
what to do with it. For example, if the tutor says "with 400 bricks per course,
how many bricks is this?" without saying "multiply", and the student recognises
unprompted that the per-course rate must be multiplied by the course count, the
student is applying the underlying principle, so the turn is absent. The turn
would be not_evidenced only if the tutor had named both the operation and its
operands so the student merely executed a fully specified calculation. The
stated-content boundary, including that a named operand counts as supplied
only when its value is literally stated and not merely its referent, is
defined once under "What counts as dictating" in the general rules; that
clause governs here.

**Stating a component figure the tutor asked for does not engage the principle.**
Computing or stating a component quantity the tutor asked for, such as a weekly
subtotal or an intermediate sum, does not engage the underlying principle unless
the student applies the principle to it. Answering a narrow factual question
about one component is execution, not principle application. For example, when
the tutor asks how many were bought in week one and the student answers
10 + 5 = 15, the student states a component figure without applying any
underlying idea, so the turn is not_evidenced. This is the principles-family
counterpart of the sub-step rule, and it keeps absent reserved for turns where
the student actually applies or selects the principle rather than reporting a
figure the tutor requested.

---

## Specific rules: Family: steps or procedures required to solve a problem

*Profile wording: problem with understanding of what steps or procedures are
required to solve a problem.*

**Boundary index (see Cross-family adjudication):** versus wrong operation ("Wrong operation versus steps"); versus comprehension ("Comprehension versus steps"); versus relevance ("Relevance versus steps"); versus principles ("Principles versus steps").

**Procedural construct.** Tracks whether the student knows what steps to take
and in what sequence.

- **present:** the turn shows the student not knowing which steps the chosen
  approach requires, omitting a required step, including a step the procedure
  does not need, or sequencing steps invalidly (e.g. omitting the original frogs from the
  pond total, per the frog pond worked example below). Feeding the wrong
  quantity into an otherwise correct step is not a steps error: operand
  selection within a step belongs to wrong operation, and misused derived
  quantities route via the derived-and-intermediate-quantities clause.
- **absent:** the student engages the correct procedural steps.
- **not_evidenced:** the turn engages no step or procedure, including a bare
  arithmetic yes/no affirmation with no procedure chosen or sequenced.

**Defining distinctions:**
- A turn that engages the correct procedure but botches the arithmetic is not
  present (the misconception is about steps, not execution).
- Distinct from strategy selection: a wrong overall approach is not this
  family but routes to its conceptual source (see "Strategy errors route to
  their conceptual source"); this family is about the steps and their order
  within the approach.
- Restating a figure is not advancing a step. Engaging the procedure requires
  the turn to perform or advance a step of the solution. Merely restating a
  correct intermediate figure, or a fact about the setup, does not by itself
  engage the procedure and is not_evidenced unless the turn carries the step
  forward. *Worked example (Scott race dialogue, turn 2):* asked to think about
  the halfway point, the student restates that each car goes from three
  passengers and one driver to four, an occupancy fact, without performing or
  advancing a step of the solution, so the turn is not_evidenced, not absent.
  The correct halfway calculation lived in an earlier turn, not in this
  restatement.
- A valid reordering of the required steps is absent, not present. This family
  judges whether the student includes all the steps the procedure requires and
  whether the logic is valid, not whether the steps are performed in a canonical
  order. If the student includes every required step and the logic is sound, a
  different but algebraically valid ordering is a correct procedure and is
  absent. Do not mark a turn present merely because the sequence differs from the
  standard one. *Worked example (frog pond dialogue, Ronny profile, turn 2):* the
  standard procedure adds the 5 original frogs to the 10 matured frogs to get 15,
  then subtracts the pond capacity of 8 to get 7. The student instead subtracts
  the capacity from the matured frogs, 10 minus 8 equals 2, then adds the 5
  original frogs to that surplus to get 7. This is the same computation reordered
  (10 minus 8 plus 5 equals 5 plus 10 minus 8), so every required step is present
  and the logic is valid, and the turn is absent. This contrasts with turn 1,
  where the student omitted the original frogs entirely, so a required step was
  missing and the turn was present. The distinction is a missing step, which is
  present, versus a reordered but complete procedure, which is absent.

---

- **Valid rearrangements are never penalised.** An algebraically equivalent
  reordering of a correct route, adding the retained five to the overflow
  rather than to the population before subtracting (1966, turn 2), is the
  valid-reordering rule applied, absent, not a route error.

## Specific rules: Family: wrong operation or operand order

*Profile wording: struggles to put the numbers in the correct order in the
equation or determine the correct operation to use.*

**Boundary index (see Cross-family adjudication):** versus steps ("Wrong operation versus steps"); versus comprehension ("Comprehension versus wrong operation"); versus relevance ("Relevance versus wrong operation"); versus principles ("Principles versus wrong operation").

**Within-step construct.** Tracks the correctness of the operation and the
placement of operands within a step.

- **present:** the turn shows the student using the wrong operation, arranging
  operands wrongly within a step, or omitting a term her own model of the
  problem includes (per the operand-omission rule below, e.g. omitting a
  category from a sum she knows belongs there). Relabelling a computed quantity
  as a different category (e.g. labelling the tennis-ball computation as soccer
  balls) is no longer labelled here by default: it routes via the
  derived-and-intermediate-quantities clause in the adjudication section, and
  lands in this family only when that clause's belief test establishes intact
  beliefs with a bookkeeping fault.
- **absent:** the student selects the correct operation and places the operands
  correctly, including when a tutor question prompts toward an operation without
  naming it (e.g. the tutor asks "how many trips is that?" and the student
  chooses to divide 28 by 4 and orders it correctly). What matters is that the
  student still had to select the operation or arrange the operands.
- **not_evidenced:** the turn engages no operation or operand assignment, *or*
  the tutor has handed the student the operation and the operands explicitly
  enough that nothing is left to select or order (e.g. the tutor says "divide
  28 by 4"). When the operation and its operand order are both supplied by the
  tutor, the student's correct execution does not engage the construct and is
  not_evidenced.

**Selecting versus executing (this family's key discrimination).** The line
between absent and not_evidenced is how much the tutor supplied. If the student
selects the operation or arranges the operands themselves, correct work is
absent and incorrect work (wrong operation, wrong operands, or wrong order) is
present. If the tutor states both the operation and the operands so the student
only executes a fully specified calculation, the turn is not_evidenced. A tutor
who supplies an operand but not the operation (e.g. "he needs another 30
seconds per trip, so that gives what?") still leaves the operation selection to
the student, so correct work there is absent, not not_evidenced. The same test
applies in the principles family, where selecting an operation the tutor named
only a rate or operand for is applying the principle and is absent. The
stated-content boundary this test applies, including that a named operand
counts as supplied only when its value is literally stated and not merely its
referent, is defined once under "What counts as dictating" in the general
rules; that clause governs here.

**Assembling versus describing (what passes the engagement gate).** For this
family the engagement gate is passed only when the student assembles operands
or selects an operation. It is not passed when the student describes, counts, or
restates something about an expression. Reporting how many addends an expression
contains, or naming which operands are present, is a description of the
equation, not an act of assembling it, so such a turn is not_evidenced even when
the description is accurate. *Worked example (Heidi phone dialogue, turn 5):*
asked how many items were summed in "100 + 200 + 2400", the student answers that
three items were summed and names them. This is counting and naming the operands
already present, not assembling or arranging them, so the turn is not_evidenced.
The turn that omits an operand while building the sum, and the turn that later
reinserts it, do engage the construct and are labelled present and absent
respectively.

**An omission driven by a wrong understanding is not an operand omission.** An
operand omission is a wrong operation error only when the student drops a term
that her own model of the problem includes, as in the Heidi phone case where the
student understood the phone had a cost and simply failed to add it. When the
student leaves out a term because she has misunderstood whether that term applies
at all, the omission is a downstream consequence of a comprehension error, not an
operand omission, and it does not fall under this family. The test is whether the
equation is wrong on the student's own logic, which is an operand omission, or
correct on her own logic but built on a wrong understanding of the problem, which
is comprehension. *Worked example (Winnie deduction dialogue):* the student
computes the pay as 9 windows times $2 and applies no deduction, because she
believes the deduction only starts after a threshold of days that was not
reached. Her equation is the correct equation for the problem as she understands
it, so no term her model includes is missing. The error is her misreading of the
deduction rule, which is comprehension, so the missing deduction is not an
operand omission and the turn is not_evidenced for this family.

**Boundary with steps/procedures:** steps/procedures is about *which* steps and
in what *sequence*; this family is narrower, about the correctness of the
operation and operand order *within* a step. Right step but wrong
operation/operand placement is this family; not knowing which step to do, or
wrong sequencing, is steps/procedures.

---

- **Conclusion-direction errors are within-move.** A correct computation
  whose conclusion assigns the result to the wrong party or direction, the
  head start awarded to the runner who is faster on the accepted premise (96,
  turn 8), is a wrong move at the point of assignment, wrong operation, not a
  conceptual error, provided the premise it operates on was accepted rather
  than misread.

## Pending / unmatched profiles

These five families cover the core family map, and every turn is labelled for
all five regardless of the dialogue's profile metadata. If a dialogue's profile
wording does not clearly match one of the five above, do not force a mapping:
flag it and settle its reading on a real dialogue, the same way each of the
above was settled.