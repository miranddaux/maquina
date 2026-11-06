#!/usr/bin/env python3
"""Inline the built viewer for an offline, deterministic candidate review."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
def main():
 base=ROOT/'web/mascot-viewer';html=(base/'index.html').read_text()
 def script(match):
  source=match.group(1).removeprefix('/mascot-viewer/')
  code=(base/source).read_text().replace('</script>','<\\/script>').replace('href:"/"','href:"curiolab-visual.html"')
  return '<script type="module">'+code+'</script>'
 def css(match):
  source=match.group(1).removeprefix('/mascot-viewer/')
  return '<style>'+(base/source).read_text()+'</style>'
 html=re.sub(r'<script[^>]*src="([^"]+)"[^>]*></script>',script,html)
 html=re.sub(r'<link[^>]*href="([^"]+\.css)"[^>]*>',css,html)
 # Only our own versioned model code is embedded; source reference files are pending.
 html=html.replace('href="/"','href="curiolab-visual.html"')
 target=ROOT/'outputs/nico-visual.html';target.write_text(html);print(target)
if __name__=='__main__':main()
