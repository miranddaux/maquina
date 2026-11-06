"""Read-only, version-pinned mascots and an opt-in adapter for reviewed SQL schemas.

Importing this module never creates a directory, database, migration or selection.
The file registry is the source of truth until a SQL migration is approved separately.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import struct


NICO_PALETTE = {
    'yellow': '#F5C63D', 'navy': '#25344D', 'brown': '#433025',
    'skin': '#C58C65', 'pink': '#EBA0A0', 'white': '#F1EEE7',
    'orange': '#F18A41', 'gray': '#313A35',
}
PIN_KEYS = ('id', 'version', 'config_sha256', 'geometry_version', 'animation_version')
_ID = re.compile(r'[a-z][a-z0-9_-]{0,63}')
_VERSION = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?')
_COMPONENT_VERSION = re.compile(r'(?:[a-z][a-z0-9-]*-)?[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?')
_SHA256 = re.compile(r'[a-f0-9]{64}')
_HEX = re.compile(r'#[0-9A-Fa-f]{6}')


class MascotValidationError(ValueError):
    """An invalid, modified, missing or unapproved mascot must not render silently."""


def canonical_json(value):
    """Encoding shared with the TypeScript build; UTF-8, sorted keys, no whitespace."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def config_sha256(config):
    return hashlib.sha256(canonical_json(config).encode('utf8')).hexdigest()


def _check_name(value, pattern, label):
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise MascotValidationError('Invalid mascot ' + label + '.')
    return value


def _no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MascotValidationError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def _read_json(path):
    try:
        if path.stat().st_size > 2 * 1024 * 1024:
            raise MascotValidationError('Mascot metadata exceeds 2 MiB.')
        value = json.loads(path.read_text(encoding='utf8'), object_pairs_hook=_no_duplicate_keys)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MascotValidationError('Cannot read mascot metadata: ' + path.name) from exc
    if not isinstance(value, dict):
        raise MascotValidationError('Mascot metadata must be a JSON object.')
    return value


def validate_config(config):
    if not isinstance(config, dict):
        raise MascotValidationError('Mascot config must be an object.')
    for key in ('id', 'version', 'status', 'palette', 'geometry_version', 'animation_version'):
        if key not in config:
            raise MascotValidationError('Missing mascot configuration: ' + key)
    _check_name(config['id'], _ID, 'id')
    _check_name(config['version'], _VERSION, 'version')
    for key in ('geometry_version', 'animation_version'):
        _check_name(config[key], _COMPONENT_VERSION, key)
    if config['status'] not in ('candidate', 'approved', 'retired'):
        raise MascotValidationError('Mascot status must be candidate, approved or retired.')
    palette = config['palette']
    if not isinstance(palette, dict) or not palette:
        raise MascotValidationError('Mascot palette must contain named RGB colors.')
    for name, color in palette.items():
        if not isinstance(name, str) or not isinstance(color, str) or not _HEX.fullmatch(color):
            raise MascotValidationError('Palette colors must use RGB hexadecimal #RRGGBB.')
    if config['id'] == 'nico':
        for name, color in NICO_PALETTE.items():
            if palette.get(name, '').upper() != color:
                raise MascotValidationError('NICO palette differs from the reference direction: ' + name)
        geometry = config.get('geometry')
        required_geometry = ('totalHeight', 'headWidth', 'headHeight', 'headDepth', 'headCenterY', 'bodyWidth', 'bodyHeight', 'bodyDepth', 'limbRadius', 'headFraction', 'torsoFraction', 'legsFeetFraction')
        if not isinstance(geometry, dict):
            raise MascotValidationError('NICO needs centralized geometry parameters.')
        for key in required_geometry:
            value = geometry.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise MascotValidationError('Invalid NICO geometry parameter: ' + key)
        if not math.isclose(sum(geometry[key] for key in ('headFraction', 'torsoFraction', 'legsFeetFraction')), 1, abs_tol=1e-6):
            raise MascotValidationError('NICO body proportions must total one.')
        required_animations = {'idle', 'walk', 'run', 'talk', 'point', 'wave', 'celebrate'}
        animations = config.get('animations')
        if not isinstance(animations, list) or any(not isinstance(item, str) for item in animations) or set(animations) != required_animations or len(animations) != 7:
            raise MascotValidationError('NICO needs all seven reusable animation names.')
        expected_roles = {'hoodie': 'yellow', 'backpack': 'navy', 'trousers': 'navy', 'hair': 'brown', 'skin': 'skin', 'cheeks': 'pink', 'sneakers': 'white', 'shoeSoles': 'orange', 'pupils': 'gray'}
        if config.get('roles') != expected_roles:
            raise MascotValidationError('NICO component colors must preserve the reference direction.')
        consistency = config.get('consistency', {})
        if consistency.get('randomizedGeometry') is not False or consistency.get('allowPerVideoPaletteOverride') is not False or consistency.get('requiresExplicitVersion') is not True:
            raise MascotValidationError('NICO requires deterministic geometry, palette and explicit versions.')
    try:
        canonical_json(config)
    except (ValueError, TypeError) as exc:
        raise MascotValidationError('Configuration must contain finite JSON values.') from exc
    return deepcopy(config)


