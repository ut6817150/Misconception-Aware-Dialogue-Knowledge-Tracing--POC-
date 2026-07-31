# Proposal: Use the Student's Initial Solution as Context for BKT

## Document status

This document describes the recommended next experiment for adding
misconception evidence to Bayesian Knowledge Tracing (BKT).

It is a design proposal, not a claim that the model has already been
implemented. Its purpose is to make the intended experiment understandable and
auditable before code is written.

The central recommendation is:

> Use the misconception annotations from the student's initial incorrect
> solution to adjust BKT's initial mastery belief. Do not turn that solution
> into an ordinary incorrect BKT response.

The main scientific comparison should be between:

1. the proposed model with the real solution annotations; and
2. the same model with the solution evidence neutralized.

This gives the two models the same data population, prediction targets,
architecture, and evaluation rules. The only meaningful difference is whether
the misconception evidence is available.

---

## 1. The problem we are trying to solve

MathDial provides an incorrect solution before the tutoring dialogue begins.
That solution can contain rich evidence about what the student:

- understands;
- misunderstands;
- can execute correctly;
- has not demonstrated at all.

The original BKT pipeline in
`extension/notebooks/03_bkt_original.ipynb` does not use the solution as a BKT
observation. Its first observations are the usable, KC-tagged student responses
inside the tutor–student dialogue.

Notebook `extension/notebooks/04_bkt_baseline.ipynb` tested a simple way of
including the solution:

- create a synthetic solution turn;
- attach the union of all KCs later found in the dialogue;
- mark every one of those KC observations as incorrect.

That experiment was useful, but it makes a very strong assumption:

> Every KC that occurs anywhere in the dialogue was attempted incorrectly and
> simultaneously in the initial solution.

The results suggest that this assumption is too strong. It forced every fitted
KC prior to the lower boundary and reduced accuracy and AUC, even though F1
rose because the model began predicting the positive class much more often.

The lesson is not that the initial solution is unhelpful. The lesson is that
the solution should not be represented as a collection of ordinary false
responses.

### Current result that motivates this proposal

The completed baselines currently give:

| Evaluation | Model | Accuracy | AUC | F1 |
| --- | --- | ---: | ---: | ---: |
| All usable real turns | Notebook 03 original BKT | 0.5980 | 0.6278 | 0.5571 |
| All usable real turns | Notebook 04 false-union solution BKT | 0.5312 | 0.5843 | 0.5936 |
| Paper-matched R2+ | Notebook 03 original BKT | 0.6050 | 0.6402 | 0.5556 |
| Paper-matched R2+ | Notebook 04 false-union solution BKT | 0.5088 | 0.5640 | 0.6064 |
| Paper-reported MathDial BKT | Published result | 0.6071 | 0.6419 | 0.5671 |

Notebook 04's higher F1 does not overturn the conclusion from accuracy and AUC.
Its positive prediction rate rose sharply, increasing recall for the positive
class while making the model worse at overall classification and ranking.

This is why the next experiment should represent the solution differently
rather than merely discarding it.

---

## 2. The proposed interpretation of turn 0

The initial solution, called **turn 0** or **S0** in this document, should be
treated as **contextual evidence about the student's starting state**.

It should not be treated as:

- a correct response;
- an incorrect response for every dialogue KC;
- a learning opportunity;
- a scored prediction target;
- an extra chronological response in the BKT sequence.

The intended timeline is:

| Stage | Information available | What the model does |
| --- | --- | --- |
| S0 | Problem and student's initial solution | Adjust the initial mastery belief using misconception annotations |
| R1 | First usable tagged dialogue response | Predict correctness, observe correctness, and update BKT state |
| R2 | Second usable tagged dialogue response | Predict correctness from the updated state, then update again |
| R3+ | Later usable tagged responses | Continue the normal BKT cycle |

This interpretation fits the temporal meaning of the data:

- the solution exists before tutoring starts;
- it provides evidence about initial knowledge;
- it does not itself prove that learning occurred between S0 and R1.

---

## 3. A short introduction to standard BKT

### 3.1 What BKT is estimating

For each knowledge component (KC), standard BKT assumes that a student is in
one of two hidden states:

- **not mastered**;
- **mastered**.

The true state is hidden. Correct and incorrect responses provide imperfect
evidence about it.

The four parameters in the current no-forgetting implementation are:

