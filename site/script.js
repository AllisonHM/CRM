// =============================================
// 🚀 SCRIPT DE INTEGRAÇÃO SITE → CRM
// =============================================

// ⚙️ CONFIGURAÇÃO
const API_CONFIG = {
    // ⚠️ ATENÇÃO: Alterar para URL do servidor em produção
    baseURL: 'http://localhost:5000',
    
    // ⚠️ ATENÇÃO: Alterar para a mesma chave configurada no .env do backend
    apiKey: 'sua-chave-secreta-aqui-123456',
    
    endpoints: {
        lead: '/api/public/lead',
        health: '/api/public/health'
    }
};

// 📋 Elementos do DOM
const formLead = document.getElementById('formLead');
const btnSubmit = document.getElementById('btnSubmit');
const mensagemStatus = document.getElementById('mensagemStatus');
const inputNome = document.getElementById('nome');
const inputEmail = document.getElementById('email');
const inputTelefone = document.getElementById('telefone');
const inputMensagem = document.getElementById('mensagem');

// =============================================
// 🎭 MÁSCARA DE TELEFONE
// =============================================

inputTelefone.addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    
    if (value.length <= 10) {
        // (XX) XXXX-XXXX
        value = value.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
    } else {
        // (XX) XXXXX-XXXX
        value = value.replace(/(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
    }
    
    e.target.value = value;
});

// =============================================
// 📤 ENVIO DO FORMULÁRIO
// =============================================

formLead.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Desabilitar botão durante envio
    btnSubmit.disabled = true;
    btnSubmit.textContent = 'Enviando...';
    mensagemStatus.style.display = 'none';
    
    // Coletar dados do formulário
    const dados = {
        nome: inputNome.value.trim(),
        email: inputEmail.value.trim(),
        telefone: inputTelefone.value.trim(),
        mensagem: inputMensagem.value.trim()
    };
    
    // Validação básica no frontend (backup)
    if (dados.nome.length < 3) {
        mostrarMensagem('erro', 'Nome deve ter no mínimo 3 caracteres');
        btnSubmit.disabled = false;
        btnSubmit.textContent = 'Enviar Mensagem';
        return;
    }
    
    if (!validarEmail(dados.email)) {
        mostrarMensagem('erro', 'Por favor, insira um e-mail válido');
        btnSubmit.disabled = false;
        btnSubmit.textContent = 'Enviar Mensagem';
        return;
    }
    
    try {
        // Enviar para API
        console.log('📤 Enviando dados para API:', `${API_CONFIG.baseURL}${API_CONFIG.endpoints.lead}`);
        
        const response = await fetch(`${API_CONFIG.baseURL}${API_CONFIG.endpoints.lead}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_CONFIG.apiKey
            },
            body: JSON.stringify(dados)
        });
        
        const resultado = await response.json();
        console.log('📥 Resposta da API:', resultado);
        
        if (response.ok) {
            // ✅ Sucesso
            mostrarMensagem('sucesso', resultado.mensagem || 'Cadastro realizado com sucesso! Em breve entraremos em contato.');
            formLead.reset();
            
            // Scroll suave para mensagem
            mensagemStatus.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Google Analytics / Facebook Pixel (opcional)
            // gtag('event', 'lead_enviado', { ... });
            // fbq('track', 'Lead');
            
        } else {
            // ❌ Erro de validação ou outro
            let erroMsg = 'Erro ao processar cadastro';
            
            if (resultado.detalhes && Array.isArray(resultado.detalhes)) {
                erroMsg = resultado.detalhes.join(', ');
            } else if (resultado.erro) {
                erroMsg = resultado.erro;
            }
            
            mostrarMensagem('erro', erroMsg);
            console.error('❌ Erro na API:', resultado);
        }
        
    } catch (erro) {
        // ❌ Erro de conexão
        console.error('❌ Erro ao enviar formulário:', erro);
        mostrarMensagem('erro', 'Erro de conexão. Verifique sua internet e tente novamente.');
    } finally {
        // Reabilitar botão
        btnSubmit.disabled = false;
        btnSubmit.textContent = 'Enviar Mensagem';
    }
});

// =============================================
// 🛠️ FUNÇÕES AUXILIARES
// =============================================

/**
 * Exibe mensagem de sucesso ou erro
 */
function mostrarMensagem(tipo, texto) {
    mensagemStatus.className = `mensagem-status ${tipo}`;
    mensagemStatus.textContent = texto;
    mensagemStatus.style.display = 'block';
}

/**
 * Valida formato de e-mail
 */
function validarEmail(email) {
    const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return regex.test(email);
}

// =============================================
// 🏥 HEALTH CHECK (opcional)
// =============================================

/**
 * Verifica se a API está online ao carregar página
 */
window.addEventListener('load', async function() {
    try {
        const response = await fetch(`${API_CONFIG.baseURL}${API_CONFIG.endpoints.health}`, {
            method: 'GET'
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ API CRM está online:', data);
        } else {
            console.warn('⚠️ API CRM retornou erro:', response.status);
        }
    } catch (erro) {
        console.error('❌ Não foi possível conectar à API CRM:', erro);
        console.warn('⚠️ Verifique se o backend está rodando e se a URL está correta');
    }
});

// =============================================
// 🎨 ANIMAÇÕES E INTERAÇÕES
// =============================================

/**
 * Smooth scroll para âncoras
 */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

/**
 * Highlight de campos com erro
 */
function highlightCampoErro(input) {
    input.style.borderColor = 'var(--error-color)';
    setTimeout(() => {
        input.style.borderColor = '';
    }, 2000);
}

// Validação em tempo real (opcional)
inputEmail.addEventListener('blur', function() {
    if (this.value && !validarEmail(this.value)) {
        highlightCampoErro(this);
    }
});

inputNome.addEventListener('blur', function() {
    if (this.value && this.value.length < 3) {
        highlightCampoErro(this);
    }
});
