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


def source_snapshot(project_root: Path) -> str:
    root = Path(project_root).resolve()
    # Only text sources (.py/.yaml/.toml/config .json/requirements) are hashed.
    return hash_files(root, _source_paths(root), normalize_newlines=True)


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


def archive_sources(project_root: Path, destination: Path) -> str:
    """Preserve actual source bytes, including uncommitted local changes.

    The returned digest equals source_snapshot: it hashes CRLF as LF like the
    snapshot does, while the archive keeps the raw bytes.
    """
    root = Path(project_root).resolve()
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix='.tmp', delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in _source_paths(root):
                name = path.relative_to(root).as_posix()
                payload = path.read_bytes()
                digest.update(name.encode('utf-8') + b'\0' + payload.replace(b'\r\n', b'\n') + b'\0')
                archive.writestr(name, payload)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return digest.hexdigest()
