# 📊 Estratégia de Backup e Restauração por Tenant

## 🎯 Objetivo

Criar backups independentes por tenant, permitindo:
- Restauração seletiva de um único tenant
- Backups regulares automatizados
- Recovery point objective (RPO) < 1 hora
- Recovery time objective (RTO) < 30 minutos

---

## 🔄 Estratégias de Backup

### 1️⃣ Backup Lógico por Tenant (Recomendado)

**Método:** `pg_dump` com filtro por `tenant_id`

#### Vantagens
✅ Backup independente por tenant  
✅ Restauração seletiva  
✅ Fácil de armazenar em cloud (S3, GCS)  
✅ Pode ser agendado por tenant  

#### Desvantagens
⚠️ Mais lento que backup físico  
⚠️ Precisa rodar para cada tenant  

---

### 2️⃣ Backup Físico Completo

**Método:** `pg_basebackup` ou `pgBackRest`

#### Vantagens
✅ Muito mais rápido  
✅ Backup de todo o cluster  
✅ Point-in-time recovery (PITR)  

#### Desvantagens
❌ Não permite restauração seletiva por tenant  
❌ Precisa restaurar tudo  

---

## 📝 Implementação: Backup por Tenant

### Script Python: Backup Automatizado

```python
#!/usr/bin/env python3
"""
backup_tenant.py
Faz backup de um tenant específico usando pg_dump com filtro
"""
import subprocess
import os
from datetime import datetime
import logging
import boto3  # Para upload no S3 (opcional)

logger = logging.getLogger(__name__)


class TenantBackup:
    """Gerenciador de backups por tenant"""
    
    def __init__(self, 
                 pg_host='localhost',
                 pg_port=5432,
                 pg_database='crm_saas',
                 pg_user='app_admin',
                 pg_password='senha_admin',
                 backup_dir='/var/backups/crm'):
        
        self.pg_host = pg_host
        self.pg_port = pg_port
        self.pg_database = pg_database
        self.pg_user = pg_user
        self.pg_password = pg_password
        self.backup_dir = backup_dir
        
        # Cria diretório de backup se não existir
        os.makedirs(backup_dir, exist_ok=True)
    
    def backup_tenant(self, tenant_id, compress=True):
        """
        Faz backup de um tenant específico
        
        Args:
            tenant_id: ID do tenant
            compress: Se True, compacta com gzip
            
        Returns:
            str: Caminho do arquivo de backup
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Nome do arquivo
        extension = '.sql.gz' if compress else '.sql'
        backup_file = os.path.join(
            self.backup_dir,
            f'tenant_{tenant_id}_{timestamp}{extension}'
        )
        
        logger.info(f"Iniciando backup do tenant {tenant_id}")
        
        try:
            # Comando pg_dump com filtro WHERE
            cmd = [
                'pg_dump',
                '-h', self.pg_host,
                '-p', str(self.pg_port),
                '-U', self.pg_user,
                '-d', self.pg_database,
                '--no-owner',
                '--no-privileges',
                '--data-only',  # Apenas dados (schema já existe)
                '--column-inserts',  # Usa INSERT com nomes de colunas
            ]
            
            # Adiciona filtro WHERE para cada tabela
            tables = self._get_tenant_tables()
            for table in tables:
                cmd.extend([
                    '--table', table,
                    '--where', f"tenant_id={tenant_id}"
                ])
            
            # Configura variável de ambiente para senha
            env = os.environ.copy()
            env['PGPASSWORD'] = self.pg_password
            
            # Executa pg_dump
            if compress:
                # Pipe para gzip
                p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env)
                p2 = subprocess.Popen(['gzip'], stdin=p1.stdout, 
                                     stdout=open(backup_file, 'wb'))
                p1.stdout.close()
                p2.communicate()
            else:
                with open(backup_file, 'w') as f:
                    subprocess.run(cmd, stdout=f, env=env, check=True)
            
            # Verifica se arquivo foi criado
            if not os.path.exists(backup_file):
                raise Exception("Arquivo de backup não foi criado")
            
            file_size = os.path.getsize(backup_file)
            logger.info(f"✅ Backup concluído: {backup_file} ({file_size} bytes)")
            
            return backup_file
        
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro no pg_dump: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao fazer backup: {e}")
            raise
    
    def _get_tenant_tables(self):
        """Retorna lista de tabelas com tenant_id"""
        return [
            'usuarios',
            'leads',
            'oportunidades',
            'atividades',
            'produtos',
            'oportunidades_produtos',
            'configuracoes'
        ]
    
    def restore_tenant(self, backup_file, tenant_id=None):
        """
        Restaura backup de um tenant
        
        Args:
            backup_file: Caminho do arquivo de backup
            tenant_id: ID do tenant (se None, usa o do backup)
            
        Returns:
            bool: True se sucesso
        """
        logger.info(f"Iniciando restore de {backup_file}")
        
        try:
            # Descompacta se necessário
            if backup_file.endswith('.gz'):
                cmd_decompress = ['gunzip', '-c', backup_file]
                p1 = subprocess.Popen(cmd_decompress, stdout=subprocess.PIPE)
                sql_content = p1.stdout
            else:
                sql_content = open(backup_file, 'r')
            
            # Comando psql para restaurar
            cmd = [
                'psql',
                '-h', self.pg_host,
                '-p', str(self.pg_port),
                '-U', self.pg_user,
                '-d', self.pg_database
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.pg_password
            
            # Executa restore
            subprocess.run(cmd, stdin=sql_content, env=env, check=True)
            
            logger.info(f"✅ Restore concluído")
            return True
        
        except Exception as e:
            logger.error(f"❌ Erro ao restaurar: {e}")
            return False
    
    def backup_all_tenants(self):
        """Faz backup de todos os tenants ativos"""
        import psycopg2
        
        # Busca todos os tenants ativos
        conn = psycopg2.connect(
            host=self.pg_host,
            port=self.pg_port,
            user=self.pg_user,
            password=self.pg_password,
            database=self.pg_database
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM tenants WHERE ativo = true")
        tenants = cursor.fetchall()
        cursor.close()
        conn.close()
        
        logger.info(f"📦 Iniciando backup de {len(tenants)} tenants")
        
        results = []
        for tenant_id, nome in tenants:
            try:
                backup_file = self.backup_tenant(tenant_id)
                results.append({
                    'tenant_id': tenant_id,
                    'nome': nome,
                    'sucesso': True,
                    'arquivo': backup_file
                })
            except Exception as e:
                logger.error(f"Erro no backup do tenant {tenant_id}: {e}")
                results.append({
                    'tenant_id': tenant_id,
                    'nome': nome,
                    'sucesso': False,
                    'erro': str(e)
                })
        
        return results
    
    def upload_to_s3(self, backup_file, bucket_name, tenant_id):
        """
        Upload do backup para S3 (opcional)
        
        Args:
            backup_file: Caminho local do backup
            bucket_name: Nome do bucket S3
            tenant_id: ID do tenant
        """
        try:
            s3 = boto3.client('s3')
            
            # Key no S3: backups/tenant_123/2024/01/backup_20240115_120000.sql.gz
            timestamp = datetime.now()
            s3_key = f"backups/tenant_{tenant_id}/{timestamp.year}/{timestamp.month:02d}/{os.path.basename(backup_file)}"
            
            # Upload
            s3.upload_file(
                backup_file, 
                bucket_name, 
                s3_key,
                ExtraArgs={'ServerSideEncryption': 'AES256'}  # Criptografia
            )
            
            logger.info(f"✅ Backup enviado para S3: s3://{bucket_name}/{s3_key}")
            
            # Remove arquivo local (opcional)
            os.remove(backup_file)
            
            return s3_key
        
        except Exception as e:
            logger.error(f"❌ Erro ao enviar para S3: {e}")
            raise
    
    def cleanup_old_backups(self, days=30):
        """Remove backups com mais de X dias"""
        import time
        
        now = time.time()
        cutoff = now - (days * 86400)
        
        for filename in os.listdir(self.backup_dir):
            filepath = os.path.join(self.backup_dir, filename)
            
            if os.path.isfile(filepath):
                file_time = os.path.getmtime(filepath)
                
                if file_time < cutoff:
                    logger.info(f"🗑️ Removendo backup antigo: {filename}")
                    os.remove(filepath)


# ========================================
# AGENDAMENTO COM CRON
# ========================================

"""
# /etc/cron.d/crm-backup

# Backup diário de todos os tenants às 2h da manhã
0 2 * * * /usr/bin/python3 /opt/crm/backup_tenant.py --all

# Backup horário de tenants premium
0 * * * * /usr/bin/python3 /opt/crm/backup_tenant.py --premium
"""


# ========================================
# SCRIPT CLI
# ========================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Backup de tenants')
    parser.add_argument('--tenant-id', type=int, help='ID do tenant específico')
    parser.add_argument('--all', action='store_true', help='Backup de todos os tenants')
    parser.add_argument('--restore', help='Restaurar de arquivo')
    parser.add_argument('--upload-s3', help='Bucket S3 para upload')
    
    args = parser.parse_args()
    
    # Configuração
    backup = TenantBackup(
        pg_host='localhost',
        pg_port=5432,
        pg_database='crm_saas',
        pg_user='app_admin',
        pg_password=os.getenv('PGPASSWORD', 'senha'),
        backup_dir='/var/backups/crm'
    )
    
    # Executa ação
    if args.restore:
        backup.restore_tenant(args.restore)
    
    elif args.all:
        results = backup.backup_all_tenants()
        print(f"\n📊 Backup de {len(results)} tenants concluído")
        
        for r in results:
            emoji = "✅" if r['sucesso'] else "❌"
            print(f"{emoji} Tenant {r['tenant_id']} ({r['nome']})")
    
    elif args.tenant_id:
        backup_file = backup.backup_tenant(args.tenant_id)
        print(f"✅ Backup criado: {backup_file}")
        
        # Upload para S3 se configurado
        if args.upload_s3:
            backup.upload_to_s3(backup_file, args.upload_s3, args.tenant_id)
    
    else:
        parser.print_help()
```

