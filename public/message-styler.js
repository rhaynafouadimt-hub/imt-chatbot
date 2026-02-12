/**
 * MESSAGE STYLER - Cible le vrai conteneur du message utilisateur
 */

console.log('💬 [MESSAGE-STYLER] Script chargé !');

class MessageStyler {
  constructor() {
    this.init();
  }

  init() {
    // Injecter le CSS global
    this.injectCSS();

    // Attendre que les messages se chargent
    setTimeout(() => {
      this.styleMessages();
    }, 500);

    // Observer les changements
    const observer = new MutationObserver(() => {
      this.styleMessages();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  injectCSS() {
    const style = document.createElement('style');
    style.id = 'message-styler-accent';
    style.textContent = `
      /* Cibler le vrai rectangle du message utilisateur */
      div[data-step-type="user_message"] .bg-accent,
      div[data-step-type="user_message"] div.rounded-3xl,
      div[data-step-type="user_message"] div[class*="bg-accent"] {
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 
                    0 0 20px rgba(99, 102, 241, 0.3) !important;
        transition: all 0.3s ease !important;
      }

      /* Effet au survol */
      div[data-step-type="user_message"] .bg-accent:hover,
      div[data-step-type="user_message"] div.rounded-3xl:hover {
        border-color: rgba(99, 102, 241, 0.6) !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6), 
                    0 0 30px rgba(99, 102, 241, 0.4) !important;
        transform: translateY(-2px) !important;
      }

      /* Texte dans le rectangle */
      div[data-step-type="user_message"] .bg-accent *,
      div[data-step-type="user_message"] div.rounded-3xl * {
        color: #f1f5f9 !important;
      }

      /* Messages ASSISTANT - PAS de changement */
      div[data-step-type="assistant_message"] {
        /* Garder le style par défaut */
      }

      div[data-step-type="assistant_message"] * {
        color: #e2e8f0 !important;
      }

      /* Animation d'apparition */
      @keyframes messageSlideIn {
        from {
          opacity: 0;
          transform: translateX(30px);
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }

      div[data-step-type="user_message"] .bg-accent {
        animation: messageSlideIn 0.4s ease-out !important;
      }
    `;

    // Supprimer l'ancien s'il existe
    const old = document.getElementById('message-styler-accent');
    if (old) old.remove();

    document.head.appendChild(style);
    console.log('✅ [MESSAGE-STYLER] CSS injecté !');
  }

  styleMessages() {
    // Trouver tous les rectangles bg-accent dans les messages user
    const userMessages = document.querySelectorAll('[data-step-type="user_message"]');

    userMessages.forEach(msg => {
      // Chercher le div avec bg-accent à l'intérieur
      const accentDiv = msg.querySelector('.bg-accent, div.rounded-3xl, div[class*="bg-accent"]');
      
      if (accentDiv && !accentDiv.dataset.styledAccent) {
        this.styleAccentDiv(accentDiv);
        accentDiv.dataset.styledAccent = 'true';
        console.log('💬 [MESSAGE-STYLER] Rectangle stylé !');
      }
    });
  }

  styleAccentDiv(element) {
    // Appliquer le style directement sur le rectangle
    Object.assign(element.style, {
      background: 'rgba(30, 41, 59, 0.7)',
      backgroundImage: 'none',
      backgroundClip: 'padding-box',
      backdropFilter: 'blur(20px) saturate(180%)',
      WebkitBackdropFilter: 'blur(20px) saturate(180%)',
      border: '1px solid rgba(99, 102, 241, 0.4)',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5), 0 0 20px rgba(99, 102, 241, 0.3)',
      transition: 'all 0.3s ease',
      animation: 'messageSlideIn 0.4s ease-out'
    });

    // Forcer la couleur du texte
    const textElements = element.querySelectorAll('*');
    textElements.forEach(el => {
      el.style.color = '#f1f5f9';
    });
  }
}

// Initialiser
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    window.messageStyler = new MessageStyler();
    console.log('💬 [MESSAGE-STYLER] Initialisé !');
  });

  setTimeout(() => {
    if (!window.messageStyler) {
      window.messageStyler = new MessageStyler();
    }
  }, 1500);
}

window.MessageStyler = MessageStyler;