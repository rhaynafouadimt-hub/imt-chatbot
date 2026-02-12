/**
 * LOGOS HEADER - Ajoute le logo IMT et le drapeau Sénégal en haut
 */

console.log('🏷️ [LOGOS] Script logos-header.js chargé !');

class LogosHeader {
  constructor() {
    this.init();
  }

  init() {
    // Attendre que le DOM soit prêt
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.addLogos());
    } else {
      this.addLogos();
    }
  }

  addLogos() {
    // Vérifier que les logos ne sont pas déjà ajoutés
    if (document.querySelector('.logos-header-container')) {
      return;
    }

    // Créer le conteneur des logos
    const logosContainer = document.createElement('div');
    logosContainer.className = 'logos-header-container';
    
    // Logo IMT à gauche
    const logoIMT = document.createElement('div');
    logoIMT.className = 'logo-imt';
    logoIMT.innerHTML = `
      <img src="/public/images/imt_logo.png" alt="IMT Logo" />
    `;

    // Drapeau Sénégal à droite
    const flagSenegal = document.createElement('div');
    flagSenegal.className = 'flag-senegal';
    flagSenegal.innerHTML = `
      <img src="/public/images/senegal.png" alt="Drapeau Sénégal" />
    `;

    // Ajouter les logos au conteneur
    logosContainer.appendChild(logoIMT);
    logosContainer.appendChild(flagSenegal);

    // Insérer au début du body
    document.body.insertBefore(logosContainer, document.body.firstChild);

    // Ajouter les styles
    this.addStyles();

    // Cacher le bouton Readme de Chainlit
    this.hideReadmeButton();

    console.log('✅ [LOGOS] Logos ajoutés !');
  }

  hideReadmeButton() {
    // Fonction pour chercher et cacher le bouton Readme
    const hideButton = () => {
      // Chercher tous les boutons
      const buttons = document.querySelectorAll('button');
      
      buttons.forEach(button => {
        const text = button.textContent || button.innerText;
        if (text && text.trim().toLowerCase() === 'readme') {
          button.style.display = 'none';
          console.log('✅ [LOGOS] Bouton Readme caché !');
        }
      });

      // Chercher aussi par aria-label
      const readmeButtons = document.querySelectorAll('[aria-label*="readme" i], [aria-label*="Readme" i]');
      readmeButtons.forEach(btn => {
        btn.style.display = 'none';
      });
    };

    // Exécuter maintenant
    hideButton();

    // Exécuter après un délai
    setTimeout(hideButton, 1000);
    setTimeout(hideButton, 2000);

    // Observer les changements pour cacher le bouton s'il apparaît
    const observer = new MutationObserver(() => {
      hideButton();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  addStyles() {
    if (document.getElementById('logos-header-styles')) return;

    const style = document.createElement('style');
    style.id = 'logos-header-styles';
    style.textContent = `
      /* Conteneur des logos */
      .logos-header-container {
        position: fixed;
        top: 20px;
        left: 0;
        right: 0;
        width: 100%;
        z-index: 1000;
        pointer-events: none;
        display: flex;
        justify-content: space-between;
        padding: 0 30px;
      }

      /* Logo IMT à gauche */
      .logo-imt {
        pointer-events: auto;
        animation: logoFadeIn 0.8s ease-out;
      }

      .logo-imt img {
        width: 80px;
        height: 80px;
        object-fit: cover;
        border-radius: 50%;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),
                    0 0 20px rgba(99, 102, 241, 0.3);
        transition: all 0.3s ease;
        border: 2px solid rgba(99, 102, 241, 0.3);
      }

      .logo-imt img:hover {
        transform: scale(1.1) rotate(5deg);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5),
                    0 0 30px rgba(99, 102, 241, 0.5);
        border-color: rgba(99, 102, 241, 0.6);
      }

      /* Drapeau Sénégal à droite */
      .flag-senegal {
        pointer-events: auto;
        animation: logoFadeIn 0.8s ease-out 0.2s backwards;
      }

      .flag-senegal img {
        width: 80px;
        height: 80px;
        object-fit: cover;
        border-radius: 50%;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),
                    0 0 20px rgba(99, 102, 241, 0.3);
        transition: all 0.3s ease;
        border: 2px solid rgba(99, 102, 241, 0.3);
      }

      .flag-senegal img:hover {
        transform: scale(1.1) rotate(-5deg);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5),
                    0 0 30px rgba(99, 102, 241, 0.5);
        border-color: rgba(99, 102, 241, 0.6);
      }

      /* Animation d'apparition */
      @keyframes logoFadeIn {
        from {
          opacity: 0;
          transform: translateY(-20px) scale(0.8);
        }
        to {
          opacity: 1;
          transform: translateY(0) scale(1);
        }
      }

      /* Responsive mobile */
      @media (max-width: 768px) {
        .logos-header-container {
          padding: 0 15px;
          top: 10px;
        }

        .logo-imt img,
        .flag-senegal img {
          width: 60px;
          height: 60px;
        }
      }

      /* Très petits écrans */
      @media (max-width: 480px) {
        .logo-imt img,
        .flag-senegal img {
          width: 50px;
          height: 50px;
        }
      }

      /* Cacher le bouton Readme (backup CSS) */
      button[aria-label*="Readme"],
      button[aria-label*="readme"] {
        display: none !important;
      }
    `;

    document.head.appendChild(style);
    console.log('✅ [LOGOS] Styles ajoutés !');
  }
}

// Initialiser
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    window.logosHeader = new LogosHeader();
    console.log('🏷️ [LOGOS] Logos header initialisé !');
  });

  // Backup
  setTimeout(() => {
    if (!window.logosHeader) {
      window.logosHeader = new LogosHeader();
    }
  }, 1000);
}

window.LogosHeader = LogosHeader;