---

## 🔐 Backup Criptografado

### Usando GPG

```bash
# Backup com criptografia
pg_dump ... | gzip | gpg --encrypt --recipient backup@empresa.com > backup.sql.gz.gpg

# Restaurar
gpg --decrypt backup.sql.gz.gpg | gunzip | psql ...
```

---

## 📊 Monitoramento de Backups

### Verificação Diária

```python
def verify_backups():
    """Verifica se todos os tenants têm backup recente"""
    import psycopg2
    from datetime import datetime, timedelta
    
    conn = psycopg2.connect(...)
    cursor = conn.cursor()
    
    # Busca tenants ativos
    cursor.execute("SELECT id, nome FROM tenants WHERE ativo = true")
    tenants = cursor.fetchall()
    
    issues = []
    
    for tenant_id, nome in tenants:
        # Verifica último backup
        backup_files = sorted([
            f for f in os.listdir(backup_dir)
            if f.startswith(f'tenant_{tenant_id}_')
        ])
        
        if not backup_files:
            issues.append(f"❌ Tenant {tenant_id} ({nome}): SEM BACKUP")
            continue
        
        # Verifica idade do backup
        last_backup = backup_files[-1]
        backup_date = datetime.strptime(
            last_backup.split('_')[2], 
            '%Y%m%d'
        )
        
        days_ago = (datetime.now() - backup_date).days
        
        if days_ago > 1:
            issues.append(f"⚠️ Tenant {tenant_id} ({nome}): Backup com {days_ago} dias")
    
    return issues
```

