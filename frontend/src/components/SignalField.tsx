"use client";

/**
 * SignalField: the hero visualization.
 *
 * A drifting field of candidate signals. Periodically a gate sweep passes
 * through: flagged signals flare spurious-rose and collapse (they had no
 * point-in-time edge), a few hold emerald (they survived verification).
 * All state lives in the vertex shader, so 900 points cost one draw call.
 */

import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

const COUNT = 900;
const FIELD = 9;

const VERT = /* glsl */ `
  uniform float uTime;
  attribute float aSeed;
  varying float vGlow;
  varying vec3 vColor;

  void main() {
    vec3 p = position;

    // slow breathing drift so the field feels alive
    p.x += 0.12 * sin(uTime * 0.22 + aSeed * 12.0);
    p.y += 0.10 * sin(uTime * 0.18 + aSeed * 31.0);
    p.z += 0.12 * cos(uTime * 0.20 + aSeed * 17.0);

    // each point lives on its own 14s cycle offset by seed
    float phase = fract(uTime / 14.0 + aSeed);
    vec3 color = vec3(0.09, 0.30, 0.24);       // idle emerald-gray
    float glow = 0.38 + 0.30 * sin(uTime * 1.1 + aSeed * 40.0);
    float size = 1.9 + 0.9 * fract(aSeed * 5.7);

    // the gate sweep: [0.55, 0.70) flag, [0.70, 0.85) collapse
    float flagged = step(fract(aSeed * 91.7), 0.82);
    float flaring = smoothstep(0.55, 0.60, phase) * (1.0 - smoothstep(0.60, 0.70, phase));
    float collapsing = smoothstep(0.70, 0.82, phase);
    color = mix(color, vec3(0.62, 0.24, 0.30), flaring * flagged);
    glow = mix(glow, 0.9, flaring * flagged);
    size *= 1.0 + 0.5 * flaring * flagged;
    size *= 1.0 - 0.85 * collapsing * flagged;
    glow *= 1.0 - 0.8 * collapsing * flagged;

    // survivors past the sweep hold bright
    float held = (1.0 - flagged) * smoothstep(0.70, 0.85, phase);
    color = mix(color, vec3(0.13, 0.48, 0.36), held);
    glow = mix(glow, 0.75, held);

    vColor = color;
    vGlow = glow;

    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    gl_PointSize = size * (52.0 / -mv.z);
    gl_Position = projectionMatrix * mv;
  }
`;

const FRAG = /* glsl */ `
  varying float vGlow;
  varying vec3 vColor;

  void main() {
    float d = length(gl_PointCoord - vec2(0.5));
    float core = smoothstep(0.5, 0.06, d);
    float halo = smoothstep(0.5, 0.32, d) * 0.35;
    vec3 c = vColor * (core + halo) * vGlow;
    gl_FragColor = vec4(c, (core + halo) * 0.55);
  }
`;

function Field() {
  const ref = useRef<THREE.Points>(null);
  const matRef = useRef<THREE.ShaderMaterial>(null);

  const { positions, seeds } = useMemo(() => {
    const positions = new Float32Array(COUNT * 3);
    const seeds = new Float32Array(COUNT);
    let i = 0;
    for (let x = 0; x < 30; x++) {
      for (let z = 0; z < 30; z++) {
        const gx = (x / 29 - 0.5) * FIELD;
        const gz = (z / 29 - 0.5) * FIELD;
        positions[i * 3] = gx + (Math.random() - 0.5) * 0.35;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 2.6;
        positions[i * 3 + 2] = gz + (Math.random() - 0.5) * 0.35;
        seeds[i] = Math.random();
        i++;
      }
    }
    return { positions, seeds };
  }, []);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (matRef.current) matRef.current.uniforms.uTime.value = t;
    if (ref.current) {
      ref.current.rotation.y = Math.sin(t * 0.05) * 0.18 + t * 0.012;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attribute-aSeed" args={[seeds, 1]} />
      </bufferGeometry>
      <shaderMaterial
        ref={matRef}
        vertexShader={VERT}
        fragmentShader={FRAG}
        uniforms={{ uTime: { value: 0 } }}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

function Rig() {
  useFrame((state) => {
    const t = state.clock.elapsedTime;
    state.camera.position.x = Math.sin(t * 0.06) * 2.2;
    state.camera.position.y = 2.1 + Math.sin(t * 0.09) * 0.35;
    state.camera.position.z = 7.6 + Math.cos(t * 0.05) * 0.6;
    state.camera.lookAt(0, -0.2, 0);
  });
  return null;
}

export default function SignalField() {
  return (
    <div className="pointer-events-none absolute inset-0" aria-hidden>
      <Canvas
        dpr={[1, 1.75]}
        camera={{ position: [0, 2.1, 7.6], fov: 42 }}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      >
        <fog attach="fog" args={["#05070a", 6.5, 13.5]} />
        <Field />
        <Rig />
      </Canvas>
      {/* fade the field into the page at every edge, protect text legibility */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_30%,#05070a_92%)]" />
      <div className="absolute inset-y-0 left-0 w-3/5 bg-gradient-to-r from-background/90 via-background/55 to-transparent" />
      <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-background to-transparent" />
    </div>
  );
}