| Parameter | Symbol | Plain-language meaning |
| --- | --- | --- |
| Prior | \(\pi_k\) | Probability that KC \(k\) is mastered before its first observed response |
| Learning | \(T_k\) | Probability of moving from not mastered to mastered after an opportunity |
| Guess | \(G_k\) | Probability of a correct response while not mastered |
| Slip | \(S_k\) | Probability of an incorrect response while mastered |

There is no forgetting parameter in the current baseline. Once the latent
state becomes mastered, it remains mastered.

### 3.2 How BKT predicts correctness

If the current probability of mastering a KC is \(L\), then the probability of
a correct response is:

\[
P(Y=1)
=
L(1-S_k) + (1-L)G_k.
\]

This equation combines two ways a correct answer can occur:

- the student has mastered the KC and does not slip;
- the student has not mastered the KC but guesses correctly.

After the real response is observed, BKT applies Bayes' rule to update the
mastery probability. It then applies the learning transition before the next
opportunity.

For a correct observation:

\[
L_{\text{post}}
=
\frac{L(1-S_k)}
{L(1-S_k)+(1-L)G_k}.
\]

For an incorrect observation:

\[
L_{\text{post}}
=
\frac{LS_k}
{LS_k+(1-L)(1-G_k)}.
\]

The learning transition is then:

\[
L_{\text{next}}
=
L_{\text{post}}+(1-L_{\text{post}})T_k.
\]

The important ordering is:

1. predict the response from the current state;
2. observe the real response;
3. update the state using that response;
4. apply the learning transition for the next opportunity.

### 3.3 What changes in the proposed model

The proposed model leaves the normal BKT response process unchanged:

- the same real correctness observations are used;
- the same learning, guess, and slip mechanisms are used;
- the same per-KC state updates are used.

Only the **starting mastery probability** changes. It becomes dependent on the
misconception evidence found in S0.

---

## 4. The contextual-prior model

### 4.1 Core equation

Let:

- \(d\) identify a dialogue;
- \(k\) identify a KC;
- \(\pi_k\) be the ordinary starting prior for KC \(k\);
- \(x_{d,0}\) be the misconception features extracted from the initial
  solution in dialogue \(d\);
- \(\beta\) be the learned effect of those features.

The contextual starting prior is:

\[
P(L_{d,k,0}=1 \mid x_{d,0})
=
\sigma\left(
\operatorname{logit}(\pi_k) + \beta^\top x_{d,0}
\right),
\]

where:

\[
\operatorname{logit}(p)=\log\left(\frac{p}{1-p}\right)
\]

and:

\[
\sigma(z)=\frac{1}{1+e^{-z}}.
\]

The logit transformation allows the model to add evidence while ensuring that
the final probability remains between 0 and 1.

### 4.2 Recommended feature encoding

The misconception annotation codebook gives each of five families one of
three labels:

- `present`;
- `absent`;
- `not_evidenced`.

The five families currently represented in the formatted data are:

1. comprehension;
2. relevance;
3. principles;
4. wrong operation;
5. steps.

The recommended first implementation gives `present` and `absent` separate
effects:

\[
\operatorname{logit}(\pi_{d,k})
=
\operatorname{logit}(\pi_k)
+
\sum_f
\left[
a_f I(x_{d,f}=\text{absent})
-
b_f I(x_{d,f}=\text{present})
\right],
\]

subject to:

\[
a_f \ge 0,\qquad b_f \ge 0.
\]

Here:

- \(f\) is a misconception family;
- \(a_f\) measures how much sound handling of that construct raises the
  starting mastery belief;
- \(b_f\) measures how much an exhibited misconception lowers it;
- `not_evidenced` contributes zero.

This produces ten learnable effect sizes: an `absent` effect and a `present`
effect for each of the five families.

### 4.3 Why use this encoding

This encoding preserves the meaning of the codebook:

| Label | Meaning | Recommended prior effect |
| --- | --- | --- |
| `present` | The construct was engaged and the misconception was exhibited | Lower the initial mastery estimate |
| `absent` | The construct was engaged and handled soundly | Raise the initial mastery estimate |
| `not_evidenced` | The construct was not demonstrated in this solution | Make no change |

Several details matter:

- `absent` does **not** mean the whole solution is correct. A known-incorrect
  solution can still handle one construct soundly while failing elsewhere.
- `not_evidenced` does **not** mean the misconception is absent. It means there
  was no usable evidence for that construct.
- The sign constraints encode the definitions of the labels. They prevent a
  small or noisy sample from learning that a demonstrated misconception should
  increase mastery.
- The magnitudes remain learned from the training data. We are not manually
  deciding how strongly each family should matter.

If the constraints prove too restrictive, an unconstrained version can be
reported as a sensitivity analysis. It should not be the first model because it
is less stable and harder to interpret.

