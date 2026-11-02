"""P12/A25: the inference demo is fenced off from plant control.

Without an accepted model the service is alive but not ready; a stub policy
exists only on explicit opt-in and is never eligible to drive a plant; inputs
of the wrong shape or with NaN/Inf are refused and non-finite outputs are never
clipped into setpoints. The plant adapter writes nothing unless the response
says the policy is control-eligible and the operator authorized writes. The
local monitor binds to loopback and only answers reads. HTTP runs in-process
(FastAPI TestClient); no port is published and no plant is contacted. None of
this is operational (OT) acceptance: that stays a separate, independent step.
"""
import importlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parents[2]
INFERENCE = REPO/'deploy/inference'
PLANT = REPO/'deploy/plant_adapter'


@pytest.fixture()
def service(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(INFERENCE))
    monkeypatch.delenv('MONGODB_URI', raising=False)
    monkeypatch.delenv('INFERENCE_DEMO_STUB', raising=False)
    monkeypatch.setenv('MODEL_PATH', str(tmp_path/'missing.onnx'))
    monkeypatch.setenv('MODEL_METADATA_PATH', str(tmp_path/'missing.metadata.json'))
    for name in ('app', 'model_loader', 'mongo_store'):
        sys.modules.pop(name, None)
    module = importlib.import_module('app')
    yield module
    for name in ('app', 'model_loader', 'mongo_store'):
        sys.modules.pop(name, None)


def _metadata(tmp_path, monkeypatch, **extra):
    payload = {'algorithm': 'matd3', 'scenario': 'E1', 'obs_dim': 3, 'action_dim': 1, 'n_agents': 2,
               'action_space': {'low': [-1.0], 'high': [1.0]}, **extra}
    path = tmp_path/'meta.json'
    path.write_text(json.dumps(payload), encoding='utf-8')
    monkeypatch.setenv('MODEL_METADATA_PATH', str(path))


def test_no_model_is_not_ready(service):
    with TestClient(service.app) as client:
        health = client.get('/health').json()
        assert health['status'] == 'ok' and health['model_loaded'] is False
        assert health['ready'] is False and health['operational_ready'] is False
        assert client.get('/ready').status_code == 503
        assert client.post('/act', json={'observations': [[0.0, 0.0, 0.0]]*2}).status_code == 503


def test_stub_requires_explicit_opt_in_and_is_never_control_eligible(service, monkeypatch, tmp_path):
    _metadata(tmp_path, monkeypatch)
    monkeypatch.setenv('INFERENCE_DEMO_STUB', '1')
    with TestClient(service.app) as client:
        assert client.get('/ready').status_code == 503
        body = client.post('/act', json={'observations': [[0.0, 0.0, 0.0]]*2}).json()
        assert body['is_stub'] is True and body['control_eligible'] is False
        assert client.get('/health').json()['ready'] is False


def test_stub_cannot_send_plant_actions(service, monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(PLANT))
    sys.modules.pop('modbus_adapter', None)
    plant = importlib.import_module('modbus_adapter')
    _metadata(tmp_path, monkeypatch)
    monkeypatch.setenv('INFERENCE_DEMO_STUB', '1')
    monkeypatch.setenv('PLANT_WRITE_AUTHORIZED', '1')
    with TestClient(service.app) as client:
        result = client.post('/act', json={'observations': [[0.0, 0.0, 0.0]]*2}).json()
    with pytest.raises(PermissionError, match='not control-eligible'):
        plant.actions_for_plant(result)
    eligible = dict(result, is_stub=False, control_eligible=True)
    monkeypatch.delenv('PLANT_WRITE_AUTHORIZED')
    with pytest.raises(PermissionError, match='PLANT_WRITE_AUTHORIZED'):
        plant.actions_for_plant(eligible)
    monkeypatch.setenv('PLANT_WRITE_AUTHORIZED', '1')
    assert plant.actions_for_plant(eligible).shape == (2, 1)
    with pytest.raises(ValueError):
        plant.actions_for_plant(dict(eligible, actions=[[float('nan')], [0.0]]))
    sys.modules.pop('modbus_adapter', None)


