import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import doctor
import install_skill as installer
from package_skill import MANIFEST, build_package, verify_package


class CompleteSkillPackage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload, cls.manifest = build_package(ROOT)

    def test_package_contains_executable_skill_and_no_private_state(self):
        with zipfile.ZipFile(io.BytesIO(self.payload)) as archive:
            names = set(archive.namelist())
            for name in ['SKILL.md', 'INSTALAR-SKILL.py', 'INSTALAR-SKILL.bat',
                         'tools/smoke_skill.py', 'web/mascot-viewer/index.html',
                         'assets/mascots/nico/1.0.0-candidate.1/nico.glb', MANIFEST]:
                self.assertIn(name, names)
            self.assertFalse(any(part in {'.local', 'node_modules', '__pycache__', '.agents', '.claude', '.env'}
                                 for name in names for part in Path(name).parts))
            self.assertEqual(archive.read('SKILL.md'), archive.read('skills/curiolab-3d/SKILL.md'))
            self.assertIsNone(archive.testzip())

    def test_integrity_verification_detects_modified_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            with zipfile.ZipFile(io.BytesIO(self.payload)) as archive:
                archive.extractall(temp)
            self.assertEqual(verify_package(temp, required=True)['status'], 'verified')
            (Path(temp) / 'engine/render.py').write_text('alterado', encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'Integridade divergente'):
                verify_package(temp, required=True)

    def test_manifest_rejects_a_path_outside_the_package(self):
        with tempfile.TemporaryDirectory() as temp:
            content = {'application': 'curiolab-3d', 'files': {'../outside': {'size': 0, 'sha256': hashlib.sha256(b'').hexdigest()}}}
            (Path(temp) / MANIFEST).write_text(json.dumps(content), encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'Caminho inválido'):
                verify_package(temp, required=True)

    def test_project_installation_is_repeatable_and_preserves_customization(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / 'skills/curiolab-3d', root / 'skills/curiolab-3d')
            with patch.object(installer, 'ROOT', root), patch.object(doctor, 'ROOT', root):
                for agent, folder in [('codex', '.agents'), ('claude', '.claude')]:
                    first = installer.install(agent)
                    self.assertFalse(first['unchanged'])
                    target = root / folder / 'skills/curiolab-3d'
                    self.assertEqual(Path(first['path']), target)
                    self.assertEqual((target / 'CURIOLAB_ROOT.txt').read_text().strip(), str(root))
                    self.assertTrue(installer.install(agent)['unchanged'])
                    custom = target / 'custom.md'
                    custom.write_text('Minha adaptação.', encoding='utf8')
                    with self.assertRaises(ValueError):
                        installer.install(agent)
                    self.assertEqual(custom.read_text(), 'Minha adaptação.')
                    updated = installer.install(agent, replace=True)
                    self.assertEqual((Path(updated['backup']) / 'custom.md').read_text(), 'Minha adaptação.')


if __name__ == '__main__':
    unittest.main()