---

## 5. What “neutral evidence” means

Neutral evidence means that the contextual feature vector is set to zero:

\[
x_{d,0}=\mathbf{0}.
\]

The contextual term then disappears:

\[
P(L_{d,k,0}=1 \mid x_{d,0}=\mathbf{0})
=
\sigma(\operatorname{logit}(\pi_k))
=
\pi_k.
\]

The model therefore starts from the ordinary BKT prior.

Neutral evidence does **not** mean:

- “no misconception is present”;
- all five families are `absent`;
- the solution is correct;
- the solution is incorrect;
- an artificial response is added;
- the dialogue is removed.

It means only:

> The model is deliberately prevented from using the S0 misconception
> annotations.

### Neutral evidence versus `not_evidenced`

These concepts are related but not identical:

| Term | Level | Meaning |
| --- | --- | --- |
| `not_evidenced` | One annotation family | The solution did not engage that particular construct |
| Neutral experimental condition | Whole model input | All S0 misconception features are hidden from the model |

Operationally, a `not_evidenced` family contributes zero. In the neutral
condition, all families contribute zero regardless of their real labels.

### Worked numerical example

Suppose a KC has an ordinary prior of:

\[
\pi_k=0.30.
\]

Assume a relevant `present` label has learned weight \(b_f=0.80\), while an
`absent` label has learned weight \(a_f=0.40\).

Approximate contextual priors would be:

| S0 evidence | Calculation on log-odds | Contextual prior |
| --- | --- | ---: |
| Neutral or `not_evidenced` | \(\operatorname{logit}(0.30)\) | 0.300 |
| `present` | \(\operatorname{logit}(0.30)-0.80\) | 0.161 |
| `absent` | \(\operatorname{logit}(0.30)+0.40\) | 0.390 |

If \(G_k=0.20\) and \(S_k=0.10\), the predicted probability of a correct first
response would be approximately:

| S0 evidence | Starting mastery | Predicted correctness |
| --- | ---: | ---: |
| Neutral | 0.300 | 0.410 |
| `present` | 0.161 | 0.313 |
| `absent` | 0.390 | 0.473 |

No artificial correctness label was required for S0. Its annotation changed
the belief from which the real response was predicted.

---

## 6. Why the original BKT is still relevant—but not the only comparison

There are two different meanings of “baseline” in this project.

### 6.1 Historical reference

Notebook 03 is the historical, paper-aligned reference:

- it shows how close the local reproduction is to the paper;
- it uses only real dialogue responses;
- it defines the established filters and evaluation contract;
- it provides the fitted correctness-only BKT parameters.

It should remain in result tables because readers need continuity with the
paper.

### 6.2 Aligned experimental control

The main control for the proposed model should use:

- the same contextual-BKT code path;
- the same retained dialogues;
- the same real observations;
- the same parameters and fallback rules;
- the same prediction masks;
- but \(x_{d,0}=\mathbf{0}\).

This is the **neutral contextual control**.

If the ordinary BKT parameters are loaded from notebook 03 and held fixed, the
neutral control should reproduce notebook 03 predictions exactly, apart from
machine-level floating-point tolerance. That equality should be an explicit
test.

The main effect of interest is:

\[
\text{actual S0 evidence}
-
\text{neutral S0 evidence}.
\]

This answers:

> Does the information in the initial-solution misconception annotations
> improve predictions, when everything else is held constant?

### 6.3 Why notebook 04 is not the primary baseline

Notebook 04 remains useful as a negative-control ablation. It asks a different
question:

> What happens if the solution is treated as an incorrect response on every KC
> in the dialogue-wide KC union?

Its answer was that this representation is too strong for the standard BKT
parameterization. It should be reported, but it should not define the main
comparison for a contextual misconception model.

---

## 7. Recommended comparison table

The final experiment should report at least the following systems:

| ID | System | How S0 is used | Purpose |
| --- | --- | --- | --- |
| P | Paper-reported BKT | Not used | Published external reference |
| B03 | Notebook 03 effective BKT | Not used | Local historical reference |
| C0 | Contextual BKT, neutral input | Features set to zero | Main aligned control |
| C1 | Contextual BKT, actual input | Real S0 misconception labels | Proposed model |
| N04 | Notebook 04 solution baseline | False response on dialogue-wide KC union | Strong naive ablation |
| S | Contextual BKT, shuffled input | S0 features assigned to the wrong training dialogues | Information sanity check |

The primary comparison is **C1 versus C0**.

