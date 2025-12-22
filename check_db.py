from CRM import app
from models import Cliente, WhatsAppMensagem

with app.app_context():
    print('--- Clientes ---')
    for c in Cliente.query.all():
        print(c.id, c.nome, c.telefone, ''.join(filter(str.isdigit, c.telefone)))
    print()
    print('--- Últimas mensagens ---')
    for m in WhatsAppMensagem.query.order_by(WhatsAppMensagem.recebido_em.desc()).limit(30).all():
        print(m.recebido_em, m.numero, m.remetente, m.mensagem)