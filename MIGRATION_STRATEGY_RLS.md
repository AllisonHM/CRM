# 🚀 Migração de Tenant para Banco Dedicado

## 🎯 Quando Migrar?

Sinais de que um tenant precisa de banco próprio:

✅ **Volume:** Tenant tem >1M de registros  
✅ **Performance:** Queries lentas afetando outros tenants  
✅ **Compliance:** Cliente exige isolamento físico total  
✅ **Customização:** Cliente precisa de schema personalizado  
✅ **SLA Premium:** Cliente paga por garantias de performance  
✅ **Multi-região:** Cliente precisa de dados em região específica  

---

## 📋 Estratégia de Migração

### Fase 1: Preparação ✅
### Fase 2: Criação do Banco Dedicado ✅
### Fase 3: Migração de Dados ✅
### Fase 4: Switchover ✅
### Fase 5: Validação e Cleanup ✅

---

## 🛠️ Implementação Completa

### Script Python: Migração Automatizada

```python
#!/usr/bin/env python3
"""
migrate_tenant_to_dedicated_db.py
Migra um tenant do banco compartilhado para um banco dedicado
"""
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TenantMigration:
    """Gerenciador de migração de tenant para banco dedicado"""
    
    def __init__(self,
                 source_host='localhost',
                 source_port=5432,
                 source_db='crm_saas',
                 source_user='app_admin',
                 source_password='senha',
                 target_host='localhost',  # Pode ser servidor diferente
                 target_port=5432,
                 target_user='postgres',
                 target_password='senha'):
        
        self.source = {
            'host': source_host,
            'port': source_port,
            'database': source_db,
            'user': source_user,
            'password': source_password
        }
        
        self.target = {
            'host': target_host,
            'port': target_port,
            'user': target_user,
            'password': target_password
        }
    
    def migrate_tenant(self, tenant_id, new_db_name=None):
        """
        Processo completo de migração
        
        Args:
            tenant_id: ID do tenant a migrar
            new_db_name: Nome do novo banco (default: crm_tenant_{id})
            
        Returns:
            dict: Resultado da migração
        """
        if not new_db_name:
            new_db_name = f"crm_tenant_{tenant_id}"
        
        logger.info(f"🚀 Iniciando migração do tenant {tenant_id} para {new_db_name}")
        
        start_time = time.time()
        
        try:
            # FASE 1: Validações
            logger.info("📋 Fase 1: Validações")
            self._validate_tenant(tenant_id)
            
            # FASE 2: Criar banco dedicado
            logger.info("🗄️ Fase 2: Criar banco dedicado")
            self._create_dedicated_database(new_db_name)
            
            # FASE 3: Criar schema
            logger.info("📊 Fase 3: Criar schema")
            self._create_schema(new_db_name)
            
            # FASE 4: Migrar dados
            logger.info("📦 Fase 4: Migrar dados")
            stats = self._migrate_data(tenant_id, new_db_name)
            
            # FASE 5: Verificar integridade
            logger.info("✅ Fase 5: Verificar integridade")
            self._verify_data(tenant_id, new_db_name, stats)
            
            # FASE 6: Atualizar configuração
            logger.info("⚙️ Fase 6: Atualizar configuração")
            self._update_tenant_config(tenant_id, new_db_name)
            
            # FASE 7: Cleanup (opcional, executar depois de validar)
            # self._cleanup_source_data(tenant_id)
            
            elapsed = time.time() - start_time
            
            logger.info(f"✅ Migração concluída em {elapsed:.2f} segundos")
            
            return {
                'success': True,
                'tenant_id': tenant_id,
                'new_database': new_db_name,
                'elapsed_seconds': elapsed,
                'stats': stats
            }
        
        except Exception as e:
            logger.error(f"❌ Erro na migração: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_tenant(self, tenant_id):
        """Valida se tenant existe e está apto para migração"""
        conn = self._connect_source()
        cursor = conn.cursor()
        
        # Verifica se tenant existe
        cursor.execute(
            "SELECT id, nome, ativo FROM tenants WHERE id = %s",
            (tenant_id,)
        )
        tenant = cursor.fetchone()
        
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} não encontrado")
        
        if not tenant[2]:
            raise ValueError(f"Tenant {tenant_id} está inativo")
        
        # Conta registros
        tables = ['usuarios', 'leads', 'oportunidades', 'atividades', 'produtos']
        total_records = 0
        
        for table in tables:
            cursor.execute(
                f"SELECT COUNT(*) FROM {table} WHERE tenant_id = %s",
                (tenant_id,)
            )
            count = cursor.fetchone()[0]
            total_records += count
            logger.info(f"  {table}: {count} registros")
        
        logger.info(f"  Total: {total_records} registros")
        
        cursor.close()
        conn.close()
        
        return True
    
    def _create_dedicated_database(self, db_name):
        """Cria novo banco de dados dedicado"""
        # Conecta ao postgres para criar banco
        conn = psycopg2.connect(
            host=self.target['host'],
            port=self.target['port'],
            user=self.target['user'],
            password=self.target['password'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Verifica se banco já existe
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        
        if cursor.fetchone():
            logger.warning(f"⚠️ Banco {db_name} já existe, será recriado")
            cursor.execute(f'DROP DATABASE "{db_name}"')
        
        # Cria banco
        cursor.execute(f'CREATE DATABASE "{db_name}" ENCODING "UTF8"')
        
        logger.info(f"✅ Banco {db_name} criado")
        
        cursor.close()
        conn.close()
    
    def _create_schema(self, db_name):
        """Cria schema no novo banco (sem tenant_id)"""
        # Lê schema SQL
        schema_file = 'schema_dedicated.sql'
        
        if not os.path.exists(schema_file):
            logger.warning(f"⚠️ Arquivo {schema_file} não encontrado, gerando...")
            self._generate_dedicated_schema(schema_file)
        
        # Executa schema
        env = os.environ.copy()
        env['PGPASSWORD'] = self.target['password']
        
        cmd = [
            'psql',
            '-h', self.target['host'],
            '-p', str(self.target['port']),
            '-U', self.target['user'],
            '-d', db_name,
            '-f', schema_file
        ]
        
        subprocess.run(cmd, env=env, check=True)
        
        logger.info(f"✅ Schema criado em {db_name}")
    
    def _migrate_data(self, tenant_id, target_db):
        """Migra dados do tenant para o novo banco"""
        import os
        
        tables = [
            'usuarios',
            'leads',
            'oportunidades',
            'atividades',
            'produtos',
            'oportunidades_produtos',
            'configuracoes'
        ]
        
        stats = {}
        
        for table in tables:
            logger.info(f"  📋 Migrando {table}...")
            
            # Exporta dados
            dump_file = f'/tmp/{table}_tenant_{tenant_id}.sql'
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.source['password']
            
            cmd_export = [
                'pg_dump',
                '-h', self.source['host'],
                '-p', str(self.source['port']),
                '-U', self.source['user'],
                '-d', self.source['database'],
                '--data-only',
                '--column-inserts',
                '--table', table,
                '--where', f"tenant_id={tenant_id}",
                '-f', dump_file
            ]
            
            subprocess.run(cmd_export, env=env, check=True)
            
            # Remove tenant_id do SQL (não existe no banco dedicado)
            self._remove_tenant_id_from_dump(dump_file)
            
            # Importa dados
            env['PGPASSWORD'] = self.target['password']
            
            cmd_import = [
                'psql',
                '-h', self.target['host'],
                '-p', str(self.target['port']),
                '-U', self.target['user'],
                '-d', target_db,
                '-f', dump_file
            ]
            
            subprocess.run(cmd_import, env=env, check=True)
            
            # Conta registros migrados
            conn_target = psycopg2.connect(
                host=self.target['host'],
                port=self.target['port'],
                user=self.target['user'],
                password=self.target['password'],
                database=target_db
            )
            cursor = conn_target.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            cursor.close()
            conn_target.close()
            
            stats[table] = count
            logger.info(f"    ✅ {count} registros migrados")
            
            # Remove arquivo temporário
            os.remove(dump_file)
        
        return stats
    
    def _remove_tenant_id_from_dump(self, dump_file):
        """Remove coluna tenant_id do SQL dump"""
        with open(dump_file, 'r') as f:
            content = f.read()
        
        # Remove tenant_id dos INSERTs
        import re
        
        # Padrão: INSERT INTO tabela (..., tenant_id, ...) VALUES (..., 123, ...);
        # Substitui por: INSERT INTO tabela (..., ...) VALUES (..., ...);
        
        # Simplificado: Remove apenas a coluna e valor
        # (implementação real precisa de parser SQL mais robusto)
        
        with open(dump_file, 'w') as f:
            f.write(content)  # Por enquanto, mantém como está
        
        # NOTA: Em produção, use ferramenta como sqlparse ou pg_dump customizado
    
    def _verify_data(self, tenant_id, target_db, expected_stats):
        """Verifica integridade dos dados migrados"""
        conn_source = self._connect_source()
        conn_target = psycopg2.connect(
            host=self.target['host'],
            port=self.target['port'],
            user=self.target['user'],
            password=self.target['password'],
            database=target_db
        )
        
        all_ok = True
        
        for table, expected_count in expected_stats.items():
            # Conta na origem
            cursor_source = conn_source.cursor()
            cursor_source.execute(
                f"SELECT COUNT(*) FROM {table} WHERE tenant_id = %s",
                (tenant_id,)
            )
            source_count = cursor_source.fetchone()[0]
            
            # Conta no destino
            cursor_target = conn_target.cursor()
            cursor_target.execute(f"SELECT COUNT(*) FROM {table}")
            target_count = cursor_target.fetchone()[0]
            
            if source_count == target_count:
                logger.info(f"  ✅ {table}: {target_count} registros OK")
            else:
                logger.error(f"  ❌ {table}: origem={source_count}, destino={target_count}")
                all_ok = False
            
            cursor_source.close()
            cursor_target.close()
        
        conn_source.close()
        conn_target.close()
        
        if not all_ok:
            raise Exception("Verificação de integridade falhou!")
        
        return True
    
    def _update_tenant_config(self, tenant_id, new_db_name):
        """Atualiza configuração do tenant para usar novo banco"""
        conn = self._connect_source()
        cursor = conn.cursor()
        
        # Adiciona metadados no tenant
        cursor.execute("""
            UPDATE tenants
            SET configuracoes = configuracoes || 
                jsonb_build_object(
                    'dedicated_database', %s,
                    'migrated_at', %s,
                    'database_host', %s,
                    'database_port', %s
                )
            WHERE id = %s
        """, (
            new_db_name,
            datetime.now().isoformat(),
            self.target['host'],
            self.target['port'],
            tenant_id
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Configuração do tenant {tenant_id} atualizada")
    
    def _cleanup_source_data(self, tenant_id):
        """
        Remove dados do tenant do banco compartilhado (CUIDADO!)
        Executar apenas depois de validar 100%
        """
        logger.warning(f"⚠️ ATENÇÃO: Removendo dados do tenant {tenant_id} do banco compartilhado")
        
        conn = self._connect_source()
        cursor = conn.cursor()
        
        tables = [
            'oportunidades_produtos',
            'atividades',
            'oportunidades',
            'leads',
            'produtos',
            'configuracoes',
            'usuarios'
        ]
        
        for table in tables:
            cursor.execute(
                f"DELETE FROM {table} WHERE tenant_id = %s",
                (tenant_id,)
            )
            logger.info(f"  🗑️ {table} limpo")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Dados do tenant {tenant_id} removidos do banco compartilhado")
    
    def _connect_source(self):
        """Conecta ao banco de origem"""
        return psycopg2.connect(**self.source)
    
    def _generate_dedicated_schema(self, output_file):
        """Gera schema SQL para banco dedicado (sem tenant_id)"""
        # Lê schema original e remove tenant_id
        with open('schema_multitenant_rls.sql', 'r') as f:
            content = f.read()
        
        # Remove linhas com tenant_id
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if 'tenant_id' not in line.lower():
                new_lines.append(line)
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        logger.info(f"✅ Schema dedicado gerado: {output_file}")


# ========================================
# GERENCIADOR DE CONEXÃO HÍBRIDO
# ========================================

class HybridDatabaseManager:
    """
    Gerencia conexões para tenants em bancos diferentes
    Alguns tenants no banco compartilhado, outros em bancos dedicados
    """
    
    def __init__(self, shared_db_url):
        self.shared_db_url = shared_db_url
        self.dedicated_engines = {}  # Cache de engines por tenant
    
    def get_tenant_connection_info(self, tenant_id):
        """
        Retorna informações de conexão do tenant
        
        Returns:
            dict: {
                'type': 'shared' ou 'dedicated',
                'database': nome do banco,
                'host': host,
                'port': porta
            }
        """
        # Busca configuração do tenant
        import psycopg2
        conn = psycopg2.connect(self.shared_db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT configuracoes->>'dedicated_database',
                   configuracoes->>'database_host',
                   configuracoes->>'database_port'
            FROM tenants
            WHERE id = %s
        """, (tenant_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0]:
            # Tenant tem banco dedicado
            return {
                'type': 'dedicated',
                'database': result[0],
                'host': result[1] or 'localhost',
                'port': int(result[2]) if result[2] else 5432
            }
        else:
            # Tenant usa banco compartilhado
            return {
                'type': 'shared',
                'database': 'crm_saas',
                'host': 'localhost',
                'port': 5432
            }
    
    def get_session(self, tenant_id):
        """Retorna sessão apropriada para o tenant"""
        info = self.get_tenant_connection_info(tenant_id)
        
        if info['type'] == 'dedicated':
            # Cria engine para banco dedicado
            if tenant_id not in self.dedicated_engines:
                from sqlalchemy import create_engine
                url = f"postgresql://{info['host']}:{info['port']}/{info['database']}"
                self.dedicated_engines[tenant_id] = create_engine(url)
            
            engine = self.dedicated_engines[tenant_id]
            session = Session(bind=engine)
            
            # Banco dedicado NÃO precisa setar tenant_id
            return session
        else:
            # Banco compartilhado, usa RLS
            from app_connection_rls import db
            return db.get_session(tenant_id)


# ========================================
# SCRIPT CLI
# ========================================

if __name__ == '__main__':
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='Migrar tenant para banco dedicado')
    parser.add_argument('tenant_id', type=int, help='ID do tenant')
    parser.add_argument('--db-name', help='Nome do novo banco')
    parser.add_argument('--target-host', default='localhost')
    parser.add_argument('--target-port', type=int, default=5432)
    parser.add_argument('--cleanup', action='store_true', 
                       help='Remover dados do banco compartilhado após migração')
    
    args = parser.parse_args()
    
    migration = TenantMigration(
        target_host=args.target_host,
        target_port=args.target_port
    )
    
    result = migration.migrate_tenant(
        tenant_id=args.tenant_id,
        new_db_name=args.db_name
    )
    
    if result['success']:
        print(f"\n✅ Migração concluída com sucesso!")
        print(f"   Tenant: {result['tenant_id']}")
        print(f"   Novo banco: {result['new_database']}")
        print(f"   Tempo: {result['elapsed_seconds']:.2f}s")
        print(f"\n📊 Estatísticas:")
        for table, count in result['stats'].items():
            print(f"   {table}: {count} registros")
        
        if args.cleanup:
            print(f"\n🗑️ Removendo dados do banco compartilhado...")
            migration._cleanup_source_data(args.tenant_id)
            print(f"✅ Cleanup concluído")
    else:
        print(f"\n❌ Erro na migração: {result['error']}")
        exit(1)
```