Other comparisons answer secondary questions:

- **B03 versus P:** how closely the local baseline matches the paper.
- **C0 versus B03:** whether the new implementation preserves the old
  correctness-only behavior.
- **N04 versus C0:** whether contextual evidence is better than a false
  pseudo-response.
- **C1 versus S:** whether real dialogue-to-solution alignment matters, rather
  than merely adding features or model capacity.

The shuffle test should be implemented as a repeated permutation test:

1. shuffle whole S0 feature vectors among training dialogues and fit the context
   weights;
2. independently shuffle whole S0 feature vectors among test dialogues for the
   declared negative-control evaluation;
3. preserve the number of dialogues and the marginal frequency of every label;
4. repeat with recorded seeds to form a null distribution.

The real, unshuffled test remains the primary evaluation. The shuffled
evaluation is reported separately and is never used to tune the real model.

---

## 8. Data preparation contract

### 8.1 Annotate first, filter for modelling second

Misconception annotation and BKT population filtering serve different
purposes.

The recommended pipeline is:

1. Format and annotate **all** available train and test dialogues.
2. Freeze the annotation prompt and codebook before evaluating the model.
3. Apply the paper's BKT filters when constructing the BKT training and test
   populations.

Annotating all data preserves future flexibility. It does not mean that every
dialogue must enter the paper-matched BKT experiment.

### 8.2 Keep the paper's real-turn filters

For the contextual model, retain notebook 03's filtering order:

1. Start from the fixed MathDial train and test splits.
2. Apply the typical-confusion and typical-interaction threshold of at least 1.
   This is a no-op on the released annotated data, but remains part of the
   declared contract.
3. Remove dialogues with failed original ATC annotations.
4. Exclude real turns without both:
   - a usable correctness value; and
   - at least one KC.
5. Apply the final tagged-turn correctness override from
   `self-correctness`.
6. Retain dialogues with at least **two usable tagged real turns**.
7. Expand each retained real turn into one pseudo-observation per KC.

### 8.3 Why the minimum is two real turns, not three units

Notebook 04 required three tagged units:

- one synthetic solution unit;
- at least two real tagged responses.

That rule was appropriate because notebook 04 represented S0 as a response
inside the BKT sequence.

In the proposed model, S0 is context rather than an observation. It is not
counted as a tagged response. Therefore, the rule returns to:

> Keep dialogues with at least two usable tagged **real** turns.

This preserves the notebook 03 population:

- 2,050 training dialogues;
- 515 test dialogues.

### 8.4 Do not use the dialogue-wide solution KC union

The S0 rows currently exported by notebook 00 can contain the union of KCs
found across the entire later dialogue. That union was created for the
retrospective notebook 04 experiment.

The contextual model does not need that union.

For each real KC sequence, the model can combine:

- the ordinary prior for the KC being predicted; and
- the five-family S0 misconception feature vector.

This avoids claiming that the student attempted every later KC in S0, and it
avoids using future KC occurrence as a feature at turn 0.

### 8.5 What S0 annotations are allowed to see

The S0 annotation must be based only on:

- the problem;
- the student's initial solution.

It must not use:

- later tutor messages;
- later student responses;
- final dialogue correctness;
- future KC annotations;
- the dialogue-wide KC union.

This matches the causal-scope rule in the annotation codebook and makes the
features available at the moment the initial solution is submitted.

---

## 9. How S0 context attaches to per-KC BKT sequences

BKT is fitted separately by KC. One dialogue can therefore contribute several
KC histories.

Suppose a dialogue has this real-turn structure:

| Real turn | Tagged KCs | Correct |
| --- | --- | --- |
| R1 | Fractions, Division | False |
| R2 | Fractions | True |
| R3 | Ratios | True |

The model creates these KC histories:

- Fractions: `[False, True]`;
- Division: `[False]`;
- Ratios: `[True]`.

The same S0 misconception feature vector is available when initializing each
history, but each history begins from its own KC prior:

\[
\pi_{\text{Fractions}},
\quad
\pi_{\text{Division}},
\quad
\pi_{\text{Ratios}}.
\]

The contextual adjustment is applied once, at the start of each
`(dialogue, KC)` history. It is not re-applied at every response.

When a true turn contains several KCs, the model:

1. predicts a correctness probability for each KC before observing the
   response;
2. averages the KC probabilities into one true-turn probability;
3. scores that true-turn probability;
4. updates each involved KC using the observed real correctness value.

This retains the paper's pseudo-turn expansion and turn-level averaging.

### Limitation of the first version

