#!/bin/bash

# ============================================
# COMANDOS ÚTEIS - DEPLOY LOCAWEB
# ============================================
# Use este arquivo como referência rápida
# Copie e cole os comandos conforme necessário

echo "📋 COMANDOS ÚTEIS PARA GERENCIAR O CRM NA LOCAWEB"
echo ""

# ============================================
# 1. CONECTAR AO SERVIDOR
# ============================================
echo "1️⃣  CONECTAR VIA SSH"
echo "ssh seu_usuario@seu_dominio.com.br"
echo ""

# ============================================
# 2. ATIVAR AMBIENTE VIRTUAL
# ============================================
echo "2️⃣  ATIVAR AMBIENTE VIRTUAL"
echo "source ~/virtualenv/python3.10/bin/activate"
echo ""

# ============================================
# 3. ATUALIZAR CÓDIGO
# ============================================
echo "3️⃣  ATUALIZAR CÓDIGO"
echo ""
echo "Via Git:"
echo "cd ~/public_html"
echo "git pull origin main"
echo ""
echo "Via FTP:"
echo "# Use FileZilla ou painel da Locaweb"
echo ""

# ============================================
# 4. INSTALAR/ATUALIZAR DEPENDÊNCIAS
# ============================================
echo "4️⃣  ATUALIZAR DEPENDÊNCIAS"
echo "cd ~/public_html"
echo "source ~/virtualenv/python3.10/bin/activate"
echo "pip install -r requirements.txt --upgrade"
echo ""

# ============================================
# 5. REINICIAR APLICAÇÃO
# ============================================
echo "5️⃣  REINICIAR APLICAÇÃO"
echo "touch ~/public_html/tmp/restart.txt"
echo "# Ou via painel: Aplicações → Reiniciar Aplicação Python"
echo ""

# ============================================
# 6. VER LOGS
# ============================================
echo "6️⃣  VER LOGS"
echo ""
echo "Logs da aplicação (últimas 50 linhas):"
echo "tail -50 ~/public_html/logs/crm.log"
echo ""
echo "Logs em tempo real:"
echo "tail -f ~/public_html/logs/crm.log"
echo ""
echo "Logs do Passenger:"
echo "tail -50 ~/passenger_logs/error.log"
echo ""
echo "Últimos erros Python:"
echo "grep ERROR ~/public_html/logs/crm.log | tail -20"
echo ""

# ============================================
# 7. BANCO DE DADOS
# ============================================
echo "7️⃣  COMANDOS DO BANCO"
echo ""
echo "Conectar ao PostgreSQL:"
echo "psql -h pgsql.locaweb.com.br -U seu_usuario -d nome_banco"
echo ""
echo "Backup do banco:"
echo "pg_dump -h pgsql.locaweb.com.br -U usuario -d database > backup_\$(date +%Y%m%d).sql"
echo ""
echo "Restaurar backup:"
echo "psql -h pgsql.locaweb.com.br -U usuario -d database < backup_20260425.sql"
echo ""
echo "Ver tabelas:"
echo "psql -h pgsql.locaweb.com.br -U usuario -d database -c '\dt'"
echo ""
echo "Contar registros:"
echo "psql -h pgsql.locaweb.com.br -U usuario -d database -c 'SELECT COUNT(*) FROM cliente;'"
echo ""

# ============================================
# 8. VERIFICAR STATUS
# ============================================
echo "8️⃣  VERIFICAR STATUS"
echo ""
echo "Processos Python rodando:"
echo "ps aux | grep python"
echo ""
echo "Uso de memória:"
echo "free -h"
echo ""
echo "Uso de disco:"
echo "df -h"
echo ""
echo "Tamanho dos uploads:"
echo "du -sh ~/public_html/static/uploads"
echo ""
echo "Tamanho dos logs:"
echo "du -sh ~/public_html/logs"
echo ""

