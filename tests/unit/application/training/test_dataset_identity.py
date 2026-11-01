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