The five misconception-family labels are dialogue-level context. They do not
provide a validated mapping from a specific misconception family to a specific
ATC KC.

The first implementation should therefore use misconception effect weights
shared across KCs. This is intentionally conservative:

- it uses far fewer parameters;
- it is less likely to overfit rare KCs;
- it works for degenerate and unseen KCs;
- it does not invent a family-to-KC mapping that the data does not contain.

The trade-off is that a misconception label can shift the starting belief for
all KCs present in that dialogue's real histories. A later hierarchical or
target-aware model can relax this assumption after the shared-effect model has
been evaluated.

---

## 10. Recommended fitting strategy

### 10.1 Phase 1: freeze ordinary BKT, learn only context effects

The first implementation should:

1. load or reproduce the notebook 03 BKT parameters;
2. freeze each KC's prior, learning, guess, and slip parameters;
3. learn only the ten S0 context weights;
4. use only training-split real responses in the likelihood.

This is recommended because it isolates the new idea. If all BKT parameters and
context weights are jointly refitted immediately, a change in performance
could be caused by:

- the misconception evidence;
- different BKT parameters;
- a different local optimum;
- interactions between the two.

Freezing the ordinary parameters makes the first result easier to interpret:

> Any prediction change comes from changing the initial mastery belief with
> S0 evidence.

### 10.2 How the context weights receive a learning signal

S0 does not need its own correctness target.

The context weights are learned from how well they help predict the subsequent
real responses. In simplified form:

1. the S0 labels adjust the initial mastery prior;
2. that prior determines the predicted probability of R1;
3. the observed correctness of R1 contributes to the likelihood;
4. later responses also contribute after ordinary BKT updates;
5. optimization changes the context weights to improve the training
   likelihood.

The model therefore learns whether a solution annotation is useful by testing
whether it predicts future real behavior.

### 10.3 Regularization

Even ten parameters can overfit when some labels are uncommon. Apply L2
regularization:

\[
\mathcal{J}(\beta)
=
-\log P(Y_{\text{train}}\mid X_{\text{train}},\beta)
+
\lambda\|\beta\|_2^2.
\]

In plain language:

- the first term rewards fitting the real training responses;
- the second discourages unnecessarily large context effects;
- \(\lambda\) controls the strength of that penalty.

Choose \(\lambda\) using group-based cross-validation inside the training
split, grouping by dialogue so that rows from one dialogue never occur in both
the fitting and validation folds.

Do not choose \(\lambda\) from test performance.

### 10.4 Restarts and reproducibility

The contextual optimization should use:

- a fixed, recorded random seed;
- several deterministic restarts if the optimizer is not globally convex in
  the implemented parameterization;
- a declared convergence tolerance;
- a declared maximum iteration count;
- selection by training objective within each fold, not by closeness to the
  paper's test metrics.

The notebook should report whether different restarts converge to materially
different weights.

### 10.5 Phase 2: joint fitting only as an ablation

After Phase 1 is understood, a second version may jointly estimate:

- BKT parameters;
- context effects.

This should be reported as a separate model, not silently substituted for the
frozen-parameter model.

Joint fitting may improve likelihood, but it introduces more identifiability
and optimization risk. For example, the model might trade a lower KC prior
against a larger positive context effect without changing predictions very
much.

---

## 11. Degenerate and unseen KCs

Notebook 03 uses an observation-count-weighted average parameter vector when a
KC:

- is all correct in training;
- is all incorrect in training;
- is not seen during training.

The contextual model should preserve that policy.

For a fallback KC:

1. start from the weighted fallback BKT prior;
2. apply the same shared S0 context adjustment;
3. use the fallback learning, guess, and slip values;
4. perform normal sequential prediction and updating.

This is preferable to inserting a fixed correctness probability because the
fallback history still responds to observed real answers.

The notebook must report:

- number of individually fitted KCs;
- number of degenerate training KCs;
- number of unseen test KCs;
- number and percentage of fallback pseudo-observations;
- fallback parameter values.

---

## 12. Missing or failed misconception annotations

`not_evidenced` is a valid annotation. A missing annotation is a technical data
problem. They must not be confused.

Recommended policy:

1. Attempt to produce complete S0 annotations for all dialogues before model
   fitting.
2. Validate that every S0 row has one allowed label for every family.
3. If an annotation is still missing or failed:
   - keep the dialogue if it otherwise passes the paper's BKT filters;
   - use neutral S0 evidence for that dialogue;
   - record a `context_available=False` audit flag;
   - report missingness separately for train and test.
