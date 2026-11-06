import { Component, Suspense, useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import { Canvas, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { Mascot3D } from './Mascot3D';
import { NICO_CONFIG, NICO_CONFIG_SHA256, verifyConfigIntegrity } from './config';
import { downloadBlob, exportMascotGLB } from './export';
import { inspectModel, type ModelMetrics } from './metrics';
import type { MascotModel } from './model';
import { ANIMATIONS, type MascotAnimation, type MascotView } from './types';
import './styles.css';

const LABELS: Record<MascotAnimation, string> = { idle: 'Em pé', walk: 'Caminhar', run: 'Correr', talk: 'Falar', point: 'Apontar', wave: 'Acenar', celebrate: 'Comemorar' };
const VIEWS: Record<MascotView, string> = { front: 'Frente', side: 'Lado', rear: 'Costas' };
const sleepFrames = () => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
type CaptureState = { animation?: MascotAnimation; timeSeconds?: number; view?: MascotView; playing?: boolean };
declare global {
  interface Window {
    __NICO?: {
      ready: boolean;
      setState: (next: CaptureState) => Promise<void>;
      getMetrics: () => ModelMetrics | null;
      getMetadata: () => object;
      exportGLB: () => Promise<number[]>;
      downloadGLB: () => Promise<void>;
    };
  }
}

class RenderBoundary extends Component<{children: ReactNode}, {error: string | null}> {
  state = { error: null as string | null };
  static getDerivedStateFromError(error: Error) { return { error: error.message }; }
  render() { return this.state.error ? <div className="renderer-error" role="alert"><b>Não foi possível abrir o 3D.</b><p>{this.state.error}</p><p>Ative a aceleração gráfica do navegador e recarregue esta página.</p></div> : this.props.children; }
}

function CameraRig({view}: {view: MascotView}) {
  const {camera, size} = useThree();
  useEffect(() => {
    const c = camera as THREE.OrthographicCamera;
    const aspect = size.width / size.height;
    const half = 1.67;
    c.left = -half * aspect; c.right = half * aspect; c.top = half; c.bottom = -half;
    c.position.set(...(view === 'front' ? [0, 1.42, 7] : view === 'side' ? [7, 1.42, 0] : [0, 1.42, -7]) as [number, number, number]);
    c.lookAt(0, 1.42, 0); c.updateProjectionMatrix();
  }, [view, camera, size]);
  return null;
}

function App() {
  const [animation, setAnimation] = useState<MascotAnimation>('idle');
  const [view, setView] = useState<MascotView>('front');
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState('');
  const [exporting, setExporting] = useState(false);
  const [contextLost, setContextLost] = useState(false);
  const modelRef = useRef<MascotModel | null>(null);
  const metricsRef = useRef<ModelMetrics | null>(null);
  const elapsedRef = useRef(0);
  const recordTime = useCallback((t: number) => { elapsedRef.current = t; }, []);
  const ready = useCallback((model: MascotModel) => {
    modelRef.current = model;
    const current = inspectModel(model.group); metricsRef.current = current; setMetrics(current);
  }, []);
  useEffect(() => { verifyConfigIntegrity().then(() => setVerified(true)).catch(e => setError(String(e.message))); }, []);
  const download = useCallback(async () => {
    setExporting(true); setError('');
    try { const bytes = await exportMascotGLB(NICO_CONFIG); downloadBlob(new Blob([bytes], { type: 'model/gltf-binary' }), `nico-${NICO_CONFIG.modelVersion}.glb`); }
    catch(e) { setError(e instanceof Error ? e.message : 'Falha ao exportar o mascote.'); }
    finally { setExporting(false); }
  }, []);
  useEffect(() => {
    window.__NICO = {
      ready: !!metrics && verified,
      async setState(next) {
        if (next.animation !== undefined) {
          if (!ANIMATIONS.includes(next.animation)) throw new Error('Animação inválida.');
          setAnimation(next.animation);
        }
        if (next.view !== undefined) {
          if (!Object.keys(VIEWS).includes(next.view)) throw new Error('Câmera inválida.');
          setView(next.view);
        }
        if (next.timeSeconds !== undefined) {
          if (!Number.isFinite(next.timeSeconds) || next.timeSeconds < 0) throw new Error('Tempo inválido.');
          setTime(next.timeSeconds); setPlaying(false);
        }
        if (next.playing !== undefined) setPlaying(next.playing);
        await sleepFrames();
      },
      getMetrics: () => metricsRef.current,
      getMetadata: () => ({ mascotId: NICO_CONFIG.mascotId, modelVersion: NICO_CONFIG.modelVersion, status: NICO_CONFIG.status, configSha256: NICO_CONFIG_SHA256, palette: NICO_CONFIG.palette }),
      exportGLB: async () => Array.from(new Uint8Array(await exportMascotGLB(NICO_CONFIG))),
      downloadGLB: download,
    };
    return () => { delete window.__NICO; };
  }, [metrics, verified, download]);
  const budgetGood = metrics && metrics.triangles <= NICO_CONFIG.performance.maxTriangles && metrics.meshes <= NICO_CONFIG.performance.maxDrawCalls;
  return <div className="studio-shell">
    <header className="topbar">
      <a className="brand" href="/" aria-label="Voltar ao painel"><span className="brand-mark">c<span>·</span></span><span>curiolab<small>ESTÚDIO DE MASCOTES</small></span></a>
      <a className="back-link" href="/">← Voltar à máquina</a>
    </header>
    <main>
      <section className="intro"><div><p className="eyebrow">SEU PERSONAGEM. SEMPRE ELE.</p><h1>Conheça o <span>NICO.</span></h1><p>Uma personalidade em cada gesto.<br className="desktop-break"/> A mesma identidade em todas as histórias.</p></div><span className="edition"><span className="status-dot"/> 3D LITE <b>01</b></span></section>
      <div className="workspace">
        <section className="viewer-card" aria-label="Prévia 3D do NICO">
          <div className="viewer-top"><span className="live-label"><span/> PRÉVIA AO VIVO</span><span className="view-label">{VIEWS[view]} · câmera ortográfica</span></div>
          <div className="canvas-wrap" data-testid="mascot-canvas">
            {verified && !error ? <RenderBoundary><Suspense fallback={<div className="loading">Preparando o NICO…</div>}><Canvas orthographic shadows dpr={[1, 2]} camera={{ position: [0, 1.42, 7], near: 0.01, far: 50 }} gl={{ antialias: true, preserveDrawingBuffer: true, alpha: false }} onCreated={({gl}) => {
              gl.setClearColor('#ebece8'); gl.toneMapping = THREE.ACESFilmicToneMapping; gl.toneMappingExposure = 0.92;
              gl.domElement.addEventListener('webglcontextlost', e => { e.preventDefault(); setContextLost(true); });
              gl.domElement.addEventListener('webglcontextrestored', () => setContextLost(false));
            }}>
              <CameraRig view={view}/>
              <ambientLight intensity={0.8}/><hemisphereLight args={['#ffffff', '#b2a58f', 0.6]}/>
              <directionalLight position={[-3, 6, 5]} intensity={2.4} castShadow shadow-mapSize={[1024, 1024]} shadow-camera-left={-3} shadow-camera-right={3} shadow-camera-top={4} shadow-camera-bottom={-3} shadow-normalBias={0.025} shadow-bias={-0.0003}/>
              <directionalLight position={[3, 4, -4]} intensity={0.7}/>
              <Mascot3D mascotId="nico" modelVersion={NICO_CONFIG.modelVersion} usage="preview" animation={animation} timeSeconds={playing ? undefined : time} onReady={ready} onTime={recordTime}/>
              <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.004, 0]} receiveShadow><planeGeometry args={[200, 200]}/><meshStandardMaterial color="#ebece8" roughness={1}/></mesh>
            </Canvas></Suspense></RenderBoundary> : <div className="loading">{error || 'Verificando a versão do personagem…'}</div>}
            {contextLost && <div className="renderer-error" role="alert"><b>O navegador pausou a visualização 3D.</b><p>Recarregue a página para recuperar a prévia. A versão do modelo está preservada.</p></div>}
            <span className="model-name">NICO<small>EXPLORADOR DE PORQUÊS</small></span>
          </div>
          <div className="viewer-controls"><div className="segmented" aria-label="Ângulo da câmera">{(Object.keys(VIEWS) as MascotView[]).map(v => <button key={v} aria-pressed={view === v} onClick={() => setView(v)}>{VIEWS[v]}</button>)}</div><button className="play-button" onClick={() => {if (playing) setTime(elapsedRef.current); setPlaying(p => !p);}} aria-label={playing ? 'Pausar animação' : 'Reproduzir animação'}>{playing ? 'Ⅱ' : '▶'}<span>{playing ? 'Pausar' : 'Reproduzir'}</span></button></div>
        </section>
        <aside className="settings">
          <section className="identity-card"><div className="section-label"><span>01 / IDENTIDADE</span><span className="lock-icon">♧</span></div><h2>Um NICO.<br/>Muitas histórias.</h2><p>Moletom amarelo, mochila azul e curiosidade de sobra. Uma base fixa para seus próximos vídeos.</p><div className="palette" aria-label="Paleta de cores fixa">{Object.entries(NICO_CONFIG.palette).slice(0, 7).map(([name, color]) => <span key={name} style={{backgroundColor: color}} title={`${name} · ${color}`}/>)}</div><div className="version-row"><span>Versão do personagem</span><b>{NICO_CONFIG.modelVersion}</b></div><div className="approval"><span>◷</span><div><b>Aguardando sua aprovação visual</b><p>Confira frente, lado e costas antes de liberar para os vídeos.</p></div></div></section>
          <section className="motion-card"><div className="section-label"><span>02 / MOVIMENTO</span><span>7 GESTOS</span></div><h2>Dê vida a ele.</h2><div className="animations">{ANIMATIONS.map((a, index) => <button key={a} aria-pressed={animation === a} onClick={() => {setAnimation(a); setTime(0);}}><span>{['○', '↗', '»', '◌', '☞', '✦', '↑'][index]}</span>{LABELS[a]}</button>)}</div><div className="timeline"><label htmlFor="pose-time">Tempo da pose <output>{time.toFixed(2)}s</output></label><input id="pose-time" type="range" min="0" max="4" step="0.01" value={time} onChange={e => {setTime(Number(e.target.value)); setPlaying(false);}}/></div></section>
          <button className="export-button" disabled={!verified || exporting || !metrics} onClick={download}>{exporting ? 'Preparando arquivo…' : '↓ Baixar modelo 3D'}<span>GLB + 7 animações</span></button>
          {error && <p role="alert" className="error-message">{error}</p>}
        </aside>
      </div>
      <footer className="statusbar"><span><i className={budgetGood ? 'good' : ''}/>{metrics ? `${metrics.triangles.toLocaleString('pt-BR')} triângulos · ${metrics.meshes} peças · ${metrics.materials} materiais` : 'Carregando geometria…'}</span><span>Geometria procedural · paleta fixa · versão verificável {verified ? '✓' : ''}</span></footer>
      <p className="candidate-note">Esta é uma versão candidata. Cada vídeo de produção usará uma versão aprovada e fixada no projeto.</p>
    </main>
  </div>;
}

createRoot(document.getElementById('root')!).render(<RenderBoundary><App/></RenderBoundary>);
