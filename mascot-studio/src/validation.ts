import { ANIMATIONS, type MascotConfig, type PaletteKey } from './types';

export const APPROVED_DIRECTION_PALETTE: Readonly<Record<PaletteKey, string>> = Object.freeze({
  yellow: '#F5C63D', navy: '#25344D', hair: '#433025', skin: '#C58C65',
  cheeks: '#EBA0A0', white: '#F1EEE7', orange: '#F18A41', dark: '#313A35',
});

export function validateConfig(input: unknown): asserts input is MascotConfig {
  if (!input || typeof input !== 'object') throw new Error('Configuração de mascote ausente.');
  const c = input as MascotConfig;
  if (c.schemaVersion !== 1) throw new Error('Versão do formato de configuração não suportada.');
  if (!/^[a-z][a-z0-9-]*$/.test(c.mascotId)) throw new Error('Identificador de mascote inválido.');
  if (!/^\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?$/.test(c.modelVersion)) throw new Error('Versão de modelo inválida.');
  if (!['candidate', 'approved', 'retired'].includes(c.status)) throw new Error('Estado do modelo inválido.');
  if (!c.displayName?.trim()) throw new Error('Nome do mascote ausente.');
  const geometryKeys = ['totalHeight', 'headWidth', 'headHeight', 'headDepth', 'headCenterY', 'bodyWidth', 'bodyHeight', 'bodyDepth', 'limbRadius'] as const;
  for (const key of geometryKeys) {
    if (!Number.isFinite(c.geometry?.[key]) || c.geometry[key] <= 0 || c.geometry[key] > 10) {
      throw new Error(`Proporção inválida: ${key}.`);
    }
  }
  for (const [key, value] of Object.entries(APPROVED_DIRECTION_PALETTE)) {
    const color=c.palette?.[key as PaletteKey];
    if (!/^#[0-9A-Fa-f]{6}$/.test(color || '')) throw new Error(`Cor RGB inválida: ${key}.`);
    if (c.mascotId==='nico' && color.toUpperCase() !== value) throw new Error(`Cor fora da paleta NICO: ${key}.`);
  }
  if (!Array.isArray(c.animations) || c.animations.length !== ANIMATIONS.length || ANIMATIONS.some(a => !c.animations.includes(a))) {
    throw new Error('O modelo precisa oferecer as sete animações NICO.');
  }
  if (!Number.isFinite(c.performance?.maxTriangles) || c.performance.maxTriangles < 1 ||
      !Number.isFinite(c.performance?.maxDrawCalls) || c.performance.maxDrawCalls < 1) throw new Error('Orçamento de desempenho inválido.');
}

export function freezeDeep<T>(object: T): Readonly<T> {
  if (object && typeof object === 'object' && !Object.isFrozen(object)) {
    for (const value of Object.values(object)) freezeDeep(value);
    Object.freeze(object);
  }
  return object;
}

export function assertProductionVersion(config: MascotConfig, pinnedVersion: string): void {
  validateConfig(config);
  if (config.status !== 'approved') throw new Error('Este modelo aguarda aprovação visual e não pode ser usado em produção.');
  if (pinnedVersion !== config.modelVersion) throw new Error('O vídeo precisa fixar a versão exata do mascote.');
}
