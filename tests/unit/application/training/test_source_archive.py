import zipfile


def test_source_archive_preserves_dirty_source_bytes(tmp_path):
    from uc3m.application.training.preflight import archive_sources
    folder = tmp_path/'uc3m'
    folder.mkdir()
    (folder/'module.py').write_bytes(b'value = 1\n')
    archive = tmp_path/'snapshot.zip'
    archive_sources(tmp_path, archive)
    (folder/'module.py').write_text('value = 2\n')
    with zipfile.ZipFile(archive) as saved:
        assert saved.read('uc3m/module.py') == b'value = 1\n'
