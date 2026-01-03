from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_socketio import SocketIO, join_room
from datetime import datetime, timedelta
import requests
from flask_migrate import Migrate
from database import db
from models import Cliente, MesaNegocio, Ocorrencia, WhatsAppMensagem, ChatbotRegra, Produto, Movimentacao, PlannerEvento
from sqlalchemy import or_

app = Flask(__name__)
app.secret_key = "seusegredo"

# ------------------- BANCO -------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:Amovoce123%40@localhost:1222/crm'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()


socketio = SocketIO(app, cors_allowed_origins="*")

migrate = Migrate(app, db)

# ------------------- Z-API -------------------
instance = "3E70C9784E1060A6F423AE9094E04006"
token = "E4E83715DE9F517EFB9A28CA"
client_token = "Fc5c052a80080460b823a2e506d4d6167S"
headers = {'client-token': client_token, 'Content-Type': 'application/json'}

def enviar_whatsapp_zapi(numero, mensagem):
    url = f"https://api.z-api.io/instances/{instance}/token/{token}/send-text"
    payload = {"phone": numero, "message": mensagem}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return {"status": "Sucesso", "detalhe": response.text}
        return {"status": "Erro", "detalhe": response.text}
    except Exception as e:
        return {"status": "Erro", "detalhe": str(e)}
    
import threading, time

def verificar_eventos_proximos():
    with app.app_context():
        while True:
            agora = datetime.now()
            limite = agora + timedelta(minutes=30)

            eventos = PlannerEvento.query.filter(
                PlannerEvento.data_hora >= agora,
                PlannerEvento.data_hora <= limite
            ).all()

            for evento in eventos:
                socketio.emit('notificacao_evento', {
                    'titulo': evento.titulo,
                    'descricao': evento.descricao,
                    'hora': evento.data_hora.strftime('%H:%M'),
                    'cliente': evento.cliente.nome if evento.cliente else "N/A"
                })

            time.sleep(60)  # roda a cada 60 segundos

threading.Thread(target=verificar_eventos_proximos, daemon=True).start()


# ------------------- ROTAS -------------------
@app.route("/")
def home():
    return redirect(url_for("menu"))

@app.route('/menu')
def menu():
    qtd_clientes = Cliente.query.count()
    qtd_mesas = MesaNegocio.query.count()
    qtd_ocorrencias = Ocorrencia.query.count()

    # Contagem de agendas no dia de hoje
    hoje = datetime.today().date()
    qtd_agendas_hoje = PlannerEvento.query.filter(PlannerEvento.data == hoje).count()

    # Pessoas físicas / jurídicas
    qtd_pf = Cliente.query.filter(Cliente.tipo_pessoa == 'Física').count()
    qtd_pj = Cliente.query.filter(Cliente.tipo_pessoa == 'Jurídica').count()

    return render_template(
        "menu.html",
        qtd_clientes=qtd_clientes,
        qtd_mesas=qtd_mesas,
        qtd_ocorrencias=qtd_ocorrencias,
        qtd_agendas_hoje=qtd_agendas_hoje,
        qtd_pf=qtd_pf,
        qtd_pj=qtd_pj
    )


# --- RELACIONAMENTO
@app.route("/relacionamento")
def relacionamento():
    clientes = Cliente.query.all()
    return render_template("relacionamento.html", clientes=clientes)

@app.route("/cliente/<int:id>")
def detalhe_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    return render_template("detalhe_cliente.html", cliente=cliente)

@app.route("/cliente/<int:id>/novo")
def detalhe_cliente_novo(id):
    cliente = Cliente.query.get_or_404(id)
    return render_template("detalhe_cliente_novo.html", cliente=cliente)

