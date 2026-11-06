import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from panel_state import CHANNEL_DEFAULTS, METHOD_DEFAULTS, PanelState

class PanelPersistence(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.store=PanelState(self.root)
    def tearDown(self):
        self.temp.cleanup()

    def test_partial_updates_preserve_nested_preferences_without_secrets(self):
        first=self.store.save_channel({'name':'Canal de teste','handle':'@teste','character':{'shirt':'#F0CC33'}})
        self.store.save_channel({'voice':{'description':'Uma voz clara.'}})
        restored=PanelState(self.root).channel()
        self.assertEqual(restored['name'],first['name'])
        self.assertEqual(restored['character']['shirt'],'#F0CC33')
        self.assertEqual(restored['character']['pants'],CHANNEL_DEFAULTS['character']['pants'])
        for invalid in [{'api_key':'secret'},{'voice':{'api_key':'secret'}},{'voice':{'token':'secret'}}]:
            with self.assertRaises(ValueError):self.store.save_channel(invalid)
        self.assertNotIn('secret',(self.root/'.local/channel.json').read_text())

    def test_invalid_colors_and_assets_do_not_replace_previous_channel(self):
        self.store.save_channel({'name':'Preservar'})
        for invalid in [{'character':{'skin':'orange'}},{'accent_color':'blue'},{'visual_style':'fake'},{'logo_asset_id':'a'*32}]:
            with self.assertRaises(ValueError):self.store.save_channel(invalid)
        self.assertEqual(self.store.channel()['name'],'Preservar')

    def test_method_reset_restores_only_selected_section(self):
        self.store.save_method({'formula':'Fórmula própria','camera':'Câmera própria'})
        restored=self.store.reset_method('formula')
        self.assertEqual(restored['formula'],METHOD_DEFAULTS['formula'])
        self.assertEqual(restored['camera'],'Câmera própria')

    def test_request_is_saved_as_data_with_frozen_channel_snapshot(self):
        self.store.save_channel({'name':'Antes'})
        prompt='Faça um vídeo sobre pontes; $(touch should-not-exist)'
        request=self.store.create_request({'prompt':prompt})
        self.store.save_channel({'name':'Depois'})
        saved=json.loads((self.root/'.local/requests'/request['id']/'request.json').read_text())
        self.assertEqual(saved['prompt'],prompt)
        self.assertEqual(saved['channel']['name'],'Antes')
        self.assertEqual(saved['status'],'awaiting_codex')
        self.assertEqual(self.store.requests()['count'],1)
        self.assertTrue((self.root/'.local/requests'/request['id']/'brief.md').is_file())
        self.assertFalse((self.root/'should-not-exist').exists())

    def test_catalog_count_requires_actual_safe_source_file(self):
        (self.root/'engine').mkdir()
        (self.root/'engine/scene.py').write_text('# actual source')
        (self.root/'engine/catalog.json').write_text(json.dumps({'models':[
            {'id':'one','name':'One','path':'engine/scene.py'},
            {'id':'missing','name':'Missing','path':'engine/missing.py'},
            {'id':'unsafe','name':'Unsafe','path':'../../etc/passwd'},
        ]}))
        result=self.store.models()
        self.assertEqual(result['count'],1)
        self.assertEqual(result['total'],3)
        self.assertFalse(result['models'][2]['available'])

    def test_readiness_is_computed_and_does_not_make_voice_mandatory(self):
        self.store.save_channel({'name':'Canal','handle':'canal'})
        (self.root/'engine').mkdir();(self.root/'engine/scene.py').write_text('# source')
        (self.root/'engine/catalog.json').write_text(json.dumps([{'id':'scene','name':'Scene','path':'engine/scene.py'}]))
        with patch('panel_state.shutil.which',return_value='/tool'):
            result=self.store.readiness()
        self.assertEqual(result['percent'],round(100*result['ready_count']/result['total']))
        voice=next(check for check in result['checks'] if check['id']=='voice')
        self.assertFalse(voice['required']);self.assertFalse(voice['ready'])
        self.assertTrue(result['can_start'])

    def test_video_gallery_uses_real_media_and_metadata_not_file_extension(self):
        out=self.root/'outputs';out.mkdir()
        (out/'invalid.mp4').write_text('not a video')
        target=out/('b'*32+'.mp4')
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=yellow:s=32x64:d=0.5','-c:v','libx264','-threads','1','-pix_fmt','yuv420p',str(target)],check=True)
        target.with_suffix('.metadata.json').write_text(json.dumps({'title':'Vídeo real','script':'Roteiro original','request_id':'b'*32}))
        data=self.store.videos()
        self.assertEqual(data['count'],1)
        video=data['videos'][0]
        self.assertEqual(video['title'],'Vídeo real')
        self.assertEqual(video['resolution'],'32x64')
        self.assertGreater(video['duration'],0)
        self.assertEqual(video['script'],'Roteiro original')
        self.assertNotIn('path',video)

if __name__=='__main__':unittest.main()
