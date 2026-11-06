import { ANIMATIONS, type MascotAnimation, type MascotRig, type Pose } from './types';

export const ANIMATION_DURATIONS: Readonly<Record<MascotAnimation, number>> = Object.freeze({ idle: 3, walk: 2, run: 2, talk: 3, point: 2, wave: 2, celebrate: 2 });

/** Every channel is reset on every sample. Seeking and switching never retain a previous pose. */
export function sampleAnimation(animation: MascotAnimation, timeSeconds: number): Pose {
  if (!ANIMATIONS.includes(animation)) throw new Error(`Animação desconhecida: ${animation}`);
  if (!Number.isFinite(timeSeconds) || timeSeconds < 0) throw new Error('O tempo deve ser finito e positivo.');
  const t = timeSeconds;
  const turn = Math.PI * 2;
  const pose: Pose = {
    rootY: 0, rootZ: 0, rootTilt: 0,
    headX: 0, headY: 0, headZ: 0,
    leftArmX: 0, rightArmX: 0, leftArmZ: 0.18, rightArmZ: -0.18,
    leftLegX: 0, rightLegX: 0, mouthScaleY: 1,
  };
  switch (animation) {
    case 'idle':
      pose.rootY = Math.sin(t * turn / 3) * 0.012;
      pose.headZ = Math.sin(t * turn / 3) * 0.025;
      pose.leftArmZ += Math.sin(t * turn / 3) * 0.018;
      pose.rightArmZ -= Math.sin(t * turn / 3) * 0.018;
      break;
    case 'walk': {
      const stride = Math.sin(t * turn * 1.5);
      pose.leftLegX = stride * 0.48;
      pose.rightLegX = -stride * 0.48;
      pose.leftArmX = -stride * 0.4;
      pose.rightArmX = stride * 0.4;
      pose.rootY = Math.abs(stride) * 0.045;
      pose.rootTilt = stride * 0.025;
      break;
    }
    case 'run': {
      const stride = Math.sin(t * turn * 2);
      pose.leftLegX = stride * 0.85;
      pose.rightLegX = -stride * 0.85;
      pose.leftArmX = -stride * 0.8 - 0.2;
      pose.rightArmX = stride * 0.8 - 0.2;
      pose.rootY = Math.abs(stride) * 0.13 + 0.03;
      pose.headX = 0.08;
      break;
    }
    case 'talk':
      pose.mouthScaleY = 0.35 + (Math.sin(t * turn * 7 / 3) * 0.5 + 0.5) * 0.9;
      pose.headX = Math.sin(t * turn * 2 / 3) * 0.045;
      pose.headY = Math.sin(t * turn / 3) * 0.045;
      pose.leftArmX = -0.28 - Math.sin(t * turn / 3) * 0.12;
      pose.rightArmX = -0.2 + Math.sin(t * turn * 2 / 3) * 0.12;
      pose.leftArmZ = 0.32;
      pose.rightArmZ = -0.28;
      break;
    case 'point':
      pose.leftArmZ = 1.48;
      pose.leftArmX = -0.12;
      pose.headY = -0.14;
      pose.headZ = -0.04;
      pose.rightArmZ = -0.2;
      break;
    case 'wave':
      pose.leftArmZ = 2.5 + Math.sin(t * turn * 2) * 0.23;
      pose.leftArmX = Math.sin(t * turn * 2) * 0.13;
      pose.headZ = -0.055;
      pose.rootY = Math.sin(t * turn / 2) * 0.012;
      break;
    case 'celebrate':
      pose.leftArmZ = 2.5 + Math.sin(t * turn * 1.5) * 0.09;
      pose.rightArmZ = -2.5 - Math.sin(t * turn * 1.5) * 0.09;
      pose.rootY = Math.max(0, Math.sin(t * turn * 1.5)) * 0.15;
      pose.headZ = Math.sin(t * turn / 2) * 0.04;
      pose.mouthScaleY = 1.15;
      break;
  }
  return pose;
}

export function applyPose(rig: MascotRig, pose: Pose): void {
  rig.root.position.set(0, pose.rootY, pose.rootZ);
  rig.root.rotation.set(0, 0, pose.rootTilt);
  rig.head.rotation.set(pose.headX, pose.headY, pose.headZ);
  rig.leftArm.rotation.set(pose.leftArmX, 0, pose.leftArmZ);
  rig.rightArm.rotation.set(pose.rightArmX, 0, pose.rightArmZ);
  rig.leftLeg.rotation.set(pose.leftLegX, 0, 0);
  rig.rightLeg.rotation.set(pose.rightLegX, 0, 0);
  rig.mouth.scale.set(1, pose.mouthScaleY, 1);
}
