"""Content identities for datasets and source snapshots, not schema-only hashes."""
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path


def hash_files(root, paths, *, normalize_newlines=False):
    """normalize_newlines hashes CRLF as LF so a Windows checkout (core.autocrlf)
    and a Linux/Colab checkout of the same text files share one digest."""
    digest = hashlib.sha256()
    for path in sorted(set(paths)):
        digest.update(path.relative_to(root).as_posix().encode('utf-8') + b'\0')
        if normalize_newlines:
            digest.update(path.read_bytes().replace(b'\r\n', b'\n'))
        else:
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024*1024), b''):
                    digest.update(chunk)
        digest.update(b'\0')
    return digest.hexdigest()


def dataset_digest(schema_path: Path) -> str:
    schema_path = Path(schema_path).resolve()
    payload = json.loads(schema_path.read_text(encoding='utf-8'))
    root = schema_path.parent
    if payload.get('root_directory') not in (None, '', '.', str(root)):
        raise ValueError('dataset root_directory must resolve to schema directory')
    references = []
    def visit(value):
        if isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str) and value.lower().endswith(('.csv', '.json')):
            path = (root/value).resolve()
            try:
                path.relative_to(root)
            except ValueError as exc:
                raise ValueError('dataset reference escapes root') from exc
            if not path.is_file():
                raise ValueError(f'missing dataset file: {value}')
            references.append(path)
    visit(payload)
    # Every dataset file is CSV or JSON text, so line endings are not content.
    return hash_files(root, [schema_path] + references, normalize_newlines=True)


def source_snapshot(project_root: Path, *, scope='legacy') -> str:
    root = Path(project_root).resolve()
    # Only text sources (.py/.yaml/.toml/config .json/requirements) are hashed.
    return hash_files(root, _scoped_paths(root, scope), normalize_newlines=True)


# The fresh campaign identity also covers dataset builders, evaluators, quality
# gates, governance registries and the lockfile, never secrets or outputs.
_FRESH_FOLDERS = ('uc3m', 'configs', 'governance', 'tools/dataset', 'tools/eval', 'tools/ops',
                  'scripts/quality', 'scripts/maintenance', 'CityLearn/configs',
                  'CityLearn/citylearn', 'CityLearn/scripts', 'external')
_FRESH_SUFFIXES = {'.py', '.yaml', '.yml', '.toml', '.ps1', '.cfg'}
_FRESH_ROOT_FILES = ('pyproject.toml', 'uv.lock', 'requirements.txt', 'requirements-dev.txt')
_SECRET_MARKERS = ('secret', 'token', 'credential', 'password')
_SECRET_SUFFIXES = {'.key', '.pem', '.pfx', '.p12'}


def _is_secret(path):
    name = path.name.casefold()
    return (name.startswith('.env') or path.suffix.casefold() in _SECRET_SUFFIXES
            or any(marker in name for marker in _SECRET_MARKERS))


def fresh_source_paths(project_root: Path):
    root = Path(project_root).resolve()
    paths = []
    for folder in _FRESH_FOLDERS:
        for path in (root/folder).rglob('*'):
            allowed = (path.suffix in _FRESH_SUFFIXES
                       or (folder.endswith('configs') and path.suffix == '.json'))
            if (path.is_file() and allowed and '.git' not in path.parts
                    and '__pycache__' not in path.parts and not _is_secret(path)):
                paths.append(path)
    paths.extend(root/name for name in _FRESH_ROOT_FILES if (root/name).is_file())
    return sorted(set(paths))


def _scoped_paths(root, scope):
    if scope == 'legacy':
        return _source_paths(root)
    if scope == 'fresh':
        return fresh_source_paths(root)
    raise ValueError(f'unknown source scope: {scope}')


def _source_paths(root):
    paths = []
    for folder in ('uc3m', 'configs', 'CityLearn/configs', 'CityLearn/citylearn', 'CityLearn/scripts', 'external'):
        for path in (root/folder).rglob('*'):
            allowed = (path.suffix in {'.py', '.yaml', '.yml', '.toml'}
                       or path.name in {'requirements.txt', 'setup.cfg'}
                       or (folder.endswith('configs') and path.suffix == '.json'))
            if path.is_file() and allowed and '.git' not in path.parts:
                paths.append(path)
    paths.extend(path for path in (root/'pyproject.toml', root/'requirements.txt') if path.is_file())
    return sorted(paths)


def archive_sources(project_root: Path, destination: Path, *, scope='legacy') -> str:
    """Preserve actual source bytes, including uncommitted local changes.

    The returned digest equals source_snapshot for the same scope: it hashes
    CRLF as LF like the snapshot does, while the archive keeps the raw bytes.
    """
    root = Path(project_root).resolve()
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix='.tmp', delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in _scoped_paths(root, scope):
                name = path.relative_to(root).as_posix()
                payload = path.read_bytes()
                digest.update(name.encode('utf-8') + b'\0' + payload.replace(b'\r\n', b'\n') + b'\0')
                archive.writestr(name, payload)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return digest.hexdigest()
