/**
 * THREE.JS BACKGROUND - Interface 3D Interactive
 * Crée un arrière-plan animé avec particules et formes géométriques
 */

class ThreeBackground {
  constructor() {
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.particles = null;
    this.geometries = [];
    this.mouse = { x: 0, y: 0 };
    this.targetMouse = { x: 0, y: 0 };
    this.time = 0;
    
    this.init();
    this.createParticles();
    this.createFloatingGeometries();
    this.addEventListeners();
    this.animate();
  }

  init() {
    // Créer le canvas container
    const container = document.createElement('div');
    container.id = 'three-background';
    document.body.insertBefore(container, document.body.firstChild);

    // Setup Scene
    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.Fog(0x0f172a, 1, 100);

    // Setup Camera
    this.camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    this.camera.position.z = 30;

    // Setup Renderer
    this.renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true
    });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(0x0f172a, 1);
    container.appendChild(this.renderer.domElement);
  }

  createParticles() {
    const particlesCount = 2000;
    const positions = new Float32Array(particlesCount * 3);
    const colors = new Float32Array(particlesCount * 3);
    const sizes = new Float32Array(particlesCount);

    const colorPalette = [
      new THREE.Color(0x6366f1), // Primary
      new THREE.Color(0x8b5cf6), // Secondary
      new THREE.Color(0xec4899), // Accent
      new THREE.Color(0x3b82f6)  // Blue
    ];

    for (let i = 0; i < particlesCount; i++) {
      // Positions
      const i3 = i * 3;
      positions[i3] = (Math.random() - 0.5) * 100;
      positions[i3 + 1] = (Math.random() - 0.5) * 100;
      positions[i3 + 2] = (Math.random() - 0.5) * 100;

      // Colors
      const color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
      colors[i3] = color.r;
      colors[i3 + 1] = color.g;
      colors[i3 + 2] = color.b;

      // Sizes
      sizes[i] = Math.random() * 2;
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    const material = new THREE.PointsMaterial({
      size: 0.5,
      vertexColors: true,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      sizeAttenuation: true
    });

    this.particles = new THREE.Points(geometry, material);
    this.scene.add(this.particles);
  }

  createFloatingGeometries() {
    const geometryTypes = [
      { geometry: new THREE.OctahedronGeometry(2, 0), count: 5 },
      { geometry: new THREE.TorusGeometry(2, 0.5, 16, 100), count: 3 },
      { geometry: new THREE.IcosahedronGeometry(1.5, 0), count: 4 },
      { geometry: new THREE.TetrahedronGeometry(2, 0), count: 3 }
    ];

    geometryTypes.forEach(({ geometry, count }) => {
      for (let i = 0; i < count; i++) {
        const material = new THREE.MeshPhongMaterial({
          color: this.getRandomColor(),
          transparent: true,
          opacity: 0.15,
          wireframe: true,
          emissive: this.getRandomColor(),
          emissiveIntensity: 0.3
        });

        const mesh = new THREE.Mesh(geometry, material);
        
        // Position aléatoire
        mesh.position.x = (Math.random() - 0.5) * 60;
        mesh.position.y = (Math.random() - 0.5) * 60;
        mesh.position.z = (Math.random() - 0.5) * 30;
        
        // Rotation aléatoire
        mesh.rotation.x = Math.random() * Math.PI;
        mesh.rotation.y = Math.random() * Math.PI;
        
        // Données d'animation
        mesh.userData = {
          rotationSpeed: {
            x: (Math.random() - 0.5) * 0.02,
            y: (Math.random() - 0.5) * 0.02,
            z: (Math.random() - 0.5) * 0.02
          },
          floatSpeed: Math.random() * 0.5 + 0.5,
          floatOffset: Math.random() * Math.PI * 2
        };
        
        this.scene.add(mesh);
        this.geometries.push(mesh);
      }
    });

    // Ajouter des lumières
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
    this.scene.add(ambientLight);

    const pointLight1 = new THREE.PointLight(0x6366f1, 1, 100);
    pointLight1.position.set(10, 10, 10);
    this.scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0xec4899, 1, 100);
    pointLight2.position.set(-10, -10, 10);
    this.scene.add(pointLight2);
  }

  getRandomColor() {
    const colors = [0x6366f1, 0x8b5cf6, 0xec4899, 0x3b82f6];
    return colors[Math.floor(Math.random() * colors.length)];
  }

  addEventListeners() {
    window.addEventListener('resize', () => this.onWindowResize());
    document.addEventListener('mousemove', (e) => this.onMouseMove(e));
  }

  onWindowResize() {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  onMouseMove(event) {
    this.targetMouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    this.targetMouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    this.time += 0.01;

    // Smooth mouse following
    this.mouse.x += (this.targetMouse.x - this.mouse.x) * 0.05;
    this.mouse.y += (this.targetMouse.y - this.mouse.y) * 0.05;

    // Rotation des particules
    if (this.particles) {
      this.particles.rotation.y = this.time * 0.05;
      this.particles.rotation.x = this.mouse.y * 0.3;
      
      // Animation ondulante des particules
      const positions = this.particles.geometry.attributes.position.array;
      for (let i = 0; i < positions.length; i += 3) {
        const x = positions[i];
        const z = positions[i + 2];
        positions[i + 1] += Math.sin(this.time + x * 0.1) * 0.02;
      }
      this.particles.geometry.attributes.position.needsUpdate = true;
    }

    // Animation des géométries flottantes
    this.geometries.forEach((mesh) => {
      // Rotation
      mesh.rotation.x += mesh.userData.rotationSpeed.x;
      mesh.rotation.y += mesh.userData.rotationSpeed.y;
      mesh.rotation.z += mesh.userData.rotationSpeed.z;
      
      // Mouvement flottant
      const floatY = Math.sin(this.time * mesh.userData.floatSpeed + mesh.userData.floatOffset) * 2;
      mesh.position.y += (floatY - mesh.position.y + mesh.userData.originalY || 0) * 0.02;
      
      // Suivre légèrement la souris
      mesh.position.x += (this.mouse.x * 5 - mesh.position.x) * 0.01;
      mesh.position.y += (this.mouse.y * 5 - mesh.position.y) * 0.01;
    });

    // Mouvement de la caméra
    this.camera.position.x = this.mouse.x * 2;
    this.camera.position.y = this.mouse.y * 2;
    this.camera.lookAt(this.scene.position);

    this.renderer.render(this.scene, this.camera);
  }
}

// Initialiser au chargement de la page
if (typeof THREE !== 'undefined') {
  window.addEventListener('load', () => {
    window.threeBackground = new ThreeBackground();
  });
} else {
  console.warn('Three.js n\'est pas chargé. Veuillez inclure Three.js avant ce script.');
}