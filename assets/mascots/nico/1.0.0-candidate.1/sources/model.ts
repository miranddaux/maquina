import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import type { MascotConfig, MascotRig, PaletteKey } from './types';

export interface MascotModel { group: THREE.Group; rig: MascotRig; dispose: () => void }

/** Original procedural geometry. Face points toward +Z; every pivot has a stable export name. */
export function createMascotModel(config: Readonly<MascotConfig>): MascotModel {
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Map<PaletteKey, THREE.MeshStandardMaterial>();
  for (const key of Object.keys(config.palette) as PaletteKey[]) {
    const material = new THREE.MeshStandardMaterial({ color: config.palette[key], roughness: 0.83, metalness: 0 });
    material.name = `NICO_material_${key}`;
    materials.set(key, material);
  }
  function group(name: string, parent?: THREE.Group, position: [number, number, number] = [0, 0, 0]) {
    const node = new THREE.Group(); node.name = name; node.position.set(...position); parent?.add(node); return node;
  }
  function mesh(name: string, geometry: THREE.BufferGeometry, color: PaletteKey, parent: THREE.Group,
    position: [number, number, number], rotation: [number, number, number] = [0, 0, 0]) {
    geometries.add(geometry);
    const node = new THREE.Mesh(geometry, materials.get(color));
    node.name = name; node.position.set(...position); node.rotation.set(...rotation);
    node.castShadow = true; node.receiveShadow = true;
    parent.add(node); return node;
  }
  function box(name: string, dimensions: [number, number, number], color: PaletteKey, parent: THREE.Group,
    position: [number, number, number], radius = 0.06, rotation: [number, number, number] = [0, 0, 0]) {
    return mesh(name, new RoundedBoxGeometry(...dimensions, 1, Math.min(radius, ...dimensions.map(n => n / 2))), color, parent, position, rotation);
  }
  function oval(name: string, scale: [number, number, number], color: PaletteKey, parent: THREE.Group,
    position: [number, number, number], segments = 10) {
    const m = mesh(name, new THREE.SphereGeometry(1, segments, 8), color, parent, position);
    m.scale.set(...scale); return m;
  }
  function extrusion(name: string, shape: THREE.Shape, depth: number, color: PaletteKey, parent: THREE.Group,
    position: [number, number, number], bevel = 0.025) {
    return mesh(name, new THREE.ExtrudeGeometry(shape, {
      depth, curveSegments: 5, steps: 1, bevelEnabled: bevel > 0,
      bevelSegments: 1, bevelSize: bevel, bevelThickness: bevel,
    }), color, parent, position);
  }
  const g = config.geometry;
  const model = group(`mascot_${config.mascotId}_${config.modelVersion}`);
  model.userData = { mascotId: config.mascotId, modelVersion: config.modelVersion, status: config.status, procedural: true };
  const root = group('NICO_Root', model);

  // Body, hoodie hem, sewn pouch, hood and backpack retain separate semantic names.
  const torso = group('NICO_Torso', root);
  box('NICO_Hoodie', [g.bodyWidth, g.bodyHeight, g.bodyDepth], 'yellow', torso, [0, 1.38, 0], 0.11);
  box('NICO_HoodieHem', [g.bodyWidth + 0.012, 0.10, g.bodyDepth + 0.012], 'yellow', torso, [0, 1.01, 0], 0.04);
  box('NICO_HoodiePocket', [0.37, 0.18, 0.035], 'yellow', torso, [0, 1.15, g.bodyDepth / 2 + 0.018], 0.045);
  box('NICO_Hood', [0.76, 0.23, 0.49], 'yellow', torso, [0, 1.79, -0.045], 0.11);
  box('NICO_HoodRearFold', [0.57, 0.30, 0.16], 'yellow', torso, [0, 1.73, -0.31], 0.10);
  for (const side of [-1, 1]) {
    box(`NICO_Drawstring_${side < 0 ? 'L' : 'R'}`, [0.026, 0.27, 0.028], 'white', torso, [side * 0.09, 1.59, g.bodyDepth / 2 + 0.023], 0.013);
    box(`NICO_BackpackStrap_${side < 0 ? 'L' : 'R'}`, [0.09, 0.70, 0.065], 'navy', torso, [side * 0.285, 1.43, g.bodyDepth / 2 + 0.028], 0.028, [0, 0, side * 0.055]);
    box(`NICO_BackpackShoulder_${side}`, [0.092, 0.10, 0.40], 'navy', torso, [side * 0.285, 1.73, 0], 0.035);
  }
  box('NICO_Backpack', [0.59, 0.66, 0.25], 'navy', torso, [0, 1.39, -0.385], 0.11);
  box('NICO_BackpackFlap', [0.55, 0.22, 0.055], 'navy', torso, [0, 1.58, -0.53], 0.055);
  box('NICO_BackpackPocket', [0.33, 0.23, 0.055], 'navy', torso, [0, 1.23, -0.53], 0.045);
  box('NICO_BackpackHandle', [0.18, 0.10, 0.09], 'navy', torso, [0, 1.75, -0.36], 0.035);

  const leftArm = group('NICO_LeftArm', root, [0.415, 1.68, 0]);
  const rightArm = group('NICO_RightArm', root, [-0.415, 1.68, 0]);
  for (const [index, arm] of [leftArm, rightArm].entries()) {
    box(`NICO_Sleeve_${index}`, [g.limbRadius * 2.12, 0.55, 0.27], 'yellow', arm, [0, -0.235, 0], 0.06);
    box(`NICO_Cuff_${index}`, [g.limbRadius * 2.16, 0.085, 0.27], 'yellow', arm, [0, -0.49, 0], 0.025);
    oval(`NICO_Hand_${index}`, [0.12, 0.145, 0.12], 'skin', arm, [0, -0.61, 0.01]);
    oval(`NICO_Thumb_${index}`, [0.046, 0.065, 0.047], 'skin', arm, [index === 0 ? -0.07 : 0.07, -0.58, 0.09]);
  }
  const leftLeg = group('NICO_LeftLeg', root, [0.205, 1.015, 0]);
  const rightLeg = group('NICO_RightLeg', root, [-0.205, 1.015, 0]);
  for (const [index, leg] of [leftLeg, rightLeg].entries()) {
    box(`NICO_Trouser_${index}`, [0.335, 0.83, 0.35], 'navy', leg, [0, -0.38, 0], 0.055);
    box(`NICO_Sneaker_${index}`, [0.36, 0.18, 0.51], 'white', leg, [0, -0.875, 0.07], 0.075);
    box(`NICO_OrangeSole_${index}`, [0.37, 0.065, 0.52], 'orange', leg, [0, -0.972, 0.07], 0.025);
  }

  const head = group('NICO_Head', root, [0, g.headCenterY, 0]);
  box('NICO_Face', [g.headWidth, g.headHeight, g.headDepth], 'skin', head, [0, 0, 0], 0.19);
  for (const side of [-1, 1]) {
    oval(`NICO_Ear_${side}`, [0.105, 0.145, 0.095], 'skin', head, [side * (g.headWidth / 2 + 0.04), -0.045, 0]);
  }
  // Hair is a beveled sculpted cap with a continuous swept silhouette, never clustered spheres.
  box('NICO_HairRearCap', [g.headWidth + 0.035, 0.64, g.headDepth + 0.035], 'hair', head, [0, 0.155, -0.055], 0.20);
  const fringe = new THREE.Shape();
  fringe.moveTo(-0.50, 0.23); fringe.lineTo(-0.49, 0.35);
  fringe.quadraticCurveTo(-0.39, 0.51, -0.13, 0.49);
  fringe.quadraticCurveTo(0.11, 0.48, 0.35, 0.39);
  fringe.quadraticCurveTo(0.51, 0.35, 0.49, 0.12);
  fringe.lineTo(0.25, 0.23); fringe.quadraticCurveTo(0.12, 0.26, -0.02, 0.22);
  fringe.lineTo(-0.45, 0.21); fringe.closePath();
  extrusion('NICO_SweptFringe', fringe, 0.06, 'hair', head, [0, 0, g.headDepth / 2 - 0.02], 0.035);
  const crest = new THREE.Shape();
  crest.moveTo(-0.45, 0.42); crest.quadraticCurveTo(-0.46, 0.53, -0.23, 0.55);
  crest.quadraticCurveTo(0.07, 0.56, 0.35, 0.49);
  crest.quadraticCurveTo(0.49, 0.43, 0.33, 0.38);
  crest.quadraticCurveTo(0.03, 0.36, -0.28, 0.36);
  crest.quadraticCurveTo(-0.43, 0.36, -0.45, 0.42); crest.closePath();
  extrusion('NICO_HairCrest', crest, 0.48, 'hair', head, [0, 0, -0.10], 0.035);
  const faceZ = g.headDepth / 2;
  for (const side of [-1, 1]) {
    oval(`NICO_EyeWhite_${side}`, [0.104, 0.124, 0.032], 'white', head, [side * 0.205, -0.025, faceZ + 0.009]);
    oval(`NICO_Pupil_${side}`, [0.071, 0.095, 0.025], 'dark', head, [side * 0.205, -0.025, faceZ + 0.037]);
    oval(`NICO_EyeHighlight_${side}`, [0.023, 0.027, 0.012], 'white', head, [side * 0.205 - 0.017, 0.015, faceZ + 0.061], 8);
    oval(`NICO_Cheek_${side}`, [0.074, 0.075, 0.014], 'cheeks', head, [side * 0.328, -0.16, faceZ + 0.005]);
    box(`NICO_Brow_${side}`, [0.13, 0.047, 0.035], 'hair', head, [side * 0.205, 0.141, faceZ + 0.036], 0.016, [0, 0, side * -0.045]);
  }
  oval('NICO_Nose', [0.065, 0.058, 0.061], 'skin', head, [0, -0.105, faceZ + 0.039]);
  const mouth = group('NICO_Mouth', head, [0, -0.21, faceZ + 0.002]);
  const mouthShape = new THREE.Shape();
  mouthShape.moveTo(-0.135, 0.035); mouthShape.quadraticCurveTo(0, 0.012, 0.135, 0.035);
  mouthShape.quadraticCurveTo(0.128, -0.115, 0, -0.118);
  mouthShape.quadraticCurveTo(-0.128, -0.115, -0.135, 0.035); mouthShape.closePath();
  extrusion('NICO_Smile', mouthShape, 0.008, 'hair', mouth, [0, 0, 0], 0);
  oval('NICO_Tongue', [0.069, 0.025, 0.013], 'cheeks', mouth, [0, -0.085, 0.02]);

  return {
    group: model, rig: { root, head, leftArm, rightArm, leftLeg, rightLeg, mouth },
    dispose() { geometries.forEach(x => x.dispose()); materials.forEach(x => x.dispose()); },
  };
}
