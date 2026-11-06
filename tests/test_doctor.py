import os,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from doctor import install_skill,process_environment,ROOT

class PortableInstallation(unittest.TestCase):
    def test_claude_skill_has_complete_project_pointer(self):
        with tempfile.TemporaryDirectory() as t:
            result=install_skill(Path(t)/'claude/skills/curiolab-3d',agent='claude')
            target=Path(result['path'])
            self.assertEqual((target/'CURIOLAB_ROOT.txt').read_text().strip(),str(ROOT))
            self.assertEqual((target/'SKILL.md').read_bytes(),(ROOT/'skills/curiolab-3d/SKILL.md').read_bytes())
            self.assertEqual(result['agent'],'claude')
    def test_existing_skill_requires_explicit_replace_and_gets_backup(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/'skill';target.mkdir();(target/'custom.md').write_text('Meu conteúdo anterior.')
            with self.assertRaises(ValueError):install_skill(target,agent='claude')
            self.assertEqual((target/'custom.md').read_text(),'Meu conteúdo anterior.')
            result=install_skill(target,replace=True,agent='claude')
            self.assertEqual((Path(result['backup'])/'custom.md').read_text(),'Meu conteúdo anterior.')
    def test_launcher_preserves_proxy_and_global_environment(self):
        base={'PATH':'/base','HTTPS_PROXY':'http://proxy:8080','SSL_CERT_FILE':'/trusted-ca'}
        child=process_environment({'blender':'/tools/blender'},base)
        self.assertEqual(child['HTTPS_PROXY'],base['HTTPS_PROXY']);self.assertEqual(child['SSL_CERT_FILE'],base['SSL_CERT_FILE'])
        self.assertEqual(base['PATH'],'/base');self.assertIn('/tools',child['PATH'])
if __name__=='__main__':unittest.main()