4. Report a complete-annotation sensitivity analysis in addition to the
   full-population result if missingness is nonzero.

Keeping the dialogue preserves population comparability. Neutral fallback also
avoids inventing a misconception label.

The model must never convert a blank cell to `absent`.

---

## 13. Evaluation protocols

All predictions must be generated before the current response is observed.

### 13.1 All real turns

| Item | Rule |
| --- | --- |
| State initialization | S0 context adjusts the prior |
| Scored responses | R1 and all later usable tagged real responses |
| State updates | Every scored response updates its KCs after prediction |

This protocol measures the model's usefulness across the complete real
dialogue. It is especially important because R1 is where S0 should have its
strongest direct effect.

### 13.2 Paper-matched evaluation

| Item | Rule |
| --- | --- |
| State initialization | S0 context adjusts the prior |
| First real response | R1 is predicted and then used as a state update, but is not scored |
| Scored responses | R2 and later usable tagged real responses |

This matches the paper's removal of the first tagged real turn from metrics.
S0 is not “removed” from scoring because it was never a response target in the
first place.

### 13.3 First-real-turn diagnostic

Report R1 alone as a diagnostic:

- it tests the point at which S0 context should matter most;
- it has not yet been diluted by a real correctness update;
- it helps distinguish a useful initial prior from later BKT dynamics.

R1-only results are supplementary and should not replace the paper-matched
headline metrics.

### 13.4 Metrics

Retain the paper's metrics:

- accuracy using `np.round`;
- ROC AUC;
- binary F1 with correct (`1`) as the positive class.

Also add probability-sensitive metrics:

- log loss;
- Brier score;
- optionally, expected calibration error with declared bins.

Why add them:

- AUC measures ranking but not calibration.
- Accuracy and F1 depend on a threshold.
- The proposal changes a probability—the initial mastery prior—so probability
  quality is scientifically relevant.

Every result row should include:

- number of scored turns;
- number of dialogues;
- observed correctness rate;
- predicted-positive rate;
- mean predicted probability.

### 13.5 Uncertainty

Use dialogue-level bootstrap confidence intervals for differences between C1
and C0:

1. sample test dialogues with replacement;
2. keep all scored turns belonging to each sampled dialogue;
3. recompute both models' metrics on the same bootstrap sample;
4. store the paired difference;
5. report a 95% interval.

Resampling individual pseudo-turn rows would incorrectly treat correlated rows
from the same dialogue as independent.

---

## 14. Leakage and fairness safeguards

### 14.1 Required safeguards

- Keep MathDial train and test dialogue IDs fixed.
- Learn BKT parameters, context weights, regularization strength, and any
  thresholds without using test outcomes.
- Generate S0 features from the problem and solution only.
- Do not use future turns when annotating S0.
- Do not use the dialogue-wide KC union as an S0 feature.
- Do not use `self-correctness` to annotate S0.
- Apply the final-turn correctness override only to the real BKT correctness
  sequence, as in notebook 03.
- Fit annotation prompts and adjudication rules on development material, then
  freeze them before final test evaluation.
- Compare C0 and C1 on identical target rows.

### 14.2 Annotation is allowed on the test inputs

At deployment time, the model would receive a new problem and initial solution.
Generating misconception features from those inputs is therefore allowed.

What is prohibited is using the test dialogue's later outcomes to:

- create its S0 features;
- tune the annotation process after inspecting model results;
- fit context weights.

### 14.3 The current `correct=False` solution field

The reformatted S0 row currently contains `correct=False`. This is useful as a
description of the known incorrect solution and for notebook 04.

The contextual model must explicitly ignore this field as a BKT observation.
Only the S0 misconception labels enter the contextual prior.

---

## 15. Recommended ablations

Ablations explain *why* a model changes, not merely whether a headline number
changes.

### Required

1. **Neutral context:** all features zero.
2. **Full context:** all five families.
3. **Shuffled context:** preserve label frequencies but break the match between
   dialogue and S0 features.
4. **Notebook 04 false-union baseline:** preserve as the strong naive
   alternative.

### Helpful if sample size permits

5. **Presence only:** use `present`; neutralize `absent`.
6. **Absence only:** use `absent`; neutralize `present`.
7. **One family at a time:** test comprehension, relevance, principles, wrong
   operation, and steps separately.
8. **Unconstrained signs:** compare against the semantically constrained model.
9. **Joint-fit version:** refit BKT and context together.

Multiple family-by-family tests should be treated as exploratory or corrected
for multiple comparisons.

---

## 16. Diagnostics the notebook should show

