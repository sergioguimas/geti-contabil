// Espera todo o conteúdo da página (HTML) carregar antes de executar o script
document.addEventListener("DOMContentLoaded", function() {

    // --- SCRIPT DO MENU DROPDOWN (Usado em várias páginas) ---
    const menuButton = document.getElementById('menu-button');
    const menuDropdown = document.getElementById('menu-dropdown');

    if (menuButton && menuDropdown) {
        menuButton.addEventListener('click', function() {
            menuDropdown.classList.toggle('show');
        });

        window.addEventListener('click', function(event) {
            if (!menuButton.contains(event.target) && !menuDropdown.contains(event.target)) {
                if (menuDropdown.classList.contains('show')) {
                    menuDropdown.classList.remove('show');
                }
            }
        });
    }

// --- SCRIPTS DO DASHBOARD (dashboard.html) ---

    // Script do Select All Checkbox
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function(e) {
            var checkboxes = document.querySelectorAll('.file-checkbox');
            for (var checkbox of checkboxes) {
                checkbox.checked = e.target.checked;
            }
        });
    }

    // Script do Pop-up de Download
    const downloadForm = document.getElementById('download-form');
    const downloadButton = document.getElementById('download-button');
    const loadingModal = document.getElementById('loading-modal');

    if (downloadForm && downloadButton && loadingModal) {
        downloadForm.addEventListener('submit', function(e) {
            
            // 1. Verifica se algum arquivo foi selecionado
            const checkedFiles = document.querySelectorAll('.file-checkbox:checked');
            if (checkedFiles.length === 0) {
                e.preventDefault();
                alert('Por favor, selecione pelo menos um arquivo para baixar.');
                return;
            }

            // 2. Mostra o pop-up
            loadingModal.style.display = 'flex';

            // 3. Desabilita o botão
            downloadButton.disabled = true;
            downloadButton.innerText = 'Preparando...';

            // 4. TRUQUE DO COOKIE
            const downloadToken = Date.now();
            
            const tokenInput = document.createElement('input');
            tokenInput.type = 'hidden';
            tokenInput.name = 'download_token';
            tokenInput.value = downloadToken;
            downloadForm.appendChild(tokenInput);

            // 5. Começa a verificar o cookie
            let checkCookieInterval = setInterval(function() {
                const cookieName = `download_token_${downloadToken}`;
                if (document.cookie.includes(cookieName + '=true')) {
                    clearInterval(checkCookieInterval);
                    
                    loadingModal.style.display = 'none'; 
                    downloadButton.disabled = false;
                    downloadButton.innerText = 'Baixar Selecionados';
                    
                    document.cookie = cookieName + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
                    downloadForm.removeChild(tokenInput);
                }
            }, 1000); 

            setTimeout(function() {
                clearInterval(checkCookieInterval);
                if (loadingModal.style.display === 'flex') {
                    loadingModal.style.display = 'none';
                    downloadButton.disabled = false;
                    downloadButton.innerText = 'Baixar Selecionados';
                    alert("Ocorreu um erro ou o tempo limite foi atingido.");
                }
            }, 120000);
        });
    }

    // Script do Auto-submit da Empresa
    const empresaSelect = document.getElementById('empresa-select-id');
    const empresaForm = document.getElementById('empresa-form');

    if (empresaSelect && empresaForm) {
        empresaSelect.addEventListener('change', function() {
            empresaForm.submit();
        });
    }

    // --- SCRIPTS DAS MÁSCARAS (admin_cadastros.html) ---    
    var cnpjInput = document.getElementById('cnpj');
    if(cnpjInput) {
      if (typeof VMasker !== 'undefined') {
        VMasker(cnpjInput).maskPattern('99.999.999/9999-99');
      }
    }

    var contatoInput = document.getElementById('contato');
    if(contatoInput) {
      if (typeof VMasker !== 'undefined') {
        VMasker(contatoInput).maskPattern('(99) 99999-9999');
      }
    }

    // --- SCRIPT DO POP-UP DE INFO ---
    const infoButton = document.getElementById('info-button');
    const infoPopup = document.getElementById('info-popup');

    if (infoButton && infoPopup) {
        
        // 1. Abrir/Fechar ao clicar no ÍCONE
        infoButton.addEventListener('click', function(event) {
            // Impede que o clique se propague para o 'window' e feche o pop-up imediatamente
            event.stopPropagation(); 
            // Alterna a classe .show
            infoPopup.classList.toggle('show');
        });

        // 2. Fechar ao clicar em QUALQUER LUGAR FORA
        window.addEventListener('click', function(event) {
            // Se o pop-up está visível E o clique NÃO foi dentro dele
            if (infoPopup.classList.contains('show') && !infoPopup.contains(event.target)) 
            {
                infoPopup.classList.remove('show');
            }
        });

        // 3. (Opcional) Impede que cliques DENTRO do pop-up o fechem
        infoPopup.addEventListener('click', function(event) {
            event.stopPropagation();
        });
    }

});