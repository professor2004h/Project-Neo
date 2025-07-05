"use client"
import type React from "react"
import { useEffect, useRef } from "react"
import { Renderer, Program, Mesh, Triangle } from "ogl"

// Vertex Shader
const vert = `
attribute vec2 uv;
attribute vec2 position;

varying vec2 vUv;

void main() {
  vUv = uv;
  gl_Position = vec4(position, 0, 1);
}
`

// Fragment Shader
const frag = `
precision highp float;

uniform float uTime;
uniform vec3 uResolution;
uniform float uIsDarkMode;

varying vec2 vUv;

void main() {
  float mr = min(uResolution.x, uResolution.y);
  vec2 uv = (vUv.xy * 2.0 - 1.0) * uResolution.xy / mr;

  float d = -uTime * 1.2;
  float a = 0.0;
  for (float i = 0.0; i < 8.0; ++i) {
      a += cos(i - d - a * uv.x);
      d += sin(uv.y * i + a);
  }
  d += uTime * 1.0;
  vec3 col = vec3(cos(uv * vec2(d, a)) * 0.6 + 0.4, cos(a + d) * 0.5 + 0.5);
  col = cos(col * cos(vec3(d, a, 2.5)) * 0.5 + 0.5);
  
  float gray = dot(col, vec3(0.299, 0.587, 0.114));
  
  vec3 finalColor;
  if (uIsDarkMode > 0.5) {
      // Dark mode: white pattern on black background
      finalColor = vec3(gray);
  } else {
      // Light mode: black pattern on white background
      finalColor = vec3(1.0 - gray);
  }
  
  gl_FragColor = vec4(finalColor, 1.0);
}
`

type NovatrixProps = {}

export const Novatrix: React.FC<NovatrixProps> = () => {
  const ctnDom = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ctnDom.current) {
      return
    }

    const ctn = ctnDom.current
    const renderer = new Renderer()
    const gl = renderer.gl
    gl.clearColor(1, 1, 1, 1)

    const geometry = new Triangle(gl)

    const program = new Program(gl, {
      vertex: vert,
      fragment: frag,
      uniforms: {
        uTime: { value: 0 },
        uIsDarkMode: { value: 0.0 },
        uResolution: {
          value: [ctn.offsetWidth, ctn.offsetHeight, ctn.offsetWidth / ctn.offsetHeight],
        },
      },
    })

    const mesh = new Mesh(gl, { geometry, program })

    function resize() {
      const scale = 1
      renderer.setSize(ctn.offsetWidth * scale, ctn.offsetHeight * scale)
      program.uniforms.uResolution.value = [gl.canvas.width, gl.canvas.height, gl.canvas.width / gl.canvas.height]
    }
    window.addEventListener("resize", resize, false)
    resize()

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
    const updateTheme = () => {
      program.uniforms.uIsDarkMode.value = mediaQuery.matches ? 1.0 : 0.0
    }

    updateTheme()
    mediaQuery.addEventListener("change", updateTheme)

    let animateId: number

    function update(t: number) {
      animateId = requestAnimationFrame(update)
      program.uniforms.uTime.value = t * 0.001
      renderer.render({ scene: mesh })
    }
    animateId = requestAnimationFrame(update)

    ctn.appendChild(gl.canvas)

    return () => {
      cancelAnimationFrame(animateId)
      window.removeEventListener("resize", resize)
      mediaQuery.removeEventListener("change", updateTheme)
      if (ctn.contains(gl.canvas)) {
        ctn.removeChild(gl.canvas)
      }
      gl.getExtension("WEBGL_lose_context")?.loseContext()
    }
  }, [])

  return <div ref={ctnDom} className="gradient-canvas h-full w-full"></div>
}

const Background = () => {
  return (
    <div className="h-screen w-screen">
      <Novatrix />
    </div>
  )
}

export default Background
