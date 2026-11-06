import importlib.util
from pathlib import Path
import unittest
try:
 import cv2
 import numpy as np
except ImportError:
 cv2=None
if cv2 is not None:
 S=importlib.util.spec_from_file_location('forensics',Path(__file__).resolve().parents[1]/'tools/video_forensics.py');m=importlib.util.module_from_spec(S);S.loader.exec_module(m)
@unittest.skipIf(cv2 is None,'Use .local/analysis/bin/python para os testes OpenCV')
class MotionTests(unittest.TestCase):
 def texture(self):
  rng=np.random.default_rng(42);a=rng.integers(0,255,(320,202),dtype=np.uint8);return cv2.GaussianBlur(a,(5,5),0)
 def test_translation_direction_and_scale(self):
  a=self.texture();b=cv2.warpAffine(a,np.array([[1,0,3],[0,1,-2]],dtype=np.float32),(202,320));r=m.estimate(a,b)
  self.assertAlmostEqual(r['dx_image_px'],3,delta=.5);self.assertAlmostEqual(r['dy_image_px'],-2,delta=.5);self.assertFalse(r['cut_candidate'])
 def test_identical_frames_are_static(self):
  a=self.texture();r=m.estimate(a,a.copy());self.assertEqual(r['state'],'static_image')
 def test_abrupt_black_white_is_cut_candidate(self):
  r=m.estimate(np.zeros((320,202),np.uint8),np.full((320,202),255,np.uint8));self.assertTrue(r['cut_candidate'])
 def test_zoom_estimate(self):
  a=self.texture();b=cv2.warpAffine(a,cv2.getRotationMatrix2D((101,160),0,1.015),(202,320));r=m.estimate(a,b);self.assertAlmostEqual(r['scale_ratio'],1.015,delta=.004);self.assertEqual(r['confidence'],'low');self.assertEqual(r['motion_warning'],'rapid_motion_or_repeated_pattern_alias')
if __name__=='__main__':unittest.main()
