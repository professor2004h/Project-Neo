'use client';

import { useEffect, useRef } from 'react';

declare global {
  interface Window {
    VANTA: any;
    THREE: any;
  }
}

interface VantaWavesProps {
  children?: React.ReactNode;
  className?: string;
}

export function VantaWaves({ children, className }: VantaWavesProps) {
  const vantaRef = useRef<HTMLDivElement>(null);
  const vantaEffect = useRef<any>(null);

  useEffect(() => {
    // Load Three.js
    const threeScript = document.createElement('script');
    threeScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js';
    
    // Load Vanta waves
    const vantaScript = document.createElement('script');
    vantaScript.src = 'https://cdn.jsdelivr.net/npm/vanta@latest/dist/vanta.waves.min.js';
    
    const initVanta = () => {
      if (vantaRef.current && window.VANTA && window.THREE) {
        vantaEffect.current = window.VANTA.WAVES({
          el: vantaRef.current,
          mouseControls: true,
          touchControls: true,
          gyroControls: false,
          minHeight: 200.00,
          minWidth: 200.00,
          scale: 1.00,
          scaleMobile: 1.00,
          color: 0x070707,
          shininess: 32.00,
          waveHeight: 20.00,
          waveSpeed: 1.00,
          zoom: 0.65
        });
      }
    };

    // Load scripts sequentially
    document.head.appendChild(threeScript);
    
    threeScript.onload = () => {
      document.head.appendChild(vantaScript);
      vantaScript.onload = initVanta;
    };

    return () => {
      if (vantaEffect.current) {
        vantaEffect.current.destroy();
      }
      // Clean up scripts
      if (document.head.contains(threeScript)) {
        document.head.removeChild(threeScript);
      }
      if (document.head.contains(vantaScript)) {
        document.head.removeChild(vantaScript);
      }
    };
  }, []);

  return (
    <div 
      ref={vantaRef} 
      className={`absolute inset-0 ${className || ''}`}
      style={{ zIndex: 0 }}
    >
      {children}
    </div>
  );
} 