---

## 📋 Checklist de Backup

- [ ] Backups automatizados configurados
- [ ] Teste de restore realizado mensalmente
- [ ] Backups armazenados em local seguro (S3/GCS)
- [ ] Criptografia ativada
- [ ] Retenção de 30 dias configurada
- [ ] Monitoramento de falhas implementado
- [ ] Documentação de restore atualizada
- [ ] RTO e RPO definidos e testados

---

## 🚨 Plano de Disaster Recovery

### Cenário 1: Tenant Acidentalmente Deletado

**Ação:**
1. Identificar último backup
2. Criar novo tenant_id (ou usar o mesmo)
3. Restaurar backup
4. Validar dados
5. Notificar cliente

**Tempo estimado:** 15-30 minutos

### Cenário 2: Corrupção de Dados

**Ação:**
1. Isolar tenant afetado
2. Identificar ponto de corrupção
3. Restaurar de backup anterior à corrupção
4. Re-aplicar transações válidas (se possível)
5. Validar integridade

**Tempo estimado:** 1-2 horas

### Cenário 3: Perda Total do Banco

**Ação:**
1. Provisionar novo servidor PostgreSQL
2. Restaurar schema
3. Restaurar backup de cada tenant
4. Validar todos os tenants
5. Atualizar DNS/conexões

**Tempo estimado:** 2-4 horas

---

## 📈 Métricas de Backup

```sql
-- Tamanho de backup estimado por tenant
SELECT 
    tenant_id,
    COUNT(*) as total_registros,
    pg_size_pretty(SUM(pg_column_size(usuarios.*))) as tamanho_usuarios,
    pg_size_pretty(SUM(pg_column_size(leads.*))) as tamanho_leads
FROM usuarios
LEFT JOIN leads USING (tenant_id)
GROUP BY tenant_id
ORDER BY SUM(pg_column_size(usuarios.*)) DESC;
```

---

## 🔗 Referências

- [pg_dump Documentation](https://www.postgresql.org/docs/current/app-pgdump.html)
- [pgBackRest](https://pgbackrest.org/)
- [Wal-G](https://github.com/wal-g/wal-g)
- [AWS RDS Backups](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_CommonTasks.BackupRestore.html)
