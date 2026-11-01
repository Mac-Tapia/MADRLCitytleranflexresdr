import json
import threading
import urllib.request


def test_local_panel_serves_ui_and_marks_corrupt_evidence_invalid(tmp_path):
    from uc3m.presentation.training_panel import make_server
    folder = tmp_path/'broken'
    folder.mkdir()
    (folder/'evidence.json').write_text('{broken')
    server = make_server(tmp_path, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f'http://127.0.0.1:{server.server_port}'
        with urllib.request.urlopen(base+'/api/runs') as response:
            rows = json.load(response)
        assert rows[0]['status'] == 'invalid_manifest'
        with urllib.request.urlopen(base) as response:
            assert 'MADRL' in response.read().decode('utf-8')
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
