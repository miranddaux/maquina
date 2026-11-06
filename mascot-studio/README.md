# NICO — procedural mascot studio

Additive React 19 + Three.js + React Three Fiber + TypeScript module. The Python app remains the host; its bundled viewer is served at `/mascot-viewer/`.

```sh
cd mascot-studio
npm ci
npm test
npm run build
```

`npm run build` writes `../web/mascot-viewer/`. The committed bundle lets users open the panel without installing Node. Development: `npm run dev`.

## Contracts

- `src/model.ts` builds original geometry and a stable named rig. `src/animations.ts` samples each pose from explicit time in seconds. Model parameters are loaded from `shared/mascots/nico/1.0.0-candidate.1/config.json`; nested configuration is frozen and checked against a pinned canonical SHA-256.
- `<Mascot3D mascotId="nico" animation="wave" />` defaults to production and resolves only the statically pinned approved version. The current candidate deliberately fails this gate. The review viewer explicitly passes `usage="preview"`. Videos may additionally pass `modelVersion="<approved version>"` to retain their original exact pin.
- No palette, geometry or model version is randomized per video. Add another immutable version and update the registry and explicit build pins for an intentional revision.
- GLB export includes the named hierarchy, eight fixed palette materials, the model/config hashes, candidate status and all seven baked animation clips sampled at 30 fps. Clips are portable keyframe animations; their sampling is deterministic. Files are generated locally in the browser without API calls.
- The viewer does not approve models or apply database migrations. Use the main application's approval/registry workflow after inspecting all views. The original reference image bytes are still pending; the viewer does not claim to store them.

## Capture API

Wait for `window.__NICO?.ready === true`. Then:

```js
await window.__NICO.setState({ view: 'front', animation: 'idle', timeSeconds: 0 });
window.__NICO.getMetrics();
window.__NICO.getMetadata();
await window.__NICO.exportGLB(); // byte array
```

Views: `front`, `side`, `rear`. State waits two animation frames before resolving. Render export at `frame / fps` for reproducible poses. A screenshot can target `[data-testid="mascot-canvas"] canvas`. `preserveDrawingBuffer` permits PNG capture. Headless Chromium on servers without a GPU typically needs `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`.

Model budget: 20,000 triangles and 100 mesh draw calls. UI displays actual geometry metrics; WebGL shadows and the studio ground add rendering overhead beyond the character-only budget.
