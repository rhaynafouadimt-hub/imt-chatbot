/**
 * INPUT STYLER - Force les styles directement en JavaScript
 */

console.log('🎨 [STYLE] Script input-styler.js chargé !');

class InputStyler {
  constructor() {
    this.init();
  }

  init() {
    // Attendre que l'input soit positionné
    setTimeout(() => {
      this.styleInput();
    }, 1000);

    // Observer pour styler les nouveaux éléments
    const observer = new MutationObserver(() => {
      this.styleInput();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  styleInput() {
    // Trouver le textarea
    const textarea = document.querySelector('textarea');
    if (!textarea) return;

    // Trouver le conteneur parent
    let container = textarea.parentElement;
    let attempts = 0;
    
    while (container && attempts < 10) {
      const hasButton = container.querySelector('button');
      if (hasButton) {
        this.applyContainerStyles(container);
        this.applyTextareaStyles(textarea);
        this.applyButtonStyles(container);
        console.log('✅ [STYLE] Styles appliqués avec succès !');
        return;
      }
      container = container.parentElement;
      attempts++;
    }
  }

  applyContainerStyles(container) {
    Object.assign(container.style, {
      background: 'rgba(30, 41, 59, 0.7)',
      backdropFilter: 'blur(20px) saturate(180%)',
      WebkitBackdropFilter: 'blur(20px) saturate(180%)',
      border: '1px solid rgba(99, 102, 241, 0.3)',
      borderRadius: '24px',
      padding: '12px 16px',
      boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(99, 102, 241, 0.3)',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
    });

    // Effet au survol
    container.addEventListener('mouseenter', () => {
      container.style.borderColor = 'rgba(99, 102, 241, 0.5)';
      container.style.boxShadow = '0 25px 70px rgba(0, 0, 0, 0.6), 0 0 60px rgba(99, 102, 241, 0.4)';
    });

    container.addEventListener('mouseleave', () => {
      container.style.borderColor = 'rgba(99, 102, 241, 0.3)';
      container.style.boxShadow = '0 20px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(99, 102, 241, 0.3)';
    });
  }

  applyTextareaStyles(textarea) {
    Object.assign(textarea.style, {
      background: 'transparent',
      color: '#f1f5f9',
      fontSize: '16px',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
      lineHeight: '1.6',
      border: 'none',
      outline: 'none',
      padding: '8px 12px',
      resize: 'none',
      width: '100%',
      minHeight: '50px',
      maxHeight: '200px'
    });

    // Animation au focus
    textarea.addEventListener('focus', () => {
      textarea.parentElement.style.animation = 'inputGlow 2s ease-in-out infinite';
    });

    textarea.addEventListener('blur', () => {
      textarea.parentElement.style.animation = '';
    });
  }

  applyButtonStyles(container) {
    // Bouton d'envoi
    const sendButton = container.querySelector('button[type="submit"], button[aria-label*="send"]');
    if (sendButton) {
      Object.assign(sendButton.style, {
        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%)',
        color: 'white',
        border: 'none',
        borderRadius: '50%',
        width: '48px',
        height: '48px',
        minWidth: '48px',
        cursor: 'pointer',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        boxShadow: '0 8px 20px rgba(99, 102, 241, 0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      });

      // Effet au survol
      sendButton.addEventListener('mouseenter', () => {
        sendButton.style.transform = 'scale(1.1) rotate(15deg)';
        sendButton.style.boxShadow = '0 12px 30px rgba(99, 102, 241, 0.6), 0 0 40px rgba(139, 92, 246, 0.5)';
      });

      sendButton.addEventListener('mouseleave', () => {
        sendButton.style.transform = 'scale(1) rotate(0deg)';
        sendButton.style.boxShadow = '0 8px 20px rgba(99, 102, 241, 0.4)';
      });

      sendButton.addEventListener('mousedown', () => {
        sendButton.style.transform = 'scale(1.05)';
      });

      sendButton.addEventListener('mouseup', () => {
        sendButton.style.transform = 'scale(1.1) rotate(15deg)';
      });
    }

    // Bouton d'upload/attach
    const uploadButton = container.querySelector('button[aria-label*="upload"], button[aria-label*="attach"]');
    if (uploadButton && uploadButton !== sendButton) {
      Object.assign(uploadButton.style, {
        background: 'rgba(99, 102, 241, 0.1)',
        color: '#94a3b8',
        border: '1px solid rgba(99, 102, 241, 0.2)',
        borderRadius: '12px',
        width: '40px',
        height: '40px',
        transition: 'all 0.3s ease',
        marginRight: '8px'
      });

      uploadButton.addEventListener('mouseenter', () => {
        uploadButton.style.background = 'rgba(99, 102, 241, 0.2)';
        uploadButton.style.color = '#6366f1';
        uploadButton.style.transform = 'scale(1.05)';
      });

      uploadButton.addEventListener('mouseleave', () => {
        uploadButton.style.background = 'rgba(99, 102, 241, 0.1)';
        uploadButton.style.color = '#94a3b8';
        uploadButton.style.transform = 'scale(1)';
      });
    }
  }
}

// Ajouter l'animation keyframe
const style = document.createElement('style');
style.textContent = `
  @keyframes inputGlow {
    0%, 100% {
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(99, 102, 241, 0.3);
    }
    50% {
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 60px rgba(99, 102, 241, 0.5), 0 0 80px rgba(139, 92, 246, 0.3);
    }
  }
`;
document.head.appendChild(style);

// Initialiser
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    window.inputStyler = new InputStyler();
    console.log('🎨 [STYLE] Input styler initialisé !');
  });

  setTimeout(() => {
    if (!window.inputStyler) {
      window.inputStyler = new InputStyler();
    }
  }, 1500);
}

window.InputStyler = InputStyler;