@pytest.mark.parametrize('observations', [
    [[0.0, 0.0, 0.0]],                       # one agent, two declared
    [[0.0, 0.0], [0.0, 0.0]],                # wrong observation width
    [[0.0, 0.0, 0.0]]*3,
    [0.0, 0.0, 0.0],                         # not 2-D
])
def test_wrong_shape_is_refused(service, monkeypatch, tmp_path, observations):
    _metadata(tmp_path, monkeypatch)
    monkeypatch.setenv('INFERENCE_DEMO_STUB', '1')
    with TestClient(service.app) as client:
        assert client.post('/act', json={'observations': observations}).status_code == 422


def test_non_finite_observations_are_refused(service, monkeypatch, tmp_path):
    _metadata(tmp_path, monkeypatch)
    monkeypatch.setenv('INFERENCE_DEMO_STUB', '1')
    model_loader = sys.modules['model_loader']
    bundle = model_loader.ModelBundle.load(tmp_path/'missing.onnx', tmp_path/'meta.json', allow_stub=True)
    for bad in (float('nan'), float('inf')):
        with pytest.raises(ValueError, match='finite'):
            bundle.validate_observations(np.array([[0.0, bad, 0.0], [0.0, 0.0, 0.0]], dtype=np.float32))


class _Session:
    def __init__(self, outputs):
        self.outputs = np.asarray(outputs, dtype=np.float32)

    def get_inputs(self):
        return [type('Input', (), {'name': 'obs'})()]

    def run(self, _names, _feed):
        return [self.outputs]


def test_non_finite_model_output_is_not_clipped_into_setpoints(service, tmp_path):
    model_loader = sys.modules['model_loader']
    meta = model_loader.ModelMetadata.from_dict({'obs_dim': 3, 'action_dim': 1, 'n_agents': 2,
                                                 'action_space': {'low': [-1.0], 'high': [1.0]}})
    bundle = model_loader.ModelBundle(session=_Session([[np.nan], [0.0]]), metadata=meta, is_stub=False)
    with pytest.raises(ValueError, match='finite'):
        bundle.act(np.zeros((2, 3), dtype=np.float32))


def test_out_of_bounds_output_is_reported(service, tmp_path):
    model_loader = sys.modules['model_loader']
    meta = model_loader.ModelMetadata.from_dict({'obs_dim': 3, 'action_dim': 1, 'n_agents': 2,
                                                 'action_space': {'low': [-1.0], 'high': [1.0]}})
    bundle = model_loader.ModelBundle(session=_Session([[3.0], [0.5]]), metadata=meta, is_stub=False)
    actions = bundle.act(np.zeros((2, 3), dtype=np.float32))
    assert actions.tolist() == [[1.0], [0.5]]
    assert bundle.last_clipped == 1


def test_real_model_without_operational_acceptance_is_not_control_eligible(service):
    model_loader = sys.modules['model_loader']
    meta = model_loader.ModelMetadata.from_dict({'obs_dim': 3, 'action_dim': 1, 'n_agents': 2})
    assert model_loader.ModelBundle(session=_Session([[0.0], [0.0]]), metadata=meta,
                                    is_stub=False).control_eligible is False
    accepted = model_loader.ModelMetadata.from_dict({'obs_dim': 3, 'action_dim': 1, 'n_agents': 2,
                                                     'acceptance': {'operational_acceptance': True}})
    assert model_loader.ModelBundle(session=_Session([[0.0], [0.0]]), metadata=accepted,
                                    is_stub=False).control_eligible is True
    assert model_loader.ModelBundle(session=None, metadata=accepted, is_stub=True).control_eligible is False


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


def test_demo_compose_publishes_only_on_loopback_and_declares_the_stub():
    import yaml
    compose = yaml.safe_load((REPO/'deploy/docker-compose.yml').read_text(encoding='utf-8'))
    for name, service in compose['services'].items():
        for port in service.get('ports') or []:
            assert str(port).startswith('127.0.0.1:'), f'{name} publishes {port} beyond loopback'
    environment = compose['services']['inference'].get('environment') or {}
    if isinstance(environment, list):
        environment = dict(item.split('=', 1) for item in environment)
    assert str(environment.get('INFERENCE_DEMO_STUB')) == '1'
    # The anonymous broker listens on the private compose network; it is reachable
    # from the host only through the loopback publication checked above.
    broker = (REPO/'deploy/mosquitto.conf').read_text(encoding='utf-8')
    assert 'allow_anonymous true' not in broker or 'demo' in broker.lower()
