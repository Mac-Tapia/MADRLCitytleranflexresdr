import json


def test_dataset_digest_covers_csv_bytes_and_rejects_missing_references(tmp_path):
    from uc3m.application.training.preflight import dataset_digest
    schema = tmp_path / 'schema.json'
    schema.write_text(json.dumps({'buildings': {'B1': {'energy_simulation': 'B1.csv'}}}))
    csv = tmp_path / 'B1.csv'
    csv.write_text('load\n1\n')
    before = dataset_digest(schema)
    csv.write_text('load\n2\n')
    assert dataset_digest(schema) != before
    csv.unlink()
    try:
        dataset_digest(schema)
    except ValueError as exc:
        assert 'missing' in str(exc)
    else:
        raise AssertionError('missing dataset file accepted')


def test_dataset_digest_is_the_same_on_windows_and_linux_checkouts(tmp_path):
    # Git stores the dataset with LF; core.autocrlf checks it out as CRLF on
    # Windows while Colab (Linux) gets LF. Both must yield one identity.
    from uc3m.application.training.preflight import dataset_digest

    def dataset(name, newline):
        root = tmp_path / name
        root.mkdir()
        (root / 'B1.csv').write_bytes(newline.join([b'hour,load', b'0,1.0', b'']))
        schema = {'buildings': {'B1': {'energy_simulation': 'B1.csv'}}}
        (root / 'schema.json').write_bytes(json.dumps(schema, indent=1).replace('\n', newline.decode()).encode())
        return root / 'schema.json'

    assert dataset_digest(dataset('linux', b'\n')) == dataset_digest(dataset('windows', b'\r\n'))


def test_source_snapshot_is_the_same_on_windows_and_linux_checkouts(tmp_path):
    # The run identity also includes the source snapshot; a CRLF checkout of the
    # same code must not look like different code.
    from uc3m.application.training.preflight import source_snapshot

    def project(name, newline):
        root = tmp_path / name
        (root / 'uc3m').mkdir(parents=True)
        (root / 'uc3m' / 'module.py').write_bytes(newline.join([b'def f():', b'    return 1', b'']))
        (root / 'pyproject.toml').write_bytes(newline.join([b'[project]', b'name = "x"', b'']))
        return root

    assert source_snapshot(project('linux', b'\n')) == source_snapshot(project('windows', b'\r\n'))
    changed = project('changed', b'\n')
    (changed / 'uc3m' / 'module.py').write_bytes(b'def f():\n    return 2\n')
    assert source_snapshot(changed) != source_snapshot(project('again', b'\n'))


def test_source_archive_digest_matches_the_snapshot_for_crlf_sources(tmp_path):
    # NativeBackend refuses a run unless archive_sources returns spec.source_sha256,
    # which is source_snapshot. With CRLF sources (Windows checkout, Colab overlay)
    # both must agree, while the archive keeps the original bytes.
    import zipfile

    from uc3m.application.training.preflight import archive_sources, source_snapshot

    root = tmp_path / 'project'
    (root / 'uc3m').mkdir(parents=True)
    original = b'def f():\r\n    return 1\r\n'
    (root / 'uc3m' / 'module.py').write_bytes(original)
    (root / 'pyproject.toml').write_bytes(b'[project]\r\nname = "x"\r\n')

    archive = tmp_path / 'source_snapshot.zip'
    assert archive_sources(root, archive) == source_snapshot(root)
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.read('uc3m/module.py') == original
