# Research Program Framework: Design Philosophy

**Languages:** English | [한국어](PHILOSOPHY.ko.md)  
[Home](../README.md) · [Project template](../template/) · [Detailed scientific specification](RESEARCH_PROGRAM_FRAMEWORK_v1.1.md)

This document explains **why** the framework is designed this way. It is a conceptual orientation, not an additional set of mandatory steps. The detailed specification and project instructions remain authoritative for implementation and day-to-day operation.

## 1. Scientific inquiry lasts longer than a conversation

Research develops over months and years. Questions, interpretations, and priorities change. A chat session is useful for thinking, but it is not a dependable permanent record. People and AI agents should be able to continue a project without access to previous conversations.

**Conversations are for reasoning; persistent project documents are for continuity.** The Research Map, plans, scientific reports, figures, and provenance are the shared basis for resuming and assessing work.

## 2. The researcher is responsible for scientific direction

The assistant is a **critical collaborator**, not an autonomous principal investigator or a passive transcription service. It should question assumptions, look for confounding, distinguish weak and strong evidence, and offer alternatives.

Yet suggestions are not decisions. Brainstorming, a successful run, or an attractive result does not authorize a new experiment, adopted hypothesis, interpretation, priority, or publication claim. Consequential choices become formal records only with explicit researcher acceptance and an intelligible rationale.

## 3. Broad direction and bounded evidence are different things

The framework separates complementary levels of scientific work:

| Concept | Role |
|---|---|
| **Research Narrative / Research Map** | The broad problem, questions, competing explanations, gaps, and evolving synthesis |
| **Workstream** | A sustained line of scientific investigation, not necessarily an assay, technology, dataset, or code repository |
| **Aim** | One specific scientific question or bounded enabling objective |
| **Strategy** | An overall approach to that Aim |
| **Tactic** | A bounded task producing one coherent package of interpretable evidence |
| **Specifications** | Material protocols, inputs, comparisons, measurements, parameters, QC, and evaluation criteria |
| **Run (optional)** | One execution, experiment, acquisition, or batch |
| **Manuscript (optional)** | A publication-specific argument selecting evidence and acknowledging limitations |

These are **conceptual responsibilities**, not an inflexible folder tree. Workstreams and Aims can connect many-to-many. One Tactic may contribute to multiple manuscripts or none. A manuscript is not the parent of the scientific program: research should not be retrospectively forced into a predetermined story.

A Tactic is normally the smallest scientific reporting unit, but it need not equal a single script, figure, or execution. Multiple controls, replicates, and runs may belong to one bounded question.

An Aim normally has the scope of a coherent results paragraph or related evidence
set, typically below a manuscript Results subsection; this is a scope heuristic,
not a publication format or count requirement. Dataset construction can be a
bounded enabling Aim. One or several Strategies and Tactics are valid, and the
researcher may choose broader scope with a rationale and completion boundary.
See the [operational Aim guidance](../template/AGENTS.md#aim-scope) and
[synthetic examples](RESEARCH_PROGRAM_FRAMEWORK_v1.1.md#23-aim-strategy-tactic-ast).

## 4. Coordination and AST sessions communicate through files

**Coordination** is where the researcher and assistant discuss the wider program, critically examine hypotheses, choose priorities, and reconsider direction using relevant evidence. It can do this without creating an AST.

A separate **AST session** reads the approved plan, discusses detailed Specifications, performs authorized work, interprets results, refines figures, and maintains its own reports. Revisions and interruptions retain the same AST identity unless a substantively distinct evidence-producing question is introduced.

Neither session needs to message the other. Coordination later **reads the saved plans and AST reports**. There is no requirement to load every old report or produce a special cross-chat summary.

## 5. Preserve epistemic distinctions

A reliable research record separates **Question**, **Hypothesis**, **Observation**, **Inference**, **Alternative explanation**, and **Synthesis**. Measurements are not interpretations. An interpretation is not a confirmed mechanism. A completed task is not a supported hypothesis.

Negative, null, inconclusive, failed, and `NOT_EVALUATED` work may be scientifically useful when faithfully documented. Unknown or reconstructed provenance should not be presented as verified fact. Contradictory evidence belongs in the record, even if it complicates a future paper.

## 6. Reports are for scientific reconstruction

A person who has not read the code or the chat should still be able to understand what was done and critically evaluate the evidence. When relevant, Methods must explain definitions, units, denominators, sample and replicate structure, controls, exclusions, transformations, settings, calculations, and uncertainty.

The framework supports corresponding English and Korean Markdown, HTML, and PDF outputs. **There is no arbitrary page-count limit.** Scientific adequacy is determined by what matters for reproducibility and interpretation, not by length. Automated checks cannot certify scientific or translation accuracy, and figure polish must not silently change what the data support.

## 7. Formalize what matters, not every thought

Free discussion may remain exploratory. Formal records are useful for accepted direction, material methods, traceable evidence, important revisions, and decisions. Creating a document for every idea would make research administration an end in itself.

Stable IDs persist across AST revisions. Older plans and reports remain inspectable. Existing historical research does not have to be bulk-converted: consult or formalize it selectively when useful.

## 8. Prefer an understandable template over a management platform

The repository is **template-first**: familiar folders, Markdown policies, and a few inspectable scripts. A researcher should understand the project by browsing `template/`. Scientific source repositories remain independent.

The shared template and helper scripts can be improved later. Updates preview proposed differences, keep project-owned records outside the managed set, and stop on unresolved local conflicts. Affected-file backups provide a practical recovery path; this is not a promise of globally atomic updates or automatic rollback.

## 9. Keep human responsibilities explicit

Experimental, computational, theoretical, observational, and hybrid research all fit the conceptual model. Researchers and authorized institutions retain scientific judgment, physical or regulated operations, primary records, and remote/HPC operations. Assistants can prepare commands and examine returned evidence, but cannot presume access, invent execution, or declare scientific truth from structural checks.

## 10. An ordinary research cycle

1. Discuss a problem and alternatives in Coordination.
2. Adopt only researcher-approved changes to the Research Map and plans.
3. Start a separate AST session, read the relevant files, and agree on bounded Specifications.
4. Perform approved work, revise interpretations and figures, and save the scientific report.
5. Later return to Coordination, read those **saved reports**, and reconsider the overall direction.

**Core idea:** Researcher-led inquiry produces traceable evidence through bounded AST work; Coordination integrates that evidence without conflating observation, inference, and publication narrative.
