import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createHash } from 'node:crypto';
import candidate from '../../shared/mascots/nico/1.0.0-candidate.1/config.json';
import { NICO_CONFIG, NICO_CONFIG_SHA256, canonicalJSON, resolveMascot, registerMascot } from '../src/config';
import { ANIMATION_DURATIONS, sampleAnimation, applyPose } from '../src/animations';
import { createMascotModel } from '../src/model';
import { inspectModel } from '../src/metrics';
import { createAnimationClips } from '../src/export';
import { ANIMATIONS } from '../src/types';
import { assertProductionVersion, validateConfig } from '../src/validation';

test('central configuration has exact palette and immutable version hash', () => {
  validateConfig(NICO_CONFIG);
  assert.equal(createHash('sha256').update(canonicalJSON(candidate)).digest('hex'), NICO_CONFIG_SHA256);
  assert.ok(Object.isFrozen(NICO_CONFIG)); assert.ok(Object.isFrozen(NICO_CONFIG.palette));
  assert.throws(() => validateConfig({...NICO_CONFIG, palette: {...NICO_CONFIG.palette, yellow: '#FFFF00'}}));
  assert.throws(() => resolveMascot('nico', 'latest'));
  assert.throws(() => resolveMascot('unknown'));
});

test('candidate cannot enter production and approval still requires an explicit exact pin', () => {
  assert.throws(() => assertProductionVersion(NICO_CONFIG, NICO_CONFIG.modelVersion), /aprovação/);
  const approved = {...NICO_CONFIG, status: 'approved' as const};
  assert.throws(() => assertProductionVersion(approved, 'latest'), /versão exata/);
  assert.doesNotThrow(() => assertProductionVersion(approved, NICO_CONFIG.modelVersion));
});

test('all seven animations are deterministic, finite and independent of seeking order', () => {
  for (const animation of ANIMATIONS) {
    const a = sampleAnimation(animation, 1.27);
    sampleAnimation('run', 20);
    assert.deepEqual(sampleAnimation(animation, 1.27), a);
    assert.ok(Object.values(a).every(Number.isFinite));
  }
  assert.throws(() => sampleAnimation('idle', Number.NaN));
  assert.throws(() => sampleAnimation('idle', -1));
});

test('procedural model remains within budget, names stable and animation never mutates config', () => {
  const original = JSON.stringify(NICO_CONFIG);
  const a = createMascotModel(NICO_CONFIG); const b = createMascotModel(NICO_CONFIG);
  const metrics = inspectModel(a.group);
  assert.ok(metrics.triangles < NICO_CONFIG.performance.maxTriangles, `${metrics.triangles} triangles`);
  assert.ok(metrics.meshes < NICO_CONFIG.performance.maxDrawCalls);
  assert.deepEqual(metrics, inspectModel(b.group));
  const names: string[] = []; a.group.traverse(n => names.push(n.name));
  assert.equal(new Set(names).size, names.length);
  assert.ok(names.includes('NICO_SweptFringe'));
  for (const animation of ANIMATIONS) applyPose(a.rig, sampleAnimation(animation, 1.2));
  applyPose(a.rig, sampleAnimation('idle', 0));
  assert.equal(a.rig.leftArm.rotation.x, 0);
  assert.equal(JSON.stringify(NICO_CONFIG), original);
  a.dispose(); b.dispose();
});

test('GLB animation clips bake seven complete deterministic tracks for named pivots', () => {
  const clips = createAnimationClips();
  assert.deepEqual(clips.map(c => c.name), [...ANIMATIONS]);
  assert.ok(clips.every(c => c.tracks.length === 8 && c.duration >= 2));
  assert.deepEqual(clips[0].tracks[0].values, createAnimationClips()[0].tracks[0].values);
  for (const animation of ANIMATIONS) {
    const start = Object.values(sampleAnimation(animation, 0));
    const end = Object.values(sampleAnimation(animation, ANIMATION_DURATIONS[animation]));
    assert.ok(start.every((value, index) => Math.abs(value - end[index]) < 1e-6), `${animation} must loop without a pose jump`);
  }
});

test('additional mascots reuse rig while immutable registered versions cannot be replaced',()=>{
 const next={...NICO_CONFIG,mascotId:'luma',modelVersion:'1.0.0',status:'approved' as const,palette:{...NICO_CONFIG.palette,yellow:'#44AACC'}};
 registerMascot(next,{configSha256:'1'.repeat(64),geometryVersion:'lite-humanoid-1.0.0',animationVersion:'lite-rig-1.0.0'},true);
 assert.equal(resolveMascot('luma').palette.yellow,'#44AACC');
 assert.throws(()=>registerMascot({...next,palette:{...next.palette,yellow:'#AABBCC'}},{configSha256:'2'.repeat(64),geometryVersion:'lite-humanoid-1.0.0',animationVersion:'lite-rig-1.0.0'}));
 assert.throws(()=>resolveMascot('nico'));
});
