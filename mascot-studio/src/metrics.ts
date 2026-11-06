import * as THREE from 'three';

export interface ModelMetrics { triangles: number; vertices: number; meshes: number; materials: number; geometries: number }
export function inspectModel(group: THREE.Object3D): ModelMetrics {
  let triangles = 0; let vertices = 0; let meshes = 0;
  const materials = new Set<THREE.Material>(); const geometries = new Set<THREE.BufferGeometry>();
  group.traverse(node => {
    if (!(node instanceof THREE.Mesh)) return;
    meshes++;
    const geometry = node.geometry as THREE.BufferGeometry;
    const count = geometry.getAttribute('position')?.count ?? 0;
    triangles += (geometry.index?.count ?? count) / 3;
    vertices += count; geometries.add(geometry);
    const nodeMaterials = Array.isArray(node.material) ? node.material : [node.material];
    nodeMaterials.forEach(material => materials.add(material));
  });
  return { triangles, vertices, meshes, materials: materials.size, geometries: geometries.size };
}
