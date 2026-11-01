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
