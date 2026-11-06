import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import app

# Small genuine PNG, no dependency on Pillow in the application.
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl6CxkAAAAASUVORK5CYII=')

class ProductionWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.patch=patch.object(app,'ASSETS',Path(self.temp.name)/'assets')
        self.patch.start()
    def tearDown(self):
        self.patch.stop();self.temp.cleanup()
    def test_uploaded_image_resolves_to_private_asset_and_arbitrary_topic_can_render(self):
        a=app.upload_asset({'filename':'scene.png','data_base64':base64.b64encode(PNG).decode()})
        self.assertNotIn('stored_name',a)
        self.assertEqual(app.asset_file(a['id'],'image').read_bytes(),PNG)
        project=app.make_project({'topic':'Por que a água congela?','mode':'slideshow','resolution':'1080x1920','duration':4,
            'scenes':[{'asset_id':a['id'],'start':0,'end':4,'caption':'A ÁGUA MUDA','motion':'zoom_in'}]})
        self.assertTrue(project['renderable'])
        self.assertEqual(project['resolution'],'1080x1920')
    def test_spoofed_asset_and_wrong_asset_role_rejected(self):
        with self.assertRaises(ValueError):app.upload_asset({'filename':'a.png','data_base64':base64.b64encode(b'not an image').decode()})
        a=app.upload_asset({'filename':'a.wav','data_base64':base64.b64encode(b'RIFF'+bytes(4)+b'WAVE'+bytes(20)).decode()})
        with self.assertRaises(ValueError):app.asset_file(a['id'],'image')
    def test_overlapping_scenes_and_unknown_asset_rejected(self):
        with self.assertRaises(ValueError):app.make_project({'topic':'Teste','mode':'slideshow','duration':8,'scenes':[
            {'start':0,'end':5},{'start':4,'end':8}]})
        with self.assertRaises(ValueError):app.asset_file('../secret')
    def test_long_video_supported_but_template_limit_respected(self):
        self.assertEqual(app.make_project({'topic':'Teste','mode':'slideshow','duration':170})['duration'],170)
        with self.assertRaises(ValueError):app.make_project({'topic':'Por que a Terra gira?','mode':'earth_rotation','duration':40})

if __name__=='__main__':unittest.main()
