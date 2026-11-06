import { useEffect, useLayoutEffect, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { resolveMascot } from './config';
import { applyPose, sampleAnimation } from './animations';
import { createMascotModel, type MascotModel } from './model';
import { assertProductionVersion } from './validation';
import type { MascotAnimation } from './types';

export interface Mascot3DProps {
  mascotId: string;
  animation?: MascotAnimation;
  modelVersion?: string;
  timeSeconds?: number;
  usage?: 'preview' | 'production';
  onReady?: (model: MascotModel) => void;
  onTime?: (timeSeconds: number) => void;
}

export function Mascot3D({ mascotId, animation = 'idle', modelVersion, timeSeconds, usage = 'production', onReady, onTime }: Mascot3DProps) {
  const config = resolveMascot(mascotId, modelVersion);
  if (usage === 'production') assertProductionVersion(config, modelVersion ?? config.modelVersion);
  const model = useMemo(() => createMascotModel(config), [config]);
  useLayoutEffect(() => {
    applyPose(model.rig, sampleAnimation(animation, timeSeconds ?? 0));
    onReady?.(model);
  }, [model, animation, timeSeconds, onReady]);
  useEffect(() => () => model.dispose(), [model]);
  useFrame(({ clock }) => {
    const sampledTime = timeSeconds ?? clock.getElapsedTime();
    applyPose(model.rig, sampleAnimation(animation, sampledTime));
    onTime?.(sampledTime);
  });
  return <primitive object={model.group} dispose={null} />;
}
