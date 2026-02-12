/**
 * SIMPLE INPUT MOVER - Version ultra-simple
 * Déplace juste l'input en bas, point final
 */

(function() {
    console.log('🎯 [SIMPLE] Tentative de déplacement de l\'input...');
    
    function moveInput() {
        // Trouver le textarea
        const textarea = document.querySelector('textarea');
        
        if (!textarea) {
            console.log('⏳ [SIMPLE] Textarea pas encore trouvé, nouvelle tentative...');
            return false;
        }
        
        // Trouver le conteneur parent qui a aussi les boutons
        let container = textarea.parentElement;
        let attempts = 0;
        
        while (container && attempts < 10) {
            const hasButton = container.querySelector('button');
            if (hasButton) {
                console.log('✅ [SIMPLE] Conteneur trouvé !', container);
                
                // Appliquer les styles
                container.style.position = 'fixed';
                container.style.bottom = '20px';
                container.style.left = '50%';
                container.style.transform = 'translateX(-50%)';
                container.style.width = 'calc(100% - 40px)';
                container.style.maxWidth = '800px';
                container.style.zIndex = '1000';
                container.style.margin = '0';
                
                console.log('🎉 [SIMPLE] Input déplacé en bas avec succès !');
                return true;
            }
            container = container.parentElement;
            attempts++;
        }
        
        return false;
    }
    
    // Essayer plusieurs fois
    let tryCount = 0;
    const maxTries = 20;
    
    const interval = setInterval(() => {
        tryCount++;
        
        if (moveInput()) {
            clearInterval(interval);
            console.log('✅ [SIMPLE] Mission accomplie !');
        } else if (tryCount >= maxTries) {
            clearInterval(interval);
            console.log('❌ [SIMPLE] Impossible de trouver l\'input après', maxTries, 'tentatives');
        }
    }, 500); // Essayer toutes les 500ms
    
})();