# Motor local de vídeo

Requisitos: Python 3.10+, Blender 4.3 e FFmpeg com libass e libx264.
Não instala pacotes Python nem faz requisições externas.

```sh
cd /workspace/maquina
python engine/render.py --project engine/demo.json --output outputs/demo.mp4 --preview
python -m unittest discover -s tests -p 'test_engine.py' -v
```

O preview é um MP4 vertical 360×640 de 8 segundos; `--preview` usa 8 quadros
3D por segundo e exporta a 24 fps. Sem a opção, renderiza 720×1280 a 24 fps.
Os quadros são animação procedural de geometria 3D real feita no Blender.
O visual é esquemático: continentes e órbita decorativa não representam
cartografia ou órbitas científicas precisas.

`earth_rotation` é o único template implementado nesta versão. Outros temas
são rejeitados; uma pauta arbitrária ainda exige a criação de um novo template.
O JSON aceita `title`, `topic`, `duration` (3–30 segundos) e `captions`
(`start`, `end`, `text`). Metadados como `sources` são preservados, mas a
renderização não verifica fontes automaticamente.

Sem áudio de entrada, a exportação é silenciosa e rotulada como demonstração.
Para incluir uma narração que você já tenha direito de usar:

```sh
python engine/render.py --project engine/demo.json --output outputs/narrado.mp4 --preview --narration /caminho/voz.mp3
```

A narração é codificada em AAC; caso seja mais curta, o restante recebe silêncio.
Caso seja mais longa, é cortada na duração do projeto. Ajuste o roteiro e a
duração antes de publicar. Esta interface não sintetiza voz nem cobra APIs.
Arquivos temporários ficam ao lado da saída e são removidos ao concluir.

## Casa e Full HD

O template adicional `house_assembly` está em `scene_house.py`; `house_demo.json` contém um exemplo. Para renderizar geometria nativa1080×1920 a30fps, use:

```sh
python engine/render.py --project engine/house_demo.json --output outputs/casa-fullhd.mp4 --full-hd
```

Câmera e entradas das peças são definidas no script do template. O argumento `--narration` rejeita áudio maior que a duração para evitar cortar a fala.

`slideshow.py` compõe imagens próprias com zoom/pan, texto e áudio opcional; isso é composição2D, não geometria3D. O JSON precisa de `width`, `height`, `duration`, `scenes` contínuas com `image_path`, `start`, `end`, `caption`, `motion`, e opcional `narration_path`. A saída FullHD usa30fps,H.264CRF18,AAC192kbps.