### 16.1 Data diagnostics

- Raw dialogue counts by split.
- Paper-filter removal counts and reasons.
- Final retained dialogue and real-turn counts.
- S0 annotation completion rate.
- Counts of `present`, `absent`, and `not_evidenced` by family and split.
- Number of dialogues with zero, one, or several `present` families.
- KC frequency and correctness balance.

### 16.2 Model diagnostics

- Frozen BKT parameter source and checksum or model path.
- Learned \(a_f\) and \(b_f\) weights with confidence intervals.
- Converted probability effects at representative baseline priors.
- Training and validation objective by restart.
- Chosen regularization strength and cross-validation results.
- Boundary or constraint activity.
- Fallback coverage.

### 16.3 Prediction diagnostics

- C0 and C1 metrics under every evaluation mask.
- Paired metric differences and dialogue-bootstrap intervals.
- R1-only, R2+, and all-real results.
- Calibration plots.
- Prediction distributions by actual correctness.
- Results by misconception family and annotation status.
- Results by dialogue length.
- Results for degenerate/fallback versus normally fitted KCs.

Subgroup results should include sample sizes. Small groups should not be given
strong causal interpretations.

---

## 17. Expected findings and how to interpret them

### If C1 improves over C0

This would support the claim:

> Misconception annotations extracted from the initial solution contain
> predictive information about subsequent dialogue correctness beyond the
> ordinary KC prior.

The strength of the claim depends on:

- whether the improvement appears on held-out test dialogues;
- whether it appears in probability-sensitive metrics;
- whether the confidence interval excludes a negligible effect;
- whether the shuffled control fails to reproduce it;
- whether the effect survives the paper-matched evaluation.

### If C1 helps R1 but not R2+

This would still be informative. It may mean:

- S0 is useful for initial state estimation;
- one real response quickly provides stronger evidence;
- ordinary BKT updates wash out the contextual advantage.

That result would motivate using the misconception features for initial
personalization rather than claiming a persistent long-horizon benefit.

### If C1 does not improve

Possible explanations include:

- the annotations do not predict correctness beyond KC priors;
- the five families are too broad to attach equally to every KC;
- annotation noise is too high;
- the model needs target-aware family-to-KC interactions;
- correctness-only BKT updates dominate quickly;
- the two-state mastery variable cannot represent a misconception state well.

Failure of this first model would not prove that misconceptions are irrelevant.
It would rule against this particular contextual-prior representation.

### If C1 improves F1 but reduces AUC or accuracy

Do not describe this simply as an improvement. Notebook 04 already showed why:
a model can raise F1 by predicting “correct” much more often while becoming
worse at ranking and overall classification.

Interpret all metrics together and report the predicted-positive rate.

---

## 18. Future models, only after the contextual prior

The contextual-prior model should be the first misconception-aware experiment
because it is simple, interpretable, and closely aligned with standard BKT.

Possible later extensions include:

### 18.1 Hierarchical KC-specific context effects

Allow each KC to deviate from the global misconception effects while shrinking
rare KCs toward the shared mean.

This could capture that a principles misconception matters more for some KCs
than others without fitting unstable independent weights for every KC.

### 18.2 Misconception evidence as a separate emission

Model the S0 annotation as evidence generated by the hidden state:

\[
P(x_{d,0}\mid L_{d,k,0}).
\]

This is more generative, but it requires assumptions about how each
misconception family relates to mastery of each KC.

### 18.3 Three-state knowledge tracing

Replace the two states with:

1. unmastered without an identified misconception;
2. misconception state;
3. mastered.

This may better represent the research question, but it is a substantially
different model. It introduces more transitions, emissions, identifiability
issues, and data requirements. It should not be the first test of whether S0
annotations carry useful signal.

---

## 19. Proposed implementation layout

No implementation files are created by this document. When implementation
begins, the recommended layout is:

| Proposed path | Responsibility |
| --- | --- |
| `extension/scripts/contextual_bkt.py` | Feature encoding, contextual-prior calculation, fitting, prediction, serialization |
| `extension/notebooks/06_bkt_misconception_context.ipynb` | Data audit, fit, aligned controls, evaluation, plots, interpretation |
| `extension/models/bkt_misconception_context.json` | Frozen BKT provenance, context weights, constraints, regularization, fallback, seed |
| `extension/results/bkt_misconception_context_metrics.csv` | Protocol-level metrics for all compared systems |
| `extension/results/bkt_misconception_context_predictions.csv` | Turn-level C0/C1 predictions and audit columns |
| `extension/results/bkt_misconception_context_bootstrap.csv` | Paired dialogue-bootstrap metric differences |

