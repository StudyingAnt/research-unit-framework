# Research Program Framework v1.1

This implementation supports researcher-directed life-science program records,
Detailed EN/KO reporting and guarded framework administration. The scientific
specification is v1.1; the implementation and JSON schema versions are separate.

Implementation 1.1.1 corrects font-presence diagnostics for project-relative
configured paths when invoked outside the project. Rendering, scientific
requirements and safe administration remain unchanged from 1.1.0. The published
1.1.0 tag and artifacts are retained.

Download the release archive and its SHA-256 file. Verify the checksum before
extracting the trusted archive, inspect `SHA256SUMS`, and keep the release
directory for update planning. Python 3.9+ on Linux/WSL is required for core
administration; reporting uses its own configured Python environment and fonts.

```bash
sha256sum -c research-program-framework-VERSION.tar.gz.sha256
tar -xzf research-program-framework-VERSION.tar.gz
python3 research-program-framework-VERSION/newproj.pyz new /absolute/new/project
```

Replace VERSION with this release's version. The standalone `newproj.pyz` asset
also embeds the starter and can create a project by itself. Existing projects
require inspected update/migration plans; never overlay the archive onto them.
See [installation](INSTALLATION.md), [migration](MIGRATION.md),
[updates/recovery](UPDATE_ENGINE.md), [scientific records](SCIENTIFIC_RECORDS.md),
[reporting](REPORTING.md), and [execution/handoffs](EXECUTION_AND_HANDOFFS.md).

No license grant has been established in this repository. Do not infer rights
to redistribute source, legacy material or third-party assets from publication
alone. Fonts and scientific dependencies are not bundled. Reporting does not
perform analyses, create environments or regenerate historical reports during
framework administration.

Known bounds: Linux/WSL single-filesystem descriptor APIs, sufficient no-atime
permissions, ordinary current-user/group ownership, no ACLs/xattrs or hardlinks
on affected files, trusted administrative state and cooperating writers. Stop
editors/jobs that could change administrative targets during apply. Checksums
are integrity checks, not publisher authentication. Backups cover administrative
changes, not scientific data. Unknown ancestors, ambiguous layouts or unresolved
conflicts require inspection. MathText is a TeX subset; full TeX environments
are explicitly unsupported. Scientific adequacy, bilingual meaning, actual
cluster behavior and every vendor's instruction loader cannot be certified by
automated tests. Review actual reports, approvals and project policies.
