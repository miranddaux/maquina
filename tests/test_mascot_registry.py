from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from mascot_registry import MascotRegistry, MascotValidationError, NICO_PALETTE, SqliteMascotStore, config_sha256, validate_config


ROOT = Path(__file__).resolve().parents[1]


def example_config(version='1.0.0-candidate.1', status='candidate'):
    return {
        'id': 'nico', 'version': version, 'status': status,
        'geometry_version': 'lite-humanoid-1.0.0', 'animation_version': 'lite-rig-1.0.0',
        'palette': deepcopy(NICO_PALETTE),
        'geometry': {'totalHeight': 2.8, 'headWidth': 1, 'headHeight': .91, 'headDepth': .8, 'headCenterY': 2.23, 'bodyWidth': .76, 'bodyHeight': .84, 'bodyDepth': .46, 'limbRadius': .12, 'headFraction': .36, 'torsoFraction': .30, 'legsFeetFraction': .34},
        'roles': {'hoodie': 'yellow', 'backpack': 'navy', 'trousers': 'navy', 'hair': 'brown', 'skin': 'skin', 'cheeks': 'pink', 'sneakers': 'white', 'shoeSoles': 'orange', 'pupils': 'gray'},
        'animations': ['idle', 'walk', 'run', 'talk', 'point', 'wave', 'celebrate'],
        'consistency': {'randomizedGeometry': False, 'allowPerVideoPaletteOverride': False, 'requiresExplicitVersion': True},
    }


class MascotRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.registry = MascotRegistry(self.root)
        self.config = example_config()
        self.publish(self.config)

    def tearDown(self):
        self.temp.cleanup()

    def publish(self, config, assets=None):
        directory = self.root / 'shared/mascots' / config['id'] / config['version']
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'config.json').write_text(json.dumps(config), encoding='utf8')
        (directory / 'manifest.json').write_text(json.dumps({
            'id': config['id'], 'version': config['version'], 'config_sha256': config_sha256(config),
            'assets': assets or [{'kind': 'reference', 'status': 'pending_original_bytes'}],
        }), encoding='utf8')
        return directory

    def test_real_candidate_loads_without_sql_or_creation_on_import(self):
        candidate = MascotRegistry(ROOT).load('nico', '1.0.0-candidate.1')
        self.assertEqual(candidate['status'], 'candidate')
        self.assertEqual(candidate['palette'], NICO_PALETTE)
        self.assertFalse((self.root / '.local').exists())

    def test_candidate_preview_allowed_but_not_falsely_approved(self):
        pin = self.registry.pin('nico', self.config['version'])
        self.assertEqual(self.registry.resolve(pin)['status'], 'candidate')
        with self.assertRaisesRegex(MascotValidationError, 'visual approval'):
            self.registry.resolve(pin, require_approved=True)

    def test_palette_roles_animation_and_geometry_validation(self):
        invalids = []
        for change in ('palette', 'roles', 'animations', 'geometry', 'consistency', 'version'):
            config = deepcopy(self.config)
            if change == 'palette': config['palette']['yellow'] = '#EEEEEE'
            if change == 'roles': config['roles']['hoodie'] = 'navy'
            if change == 'animations': config['animations'].remove('wave')
            if change == 'geometry': config['geometry']['headWidth'] = -1
            if change == 'consistency': config['consistency']['randomizedGeometry'] = True
            if change == 'version': config['version'] = 'latest'
            invalids.append(config)
        for config in invalids:
            with self.subTest(config=config), self.assertRaises(MascotValidationError):
                validate_config(config)

    def test_additional_mascot_can_have_its_own_palette(self):
        config = {'id': 'robot', 'version': '1.0.0', 'status': 'candidate', 'geometry_version': 'robot-1.0.0', 'animation_version': 'lite-rig-1.0.0', 'palette': {'shell': '#00AACC'}}
        self.publish(config)
        self.assertEqual(self.registry.pin('robot', '1.0.0')['id'], 'robot')

    def test_frozen_snapshot_stays_on_exact_version_and_detects_rewritten_config(self):
        pin = self.registry.pin('nico', self.config['version'])
        self.publish(example_config('1.0.0', 'approved'))
        self.assertEqual(self.registry.resolve(pin)['version'], '1.0.0-candidate.1')
        changed = deepcopy(self.config)
        changed['geometry']['bodyWidth'] = .8
        self.publish(changed)
        with self.assertRaisesRegex(MascotValidationError, 'Pinned mascot changed'):
            self.registry.resolve(pin)

    def test_stale_manifest_is_rejected_and_catalog_reports_error(self):
        directory = self.root / 'shared/mascots/nico' / self.config['version']
        changed = deepcopy(self.config)
        changed['geometry']['bodyWidth'] = .8
        (directory / 'config.json').write_text(json.dumps(changed))
        with self.assertRaisesRegex(MascotValidationError, 'checksum mismatch'):
            self.registry.load('nico', self.config['version'])
        catalog = self.registry.catalog()
        self.assertEqual(catalog['count'], 0)
        self.assertEqual(len(catalog['errors']), 1)

    def test_paths_and_metadata_symlinks_cannot_escape(self):
        for mascot_id, version in [('../nico', '1.0.0'), ('nico', '../../outside'), ('nico', 'latest')]:
            with self.subTest(mascot_id=mascot_id, version=version), self.assertRaises(MascotValidationError):
                self.registry.load(mascot_id, version)
        outside = self.root / 'outside.json'
        outside.write_text(json.dumps(self.config))
        path = self.root / 'shared/mascots/nico' / self.config['version'] / 'config.json'
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaisesRegex(MascotValidationError, 'version directory'):
            self.registry.load('nico', self.config['version'])

    def test_asset_bytes_validated_and_pending_references_are_not_fabricated(self):
        asset = self.root / 'public/mascots/nico/model.glb'
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b'example model asset')
        metadata = {'kind': 'model', 'path': 'public/mascots/nico/model.glb', 'sha256': hashlib.sha256(asset.read_bytes()).hexdigest()}
        self.publish(self.config, [metadata])
        self.registry.load('nico', self.config['version'])
        asset.write_bytes(b'changed model')
        with self.assertRaisesRegex(MascotValidationError, 'asset checksum mismatch'):
            self.registry.load('nico', self.config['version'])
        self.publish(self.config, [{'kind': 'reference', 'status': 'pending_original_bytes', 'path': 'invented.png'}])
        with self.assertRaisesRegex(MascotValidationError, 'cannot be claimed'):
            self.registry.load('nico', self.config['version'])
        self.publish(self.config, [{'kind': 'model', 'path': '../outside.glb', 'sha256': '0' * 64}])
        with self.assertRaisesRegex(MascotValidationError, 'escapes'):
            self.registry.load('nico', self.config['version'])

    def test_approved_label_alone_does_not_bypass_original_assets_gate(self):
        approved=example_config('1.0.0','approved');self.publish(approved)
        with self.assertRaisesRegex(MascotValidationError,'Original reference'):
            self.registry.load('nico','1.0.0',require_approved=True)

    def test_canonical_hash_ignores_json_formatting_and_order(self):
        self.assertEqual(config_sha256(self.config), config_sha256(dict(reversed(list(self.config.items())))))

    def test_sql_adapter_requires_approval_existing_database_and_schema(self):
        database = self.root / 'missing.sqlite'
        with self.assertRaisesRegex(MascotValidationError, 'approve'):
            SqliteMascotStore(database)
        with self.assertRaisesRegex(MascotValidationError, 'Existing'):
            SqliteMascotStore(database, approved_schema=True)
        self.assertFalse(database.exists())
        with sqlite3.connect(database) as connection:
            connection.execute('CREATE TABLE unrelated (value TEXT)')
        with self.assertRaisesRegex(MascotValidationError, 'not installed'):
            SqliteMascotStore(database, approved_schema=True)
        with sqlite3.connect(database) as connection:
            self.assertEqual(connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(), [('unrelated',)])

    def test_sql_temp_schema_enforces_immutable_versions_and_video_pins(self):
        database = self.root / 'reviewed-test-only.sqlite'
        with sqlite3.connect(database) as connection:
            connection.executescript((ROOT / 'migrations/001_mascot_registry.sql').read_text())
        store = SqliteMascotStore(database, approved_schema=True)
        try:
            pin = store.register_version(self.registry, 'nico', self.config['version'])
            self.assertEqual(store.assign_video('video-one', pin), pin)
            self.assertEqual(store.video_pin('video-one'), pin)
            self.assertEqual(store.register_version(self.registry, 'nico', self.config['version']), pin)
            changed = deepcopy(self.config)
            changed['geometry']['bodyWidth'] = .8
            self.publish(changed)
            with self.assertRaisesRegex(MascotValidationError, 'immutable'):
                store.register_version(self.registry, 'nico', self.config['version'])
            self.publish(example_config('1.0.0', 'approved'))
            other = store.register_version(self.registry, 'nico', '1.0.0')
            with self.assertRaisesRegex(MascotValidationError, 'immutable'):
                store.assign_video('video-one', other)
            forged = deepcopy(pin)
            forged['config_sha256'] = '0' * 64
            with self.assertRaisesRegex(MascotValidationError, 'does not match'):
                store.assign_video('video-two', forged)
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("UPDATE mascot_versions SET status='approved'")
            store.connection.rollback()
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute('DELETE FROM video_mascots')
        finally:
            store.close()

    def test_sql_registered_assets_cannot_be_replaced_by_editing_manifest(self):
        database = self.root / 'asset-test-only.sqlite'
        with sqlite3.connect(database) as connection:
            connection.executescript((ROOT / 'migrations/001_mascot_registry.sql').read_text())
        asset = self.root / 'model.glb'
        asset.write_bytes(b'first')
        def metadata():
            return {'kind': 'model', 'path': 'model.glb', 'sha256': hashlib.sha256(asset.read_bytes()).hexdigest()}
        self.publish(self.config, [metadata()])
        store = SqliteMascotStore(database, approved_schema=True)
        try:
            store.register_version(self.registry, 'nico', self.config['version'])
            asset.write_bytes(b'replacement')
            self.publish(self.config, [metadata()])
            with self.assertRaisesRegex(MascotValidationError, 'assets are immutable'):
                store.register_version(self.registry, 'nico', self.config['version'])
        finally:
            store.close()


if __name__ == '__main__':
    unittest.main()
