# Releasing the Visible Template

Update VERSION, template-manifest.json and release notes together. Validate with
the complete core suite and renderer-enabled acceptance in a verified environment.
Inspect the full candidate, including new files, for private content. Keep local
context ignored, and leave existing research projects read-only.

Commit on a development branch. From a clean committed tree:

```bash
python3 -B tools/audit_public.py
python3 -B tools/package_release.py
```

The output is a standard browsable source tar.gz and checksum, exported from
the exact Git commit. Extract it elsewhere and test project creation and copied
helpers independently. Check version equality and checksum before publication.
No special installed runtime, compiled schema or archive loader is involved.

Push the reviewed development branch and observe CI. Once validated, advance
main without rewriting history, push the new version tag and observe the release
workflow. It tests both supported core interpreters, packages the tagged source
and publishes new assets. It refuses an existing release. Keep prior tags and
releases unchanged. Inspect the published archive/checksum and independently
create a synthetic project from the downloaded artifact.

Actual fonts/dependencies stay external. Publication does not invent a license
grant or authorize release of scientific records. The framework version is 2.x;
the retained scientific design specification version is 1.1.