@app.route("/cliente/<int:id>/editar", methods=["GET", "POST"])
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == "POST":
        cliente.nome = request.form.get('nome', cliente.nome)
        cliente.email = request.form.get('email', cliente.email)
        cliente.telefone = request.form.get('telefone', cliente.telefone)
        cliente.endereco = request.form.get('endereco', cliente.endereco)
        cliente.segmento = request.form.get('segmento', cliente.segmento)
        
        # Pessoa Física
        if 'data_nascimento' in request.form and request.form.get('data_nascimento'):
            try:
                cliente.data_nascimento = datetime.strptime(request.form.get('data_nascimento'), '%Y-%m-%d').date()
            except:
                pass
        
        if 'renda' in request.form and request.form.get('renda'):
            try:
                cliente.renda = float(request.form.get('renda'))
            except:
                pass
        
        cliente.segmento_trabalho = request.form.get('segmento_trabalho', cliente.segmento_trabalho)
        
        # Pessoa Jurídica
        if 'data_abertura' in request.form and request.form.get('data_abertura'):
            try:
                cliente.data_abertura = datetime.strptime(request.form.get('data_abertura'), '%Y-%m-%d').date()
            except:
                pass
        
        if 'faturamento' in request.form and request.form.get('faturamento'):
            try:
                cliente.faturamento = float(request.form.get('faturamento'))
            except:
                pass
        
        if 'qtd_funcionarios' in request.form and request.form.get('qtd_funcionarios'):
            try:
                cliente.qtd_funcionarios = int(request.form.get('qtd_funcionarios'))
            except:
                pass
        
        db.session.commit()
        return redirect(url_for('detalhe_cliente_novo', id=cliente.id))
    
    return render_template("editar_cliente.html", cliente=cliente)

