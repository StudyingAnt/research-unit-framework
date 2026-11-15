"""Portable structural schemas; Python validators enforce semantic/path safety."""

from .manifests import manifest_schema


def _object(properties, required=None):
    return {'type': 'object', 'additionalProperties': False, 'properties': properties,
            'required': list(properties) if required is None else required}


def definitions():
    string = {'type': 'string'}
    nonempty = {'type': 'string', 'minLength': 1}
    sha = {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}
    nullable_sha = {'anyOf': [sha, {'type': 'null'}]}
    array = {'type': 'array'}
    approval = _object({'by': nonempty, 'reference': nonempty, 'date': {'type': 'string', 'format': 'date'}})
    fingerprint = _object({'size': {'type': 'integer', 'minimum': 0}, 'sha256': sha, 'mode': {'enum': ['0644', '0755']}})
    provenance = _object({'category': {'enum': ['protocol', 'sample', 'acquisition', 'computation', 'environment', 'input', 'output', 'interpretation', 'approval']},
        'verification': {'enum': ['planned', 'source_default', 'reconstructed', 'verified_effective', 'unknown']},
        'reference': nonempty, 'description': nonempty,
        'producing_revision': {'type': ['string', 'null']}, 'available_revision': {'type': ['string', 'null']},
        'dirty_source_hashes': {'type': 'object', 'additionalProperties': sha}})
    from .records import STATUS, OUTCOME
    release = manifest_schema(); release.pop('$id', None)
    installation = _object({'schema_version': {'const': 1}, 'kind': {'const': 'framework_installation'},
        'project_id': {'type': 'string', 'pattern': '^[0-9a-f]{32}$'}, 'generation': {'type': 'integer', 'minimum': 0},
        'release': release, 'installed': {'type': 'object', 'additionalProperties': {'anyOf': [fingerprint, {'type': 'null'}]}},
        'last_operation': {'type': ['string', 'null']}, 'project_owned': {'type': 'object', 'additionalProperties': {'enum': ['B', 'C']}}},
        ['schema_version', 'kind', 'project_id', 'generation', 'release', 'installed', 'last_operation'])
    record = _object({'id': nonempty, 'kind': {'enum': ['W', 'A', 'S', 'T', 'M']}, 'parent': {'type': ['string', 'null']},
        'title': nonempty, 'path': nonempty, 'links': {'type': 'array', 'items': nonempty, 'uniqueItems': True},
        'approval': approval, 'state': {'enum': ['pending', 'active', 'retired']}, 'sha256': sha, 'history': array})
    registry = _object({'schema_version': {'const': 1}, 'revision': {'type': 'integer', 'minimum': 0},
                        'records': {'type': 'array', 'maxItems': 10000, 'items': record}})
    run = _object({'schema_version': {'const': 1}, 'unit_id': nonempty, 'run_id': {'type': 'string', 'pattern': '^R[0-9]{3}$'},
        'status': {'enum': list(STATUS)}, 'performer': nonempty, 'started_at': {'type': ['string', 'null']},
        'completed_at': {'type': ['string', 'null']}, 'command': {'type': ['string', 'null']},
        'external_id': {'type': ['string', 'null']}, 'provenance': {'type': 'array', 'items': provenance}, 'outputs': array,
        'validation': _object({k: array for k in ('expected', 'received', 'checks', 'missing')})})
    handoff = _object({'schema_version': {'const': 1}, 'unit_id': nonempty, 'resume_id': nonempty,
        'status': {'enum': list(STATUS)}, 'approved_scope_reference': nonempty,
        **{k: array for k in ('known_execution_ids', 'evidence_received', 'evidence_missing', 'expected_outputs')},
        'next_human_step': nonempty, 'updated_at': nonempty})
    report = _object({'schema_version': {'const': 1}, 'unit_id': nonempty, 'status': {'enum': list(STATUS)},
        'outcome': {'enum': list(OUTCOME)}, 'outcome_reason': string,
        'revision': {'type': 'string', 'pattern': '^REV[0-9]{3}$'}, 'figures': array,
        'provenance': {'type': 'array', 'items': provenance},
        'review': _object({**{k: {'type': 'boolean'} for k in ('methods', 'bilingual', 'visual')}, 'references': array})})
    return {name: {'$schema': 'https://json-schema.org/draft/2020-12/schema',
                   'title': title, **body} for name, title, body in [
        ('installation', 'Framework installation receipt', installation), ('id-registry', 'Scientific ID registry', registry),
        ('approval', 'Researcher approval reference', approval), ('provenance', 'Evidence verification boundaries', provenance),
        ('run', 'Optional execution Run', run), ('handoff', 'Cross-agent handoff', handoff), ('report', 'Paired scientific report metadata', report)]}
