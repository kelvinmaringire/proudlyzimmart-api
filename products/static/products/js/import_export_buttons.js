// Add import/export buttons to product admin page
(function() {
    'use strict';
    
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addButtons);
    } else {
        addButtons();
    }
    
    function addButtons() {
        // Find the header extra actions area
        const headerExtra = document.querySelector('[data-header-extra]') || 
                           document.querySelector('.w-header__extra-actions') ||
                           document.querySelector('.header-extra');
        
        if (!headerExtra) {
            // Try to find the add button and add next to it
            const addButton = document.querySelector('a[href*="/add/"]');
            if (addButton && addButton.parentElement) {
                const container = addButton.parentElement;
                
                // Get URLs from data attributes or construct them
                const currentPath = window.location.pathname;
                const importUrl = currentPath + 'import/';
                const exportCsvUrl = currentPath + 'export/?format=csv';
                const exportXlsxUrl = currentPath + 'export/?format=xlsx';
                
                // Create Import button
                const importBtn = document.createElement('a');
                importBtn.href = importUrl;
                importBtn.className = 'button bicolor icon icon-download';
                importBtn.textContent = 'Import';
                importBtn.style.marginLeft = '1em';
                
                // Create Export CSV button
                const exportCsvBtn = document.createElement('a');
                exportCsvBtn.href = exportCsvUrl;
                exportCsvBtn.className = 'button bicolor icon icon-download';
                exportCsvBtn.textContent = 'Export CSV';
                exportCsvBtn.style.marginLeft = '0.5em';
                
                // Create Export Excel button
                const exportXlsxBtn = document.createElement('a');
                exportXlsxBtn.href = exportXlsxUrl;
                exportXlsxBtn.className = 'button bicolor icon icon-download';
                exportXlsxBtn.textContent = 'Export Excel';
                exportXlsxBtn.style.marginLeft = '0.5em';
                
                // Add buttons
                container.appendChild(importBtn);
                container.appendChild(exportCsvBtn);
                container.appendChild(exportXlsxBtn);
            }
        }
    }
})();

