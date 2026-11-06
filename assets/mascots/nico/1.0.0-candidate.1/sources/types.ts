import type { Group } from 'three';

export const ANIMATIONS = ['idle', 'walk', 'run', 'talk', 'point', 'wave', 'celebrate'] as const;
export type MascotAnimation = typeof ANIMATIONS[number];
export type MascotView = 'front' | 'side' | 'rear';
export type PaletteKey = 'yellow' | 'navy' | 'hair' | 'skin' | 'cheeks' | 'white' | 'orange' | 'dark';
export interface MascotConfig {
  schemaVersion: number;
  mascotId: string;
  modelVersion: string;
  status: 'candidate' | 'approved' | 'retired';
  displayName: string;
  geometry: {
    totalHeight: number;
    headWidth: number;
    headHeight: number;
    headDepth: number;
    headCenterY: number;
    bodyWidth: number;
    bodyHeight: number;
    bodyDepth: number;
    limbRadius: number;
  };
  palette: Record<PaletteKey, string>;
  performance: { maxTriangles: number; maxDrawCalls: number };
  animations: MascotAnimation[];
}
export interface MascotRig {
  root: Group;
  head: Group;
  leftArm: Group;
  rightArm: Group;
  leftLeg: Group;
  rightLeg: Group;
  mouth: Group;
}
export interface Pose {
  rootY: number;
  rootZ: number;
  rootTilt: number;
  headX: number;
  headY: number;
  headZ: number;
  leftArmX: number;
  rightArmX: number;
  leftArmZ: number;
  rightArmZ: number;
  leftLegX: number;
  rightLegX: number;
  mouthScaleY: number;
}