# ============================================
# 9. LIMPAR DADOS ANTIGOS
# ============================================
echo "9️⃣  LIMPAR DADOS ANTIGOS"
echo ""
echo "Logs com mais de 7 dias:"
echo "find ~/public_html/logs -name '*.log.*' -mtime +7 -delete"
echo ""
echo "Arquivos temporários:"
echo "rm -rf ~/public_html/tmp/*.pyc"
echo ""
echo "Cache Python:"
echo "find ~/public_html -type d -name __pycache__ -exec rm -rf {} +"
echo ""

# ============================================
# 10. BACKUP COMPLETO
# ============================================
echo "🔟 BACKUP COMPLETO"
echo ""
echo "Criar backup de tudo:"
echo "cd ~"
echo "tar -czf backup_crm_\$(date +%Y%m%d_%H%M%S).tar.gz public_html/"
echo ""
echo "Backup apenas do código:"
echo "cd ~/public_html"
echo "tar -czf ~/backup_codigo_\$(date +%Y%m%d).tar.gz --exclude='*.pyc' --exclude='__pycache__' --exclude='logs/*' --exclude='static/uploads/*' ."
echo ""

# ============================================
# 11. PERMISSÕES
# ============================================
echo "1️⃣1️⃣  AJUSTAR PERMISSÕES"
echo ""
echo "Permissões de diretórios:"
echo "chmod 755 ~/public_html"
echo "chmod 755 ~/public_html/static"
echo "chmod 755 ~/public_html/static/uploads -R"
echo "chmod 755 ~/public_html/logs"
echo ""
echo "Permissões de arquivos:"
echo "chmod 644 ~/public_html/*.py"
echo "chmod 755 ~/public_html/passenger_wsgi.py"
echo "chmod 600 ~/public_html/.env"
echo ""

# ============================================
# 12. TROUBLESHOOTING
# ============================================
echo "1️⃣2️⃣  TROUBLESHOOTING"
echo ""
echo "Site não carrega? Verificar:"
echo "1. tail -50 ~/passenger_logs/error.log"
echo "2. python ~/public_html/passenger_wsgi.py  # Testar manualmente"
echo "3. cat ~/public_html/.env | grep DATABASE_URL  # Verificar config"
echo ""
echo "Erro 502? Reinstalar dependências:"
echo "cd ~/public_html"
echo "source ~/virtualenv/python3.10/bin/activate"
echo "pip install -r requirements.txt --force-reinstall"
echo "touch tmp/restart.txt"
echo ""
echo "Upload não funciona? Criar e ajustar:"
echo "mkdir -p ~/public_html/static/uploads/canais"
echo "chmod 755 ~/public_html/static/uploads -R"
echo ""

# ============================================
# 13. MONITORAMENTO
# ============================================
echo "1️⃣3️⃣  MONITORAMENTO"
echo ""
echo "Ver acessos em tempo real:"
echo "tail -f ~/access-logs/seu_dominio.com.br-https-access_log"
echo ""
echo "Erros 500 hoje:"
echo "grep '\" 500 ' ~/access-logs/seu_dominio.com.br-https-access_log | wc -l"
echo ""
echo "IPs que mais acessam:"
echo "awk '{print \$1}' ~/access-logs/seu_dominio.com.br-https-access_log | sort | uniq -c | sort -rn | head -10"
echo ""

# ============================================
# 14. CRIAR USUÁRIO ADMIN
# ============================================
echo "1️⃣4️⃣  CRIAR USUÁRIO ADMIN"
echo "cd ~/public_html"
echo "source ~/virtualenv/python3.10/bin/activate"
echo "python criar_usuario_crm.py"
echo ""

# ============================================
# 15. APLICAR ÍNDICES
# ============================================
echo "1️⃣5️⃣  APLICAR/REAPLICAR ÍNDICES"
echo "cd ~/public_html"
echo "source ~/virtualenv/python3.10/bin/activate"
echo "python aplicar_indices.py"
echo ""

# ============================================
# FIM
# ============================================
echo ""
echo "✅ COMANDOS SALVOS!"
echo "📖 Mantenha este arquivo como referência"
echo ""
