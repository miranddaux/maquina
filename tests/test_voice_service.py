import io,json,os,stat,subprocess,tempfile,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
from integrations.voice_service import VoiceService,VoiceServiceError

class Response:
    def __init__(self,content):self.content=content
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def read(self,_):return self.content

class VoiceIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.voice=VoiceService(self.root)
        self.env=patch.dict(os.environ,{'ELEVENLABS_API_KEY':'','OPENAI_API_KEY':''});self.env.start()
    def tearDown(self):self.env.stop();self.temp.cleanup()
    def test_key_is_private_not_returned_and_configure_does_not_call_api(self):
        with patch('urllib.request.urlopen') as http:
            result=self.voice.configure('elevenlabs','local-test-credential')
        http.assert_not_called();self.assertNotIn('local-test-credential',json.dumps(result))
        self.assertEqual(stat.S_IMODE(self.voice.vault.stat().st_mode),0o600)
        self.assertFalse(result['providers'][0]['connection_tested'])
    def test_real_read_only_contract_and_receipt_tracks_key_change(self):
        self.voice.configure('elevenlabs','local-test-credential')
        with patch('urllib.request.urlopen',return_value=Response(b'{"voices":[{"voice_id":"voice123","name":"Teste"}]}')) as http:
            result=self.voice.test_connection('elevenlabs')
        request=http.call_args.args[0]
        self.assertEqual(request.full_url,'https://api.elevenlabs.io/v1/voices');self.assertEqual(request.method,'GET')
        self.assertEqual(result['voices'][0]['id'],'voice123')
        self.assertTrue(self.voice.connection_status('elevenlabs')['providers'][0]['connection_tested'])
        self.voice.configure('elevenlabs','changed-test-credential')
        self.assertFalse(self.voice.connection_status('elevenlabs')['providers'][0]['connection_tested'])
    def test_upstream_errors_never_echo_body_or_key(self):
        self.voice.configure('elevenlabs','local-test-credential')
        error=urllib.error.HTTPError('https://api.elevenlabs.io',401,'bad credential',{},io.BytesIO(b'local-test-credential'))
        with patch('urllib.request.urlopen',side_effect=error):
            with self.assertRaises(VoiceServiceError) as caught:self.voice.test_connection('elevenlabs')
        self.assertNotIn('local-test-credential',str(caught.exception));self.assertEqual(caught.exception.category,'authentication')
    def test_speech_request_writes_verified_audio(self):
        fixture=self.root/'fixture.mp3'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i','sine=frequency=440:duration=0.2','-y',str(fixture)],check=True)
        self.voice.configure('elevenlabs','local-test-credential')
        with patch('urllib.request.urlopen',return_value=Response(fixture.read_bytes())) as http:
            result=self.voice.synthesize('elevenlabs','voice123','Uma amostra original.',self.root/'voice.mp3')
        req=http.call_args.args[0];payload=json.loads(req.data)
        self.assertEqual(req.method,'POST');self.assertEqual(payload['model_id'],'eleven_multilingual_v2')
        self.assertEqual(payload['text'],'Uma amostra original.');self.assertTrue((self.root/'voice.mp3').is_file())
        self.assertNotIn('local-test-credential',json.dumps(result))
    def test_missing_credentials_cannot_be_treated_as_connected(self):
        with self.assertRaises(VoiceServiceError) as caught:self.voice.test_connection('elevenlabs')
        self.assertEqual(caught.exception.category,'missing_credentials')
if __name__=='__main__':unittest.main()
