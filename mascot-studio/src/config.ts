import candidate from '../../shared/mascots/nico/1.0.0-candidate.1/config.json';
import type { MascotConfig } from './types';
import { freezeDeep, validateConfig } from './validation';

/** These pins change only when a new immutable model version is deliberately registered. */
export const NICO_CONFIG_SHA256 = 'eac0ec53d8a15f055d35d639ea7c1fe474a618dae2c25faa86777636e2444278';
export const NICO_GEOMETRY_VERSION = candidate.geometry_version;
export const NICO_ANIMATION_VERSION = candidate.animation_version;
export const NICO_ASSET_PATH = '/shared/mascots/nico/1.0.0-candidate.1';

// Normalize the repository's snake_case storage contract once at this module boundary.
const normalized = {
  schemaVersion: candidate.schema_version,
  mascotId: candidate.id,
  modelVersion: candidate.version,
  status: candidate.status,
  displayName: candidate.display_name,
  geometry: candidate.geometry,
  palette: {
    yellow: candidate.palette.yellow, navy: candidate.palette.navy,
    hair: candidate.palette.brown, skin: candidate.palette.skin,
    cheeks: candidate.palette.pink, white: candidate.palette.white,
    orange: candidate.palette.orange, dark: candidate.palette.gray,
  },
  performance: candidate.performance,
  animations: candidate.animations,
};
validateConfig(normalized);
export const NICO_CONFIG = freezeDeep(normalized) as Readonly<MascotConfig>;

export interface MascotVersionPin { configSha256:string; geometryVersion:string; animationVersion:string }
const installed = new Map<string,{config:Readonly<MascotConfig>,pin:Readonly<MascotVersionPin>}>();
const productionDefaults = new Map<string,string>();

/** Registration is explicit and immutable; never replace an existing id@version. */
export function registerMascot(config:MascotConfig,pin:MascotVersionPin,defaultForProduction=false):Readonly<MascotConfig> {
  validateConfig(config);
  if(!/^[a-f0-9]{64}$/.test(pin.configSha256)||!pin.geometryVersion||!pin.animationVersion)throw new Error('Pin de versão incompleto.');
  const key=`${config.mascotId}@${config.modelVersion}`;
  const existing=installed.get(key);
  if(existing && (canonicalJSON(existing.config)!==canonicalJSON(config)||canonicalJSON(existing.pin)!==canonicalJSON(pin)))throw new Error('Versão instalada é imutável; crie outra versão.');
  if(defaultForProduction && config.status!=='approved')throw new Error('A versão padrão precisa estar aprovada.');
  const frozen=existing?.config??freezeDeep(structuredClone(config));
  installed.set(key,{config:frozen,pin:freezeDeep({...pin})});
  if(defaultForProduction)productionDefaults.set(config.mascotId,config.modelVersion);
  return frozen;
}
registerMascot(NICO_CONFIG as MascotConfig,{configSha256:NICO_CONFIG_SHA256,geometryVersion:NICO_GEOMETRY_VERSION,animationVersion:NICO_ANIMATION_VERSION},NICO_CONFIG.status==='approved');

export function resolveMascot(mascotId:string,version?:string):Readonly<MascotConfig> {
  const exact=version??productionDefaults.get(mascotId);
  const entry=exact?installed.get(`${mascotId}@${exact}`):undefined;
  if(!entry)throw new Error('Versão exata aprovada não instalada; use uma prévia candidata explicitamente.');
  return entry.config;
}
export function getMascotPin(config:Readonly<MascotConfig>):Readonly<MascotVersionPin> {
  const entry=installed.get(`${config.mascotId}@${config.modelVersion}`);
  if(!entry || canonicalJSON(entry.config)!==canonicalJSON(config))throw new Error('Modelo não corresponde à configuração registrada.');
  return entry.pin;
}

export function canonicalJSON(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonicalJSON).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${canonicalJSON((value as Record<string, unknown>)[k])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

export async function verifyConfigIntegrity(): Promise<boolean> {
  const bytes = new TextEncoder().encode(canonicalJSON(candidate));
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  const actual = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
  if (actual !== NICO_CONFIG_SHA256) throw new Error('A configuração foi alterada sem criar uma versão. Restaure o ativo registrado.');
  return true;
}
