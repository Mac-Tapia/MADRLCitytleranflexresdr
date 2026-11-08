"""The local training monitor binds to loopback and only answers reads."""
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def test_panel_loopback_read_only(tmp_path):
    from uc3m.presentation.training_panel import make_server
    import threading
    server = make_server(tmp_path, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        assert host == '127.0.0.1'
        request = urllib.request.Request(f'http://127.0.0.1:{port}/api/runs', data=b'{}', method='POST')
        with pytest.raises(urllib.error.HTTPError) as refused:
            urllib.request.urlopen(request, timeout=5)
        assert refused.value.code in (405, 501)
    finally:
        server.shutdown()
        server.server_close()
