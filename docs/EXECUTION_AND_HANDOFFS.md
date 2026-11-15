# Execution, Provenance and Human-Operated Handoffs

Execution is optional within a Tactic. Experimental acquisition, computational
runs, theoretical derivations, observational evidence and hybrid work can use
the same durable records without requiring source code or a remote scheduler.
Source code remains in its independent repository and retains its entry point.

`run-record PROJECT --record-file FILE` validates an explicit R### record nested
under an approved Tactic. New Runs and APPROVED state require an actual approval
file. A current hash is required when updating an existing record. Registered
Run IDs survive deletion and are never recycled. Earlier records are retained.
The command records supplied evidence; it neither runs an experiment nor submits
a job. A report REV### is not an execution R###. No Run is needed when it adds
no useful execution distinction.

Provenance distinguishes planned, source_default, reconstructed,
verified_effective and unknown. Available and producing source revisions are
separate; unverified history cannot assert a producing hash. Relevant dirty
source hashes can supplement a producing revision. Protocol, sample, acquisition,
input/output, computation, environment, interpretation and approval references
retain their primary-system identities and access boundaries. Never copy
restricted data just to populate a public record.

Completion requires actual timezone-aware start/end evidence and output checks;
known missing required outputs prohibit COMPLETED. Scheduler exit status and
scientific quality are separate. A null external ID or producing revision stays
null until actual evidence exists. These checks are structured consistency
validation, not authentication of an operator's factual statements.

`handoff PROJECT --record-file FILE` saves a cross-agent/human record with the
same resume ID, approved scope reference, actual status, known execution IDs,
received/missing evidence, expected outputs and next human step. Replacing it
requires its current hash and preserves its predecessor. WAITING is appropriate
when operator output is pending. Resume under the existing ID; do not allocate
a new unit because a chat or process was interrupted. Read durable records and
local policies explicitly rather than relying on proprietary chat memory.

The project HPC instructions follow the verified development manual's generic
rules without shipping its workstation location or site-specific examples.
`launcher-check FILE` checks Bash/SBATCH ordering, rejects routine package
installation/embedded programs, and requires module loading, Conda initialization
and absolute-prefix activation inside Conda jobs. Static checks do not establish
remote resource adequacy, package imports or cluster-policy compliance.

`hpc-commands PROJECT --record-file FILE` prepares separate pull, submission,
monitoring/accounting and narrow retrieval commands from explicitly verified
project-specific information. It never executes them. Preserve nested repository
working-directory contracts. When Slurm is available, submit/monitor requires no
login Conda activation or extra module loading. Add a verified Slurm module only
after actual unavailability is established. Existing job-internal setup remains
necessary. Environment provisioning stays separate from science jobs.

Humans perform remote access, pull, submission, monitoring and transfers. No
invented job ID, automated cancellation, destructive rsync, speculative success
or implicit SSH access is supported. Verify logs, accounting, exit codes and
expected output quality after actual returned evidence. Sensitive physical,
regulated and primary-system activities remain with authorized people/institutions.