# --- MESAS DE NEGÓCIO
@app.route("/cliente/<int:id>/add_mesa", methods=["GET", "POST"])
def add_mesa(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == "POST":
        mesa = MesaNegocio(
            cliente_id=id,
            topico=request.form["topico"],
            produtos=request.form["produtos"],
            situacao=request.form["situacao"],
            valor_total=float(request.form["valor_total"]),
            descricao=request.form.get("descricao"),
            data_registro=datetime.today().date(),
            hora_registro=datetime.now().time()
        )
        db.session.add(mesa)
        db.session.commit()
        return redirect(url_for("mesas_negocio"))
    return render_template("add_mesa.html", cliente=cliente)

@app.route("/mesas_negocio")
def mesas_negocio():
    mesas = MesaNegocio.query.all()
    return render_template("mesas_negocio.html", mesas=mesas)

@app.route("/mesas/<int:id>")
def detalhe_mesa(id):
    mesa = MesaNegocio.query.get_or_404(id)
    return render_template("detalhe_mesa.html", mesa=mesa)

# --- OCORRÊNCIAS
@app.route("/cliente/<int:id>/add_ocorrencia", methods=["GET", "POST"])
def add_ocorrencia(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == "POST":
        ocorrencia = Ocorrencia(
            cliente_id=id,
            topico=request.form["topico"],
            status=request.form["status"],
            descricao=request.form["descricao"],
            data_registro=datetime.today().date(),
            hora_registro=datetime.now().time()
        )
        db.session.add(ocorrencia)
        db.session.commit()
        return redirect(url_for("ocorrencias"))
    return render_template("add_ocorrencia.html", cliente=cliente)

@app.route("/ocorrencias")
def ocorrencias():
    ocorrencias = Ocorrencia.query.all()
    return render_template("ocorrencias.html", ocorrencias=ocorrencias)

@app.route("/ocorrencia/<int:id>")
def detalhe_ocorrencia(id):
    ocorrencia = Ocorrencia.query.get_or_404(id)
    # pega o cliente se houver relação
    cliente = ocorrencia.cliente if hasattr(ocorrencia, 'cliente') else None
    return render_template("detalhe_ocorrencia.html", ocorrencia=ocorrencia, cliente=cliente)

@app.route("/ocorrencia/<int:id>/atualizar", methods=["POST"])
def atualizar_ocorrencia(id):
    ocorrencia = Ocorrencia.query.get_or_404(id)
    ocorrencia.situacao = request.form["situacao"]
    db.session.commit()
    return redirect(url_for("ocorrencias"))

# --- CADASTRO CLIENTE
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        email = request.form["email"]
        tipo_pessoa = request.form["tipo_pessoa"]

        cliente = Cliente(nome=nome, telefone=telefone, email=email, tipo_pessoa=tipo_pessoa)

        if tipo_pessoa == "Física":
            if request.form.get("data_nascimento"):
                cliente.data_nascimento = datetime.strptime(request.form["data_nascimento"], "%Y-%m-%d").date()
            cliente.renda = request.form.get("renda") or None
            cliente.segmento_trabalho = request.form.get("segmento_trabalho")
            cliente.endereco = request.form.get("endereco")
        else:
            if request.form.get("data_abertura"):
                cliente.data_abertura = datetime.strptime(request.form["data_abertura"], "%Y-%m-%d").date()
            cliente.faturamento = request.form.get("faturamento") or None
            cliente.segmento = request.form.get("segmento")
            cliente.endereco = request.form.get("endereco")
            cliente.qtd_funcionarios = request.form.get("qtd_funcionarios") or None

        db.session.add(cliente)
        db.session.commit()
        return redirect(url_for("cadastro"))

    # 🔹 Lista de clientes mostrada na página
    clientes = Cliente.query.all()
    return render_template("cadastro.html", clientes=clientes)


@app.route("/cliente/<int:id>/excluir", methods=["POST"])
def excluir_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    
    # Excluir todas as ocorrências vinculadas
    if cliente.ocorrencias:
        for ocorrencia in cliente.ocorrencias:
            db.session.delete(ocorrencia)
    
    # Excluir todas as mesas vinculadas
    if cliente.mesas:
        for mesa in cliente.mesas:
            db.session.delete(mesa)
    
    # Excluir o cliente
    db.session.delete(cliente)
    db.session.commit()
    
    flash(f"Cliente '{cliente.nome}' e todos os seus dados foram excluídos com sucesso!", "success")
    return redirect(url_for('cadastro'))

@app.route("/cliente/<int:id>/delete", methods=["POST"])
def deletar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    try:
        db.session.delete(cliente)
        db.session.commit()
        flash("Cliente excluído com sucesso!", "success")  # Mensagem verde
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir cliente: {str(e)}", "danger")  # Mensagem vermelha
    return redirect(url_for("cadastro"))

@app.route("/mesas/<int:id>/atualizar", methods=["POST"])
def atualizar_mesa(id):
    mesa = MesaNegocio.query.get_or_404(id)
    nova_situacao = request.form.get("situacao")

    if not nova_situacao:
        flash("Informe uma nova situação.", "danger")
        return redirect(url_for("detalhe_mesa", id=id))

    mesa.situacao = nova_situacao
    db.session.commit()
    flash("Situação atualizada com sucesso!", "success")

    return redirect(url_for("detalhe_mesa", id=id))

# --- WHATSAPP
@app.route("/whatsapp")
def whatsapp_index():
    mensagens = WhatsAppMensagem.query.all()
    return render_template("whatsapp.html", mensagens=mensagens)



@app.route("/whatsapp/enviar", methods=["POST"])
def whatsapp_enviar():
    data = request.get_json(silent=True)
    if data:
        numero = data.get("numero")
        mensagem = data.get("mensagem")
    else:
        numero = request.form.get("numero")
        mensagem = request.form.get("mensagem")

    if not numero or not mensagem:
        return render_template("mensagem_status.html", status="erro", voltar_url=url_for("whatsapp_index"))

    resultado = enviar_whatsapp_zapi(numero, mensagem)

    if resultado["status"] == "Sucesso":
        return render_template("mensagem_status.html", status="sucesso", voltar_url=url_for("whatsapp_index"))
    else:
        return render_template("mensagem_status.html", status="erro", voltar_url=url_for("whatsapp_index"))

@app.route("/canais/webhook", methods=["POST"])
@app.route("/webhook/messages", methods=["POST"])
def receber_mensagem_webhook():
    data = request.get_json(silent=True) or {}

    print("📩 Webhook recebido (raw):", data)

    # tenta extrair telefone a partir de várias chaves comuns
    phone = None
    # chaves diretas
    for k in ("phone", "from", "from_number", "sender", "contact", "wa_id", "number"):
        v = data.get(k)
        if v:
            phone = v
            break

    # se ainda não encontrou, procura recursivamente por campos que pareçam telefone
    def find_phone(obj):
        if isinstance(obj, dict):
            for kk, vv in obj.items():
                if kk.lower() in ("phone", "from", "number", "wa_id", "id", "contact") and vv:
                    return vv
                res = find_phone(vv)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = find_phone(item)
                if res:
                    return res
        return None

    if not phone:
        phone = find_phone(data)

    # tenta extrair texto em formatos comuns (apenas campos explícitos)
    text = None
    explicit_text = None
    txt = data.get("text")
    if isinstance(txt, dict):
        explicit_text = txt.get("message") or txt.get("body") or txt.get("text")
    elif isinstance(txt, str):
        explicit_text = txt
    explicit_text = explicit_text or data.get("message") or data.get("body") or data.get("text_message")

    # filtra callbacks que não são mensagens (presença/status) quando possível
    tipo = data.get("type", "").lower()
    non_message_types = ("presencechatcallback", "messagestatuscallback", "deliverycallback", "messagestatuscallback")

    # se for um tipo claramente não-mensagem e não houver texto explícito (campo text/message/body), ignorar
    if tipo in non_message_types and not explicit_text:
        print(f"Webhook ignorado (tipo {data.get('type')} sem texto explícito)")
        return {"status": "ignored"}, 200

    # agora tenta encontrar texto recursivamente, MAS apenas buscando campos nominais (message/body/text/caption)
    def find_text(obj):
        if isinstance(obj, dict):
            for kk, vv in obj.items():
                if kk.lower() in ("message", "body", "text", "caption") and isinstance(vv, str):
                    return vv
                res = find_text(vv)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = find_text(item)
                if res:
                    return res
        return None

    # prefer explicit_text quando existir, senão use find_text
    text = explicit_text or find_text(data)

    # filtra callbacks que não são mensagens (presença/status) quando possível
    tipo = data.get("type", "").lower()
    non_message_types = ("presencechatcallback", "messagestatuscallback", "deliverycallback", "messageStatusCallback")

    # se for um tipo claramente não-mensagem e não houver texto extraído, ignorar
    if tipo in non_message_types and not text:
        print(f"Webhook ignorado (tipo {data.get('type')} sem texto)")
        return {"status": "ignored"}, 200

    if not phone or not text:
        print("Webhook ignorado: phone/text não encontrados")
        return {"status": "ignored"}, 200

    # evita salvar valores como instanceId que foram capturados como 'text'
    if isinstance(text, str) and text == data.get("instanceId"):
        print("Webhook ignorado: texto igual a instanceId")
        return {"status": "ignored"}, 200

    # normaliza número para apenas dígitos
    numero = str(phone)
    numero = numero.replace("+", "").replace(" ", "").strip()
    import re
    numero = re.sub(r"\D", "", numero)

    # salvar no banco (WhatsAppMensagem)
    msg = WhatsAppMensagem(
        numero=numero,
        remetente="Cliente",
        mensagem=text,
        recebido_em=datetime.utcnow()
    )
    db.session.add(msg)
    db.session.commit()

    # emitir para a sala correta
    payload = {
        "id": msg.id,
        "numero": numero,
        "remetente": "Cliente",
        "mensagem": text,
        "hora": datetime.now().strftime("%H:%M")
    }

    rooms_to_emit = {numero}
    if len(numero) >= 6:
        rooms_to_emit.add(numero[-6:])
    if len(numero) >= 8:
        rooms_to_emit.add(numero[-8:])

    for r in rooms_to_emit:
        try:
            socketio.emit("nova_mensagem", payload, room=r)
        except Exception:
            pass

    print(f"✅ Mensagem emitida para salas: {', '.join(sorted(rooms_to_emit))}")

    return {"status": "ok"}, 200

@socketio.on('join')
def join_room_event(data):
    numero = data.get("numero")
    if not numero:
        return

    numero_norm = numero.replace("+", "").replace(" ", "").strip()
    # entra na sala completa e em salas por sufixo (últimos 6 e 8 dígitos) para tolerância de formatos
    rooms_joined = set()
    join_room(numero_norm)
    rooms_joined.add(numero_norm)
    if len(numero_norm) >= 6:
        s6 = numero_norm[-6:]
        join_room(s6)
        rooms_joined.add(s6)
    if len(numero_norm) >= 8:
        s8 = numero_norm[-8:]
        join_room(s8)
        rooms_joined.add(s8)

    print(f"🔵 Usuário entrou nas salas: {', '.join(sorted(rooms_joined))}")

@app.route("/canais/enviar", methods=["POST"])
def enviar_mensagem_canais():
    data = request.get_json()
    numero = data.get("numero")
    mensagem = data.get("mensagem")

    if not numero or not mensagem:
        return jsonify({"status": "Erro"}), 400

    numero_norm = numero.replace("+", "").replace(" ", "").strip()

    resultado = enviar_whatsapp_zapi(numero_norm, mensagem)

    if resultado["status"] == "Sucesso":
        # salvar no banco
        msg = WhatsAppMensagem(
            numero=numero_norm,
            remetente="Você",
            mensagem=mensagem,
            recebido_em=datetime.utcnow()
        )
        db.session.add(msg)
        db.session.commit()

        # emitir para a sala
        payload = {
            "id": msg.id,
            "numero": numero_norm,
            "remetente": "Você",
            "mensagem": mensagem,
            "hora": datetime.now().strftime("%H:%M")
        }
        try:
            socketio.emit("nova_mensagem", payload, room=numero_norm)
        except Exception:
            pass

        return jsonify({"status": "Sucesso"})

    return jsonify({"status": "Erro"})


# --- CHATBOT
@app.route("/chatbot", methods=["GET", "POST"])
def configurar_chatbot():
    if request.method == "POST":
        palavra = request.form["palavra_chave"]
        resposta = request.form["resposta"]
        regra = ChatbotRegra(palavra_chave=palavra, resposta=resposta)
        db.session.add(regra)
        db.session.commit()

@app.route("/mensagens")
def mensagens():
    mensagens = WhatsAppMensagem.query.order_by(WhatsAppMensagem.recebido_em.desc()).all()
    return render_template("mensagens.html", mensagens=mensagens)

@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    if request.method == "POST":
        palavra = request.form["palavra"]
        resposta = request.form["resposta"]
        prioridade = request.form["prioridade"]
        regra = ChatbotRegra(palavra_chave=palavra, resposta=resposta, prioridade=prioridade)
        db.session.add(regra)
        db.session.commit()
        flash("Regra adicionada com sucesso!")
        return redirect(url_for("configuracoes"))

    regras = ChatbotRegra.query.all()
    return render_template("configuracoes.html", regras=regras)

@app.route("/canais")
def canais():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template("canais.html", clientes=clientes)


@app.route("/canais/ultimas")
def ultimas_notificacoes():
    """
    Retorna as últimas mensagens recebidas agrupadas por número de telefone.
    Para cada número, retorna apenas a mensagem mais recente.
    """
    from sqlalchemy import func
    
    # Subquery para encontrar a data mais recente por número
    subq = db.session.query(
        WhatsAppMensagem.numero,
        func.max(WhatsAppMensagem.recebido_em).label('max_data')
    ).group_by(WhatsAppMensagem.numero).subquery()
    
    # Query principal para buscar as mensagens mais recentes
    ultimas = db.session.query(WhatsAppMensagem).join(
        subq,
        (WhatsAppMensagem.numero == subq.c.numero) & 
        (WhatsAppMensagem.recebido_em == subq.c.max_data)
    ).order_by(WhatsAppMensagem.recebido_em.desc()).limit(20).all()
    
    resultado = []
    for msg in ultimas:
        # Tentar encontrar o cliente pelo telefone
        cliente = Cliente.query.filter_by(telefone=msg.numero).first()
        nome = cliente.nome if cliente else msg.numero
        
        resultado.append({
            "numero": msg.numero,
            "nome": nome,
            "mensagem": msg.mensagem,
            "recebido_em": msg.recebido_em.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return jsonify(resultado)


@app.route("/api/clientes/busca")
def buscar_clientes():
    q = request.args.get("q", "").strip()

    if len(q) < 2:
        return jsonify([])

    clientes = Cliente.query.filter(
        or_(
            Cliente.nome.ilike(f"%{q}%"),
            Cliente.telefone.ilike(f"%{q}%")
        )
    ).limit(20).all()

    return jsonify([
        {
            "id": c.id,
            "nome": c.nome,
            "telefone": c.telefone
        }
        for c in clientes
    ])

# busca histórico por número (usa numero como string)
@app.route("/canais/<string:numero>/mensagens")
def carregar_mensagens(numero):
    # opcional: normalizar numero (remover espaços/+ etc.)
    numero_norm = numero.replace("+", "").replace(" ", "").strip()
    # busca por número exato ou por sufixo (últimos 8 e 6 dígitos) para tolerância a formatos
    s6 = numero_norm[-6:] if len(numero_norm) >= 6 else None
    s8 = numero_norm[-8:] if len(numero_norm) >= 8 else None
    from sqlalchemy import or_
    query = WhatsAppMensagem.query
    filters = [WhatsAppMensagem.numero == numero_norm]
    if s8:
        filters.append(WhatsAppMensagem.numero.like(f"%{s8}"))
    if s6:
        filters.append(WhatsAppMensagem.numero.like(f"%{s6}"))

    msgs = query.filter(or_(*filters)).order_by(WhatsAppMensagem.recebido_em.asc()).all()
    mensagens_list = []
    for m in msgs:
        mensagens_list.append({
            "id": m.id,
            "remetente": m.remetente,
            "mensagem": m.mensagem,
            "hora": m.recebido_em.strftime("%Y-%m-%d %H:%M:%S")
        })
    # também devolve nome do cliente (se existir)
    cliente = Cliente.query.filter_by(telefone=numero_norm).first()
    nome = cliente.nome if cliente else numero_norm
    return jsonify({"cliente": {"numero": numero_norm, "nome": nome}, "mensagens": mensagens_list})

@app.route("/canais/<string:numero>/deletar", methods=["DELETE"])
def deletar_conversa(numero):
    """
    Deleta todas as mensagens de uma conversa.
    """
    numero_norm = numero.replace("+", "").replace(" ", "").strip()
    
    try:
        # Buscar todas as mensagens do número
        s6 = numero_norm[-6:] if len(numero_norm) >= 6 else None
        s8 = numero_norm[-8:] if len(numero_norm) >= 8 else None
        
        from sqlalchemy import or_
        filters = [WhatsAppMensagem.numero == numero_norm]
        if s8:
            filters.append(WhatsAppMensagem.numero.like(f"%{s8}"))
        if s6:
            filters.append(WhatsAppMensagem.numero.like(f"%{s6}"))
        
        # Deletar mensagens
        WhatsAppMensagem.query.filter(or_(*filters)).delete()
        db.session.commit()
        
        return jsonify({"success": True, "message": "Conversa deletada com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/tickets/<int:ticket_id>/send", methods=["POST"])
def send_message(ticket_id):
    body = request.get_json()
    text = body.get("text")

    ticket = Ticket.query.get_or_404(ticket_id)

    response = requests.post(
        f"https://api.z-api.io/instances/SUA_INSTANCIA/token/SEU_TOKEN/send-text",
        json={
            "phone": ticket.contact_phone,
            "message": text
        }
    )

    msg_id = response.json().get("messageId")

    msg = Message(
        ticket_id=ticket.id,
        direction="out",
        body=text,
        external_id=msg_id
    )
    db.session.add(msg)
    db.session.commit()

    socketio.emit(
        "ticket_update",
        {"ticket_id": ticket.id},
        broadcast=True
    )

    return {"sent": True}


@app.route("/produtos")
def produtos():
    # página principal do controle de produtos
    return render_template("produtos.html")

# Endpoint para listar produtos (JSON) - usado pelo frontend para atualizar lista
@app.route("/api/produtos")
def api_listar_produtos():
    q = request.args.get("q", "").strip()
    query = Produto.query
    if q:
        query = query.filter(Produto.nome.ilike(f"%{q}%"))
    produtos = query.order_by(Produto.nome).all()
    data = []
    for p in produtos:
        data.append({
            "id": p.id,
            "nome": p.nome,
            "descricao": p.descricao,
            "quantidade": p.quantidade,
            "ultima_movimentacao_data": p.ultima_movimentacao_data.strftime("%Y-%m-%d %H:%M:%S") if p.ultima_movimentacao_data else None,
            "ultima_movimentacao_descricao": p.ultima_movimentacao_descricao
        })
    return jsonify({"produtos": data})

# Cadastrar produto (via fetch / form)
@app.route("/api/produtos/add", methods=["POST"])
def api_add_produto():
    dados = request.get_json() or {}
    nome = (dados.get("nome") or "").strip()
    descricao = (dados.get("descricao") or "").strip()
    if not nome:
        return jsonify({"status": "erro", "detalhe": "Nome é obrigatório"}), 400
    if not descricao:
        return jsonify({"status": "erro", "detalhe": "Descrição é obrigatória"}), 400

    # evita duplicados
    if Produto.query.filter_by(nome=nome).first():
        return jsonify({"status": "erro", "detalhe": "Produto com esse nome já existe"}), 400

    p = Produto(nome=nome, descricao=descricao, quantidade=0)
    db.session.add(p)
    db.session.commit()
    return jsonify({"status": "sucesso", "produto": {"id": p.id, "nome": p.nome}}), 201

# Realizar movimentação (entrada/saída)
@app.route("/api/produtos/<int:produto_id>/movimentar", methods=["POST"])
def api_movimentar(produto_id):
    dados = request.get_json() or {}
    tipo = dados.get("tipo")  # 'entrada' ou 'saida'
    quantidade = dados.get("quantidade")
    descricao = (dados.get("descricao") or "").strip()

    if tipo not in ("entrada", "saida"):
        return jsonify({"status": "erro", "detalhe": "Tipo inválido"}), 400
    try:
        quantidade = int(quantidade)
    except Exception:
        return jsonify({"status": "erro", "detalhe": "Quantidade inválida"}), 400
    if quantidade <= 0:
        return jsonify({"status": "erro", "detalhe": "Quantidade deve ser maior que zero"}), 400
    if not descricao:
        return jsonify({"status": "erro", "detalhe": "Descrição (justificativa) é obrigatória"}), 400

    produto = Produto.query.get_or_404(produto_id)

    # valida saída
    if tipo == "saida" and produto.quantidade - quantidade < 0:
        return jsonify({"status": "erro", "detalhe": "Estoque insuficiente"}), 400

    # atualiza quantidade
    if tipo == "entrada":
        produto.quantidade += quantidade
    else:
        produto.quantidade -= quantidade

    # atualiza ultima movimentação
    produto.ultima_movimentacao_data = datetime.utcnow()
    produto.ultima_movimentacao_descricao = descricao

    # registra movimentacao
    mov = Movimentacao(
        produto=produto,
        tipo=tipo,
        quantidade=quantidade,
        descricao=descricao,
        data_registro=datetime.utcnow()
    )
    db.session.add(mov)
    db.session.commit()

    return jsonify({
        "status": "sucesso",
        "produto": {"id": produto.id, "quantidade": produto.quantidade},
        "movimentacao": {"id": mov.id}
    }), 200

# Histórico de movimentações de um produto (GET)
@app.route("/api/produtos/<int:produto_id>/historico")
def api_historico(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    movs = Movimentacao.query.filter_by(produto_id=produto.id).order_by(Movimentacao.data_registro.desc()).all()
    data = []
    for m in movs:
        data.append({
            "id": m.id,
            "tipo": m.tipo,
            "quantidade": m.quantidade,
            "descricao": m.descricao,
            "data_registro": m.data_registro.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify({"produto": {"id": produto.id, "nome": produto.nome}, "movimentacoes": data})

# Excluir produto
@app.route("/api/produtos/<int:produto_id>", methods=["DELETE"])
def api_deletar_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    nome_produto = produto.nome
    
    # Deleta movimentações associadas (cascade)
    Movimentacao.query.filter_by(produto_id=produto_id).delete()
    
    # Deleta produto
    db.session.delete(produto)
    db.session.commit()
    
    return jsonify({"status": "sucesso", "mensagem": f"Produto '{nome_produto}' excluído com sucesso"}), 200

@app.route("/produtos/<int:produto_id>/movimentacoes")
def historico_movimentacoes(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    movimentacoes = Movimentacao.query.filter_by(produto_id=produto.id).order_by(Movimentacao.data.desc()).all()
    return render_template("movimentacoes.html", produto=produto, movimentacoes=movimentacoes)

@app.route("/planner")
def planner():
    # Semana desejada
    week_offset = int(request.args.get("week", 0))
    today = datetime.now().date() + timedelta(weeks=week_offset)

    # Segunda da semana
    monday = today - timedelta(days=today.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]

    # Horários
    horarios = []
    hora_atual = datetime.strptime("08:00", "%H:%M")
    hora_limite = datetime.strptime("20:00", "%H:%M")

    while hora_atual <= hora_limite:
        horarios.append(hora_atual.time())
        hora_atual += timedelta(minutes=30)

    # Eventos da semana
    eventos = PlannerEvento.query.filter(
        PlannerEvento.data >= monday,
        PlannerEvento.data <= monday + timedelta(days=6)
    ).all()

    return render_template(
        "planner.html",
        dias=days,
        horarios=horarios,
        eventos=eventos,
        semana_offset=week_offset
    )

@app.route("/planner/salvar", methods=["POST"])
def salvar_evento():
    tipo = request.form["tipo"]
    cliente = request.form.get("cliente")
    data_str = request.form["data"]
    hora_str = request.form["hora"]
    descricao = request.form.get("descricao")

    # Junta a data + hora corretamente
    data_hora = datetime.strptime(f"{data_str} {hora_str}", "%Y-%m-%d %H:%M")

    novo = PlannerEvento(
        tipo=tipo,
        cliente=cliente,
        data=datetime.strptime(data_str, "%Y-%m-%d").date(),
        hora=datetime.strptime(hora_str, "%H:%M").time(),
        data_hora=data_hora,   # <- AQUI ESTÁ O QUE FALTAVA
        descricao=descricao
    )

    db.session.add(novo)
    db.session.commit()

    return redirect(url_for("planner"))

@app.route("/planner/excluir/<int:id>", methods=["POST"])
def excluir_evento(id):
    evento = PlannerEvento.query.get(id)

    if not evento:
        return "Evento não encontrado", 404

    db.session.delete(evento)
    db.session.commit()

    return redirect(url_for("planner"))

@app.route("/tickets")
def list_tickets():
    tickets = Ticket.query.filter_by(status="open").all()
    return jsonify([
        {
            "id": t.id,
            "contact": t.contact_phone,
            "lastMessage": t.messages[-1].body if t.messages else "",
            "unread": count_unread(t.id)
        }
        for t in tickets
    ])

@app.route("/tickets/<int:ticket_id>/messages")
def ticket_messages(ticket_id):
    msgs = Message.query.filter_by(ticket_id=ticket_id).all()
    return jsonify([
        {
            "direction": m.direction,
            "body": m.body,
            "time": m.created_at.strftime("%H:%M")
        }
        for m in msgs
    ])


# quando criar cliente, emitir novo_contato para atualizar lista (opcional)
def emitir_novo_contato(cliente):
    socketio.emit('novo_contato', {
        'id': cliente.id,
        'nome': cliente.nome,
        'telefone': cliente.telefone
    }, broadcast=True)

requests.post(
  "https://proaristocracy-breathtakingly-indira.ngrok-free.dev/webhook/messages",
  json={"phone":"+5547999471874","text":{"message":"Teste via ngrok"}}
)

if __name__ == "__main__":
    print("✅ Servidor rodando em: http://127.0.0.1:5000")
    # use socketio.run para suportar corretamente socket.io
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)



