'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface ThreeSpinnerProps {
  size?: number;
  color?: string;
  className?: string;
}

export function ThreeSpinner({ 
  size = 16, 
  color = 'currentColor',
  className = '' 
}: ThreeSpinnerProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const frameRef = useRef<number>();

  useEffect(() => {
    if (!mountRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ 
      alpha: true, 
      antialias: true,
      powerPreference: 'low-power'
    });
    
    renderer.setSize(size, size);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0); // Transparent background
    
    mountRef.current.appendChild(renderer.domElement);

    // Create wireframe geometry - icosphere for clean look
    const geometry = new THREE.IcosahedronGeometry(1, 1);
    
    // Parse color - handle CSS variables and currentColor
    let threeColor = new THREE.Color(0x666666); // fallback
    if (color === 'currentColor') {
      // Get computed color from parent element
      const computedStyle = getComputedStyle(mountRef.current.parentElement || document.body);
      const currentColor = computedStyle.color;
      try {
        threeColor = new THREE.Color(currentColor);
      } catch {
        threeColor = new THREE.Color(0x666666);
      }
    } else {
      try {
        threeColor = new THREE.Color(color);
      } catch {
        threeColor = new THREE.Color(0x666666);
      }
    }

    // Create wireframe material
    const material = new THREE.MeshBasicMaterial({
      color: threeColor,
      wireframe: true,
      transparent: true,
      opacity: 0.8
    });

    // Create mesh
    const wireframe = new THREE.Mesh(geometry, material);
    scene.add(wireframe);

    // Add some inner structure for more interesting visual
    const innerGeometry = new THREE.OctahedronGeometry(0.6, 0);
    const innerMaterial = new THREE.MeshBasicMaterial({
      color: threeColor,
      wireframe: true,
      transparent: true,
      opacity: 0.6
    });
    const innerWireframe = new THREE.Mesh(innerGeometry, innerMaterial);
    scene.add(innerWireframe);

    // Position camera
    camera.position.z = 2.5;

    // Store refs
    sceneRef.current = scene;
    rendererRef.current = renderer;

    // Animation loop
    let startTime = Date.now();
    const animate = () => {
      const elapsed = (Date.now() - startTime) * 0.001; // Convert to seconds
      
      // Smooth rotation with easing
      wireframe.rotation.x = elapsed * 0.5;
      wireframe.rotation.y = elapsed * 0.3;
      wireframe.rotation.z = elapsed * 0.1;
      
      // Counter-rotate inner structure for more dynamic effect
      innerWireframe.rotation.x = -elapsed * 0.3;
      innerWireframe.rotation.y = elapsed * 0.6;
      innerWireframe.rotation.z = -elapsed * 0.2;

      renderer.render(scene, camera);
      frameRef.current = requestAnimationFrame(animate);
    };

    animate();

    // Cleanup function
    return () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
      
      if (rendererRef.current) {
        rendererRef.current.dispose();
      }
      
      if (sceneRef.current) {
        // Dispose of geometries and materials
        sceneRef.current.traverse((object) => {
          if (object instanceof THREE.Mesh) {
            object.geometry.dispose();
            if (Array.isArray(object.material)) {
              object.material.forEach(material => material.dispose());
            } else {
              object.material.dispose();
            }
          }
        });
      }
      
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
    };
  }, [size, color]);

  return (
    <div 
      ref={mountRef} 
      className={className}
      style={{ 
        width: size, 
        height: size,
        display: 'inline-block'
      }} 
    />
  );
} 