/**
 * Vincere RT — Hero 3D vetorizado
 * WebGL com Three.js: abrigo geométrico abstrato + partículas + parallax
 */
(function () {
  const canvasHost = document.getElementById('hero-3d');
  if (!canvasHost) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function boot(THREE) {
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x0c332c, 0.028);

    const camera = new THREE.PerspectiveCamera(
      42,
      canvasHost.clientWidth / Math.max(canvasHost.clientHeight, 1),
      0.1,
      100
    );
    camera.position.set(0, 1.1, 8.2);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(canvasHost.clientWidth, canvasHost.clientHeight);
    renderer.setClearColor(0x000000, 0);
    canvasHost.appendChild(renderer.domElement);

    // Lights
    const ambient = new THREE.AmbientLight(0xb8d4c8, 0.55);
    scene.add(ambient);

    const key = new THREE.DirectionalLight(0xf0e6d2, 1.15);
    key.position.set(4, 6, 3);
    scene.add(key);

    const rim = new THREE.DirectionalLight(0x6f9486, 0.7);
    rim.position.set(-5, 2, -4);
    scene.add(rim);

    const gold = new THREE.PointLight(0xb8956a, 1.4, 18);
    gold.position.set(2.5, 2.2, 3);
    scene.add(gold);

    const root = new THREE.Group();
    root.position.set(1.6, -0.4, 0);
    scene.add(root);

    const matSolid = new THREE.MeshStandardMaterial({
      color: 0xdce8e3,
      metalness: 0.08,
      roughness: 0.42,
      flatShading: true,
    });

    const matAccent = new THREE.MeshStandardMaterial({
      color: 0xb8956a,
      metalness: 0.35,
      roughness: 0.35,
      flatShading: true,
    });

    const matGlass = new THREE.MeshPhysicalMaterial({
      color: 0x7a9e8f,
      metalness: 0,
      roughness: 0.15,
      transmission: 0.55,
      thickness: 0.6,
      transparent: true,
      opacity: 0.85,
      flatShading: true,
    });

    // Base plinth
    const base = new THREE.Mesh(new THREE.CylinderGeometry(2.4, 2.7, 0.18, 6), matSolid);
    base.position.y = -1.15;
    root.add(base);

    // Shelter walls (abstract home)
    const wallL = new THREE.Mesh(new THREE.BoxGeometry(0.18, 2.2, 2.4), matSolid);
    wallL.position.set(-1.1, 0, 0);
    root.add(wallL);

    const wallR = new THREE.Mesh(new THREE.BoxGeometry(0.18, 2.2, 2.4), matSolid);
    wallR.position.set(1.1, 0, 0);
    root.add(wallR);

    const back = new THREE.Mesh(new THREE.BoxGeometry(2.4, 2.2, 0.18), matGlass);
    back.position.set(0, 0, -1.15);
    root.add(back);

    // Roof — pitched vector form
    const roofGeo = new THREE.ConeGeometry(1.85, 1.35, 4);
    const roof = new THREE.Mesh(roofGeo, matAccent);
    roof.position.y = 1.55;
    roof.rotation.y = Math.PI / 4;
    root.add(roof);

    // Floating rings (care / continuity)
    const ringMat = new THREE.MeshStandardMaterial({
      color: 0xd4b896,
      metalness: 0.5,
      roughness: 0.3,
      flatShading: true,
      side: THREE.DoubleSide,
    });

    const ring1 = new THREE.Mesh(new THREE.TorusGeometry(2.9, 0.035, 6, 48), ringMat);
    ring1.rotation.x = Math.PI / 2.4;
    root.add(ring1);

    const ring2 = new THREE.Mesh(new THREE.TorusGeometry(3.35, 0.025, 6, 56), ringMat);
    ring2.rotation.x = Math.PI / 2.1;
    ring2.rotation.z = 0.3;
    root.add(ring2);

    // Orbiting polyhedra
    const orbiters = new THREE.Group();
    root.add(orbiters);

    const shapes = [
      new THREE.OctahedronGeometry(0.28, 0),
      new THREE.IcosahedronGeometry(0.22, 0),
      new THREE.TetrahedronGeometry(0.26, 0),
    ];

    shapes.forEach((geo, i) => {
      const m = new THREE.Mesh(geo, i === 1 ? matAccent : matSolid);
      const angle = (i / shapes.length) * Math.PI * 2;
      m.position.set(Math.cos(angle) * 2.6, 0.4 + i * 0.25, Math.sin(angle) * 2.6);
      m.userData = { angle, radius: 2.6 + i * 0.15, speed: 0.25 + i * 0.08, y: m.position.y };
      orbiters.add(m);
    });

    // Soft particle field
    const count = reduceMotion ? 40 : 120;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 14;
      positions[i * 3 + 1] = (Math.random() - 0.3) * 8;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10 - 2;
    }
    const pGeo = new THREE.BufferGeometry();
    pGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particles = new THREE.Points(
      pGeo,
      new THREE.PointsMaterial({
        color: 0xd4b896,
        size: 0.045,
        transparent: true,
        opacity: 0.65,
        depthWrite: false,
      })
    );
    scene.add(particles);

    // Pointer parallax
    const pointer = { x: 0, y: 0 };
    const target = { x: 0, y: 0 };

    function onPointer(e) {
      const x = e.touches ? e.touches[0].clientX : e.clientX;
      const y = e.touches ? e.touches[0].clientY : e.clientY;
      target.x = (x / window.innerWidth - 0.5) * 2;
      target.y = (y / window.innerHeight - 0.5) * 2;
    }

    if (!reduceMotion) {
      window.addEventListener('pointermove', onPointer, { passive: true });
    }

    function onResize() {
      const w = canvasHost.clientWidth;
      const h = canvasHost.clientHeight;
      camera.aspect = w / Math.max(h, 1);
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    }

    window.addEventListener('resize', onResize);

    let raf = 0;
    const clock = new THREE.Clock();

    function frame() {
      raf = requestAnimationFrame(frame);
      const t = clock.getElapsedTime();

      pointer.x += (target.x - pointer.x) * 0.04;
      pointer.y += (target.y - pointer.y) * 0.04;

      if (!reduceMotion) {
        root.rotation.y = t * 0.12 + pointer.x * 0.25;
        root.rotation.x = Math.sin(t * 0.35) * 0.04 + pointer.y * -0.08;
        root.position.y = -0.4 + Math.sin(t * 0.6) * 0.08;

        ring1.rotation.z = t * 0.15;
        ring2.rotation.z = -t * 0.1;

        orbiters.children.forEach((m) => {
          const d = m.userData;
          const a = d.angle + t * d.speed;
          m.position.x = Math.cos(a) * d.radius;
          m.position.z = Math.sin(a) * d.radius;
          m.position.y = d.y + Math.sin(t * 1.2 + d.angle) * 0.2;
          m.rotation.x = t * 0.6;
          m.rotation.y = t * 0.4;
        });

        particles.rotation.y = t * 0.02;
        gold.intensity = 1.2 + Math.sin(t * 1.5) * 0.25;
      }

      camera.position.x = pointer.x * 0.35;
      camera.position.y = 1.1 + pointer.y * -0.2;
      camera.lookAt(1.2, 0.2, 0);

      renderer.render(scene, camera);
    }

    frame();

    // Pause when offscreen
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            if (!raf) frame();
          } else {
            cancelAnimationFrame(raf);
            raf = 0;
          }
        },
        { threshold: 0.05 }
      );
      io.observe(canvasHost);
    }
  }

  // Load Three.js from CDN
  const script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.min.js';
  script.defer = true;
  script.onload = () => {
    if (window.THREE) boot(window.THREE);
  };
  script.onerror = () => {
    canvasHost.classList.add('hero__canvas--fallback');
  };
  document.head.appendChild(script);
})();
