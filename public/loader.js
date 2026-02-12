/**
 * LOADER.JS - Charge tous les scripts nécessaires pour l'interface 3D
 * Ce fichier charge les dépendances dans le bon ordre
 */

(function() {
    'use strict';
    
    console.log('🚀 Chargement des scripts d\'interface 3D...');
    
    // Liste des scripts à charger dans l'ordre
    const scripts = [
        {
            src: 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
            name: 'Three.js',
            global: 'THREE'
        },
        {
            src: '/public/robot-logo.js',
            name: 'Robot Logo',
            global: 'RobotLogo'
        },
        {
            src: '/public/three-bg.js',
            name: 'Three.js Background',
            global: 'ThreeBackground'
        },
        {
            src: '/public/background.js',
            name: 'Background Effects',
            global: 'BackgroundEffects'
        },
        {
            src: '/public/interactive.js',
            name: 'Interactive Effects',
            global: 'InteractiveEffects'
        },
        {
            src: '/public/simple-input-mover.js',
            name: 'Simple Input Mover',
            global: null
        },
        {
            src: '/public/input-styler.js',
            name: 'Input Styler',
            global: 'InputStyler'
        },
        {
            src: '/public/message-styler.js',
            name: 'Message Styler',
            global: 'MessageStyler'
        },
        {
            src: '/public/logos-header.js',
            name: 'Logos Header',
            global: 'LogosHeader'
        }
    ];
    
    let currentScriptIndex = 0;
    
    /**
     * Charge un script de manière asynchrone
     */
    function loadScript(scriptConfig) {
        return new Promise((resolve, reject) => {
            // Vérifier si le script est déjà chargé
            if (scriptConfig.global && window[scriptConfig.global]) {
                console.log(`✓ ${scriptConfig.name} déjà chargé`);
                resolve();
                return;
            }
            
            const script = document.createElement('script');
            script.src = scriptConfig.src;
            script.async = false; // Charger dans l'ordre
            
            script.onload = () => {
                console.log(`✓ ${scriptConfig.name} chargé avec succès`);
                resolve();
            };
            
            script.onerror = () => {
                console.error(`✗ Erreur lors du chargement de ${scriptConfig.name}`);
                reject(new Error(`Failed to load ${scriptConfig.name}`));
            };
            
            document.head.appendChild(script);
        });
    }
    
    /**
     * Charge tous les scripts séquentiellement
     */
    async function loadAllScripts() {
        try {
            for (const script of scripts) {
                await loadScript(script);
                currentScriptIndex++;
            }
            
            console.log('🎉 Tous les scripts sont chargés !');
            
            // Initialiser les composants après le chargement
            initializeComponents();
            
        } catch (error) {
            console.error('❌ Erreur lors du chargement des scripts:', error);
        }
    }
    
    /**
     * Initialise les composants après que tous les scripts soient chargés
     */
    function initializeComponents() {
        // Attendre que le DOM soit complètement chargé
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
    }
    
    function init() {
        console.log('🎨 Initialisation des composants...');
        
        // Vérifier que Three.js est chargé avant d'initialiser le background 3D
        if (typeof THREE !== 'undefined') {
            console.log('✓ Three.js détecté, initialisation du background 3D...');
        } else {
            console.warn('⚠ Three.js non disponible, background 3D désactivé');
        }
        
        console.log('✨ Interface 3D prête !');
    }
    
    // Démarrer le chargement des scripts
    loadAllScripts();
    
})();