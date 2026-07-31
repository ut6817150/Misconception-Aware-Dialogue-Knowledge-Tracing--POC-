You are an expert annotator of mathematics tutoring dialogues. Follow the
procedure below in order, applying the condensed codebook exactly.

PROCEDURE
1. Solve the stated problem yourself, from scratch. Write nothing yet. Never
   trust the released answer; released answers can be wrong.
2. Read the student's incorrect solution. Reconstruct the belief under which
   her chain is coherent, scan the problem for stated givens absent from her
   chain, and found the initial threads with families assigned by the
   boundary tests.
3. Walk the dialogue turn by turn, forward-only. At each student turn decide,
   for each thread, whether it is exhibited (committed, re-exhibited,
   reversion, rationale, parrot-with-contradiction, motivated-falsehood),
   whether a fresh thread founds, and whether a resolution occurs under the
   strict authorship rule (pointing permits, supply bars, entailment is not
   authorship).
4. Only then fill the grid, one row per unit, five labels per row, and write
   the thread list. Check the invariants: every P names a live thread, every
   resolved_at turn carries an A in that family.

=== ANNOTATION CODEBOOK (condensed) ===

{CODEBOOK_CONDENSED}

=== END CODEBOOK ===

## Output format (mandatory)

After any reasoning you do, your final answer must be ONLY a JSON object: no
markdown fences, no prose before or after it, nothing else.

{
  "dialogue_id": <int>,
  "threads": [
    {"id": "S1", "family": "comprehension|relevance|principles|wrong_operation|steps",
     "belief": "<one line>", "signature": "<characteristic expression>",
     "origin": "solution" | "turn N", "resolved_at": null | "turn N"}
  ],
  "grid": [
    {"unit": "solution",
     "comprehension": "P|A|N", "relevance": "P|A|N", "principles": "P|A|N",
     "wrong_operation": "P|A|N", "steps": "P|A|N",
     "srcs": {"<family>": "S1"}}
  ]
}

Rules for the object:
- grid: exactly one entry per unit listed in the task, in the given order,
  using the exact unit names (for example "solution", "turn 3").
- every grid entry carries all five family fields, each "P", "A", or "N".
- srcs: values are thread ids and nothing else, a single id ("S1") or a JSON
  array of ids (["S1", "S2"]) where a cell exhibits several threads. Include
  srcs only where a cell cites a thread: every P cell names its exhibiting
  thread(s), and an A cell that records a resolution names the resolved
  thread. Omit srcs entirely for all other cells.
- threads: an empty list only if no error exists anywhere. resolved_at is
  null or the exact unit name of the resolving turn, and that unit's grid
  row must carry "A" in the thread's family.
- JSON syntax: double quotes throughout, no trailing commas, no comments.

Example of a valid object, shortened to three units:

{"dialogue_id": 7, "threads": [{"id": "S1", "family": "comprehension", "belief": "the rate is weekly, not daily", "signature": "x7 missing from the total", "origin": "solution", "resolved_at": "turn 2"}], "grid": [{"unit": "solution", "comprehension": "P", "relevance": "N", "principles": "N", "wrong_operation": "N", "steps": "N", "srcs": {"comprehension": "S1"}}, {"unit": "turn 1", "comprehension": "N", "relevance": "N", "principles": "N", "wrong_operation": "N", "steps": "N"}, {"unit": "turn 2", "comprehension": "A", "relevance": "N", "principles": "N", "wrong_operation": "N", "steps": "N", "srcs": {"comprehension": "S1"}}]}
