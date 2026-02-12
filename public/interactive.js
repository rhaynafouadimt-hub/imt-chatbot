/**
 * INTERACTIVE.JS - Effets interactifs et animations dynamiques
 * Gère les interactions utilisateur et effets visuels supplémentaires
 */

class InteractiveEffects {
  constructor() {
    this.cursor = null;
    this.cursorFollower = null;
    this.ripples = [];
    
    this.init();
  }

  init() {
    this.createCustomCursor();
    this.addRippleEffect();
    this.addHoverEffects();
    this.addScrollEffects();
    this.initParallax();
  }

  /**
   * Créer un curseur personnalisé avec effet de suivi
   */
  createCustomCursor() {
    // Curseur principal
    this.cursor = document.createElement('div');
    this.cursor.className = 'custom-cursor';
    this.cursor.style.cssText = `
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: linear-gradient(135deg, #6366f1, #ec4899);
      position: fixed;
      pointer-events: none;
      z-index: 10000;
      mix-blend-mode: difference;
      transition: transform 0.15s ease;
      transform: translate(-50%, -50%);
    `;
    
    // Curseur suiveur (plus grand)
    this.cursorFollower = document.createElement('div');
    this.cursorFollower.className = 'custom-cursor-follower';
    this.cursorFollower.style.cssText = `
      width: 40px;
      height: 40px;
      border-radius: 50%;
      border: 2px solid rgba(99, 102, 241, 0.5);
      position: fixed;
      pointer-events: none;
      z-index: 9999;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      transform: translate(-50%, -50%);
    `;
    
    document.body.appendChild(this.cursor);
    document.body.appendChild(this.cursorFollower);
    
    // Suivre le mouvement de la souris
    document.addEventListener('mousemove', (e) => {
      // Curseur principal (rapide)
      this.cursor.style.left = e.clientX + 'px';
      this.cursor.style.top = e.clientY + 'px';
      
      // Curseur suiveur (avec délai)
      setTimeout(() => {
        this.cursorFollower.style.left = e.clientX + 'px';
        this.cursorFollower.style.top = e.clientY + 'px';
      }, 50);
    });
    
    // Agrandir au survol d'éléments cliquables
    const clickables = 'a, button, .MuiListItemButton-root, .MuiIconButton-root, input, textarea';
    document.addEventListener('mouseover', (e) => {
      if (e.target.matches(clickables) || e.target.closest(clickables)) {
        this.cursor.style.transform = 'translate(-50%, -50%) scale(1.5)';
        this.cursorFollower.style.transform = 'translate(-50%, -50%) scale(1.5)';
        this.cursorFollower.style.borderColor = 'rgba(236, 72, 153, 0.8)';
      }
    });
    
    document.addEventListener('mouseout', (e) => {
      if (e.target.matches(clickables) || e.target.closest(clickables)) {
        this.cursor.style.transform = 'translate(-50%, -50%) scale(1)';
        this.cursorFollower.style.transform = 'translate(-50%, -50%) scale(1)';
        this.cursorFollower.style.borderColor = 'rgba(99, 102, 241, 0.5)';
      }
    });
  }

  /**
   * Effet de vague (ripple) au clic
   */
  addRippleEffect() {
    document.addEventListener('click', (e) => {
      const ripple = document.createElement('div');
      ripple.className = 'ripple-effect';
      ripple.style.cssText = `
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.6), transparent);
        position: fixed;
        left: ${e.clientX}px;
        top: ${e.clientY}px;
        transform: translate(-50%, -50%);
        pointer-events: none;
        z-index: 9998;
        animation: rippleExpand 0.6s ease-out forwards;
      `;
      
      document.body.appendChild(ripple);
      
      setTimeout(() => ripple.remove(), 600);
    });
    
    // Ajouter l'animation CSS
    if (!document.getElementById('ripple-animation')) {
      const style = document.createElement('style');
      style.id = 'ripple-animation';
      style.textContent = `
        @keyframes rippleExpand {
          to {
            width: 100px;
            height: 100px;
            opacity: 0;
          }
        }
      `;
      document.head.appendChild(style);
    }
  }

