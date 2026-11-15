# Researcher-Directed Scientific Records

New projects start with an unadopted Research Map and empty registry. Program
review, literature discussion, and synthesis do not require an AST unit. The
tool does not choose a scientific question, priority, method or publication claim.

Record adoption requires an explicit JSON approval reference:

```json
{"by":"Actual investigator name","reference":"Dated decision record or explicit instruction","date":"2026-11-14"}
```

This is a recorded attestation, not authentication or proof of consent. An agent
must never invent an approval to satisfy a validator. Use proposal notes until
the actual researcher accepts consequential choices. Registration approval alone
does not authorize execution, physical experiments, or access to controlled data.

`record-new PROJECT KIND --title TITLE --body-file FILE --approval-file FILE`
creates W, A, S, T or M records. S requires an active A parent; T requires an
active S parent. Use `--parent A001` or `--parent A001-S01` respectively. A Tactic
body must contain `## Question` and `## Specifications`. Describe all material
protocols, inputs, sample/measurement definitions, controls, parameters, quality
checks and evaluation criteria applicable to that approved question. Do not fill
irrelevant fields with invented science. No computational repository is required.

`new-unit` is the Tactic adapter and additionally creates paired draft reports.
The underlying stable identity is `A###-S##-T##`; descriptive file names never
replace it. W and M use independent W## and M## identities. IDs are bounded and
never recycled, including retired or interrupted registrations. Existing plans,
reports and analyses are checked for collisions. Legacy abbreviated Strategy/
Tactic references are conservatively reserved; ambiguous layouts need inspection.
`register-existing` registers explicitly inspected existing records without
rewriting their contents. It does not infer past approvals.

W–A associations may be many-to-many. `record-links` changes them with an approval
and expected registry revision. A manuscript may link several Tactics; a Tactic
may contribute to multiple manuscripts or none. Manuscript prose must distinguish
Claims, Supporting Evidence, Contradictory Evidence, Limitations and Decisions.
The researcher controls adoption of claims, evidence selection, figure order,
authorship and publication; links do not establish evidential support by themselves.

`map-adopt` accepts a complete approved Markdown map and expected current hash,
retains the predecessor and decision, and allocates no AST identity. It preserves
Question/Hypothesis/Observation/Inference/Alternative/Synthesis categories,
relationships, priorities, dependencies and gaps. Its scientific sufficiency and
semantic accuracy require researcher review.

The registry indexes identities and relationships rather than duplicating the
scientific narrative. Readable Markdown remains authoritative scientific prose.
Creation durably reserves the ID before publishing its body. `record-resume`
uses the existing ID and verified stored body after interruption; conflicting
local work is preserved and requires explicit resolution. `record-revise` retains
the exact previous body, requires its current hash and renewed approval, and uses
the same recoverable reservation mechanism. `record-retire` preserves identity
and content. Direct human edits remain possible; review their current hash before
an approved revision instead of silently replacing them.

Default path mappings are project configuration. Mapping into tools, templates,
private framework state, independent Git checkouts or unsafe paths is refused.
The project root need not be a Git repository. Existing ELN/LIMS, protocol,
sample/acquisition and controlled-archive references remain in their authorized
primary systems; record stable references and access boundaries, not restricted
content. Optional Runs and evidence handoffs are separate from report revisions.
