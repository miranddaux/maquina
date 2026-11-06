import * as THREE from 'three';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import { ANIMATION_DURATIONS, applyPose, sampleAnimation } from './animations';
import { getMascotPin } from './config';
import { createMascotModel } from './model';
import { ANIMATIONS, type MascotAnimation, type MascotConfig, type Pose } from './types';

export function createAnimationClips(fps = 30): THREE.AnimationClip[] {
  if (!Number.isInteger(fps) || fps < 1 || fps > 120) throw new Error('FPS de animação inválido.');
  const q = new THREE.Quaternion(); const e = new THREE.Euler();
  return ANIMATIONS.map(animation => {
    const times: number[] = [];
    const channels = new Map<string, number[]>();
    const append = (name: string, value: number[]) => channels.set(name, [...(channels.get(name) ?? []), ...value]);
    const rotate = (name: string, x: number, y: number, z: number) => append(`${name}.quaternion`, q.setFromEuler(e.set(x, y, z)).toArray());
    for (let frame = 0; frame <= ANIMATION_DURATIONS[animation] * fps; frame++) {
      const t = frame / fps; times.push(t);
      const p: Pose = sampleAnimation(animation, t);
      append('NICO_Root.position', [0, p.rootY, p.rootZ]);
      rotate('NICO_Root', 0, 0, p.rootTilt);
      rotate('NICO_Head', p.headX, p.headY, p.headZ);
      rotate('NICO_LeftArm', p.leftArmX, 0, p.leftArmZ);
      rotate('NICO_RightArm', p.rightArmX, 0, p.rightArmZ);
      rotate('NICO_LeftLeg', p.leftLegX, 0, 0);
      rotate('NICO_RightLeg', p.rightLegX, 0, 0);
      append('NICO_Mouth.scale', [1, p.mouthScaleY, 1]);
    }
    const tracks = [...channels].map(([name, values]) => name.endsWith('quaternion')
      ? new THREE.QuaternionKeyframeTrack(name, times, values)
      : new THREE.VectorKeyframeTrack(name, times, values));
    return new THREE.AnimationClip(animation, ANIMATION_DURATIONS[animation], tracks);
  });
}

export async function exportMascotGLB(config: Readonly<MascotConfig>): Promise<ArrayBuffer> {
  const pin=getMascotPin(config);
  const model = createMascotModel(config);
  applyPose(model.rig, sampleAnimation('idle', 0));
  model.group.userData = {
    ...model.group.userData,
    configSha256: pin.configSha256,
    geometryVersion: pin.geometryVersion,
    animationVersion: pin.animationVersion,
    animationSamplingFps: 30,
    animationNames: [...ANIMATIONS],
    generator: 'CurioLab deterministic procedural mascot',
    units: 'meters',
    forwardAxis: '+Z',
    approvalRequired: config.status !== 'approved',
  };
  model.group.updateMatrixWorld(true);
  try {
    return await new GLTFExporter().parseAsync(model.group, {
      binary: true, animations: createAnimationClips(), onlyVisible: true,
    }) as ArrayBuffer;
  } finally { model.dispose(); }
}

export function downloadBlob(blob: Blob, name: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a'); link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
