"""Actual loopback HTTP requests: rejection consumes its bounded body."""
import http.client
import threading

import pytest

from uc3m.presentation.training_panel import make_server


def test_write_methods_return_405_without_aborting_and_never_change_files(tmp_path):
    server = make_server(tmp_path, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            for _ in range(16):
                connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
                try:
                    connection.request(method, '/api/runs', body=b'x'*2048)
                    response = connection.getresponse()
                    assert response.status == 405
                    assert response.getheader('Allow') == 'GET'
                    assert response.getheader('Cache-Control') == 'no-store'
                    assert response.read() == b''
                finally:
                    connection.close()
        assert list(tmp_path.iterdir()) == []
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_slow_body_cannot_extend_the_total_rejection_deadline(tmp_path):
    server = make_server(tmp_path, port=0)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
    stop = threading.Event()
    sender = None
    try:
        connection.putrequest('POST', '/api/runs')
        connection.putheader('Content-Length', '5')
        connection.endheaders()
        connection.send(b'x')

        def drip():
            for _ in range(4):
                if stop.wait(0.75):
                    return
                try:
                    connection.send(b'x')
                except OSError:
                    return

        sender = threading.Thread(target=drip, daemon=True)
        sender.start()
        with pytest.raises((http.client.RemoteDisconnected, ConnectionResetError, ConnectionAbortedError)):
            connection.getresponse()
    finally:
        stop.set()
        connection.close()
        if sender is not None:
            sender.join(timeout=2)
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)
