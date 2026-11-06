import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
import zipfile
from http.server import ThreadingHTTPServer
import app

class StudioAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.data_patch=patch.object(app,'DATA',Path(cls.temp.name)/'projects')
        cls.data_patch.start()
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        cls.base='http://127.0.0.1:'+str(cls.server.server_port)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close()
        cls.data_patch.stop();cls.temp.cleanup()
    def request(self,path,data=None,origin=None):
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        req=urllib.request.Request(self.base+path,data=None if data is None else json.dumps(data).encode(),headers=headers)
        return urllib.request.urlopen(req)
    def test_project_persists_user_script_and_download(self):
        with self.request('/api/projects',{'topic':'Por que a Terra gira?','script':'Roteiro editado pelo usuário.'}) as response:
            p=json.load(response)
        with self.request('/api/projects/'+p['id']+'/download') as response:
            self.assertEqual(json.load(response)['script'],'Roteiro editado pelo usuário.')
            self.assertIn('attachment',response.headers['Content-Disposition'])
    def test_unsupported_subject_does_not_render_earth(self):
        with self.request('/api/projects',{'topic':'Por que peixes respiram na água?'}) as r:p=json.load(r)
        self.assertFalse(p['renderable'])
        with self.assertRaises(urllib.error.HTTPError) as e:
            self.request('/api/projects/'+p['id']+'/render',{})
        self.assertEqual(e.exception.code,400)
    def test_cross_origin_writes_are_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as e:
            self.request('/api/projects',{'topic':'Teste'},origin='https://outro.example')
        self.assertEqual(e.exception.code,403)
    def test_bundle_contains_engine_but_no_private_data(self):
        with self.request('/api/skill/download') as r:z=zipfile.ZipFile(io.BytesIO(r.read()))
        self.assertIn('skills/curiolab-3d/SKILL.md',z.namelist())
        self.assertIn('engine/render.py',z.namelist())
        self.assertFalse(any('.local/' in n or '.env' in n or '__pycache__' in n for n in z.namelist()))
    def test_invalid_json_payload(self):
        with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/projects',[])
        self.assertEqual(e.exception.code,400)

if __name__=='__main__':unittest.main()
