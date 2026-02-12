/**
 * ROBOT LOGO - Ajoute un robot animé qui cligne des yeux
 * Se cache automatiquement quand la conversation commence
 */

console.log('🤖 [ROBOT] Script robot-logo.js chargé !');

class RobotLogo {
  constructor() {
    console.log('🤖 [ROBOT] Constructeur appelé');
    this.robotAdded = false;
    this.init();
  }

  init() {
    // Forcer l'ajout immédiat
    setTimeout(() => {
      this.addRobot();
    }, 100);

    // Attendre que le DOM soit complètement chargé
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        this.addRobot();
      });
    } else {
      this.addRobot();
    }

    // Observer les changements dans le DOM
    const observer = new MutationObserver(() => {
      if (!this.robotAdded) {
        this.addRobot();
      }
      // Vérifier s'il y a des messages et cacher le robot
      this.checkForMessages();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  addRobot() {
    // Si le robot est déjà ajouté, ne rien faire
    if (this.robotAdded || document.querySelector('.robot-logo-main-container')) {
      return;
    }

    this.createRobotInCenter();
    this.robotAdded = true;
    console.log('✅ [ROBOT] Robot créé et ajouté !');
  }

  checkForMessages() {
    const robot = document.querySelector('.robot-logo-main-container');
    if (!robot) return;

    // Chercher les messages dans le chat
    const messages = document.querySelectorAll('[class*="message"], [class*="Message"], .step-container, [role="article"]');
    
    // Chercher aussi les starters cliqués (bulle de message utilisateur)
    const userMessages = document.querySelectorAll('[class*="userMessage"], [class*="user-message"]');
    
    // Si il y a des messages (au moins 1), cacher le robot
    if (messages.length > 0 || userMessages.length > 0) {
      robot.style.opacity = '0';
      robot.style.pointerEvents = 'none';
      robot.style.transition = 'opacity 0.5s ease-out';
      console.log('👻 [ROBOT] Robot caché - conversation active');
    } else {
      // Sinon, montrer le robot (page d'accueil)
      robot.style.opacity = '1';
      robot.style.pointerEvents = 'none';
      robot.style.transition = 'opacity 0.5s ease-in';
      console.log('👋 [ROBOT] Robot affiché - page d\'accueil');
    }
  }

  createRobotInCenter() {
    // Créer le conteneur principal du robot
    const robotMainContainer = document.createElement('div');
    robotMainContainer.className = 'robot-logo-main-container';
    robotMainContainer.style.cssText = `
      position: fixed !important;
      top: 30% !important;
      left: 50% !important;
      transform: translate(-50%, -50%) !important;
      z-index: 100 !important;
      pointer-events: none !important;
      display: flex !important;
      flex-direction: column !important;
      align-items: center !important;
      gap: 20px !important;
      opacity: 1 !important;
      transition: opacity 0.5s ease-out !important;
    `;
    
    robotMainContainer.innerHTML = `
      <div class="robot-logo-wrapper" style="display: flex; flex-direction: column; align-items: center; gap: 20px; animation: robotFadeIn 1s ease-out;">
        <div class="robot-logo-container" style="width: 150px; height: 150px; display: flex; align-items: center; justify-content: center; animation: robotFloat 3s ease-in-out infinite;">
          ${this.createRobotSVG()}
        </div>
      </div>
    `;

    // Insérer le robot au début du body
    document.body.insertBefore(robotMainContainer, document.body.firstChild);

    // Ajouter les styles
    this.addStyles();

    // Démarrer l'animation
    this.startBlinking();

    // Vérifier immédiatement s'il y a des messages
    setTimeout(() => {
      this.checkForMessages();
    }, 500);
  }

  createRobotSVG() {
    return `
      <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" class="robot-svg" style="width: 100%; height: 100%; filter: drop-shadow(0 10px 30px rgba(93, 213, 245, 0.4));">
        <!-- Tête du robot -->
        <ellipse cx="100" cy="100" rx="70" ry="60" fill="#5DD5F5" class="robot-head"/>
        
        <!-- Casque/Antennes -->
        <ellipse cx="100" cy="65" rx="50" ry="30" fill="#5DD5F5" class="robot-helmet"/>
        <line x1="100" y1="45" x2="100" y2="20" stroke="#5DD5F5" stroke-width="4" stroke-linecap="round"/>
        <circle cx="100" cy="15" r="6" fill="#5DD5F5"/>
        
        <!-- Antenne gauche -->
        <line x1="60" y1="70" x2="45" y2="40" stroke="#5DD5F5" stroke-width="4" stroke-linecap="round"/>
        <rect x="40" y="35" width="10" height="15" rx="2" fill="#5DD5F5"/>
        
        <!-- Antenne droite -->
        <line x1="140" y1="70" x2="155" y2="40" stroke="#5DD5F5" stroke-width="4" stroke-linecap="round"/>
        <rect x="150" y="35" width="10" height="15" rx="2" fill="#5DD5F5"/>
        
        <!-- Oreilles/Écouteurs -->
        <circle cx="35" cy="100" r="20" fill="#5DD5F5" class="robot-ear-left"/>
        <circle cx="165" cy="100" r="20" fill="#5DD5F5" class="robot-ear-right"/>
        
        <!-- Cercles intérieurs des oreilles -->
        <circle cx="35" cy="100" r="12" fill="#4FC3E4"/>
        <circle cx="165" cy="100" r="12" fill="#4FC3E4"/>
        
        <!-- Visage blanc -->
        <ellipse cx="100" cy="105" rx="50" ry="45" fill="#E8F6FA" class="robot-face"/>
        
        <!-- Yeux -->
        <g class="robot-eyes">
          <!-- Oeil gauche -->
          <g class="eye-left">
            <rect x="75" y="90" width="10" height="25" rx="5" fill="#5DD5F5" class="eye-open"/>
            <line x1="75" y1="102.5" x2="85" y2="102.5" stroke="#4FC3E4" stroke-width="2" class="eye-closed" style="opacity: 0;"/>
          </g>
          
          <!-- Oeil droit -->
          <g class="eye-right">
            <rect x="115" y="90" width="10" height="25" rx="5" fill="#5DD5F5" class="eye-open"/>
            <line x1="115" y1="102.5" x2="125" y2="102.5" stroke="#4FC3E4" stroke-width="2" class="eye-closed" style="opacity: 0;"/>
          </g>
        </g>
        
        <!-- Sourire -->
        <path d="M 85 125 Q 100 135 115 125" stroke="#5DD5F5" stroke-width="3" fill="none" stroke-linecap="round" class="robot-smile"/>
        
        <!-- Détails décoratifs sur le casque -->
        <line x1="70" y1="60" x2="130" y2="60" stroke="#4FC3E4" stroke-width="2" opacity="0.5"/>
        
        <!-- Highlights -->
        <ellipse cx="85" cy="80" rx="15" ry="10" fill="#FFFFFF" opacity="0.3"/>
        <ellipse cx="55" cy="95" rx="8" ry="6" fill="#FFFFFF" opacity="0.3"/>
        <ellipse cx="145" cy="95" rx="8" ry="6" fill="#FFFFFF" opacity="0.3"/>
      </svg>
    `;
  }

  addStyles() {
    if (document.getElementById('robot-logo-styles')) return;

    const style = document.createElement('style');
    style.id = 'robot-logo-styles';
    style.textContent = `
      /* Animation de fade in */
      @keyframes robotFadeIn {
        from {
          opacity: 0;
          transform: scale(0.8) translateY(20px);
        }
        to {
          opacity: 1;
          transform: scale(1) translateY(0);
        }
      }

      /* Animation de flottement */
      @keyframes robotFloat {
        0%, 100% {
          transform: translateY(0px);
        }
        50% {
          transform: translateY(-15px);
        }
      }

      /* Animation de clignement des yeux */
      @keyframes blink {
        0%, 90%, 100% {
          opacity: 1;
        }
        95% {
          opacity: 0;
        }
      }

      @keyframes blinkClosed {
        0%, 90%, 100% {
          opacity: 0;
        }
        95% {
          opacity: 1;
        }
      }

      .robot-eyes .eye-open {
        animation: blink 4s infinite;
      }

      .robot-eyes .eye-closed {
        animation: blinkClosed 4s infinite;
      }

      /* Animation des oreilles */
      .robot-ear-left, .robot-ear-right {
        animation: earPulse 2s ease-in-out infinite;
      }

      .robot-ear-right {
        animation-delay: 1s;
      }

      @keyframes earPulse {
        0%, 100% {
          transform: scale(1);
        }
        50% {
          transform: scale(1.05);
        }
      }

      /* Animation de la tête */
      .robot-head {
        animation: headGlow 3s ease-in-out infinite;
      }

      @keyframes headGlow {
        0%, 100% {
          filter: brightness(1);
        }
        50% {
          filter: brightness(1.1);
        }
      }

      /* Responsive */
      @media (max-width: 768px) {
        .robot-logo-main-container {
          top: 25% !important;
        }
        
        .robot-logo-container {
          width: 100px !important;
          height: 100px !important;
        }
      }

      /* Responsive pour très petits écrans */
      @media (max-width: 480px) {
        .robot-logo-main-container {
          top: 20% !important;
        }
        
        .robot-logo-container {
          width: 80px !important;
          height: 80px !important;
        }
      }
    `;

    document.head.appendChild(style);
  }

  startBlinking() {
    // Animation de clignement aléatoire supplémentaire
    setInterval(() => {
      const eyes = document.querySelectorAll('.robot-eyes');
      eyes.forEach(eyeGroup => {
        if (Math.random() > 0.7) {
          eyeGroup.style.animation = 'none';
          setTimeout(() => {
            eyeGroup.style.animation = '';
          }, 100);
        }
      });
    }, 5000);
  }
}

// Initialiser le robot
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    window.robotLogo = new RobotLogo();
    console.log('🤖 Robot logo initialisé avec succès !');
  });
  
  // Backup au cas où load ne se déclenche pas
  setTimeout(() => {
    if (!window.robotLogo) {
      window.robotLogo = new RobotLogo();
      console.log('🤖 Robot logo initialisé (backup timer) !');
    }
  }, 2000);
}

window.RobotLogo = RobotLogo;