/**
 * BACKGROUND.JS - Effets de fond additionnels
 * Gère les effets de fond canvas 2D et animations de particules légères
 */

class BackgroundEffects {
  constructor() {
    this.canvas = null;
    this.ctx = null;
    this.particles = [];
    this.waves = [];
    this.gradientOffset = 0;
    
    this.init();
  }

  init() {
    this.createCanvas();
    this.createParticles(100);
    this.createWaves(5);
    this.animate();
    this.addEventListeners();
  }

  /**
   * Créer le canvas pour les effets 2D
   */
  createCanvas() {
    this.canvas = document.createElement('canvas');
    this.canvas.id = 'background-canvas';
    this.canvas.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: -1;
      pointer-events: none;
    `;
    
    document.body.insertBefore(this.canvas, document.body.firstChild);
    this.ctx = this.canvas.getContext('2d');
    this.resize();
  }

  /**
   * Créer des particules flottantes
   */
  createParticles(count) {
    for (let i = 0; i < count; i++) {
      this.particles.push({
        x: Math.random() * this.canvas.width,
        y: Math.random() * this.canvas.height,
        radius: Math.random() * 3 + 1,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        opacity: Math.random() * 0.5 + 0.2,
        color: this.getRandomColor()
      });
    }
  }

  /**
   * Créer des vagues animées
   */
  createWaves(count) {
    for (let i = 0; i < count; i++) {
      this.waves.push({
        y: (this.canvas.height / count) * i,
        length: Math.random() * 100 + 200,
        amplitude: Math.random() * 30 + 20,
        frequency: Math.random() * 0.01 + 0.005,
        opacity: Math.random() * 0.1 + 0.05,
        color: this.getRandomColor(),
        speed: (Math.random() - 0.5) * 0.5
      });
    }
  }

  /**
   * Obtenir une couleur aléatoire de la palette
   */
  getRandomColor() {
    const colors = [
      'rgba(99, 102, 241, ',   // Primary
      'rgba(139, 92, 246, ',   // Secondary
      'rgba(236, 72, 153, ',   // Accent
      'rgba(59, 130, 246, '    // Blue
    ];
    return colors[Math.floor(Math.random() * colors.length)];
  }

  /**
   * Redimensionner le canvas
   */
  resize() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  /**
   * Dessiner les particules
   */
  drawParticles() {
    this.particles.forEach(particle => {
      // Mettre à jour la position
      particle.x += particle.vx;
      particle.y += particle.vy;
      
      // Rebondir sur les bords
      if (particle.x < 0 || particle.x > this.canvas.width) {
        particle.vx *= -1;
      }
      if (particle.y < 0 || particle.y > this.canvas.height) {
        particle.vy *= -1;
      }
      
      // Dessiner la particule
      this.ctx.beginPath();
      this.ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
      this.ctx.fillStyle = particle.color + particle.opacity + ')';
      this.ctx.fill();
      
      // Effet de glow
      const gradient = this.ctx.createRadialGradient(
        particle.x, particle.y, 0,
        particle.x, particle.y, particle.radius * 3
      );
      gradient.addColorStop(0, particle.color + particle.opacity + ')');
      gradient.addColorStop(1, particle.color + '0)');
      this.ctx.fillStyle = gradient;
      this.ctx.fill();
    });
  }

  /**
   * Dessiner les connexions entre particules proches
   */
  drawConnections() {
    const maxDistance = 150;
    
    for (let i = 0; i < this.particles.length; i++) {
      for (let j = i + 1; j < this.particles.length; j++) {
        const dx = this.particles[i].x - this.particles[j].x;
        const dy = this.particles[i].y - this.particles[j].y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance < maxDistance) {
          const opacity = (1 - distance / maxDistance) * 0.2;
          this.ctx.beginPath();
          this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
          this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
          this.ctx.strokeStyle = `rgba(99, 102, 241, ${opacity})`;
          this.ctx.lineWidth = 1;
          this.ctx.stroke();
        }
      }
    }
  }

  /**
   * Dessiner les vagues
   */
  drawWaves() {
    this.waves.forEach(wave => {
      this.ctx.beginPath();
      
      for (let x = 0; x < this.canvas.width; x++) {
        const y = wave.y + Math.sin(x * wave.frequency + this.gradientOffset) * wave.amplitude;
        
        if (x === 0) {
          this.ctx.moveTo(x, y);
        } else {
          this.ctx.lineTo(x, y);
        }
      }
      
      this.ctx.strokeStyle = wave.color + wave.opacity + ')';
      this.ctx.lineWidth = 2;
      this.ctx.stroke();
      
      // Déplacer la vague
      wave.y += wave.speed;
      
      // Réinitialiser si hors écran
      if (wave.y > this.canvas.height + 100) {
        wave.y = -100;
      } else if (wave.y < -100) {
        wave.y = this.canvas.height + 100;
      }
    });
  }

  /**
   * Dessiner un gradient animé en arrière-plan
   */
  drawAnimatedGradient() {
    const gradient = this.ctx.createLinearGradient(
      0, 0,
      this.canvas.width,
      this.canvas.height
    );
    
    const offset = Math.sin(this.gradientOffset * 0.5) * 0.2;
    
    gradient.addColorStop(0, `rgba(15, 23, 42, 1)`);
    gradient.addColorStop(0.5 + offset, `rgba(30, 41, 59, 0.8)`);
    gradient.addColorStop(1, `rgba(15, 23, 42, 1)`);
    
    this.ctx.fillStyle = gradient;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
  }

  /**
   * Créer des cercles concentriques au clic
   */
  createRipple(x, y) {
    const ripple = {
      x: x,
      y: y,
      radius: 0,
      maxRadius: 200,
      opacity: 0.5,
      growing: true
    };
    
    const animateRipple = () => {
      if (ripple.growing) {
        ripple.radius += 5;
        ripple.opacity -= 0.01;
        
        if (ripple.radius >= ripple.maxRadius || ripple.opacity <= 0) {
          return;
        }
        
        this.ctx.beginPath();
        this.ctx.arc(ripple.x, ripple.y, ripple.radius, 0, Math.PI * 2);
        this.ctx.strokeStyle = `rgba(99, 102, 241, ${ripple.opacity})`;
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        
        requestAnimationFrame(animateRipple);
      }
    };
    
    animateRipple();
  }

  /**
   * Ajouter les écouteurs d'événements
   */
  addEventListeners() {
    window.addEventListener('resize', () => this.resize());
    
    // Créer un ripple au clic
    document.addEventListener('click', (e) => {
      this.createRipple(e.clientX, e.clientY);
    });
    
    // Ajouter des particules au mouvement de la souris
    let lastMouseMove = 0;
    document.addEventListener('mousemove', (e) => {
      const now = Date.now();
      if (now - lastMouseMove > 100) {
        this.particles.push({
          x: e.clientX,
          y: e.clientY,
          radius: Math.random() * 2 + 1,
          vx: (Math.random() - 0.5) * 2,
          vy: (Math.random() - 0.5) * 2,
          opacity: 0.8,
          color: this.getRandomColor(),
          lifetime: 60
        });
        lastMouseMove = now;
      }
    });
  }

  /**
   * Boucle d'animation principale
   */
  animate() {
    // Effacer le canvas
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    // Dessiner le gradient animé
    this.drawAnimatedGradient();
    
    // Dessiner les vagues
    this.drawWaves();
    
    // Dessiner les particules
    this.drawParticles();
    
    // Dessiner les connexions
    this.drawConnections();
    
    // Incrémenter l'offset du gradient
    this.gradientOffset += 0.01;
    
    // Nettoyer les particules avec lifetime
    this.particles = this.particles.filter(particle => {
      if (particle.lifetime !== undefined) {
        particle.lifetime--;
        particle.opacity *= 0.95;
        return particle.lifetime > 0;
      }
      return true;
    });
    
    // Continuer l'animation
    requestAnimationFrame(() => this.animate());
  }

  /**
   * Ajouter une explosion de particules
   */
  explode(x, y, count = 30) {
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count;
      const velocity = Math.random() * 3 + 2;
      
      this.particles.push({
        x: x,
        y: y,
        radius: Math.random() * 3 + 1,
        vx: Math.cos(angle) * velocity,
        vy: Math.sin(angle) * velocity,
        opacity: 1,
        color: this.getRandomColor(),
        lifetime: 120
      });
    }
  }
}

// Initialiser au chargement
window.addEventListener('DOMContentLoaded', () => {
  window.backgroundEffects = new BackgroundEffects();
  console.log('🎨 Effets de fond initialisés');
});

// Exporter pour utilisation externe
window.BackgroundEffects = BackgroundEffects;