  /**
   * Effets de survol avancés
   */
  addHoverEffects() {
    // Observer les nouveaux éléments ajoutés au DOM
    const observer = new MutationObserver(() => {
      this.applyHoverEffects();
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    this.applyHoverEffects();
  }

  applyHoverEffects() {
    // Effet tilt sur les cartes
    const cards = document.querySelectorAll('.MuiPaper-root, .MuiCard-root');
    
    cards.forEach(card => {
      if (card.dataset.tiltApplied) return;
      card.dataset.tiltApplied = 'true';
      
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 10;
        const rotateY = (centerX - x) / 10;
        
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
      });
      
      card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
      });
    });
  }

  /**
   * Effets de parallaxe au scroll
   */
  addScrollEffects() {
    let ticking = false;
    
    window.addEventListener('scroll', () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          this.updateScrollEffects();
          ticking = false;
        });
        ticking = true;
      }
    });
  }

  updateScrollEffects() {
    const scrolled = window.pageYOffset;
    
    // Parallaxe sur le background
    const bgElements = document.querySelectorAll('#three-background');
    bgElements.forEach(element => {
      element.style.transform = `translateY(${scrolled * 0.5}px)`;
    });
  }

  /**
   * Effet parallaxe au mouvement de la souris
   */
  initParallax() {
    document.addEventListener('mousemove', (e) => {
      const moveX = (e.clientX - window.innerWidth / 2) / 50;
      const moveY = (e.clientY - window.innerHeight / 2) / 50;
      
      // Appliquer l'effet aux éléments avec classe parallax
      const parallaxElements = document.querySelectorAll('.parallax-element');
      parallaxElements.forEach((element, index) => {
        const speed = (index + 1) * 0.5;
        element.style.transform = `translate(${moveX * speed}px, ${moveY * speed}px)`;
      });
    });
  }

  /**
   * Créer des particules flottantes au survol
   */
  createFloatingParticles(x, y) {
    const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#3b82f6'];
    
    for (let i = 0; i < 5; i++) {
      const particle = document.createElement('div');
      const color = colors[Math.floor(Math.random() * colors.length)];
      const size = Math.random() * 6 + 2;
      const angle = (Math.PI * 2 * i) / 5;
      const velocity = Math.random() * 2 + 1;
      
      particle.style.cssText = `
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        background: ${color};
        position: fixed;
        left: ${x}px;
        top: ${y}px;
        pointer-events: none;
        z-index: 9997;
        box-shadow: 0 0 10px ${color};
      `;
      
      document.body.appendChild(particle);
      
      const destX = x + Math.cos(angle) * 100 * velocity;
      const destY = y + Math.sin(angle) * 100 * velocity;
      
      particle.animate([
        { transform: 'translate(-50%, -50%) scale(1)', opacity: 1 },
        { 
          transform: `translate(calc(-50% + ${destX - x}px), calc(-50% + ${destY - y}px)) scale(0)`,
          opacity: 0 
        }
      ], {
        duration: 1000,
        easing: 'cubic-bezier(0, 0.5, 0.5, 1)'
      }).onfinish = () => particle.remove();
    }
  }

  /**
   * Ajouter un effet de glow pulsant
   */
  addGlowPulse(element) {
    element.style.animation = 'glowPulse 2s ease-in-out infinite';
    
    if (!document.getElementById('glow-pulse-animation')) {
      const style = document.createElement('style');
      style.id = 'glow-pulse-animation';
      style.textContent = `
        @keyframes glowPulse {
          0%, 100% {
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.5),
                        0 0 40px rgba(99, 102, 241, 0.3);
          }
          50% {
            box-shadow: 0 0 30px rgba(99, 102, 241, 0.8),
                        0 0 60px rgba(99, 102, 241, 0.5),
                        0 0 80px rgba(99, 102, 241, 0.3);
          }
        }
      `;
      document.head.appendChild(style);
    }
  }
}

// Initialiser les effets interactifs
window.addEventListener('DOMContentLoaded', () => {
  window.interactiveEffects = new InteractiveEffects();
  console.log('✨ Effets interactifs initialisés');
});

// Exporter pour utilisation externe
window.InteractiveEffects = InteractiveEffects;