def validate_pin(pin):
    if not isinstance(pin, dict) or set(pin) != set(PIN_KEYS):
        raise MascotValidationError('An explicit complete mascot version snapshot is required.')
    _check_name(pin['id'], _ID, 'id')
    _check_name(pin['version'], _VERSION, 'version')
    for key in ('geometry_version', 'animation_version'):
        _check_name(pin[key], _COMPONENT_VERSION, key)
    _check_name(pin['config_sha256'], _SHA256, 'checksum')
    return deepcopy(pin)


def _pin_config(config):
    return {
        'id': config['id'], 'version': config['version'],
        'config_sha256': config_sha256(config),
        'geometry_version': config['geometry_version'],
        'animation_version': config['animation_version'],
    }


class MascotRegistry:
    """Exact-version reader. No selection defaults and no configuration mutation API."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.directory = (self.root / 'shared' / 'mascots').resolve()
        if not self.directory.is_relative_to(self.root):
            raise MascotValidationError('Mascot registry must stay inside the project.')

    def _version_path(self, mascot_id, version):
        _check_name(mascot_id, _ID, 'id')
        _check_name(version, _VERSION, 'version')
        path = (self.directory / mascot_id / version).resolve()
        if not path.is_relative_to(self.directory):
            raise MascotValidationError('Mascot path escapes the version registry.')
        return path

    def _asset_path(self, path):
        if not isinstance(path, str) or not path or Path(path).is_absolute() or '\\' in path:
            raise MascotValidationError('Asset paths must be project-relative paths.')
        resolved = (self.root / path).resolve()
        if not resolved.is_relative_to(self.root):
            raise MascotValidationError('Mascot asset escapes the project.')
        return resolved

    def _read_version(self, mascot_id, version):
        directory = self._version_path(mascot_id, version)
        config_path = (directory / 'config.json').resolve()
        manifest_path = (directory / 'manifest.json').resolve()
        if not config_path.is_relative_to(directory) or not manifest_path.is_relative_to(directory):
            raise MascotValidationError('Version metadata must stay in its version directory.')
        config = validate_config(_read_json(config_path))
        manifest = _read_json(manifest_path)
        if config['id'] != mascot_id or config['version'] != version:
            raise MascotValidationError('Config identity does not match its version path.')
        if manifest.get('id') != mascot_id or manifest.get('version') != version:
            raise MascotValidationError('Manifest identity does not match its version path.')
        checksum = config_sha256(config)
        if manifest.get('config_sha256') != checksum:
            raise MascotValidationError('Mascot configuration checksum mismatch.')
        assets = manifest.get('assets', [])
        if not isinstance(assets, list):
            raise MascotValidationError('Manifest assets must be a list.')
        for asset in assets:
            if not isinstance(asset, dict) or not isinstance(asset.get('kind'), str):
                raise MascotValidationError('Manifest asset needs a kind.')
            if asset.get('status') == 'pending_original_bytes':
                if asset.get('path') or asset.get('sha256'):
                    raise MascotValidationError('Pending reference bytes cannot be claimed as stored.')
                continue
            asset_path = self._asset_path(asset.get('path'))
            _check_name(asset.get('sha256'), _SHA256, 'asset checksum')
            try:
                with asset_path.open('rb') as source:
                    actual = hashlib.file_digest(source, 'sha256').hexdigest()
            except OSError as exc:
                raise MascotValidationError('Missing versioned mascot asset.') from exc
            if actual != asset['sha256']:
                raise MascotValidationError('Mascot asset checksum mismatch: ' + asset['path'])
        return config, manifest

    def load(self, mascot_id, version, *, require_approved=False):
        config, manifest = self._read_version(mascot_id, version)
        if require_approved and config['status'] != 'approved':
            raise MascotValidationError('This mascot version still needs visual approval.')
        if require_approved and config['id']=='nico':
            assets=manifest.get('assets',[])
            if any(a.get('status')=='pending_original_bytes' for a in assets):raise MascotValidationError('Original reference assets still need archiving before production.')
            if not any(a.get('kind')=='model' and str(a.get('path','')).endswith('.glb') for a in assets):raise MascotValidationError('Approved production needs the canonical GLB asset.')
            if sum(a.get('kind')=='reference' and bool(a.get('path')) for a in assets)<2:raise MascotValidationError('Both approved original reference files must be archived.')
            model=next(a for a in assets if a.get('kind')=='model' and str(a.get('path','')).endswith('.glb'))
            data=(self.root/model['path']).read_bytes()
            if len(data)<20 or data[:4]!=b'glTF' or struct.unpack_from('<I',data,4)[0]!=2 or struct.unpack_from('<I',data,8)[0]!=len(data):raise MascotValidationError('Canonical model is not a valid GLB2 asset.')
            length,kind=struct.unpack_from('<II',data,12)
            if kind!=0x4E4F534A or length>2*1024*1024:raise MascotValidationError('GLB model metadata is invalid.')
            try:document=json.loads(data[20:20+length])
            except (ValueError,UnicodeError):raise MascotValidationError('GLB model metadata is invalid.') from None
            metadata=[n.get('extras',{}) for n in document.get('nodes',[]) if isinstance(n,dict)]
            expected={'mascotId':config['id'],'modelVersion':config['version'],'configSha256':config_sha256(config),'geometryVersion':config['geometry_version'],'animationVersion':config['animation_version']}
            if not any(all(extra.get(k)==v for k,v in expected.items()) for extra in metadata):raise MascotValidationError('GLB model version does not match its approved configuration pin.')

        return deepcopy(config)

    def pin(self, mascot_id, version, *, require_approved=False):
        config = self.load(mascot_id, version, require_approved=require_approved)
        return _pin_config(config)

    def resolve(self, snapshot, *, require_approved=False):
        pin = validate_pin(snapshot)
        config = self.load(pin['id'], pin['version'], require_approved=require_approved)
        actual = _pin_config(config)
        if actual != pin:
            raise MascotValidationError('Pinned mascot changed; create a new version instead.')
        return config

    def catalog(self):
        """Report invalid versions explicitly, without substituting another version."""
        versions, errors = [], []
        if self.directory.is_dir():
            for config_path in sorted(self.directory.glob('*/*/config.json')):
                mascot_id, version = config_path.parent.parent.name, config_path.parent.name
                try:
                    config, manifest = self._read_version(mascot_id, version)
                    versions.append({
                        **_pin_config(config), 'status': config['status'],
                        'name': config.get('display_name', config.get('name', mascot_id)), 'assets': manifest.get('assets', []),
                    })
                except MascotValidationError as exc:
                    errors.append({'id': mascot_id, 'version': version, 'error': str(exc)})
        return {'mascots': versions, 'count': len(versions), 'errors': errors}


class SqliteMascotStore:
    """Optional adapter; opens only an existing, explicitly approved schema, never DDL.

    The host owns the connection lifecycle. `approved_schema=True` must only follow
    the user's approval and separate execution of the reviewed migration.
    """
    _COLUMNS = {
        'mascot_versions': {'mascot_id', 'version', 'status', 'config_sha256', 'geometry_version', 'animation_version', 'config_json'},
        'mascot_assets': {'mascot_id', 'mascot_version', 'kind', 'path', 'sha256'},
        'video_mascots': {'video_id', 'mascot_id', 'mascot_version', 'config_sha256', 'geometry_version', 'animation_version'},
    }

    def __init__(self, database_path, *, approved_schema=False):
        if not approved_schema:
            raise MascotValidationError('Review and approve the SQL proposal before opening a database.')
        path = Path(database_path).resolve()
        if not path.is_file():
            raise MascotValidationError('Existing SQLite database required; automatic creation is disabled.')
        self.connection = sqlite3.connect(path.as_uri() + '?mode=rw', uri=True)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys = ON')
        try:
            for table, required in self._COLUMNS.items():
                columns = {row['name'] for row in self.connection.execute('PRAGMA table_info(' + table + ')')}
                if not required.issubset(columns):
                    raise MascotValidationError('Reviewed mascot SQL schema is not installed: ' + table)
        except Exception:
            self.connection.close()
            raise

    def close(self):
        self.connection.close()

    def register_version(self, registry, mascot_id, version):
        """Insert once; a changed existing version is rejected, including candidates."""
        config, manifest = registry._read_version(mascot_id, version)
        pin = _pin_config(config)
        serialized = canonical_json(config)
        with self.connection:
            existing = self.connection.execute(
                'SELECT config_json, config_sha256 FROM mascot_versions WHERE mascot_id=? AND version=?',
                (mascot_id, version),
            ).fetchone()
            if existing:
                if existing['config_json'] != serialized or existing['config_sha256'] != pin['config_sha256']:
                    raise MascotValidationError('Registered mascot versions are immutable; publish a new version.')
                registered_assets = sorted(tuple(row) for row in self.connection.execute(
                    'SELECT kind,path,sha256 FROM mascot_assets WHERE mascot_id=? AND mascot_version=?',
                    (mascot_id, version),
                ))
                manifest_assets = sorted((asset['kind'], asset['path'], asset['sha256'])
                                         for asset in manifest.get('assets', [])
                                         if asset.get('status') != 'pending_original_bytes')
                if registered_assets != manifest_assets:
                    raise MascotValidationError('Registered mascot assets are immutable; publish a new version.')
                return pin
            self.connection.execute(
                'INSERT INTO mascot_versions (mascot_id,version,status,config_sha256,geometry_version,animation_version,config_json) VALUES (?,?,?,?,?,?,?)',
                (mascot_id, version, config['status'], pin['config_sha256'], pin['geometry_version'], pin['animation_version'], serialized),
            )
            for asset in manifest.get('assets', []):
                if asset.get('status') == 'pending_original_bytes':
                    continue
                self.connection.execute(
                    'INSERT INTO mascot_assets (mascot_id,mascot_version,kind,path,sha256) VALUES (?,?,?,?,?)',
                    (mascot_id, version, asset['kind'], asset['path'], asset['sha256']),
                )
        return pin

    def assign_video(self, video_id, snapshot):
        pin = validate_pin(snapshot)
        if not isinstance(video_id, str) or not video_id or len(video_id) > 128 or '\x00' in video_id:
            raise MascotValidationError('Video identity is required.')
        expected = (pin['id'], pin['version'], pin['config_sha256'], pin['geometry_version'], pin['animation_version'])
        with self.connection:
            row = self.connection.execute(
                'SELECT mascot_id,version,config_sha256,geometry_version,animation_version FROM mascot_versions WHERE mascot_id=? AND version=?',
                (pin['id'], pin['version']),
            ).fetchone()
            if row is None or tuple(row) != expected:
                raise MascotValidationError('Video pin does not match a registered version.')
            existing = self.video_pin(video_id)
            if existing is not None:
                if existing != pin:
                    raise MascotValidationError('Existing video mascot assignment is immutable.')
                return pin
            self.connection.execute(
                'INSERT INTO video_mascots (video_id,mascot_id,mascot_version,config_sha256,geometry_version,animation_version) VALUES (?,?,?,?,?,?)',
                (video_id,) + expected,
            )
        return pin

    def video_pin(self, video_id):
        row = self.connection.execute(
            'SELECT mascot_id,mascot_version,config_sha256,geometry_version,animation_version FROM video_mascots WHERE video_id=?',
            (video_id,),
        ).fetchone()
        return dict(zip(PIN_KEYS, tuple(row))) if row else None


def configured_sql_store(environ=None):
    """Opt in only after schema review; never create a DB or apply DDL."""
    import os
    values=os.environ if environ is None else environ
    path=values.get('CURIOLAB_MASCOT_SQLITE_PATH')
    if not path:return None
    if values.get('CURIOLAB_MASCOT_SCHEMA_APPROVED')!='1':
        raise MascotValidationError('SQL integration requires explicit reviewed-schema approval.')
    return SqliteMascotStore(path,approved_schema=True)