The script should hold reusable model logic. The notebook should explain,
invoke, audit, and visualize that logic rather than duplicating the
implementation in many cells.

---

## 20. Required validation checks

Before accepting an implementation, assert all of the following:

### Population and sequence checks

- [ ] C0 and C1 contain exactly the same dialogues.
- [ ] C0 and C1 score exactly the same real turns.
- [ ] The contextual model retains 2,050 train and 515 test dialogues when the
      same source data and notebook 03 filters are used.
- [ ] Every retained dialogue has at least two usable tagged real turns.
- [ ] S0 is absent from the correctness observation sequence.
- [ ] S0 is absent from all scoring masks.
- [ ] R1 is scored in all-real evaluation.
- [ ] R1 is an update but not a scored target in paper-matched evaluation.

### Context checks

- [ ] Every complete S0 annotation has one allowed status per family.
- [ ] Missing annotations are never converted to `absent`.
- [ ] Neutral context produces a zero feature vector.
- [ ] `not_evidenced` contributes no prior adjustment for its family.
- [ ] `present` cannot raise the prior in the constrained model.
- [ ] `absent` cannot lower the prior in the constrained model.
- [ ] S0 feature construction does not read later dialogue turns or KC unions.

### Equivalence and leakage checks

- [ ] With neutral context and frozen notebook 03 parameters, predictions match
      notebook 03 within numerical tolerance.
- [ ] Context weights are fit from training responses only.
- [ ] Regularization is selected without test outcomes.
- [ ] Test metrics are computed only after model choices are frozen.
- [ ] The shuffled control preserves marginal feature counts while breaking
      dialogue alignment.

### Output checks

- [ ] Saved metrics can be reconstructed from saved turn predictions.
- [ ] Model reload reproduces predictions exactly within numerical tolerance.
- [ ] Result files record data paths, seeds, filter counts, model configuration,
      and annotation coverage.
- [ ] Metric tables include sample sizes and predicted-positive rates.

---

## 21. Decision register

| Decision | Recommended choice | Reason |
| --- | --- | --- |
| Role of S0 | Context for the initial prior | S0 precedes tutoring and describes starting knowledge |
| S0 correctness | Do not use as a BKT observation | “Incorrect overall” does not imply every KC was attempted incorrectly |
| Solution KC union | Do not use | It is retrospective and overstates which KCs S0 attempted |
| Context target | Adjust KC prior | Minimal, interpretable extension of standard BKT |
| Feature statuses | Separate `present`, `absent`, and `not_evidenced` | They have different meanings in the codebook |
| Feature signs | Constrain present downward and absent upward | Matches label semantics and improves stability |
| Initial effect scope | Shared across KCs | Avoids sparse KC-specific estimates and invented KC-family mappings |
| First fitting stage | Freeze notebook 03 BKT parameters | Isolates the value of misconception evidence |
| Main control | Same model with all context neutralized | Holds architecture, observations, and targets constant |
| Historical reference | Keep notebook 03 in tables | Maintains comparability with the paper |
| Notebook 04 role | Naive negative-control ablation | It tests a different, deliberately strong representation |
| Dialogue-length filter | At least two usable tagged real turns | S0 is context, not a third observation |
| Main scored protocols | All-real and paper-matched R2+ | Measures full utility and preserves published comparability |
| Additional diagnostic | R1 only | S0 should have its clearest effect before a real response update |
| Missing S0 annotation | Neutral fallback plus audit flag | Preserves population without inventing evidence |
| Hyperparameter selection | Group CV within training dialogues | Prevents dialogue and test leakage |
| Uncertainty | Paired dialogue-level bootstrap | Respects within-dialogue dependence |

---

## 22. Bottom line

The scientifically clean experiment is not:

> “Does BKT with an extra false solution turn beat BKT without that turn?”

It is:

> “Within the same contextual BKT architecture, do real misconception
> annotations from the initial solution improve predictions relative to
> neutralized solution evidence?”

Notebook 03 remains the paper-aligned historical reference. Notebook 04 remains
evidence that representing the solution as false responses on a future-derived
KC union is too strong.

The proposed contextual-prior model aligns the comparison by:

- keeping the real correctness sequence unchanged;
- retaining the paper's data filters;
- using the same target turns;
- treating S0 as evidence about initial state rather than as a response;
- comparing actual and neutral S0 evidence through the same code path.

That design allows any measured difference between the main proposed model and
its control to be attributed specifically to the misconception information in
the student's initial solution.
