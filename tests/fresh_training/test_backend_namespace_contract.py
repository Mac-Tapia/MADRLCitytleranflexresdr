"""Backend namespace declarations never whitelist arbitrary project imports."""
from tools.ops.audit_github_readiness import undeclared_runtime_imports


def test_backend_namespace_is_scoped_to_consumer_and_import_context(tmp_path):
    relative = 'uc3m/adapters/citylearn/policy_inference.py'
    target = tmp_path/relative
    target.parent.mkdir(parents=True)
    (tmp_path/'pyproject.toml').write_text(
        '[project]\nname="fixture"\ndependencies=[]\n'
        '[tool.uc3m.backend-namespaces]\n'
        f'common={{root="external/MARL/src", consumers=["{relative}"]}}\n', encoding='utf-8')
    target.write_text('import common\n', encoding='utf-8')
    assert undeclared_runtime_imports(tmp_path) == {'common': relative}
    target.write_text('with _backend_import_scope(root, names):\n    import common\n', encoding='utf-8')
    assert undeclared_runtime_imports(tmp_path) == {}
    other = tmp_path/'uc3m/other.py'
    other.write_text('with _backend_import_scope(root, names):\n    import common\n', encoding='utf-8')
    assert undeclared_runtime_imports(tmp_path) == {'common': 'uc3m/other.py'}