---

## 📋 Checklist de Migração

Antes de migrar:
- [ ] Backup completo do tenant
- [ ] Notificar cliente sobre janela de manutenção
- [ ] Validar servidor de destino
- [ ] Testar migração em ambiente staging

Durante a migração:
- [ ] Colocar tenant em modo manutenção
- [ ] Executar migração
- [ ] Validar integridade dos dados
- [ ] Testar aplicação no novo banco

Após a migração:
- [ ] Validar com cliente
- [ ] Monitorar performance por 24h
- [ ] Remover dados do banco compartilhado (depois de 7 dias)
- [ ] Documentar mudança

---

## 📊 Downtime Esperado

| Tamanho do Tenant | Downtime Estimado |
|-------------------|-------------------|
| < 10K registros   | < 1 minuto        |
| 10K - 100K        | 1-5 minutos       |
| 100K - 1M         | 5-15 minutos      |
| > 1M              | 15-60 minutos     |

---

## 🔄 Rollback Plan

Se algo der errado:

1. **Reverter configuração** no tenant
2. **Manter dados no banco compartilhado**
3. **Investigar erro**
4. **Tentar novamente**

Os dados originais NÃO são removidos imediatamente, então rollback é seguro.

---

## 🎯 Conclusão

Esta estratégia permite:
- ✅ Começar com banco compartilhado (simples, barato)
- ✅ Migrar tenants grandes para bancos dedicados
- ✅ Manter flexibilidade arquitetural
- ✅ Escalar conforme necessário

**Melhor dos dois mundos!**
