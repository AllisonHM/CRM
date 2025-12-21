# routes.py
from flask import render_template, request, redirect, url_for, flash
from app import app, db
from models import Cliente
from datetime import datetime

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        email = request.form['email']
        tipo_pessoa = request.form['tipo_pessoa']

        cliente = Cliente(
            nome_completo=nome,
            telefone=telefone,
            email=email,
            tipo_pessoa=tipo_pessoa
        )

        # Pessoa Física
        if tipo_pessoa == "Física":
            cliente.data_nascimento = request.form.get('data_nascimento') or None
            cliente.renda = request.form.get('renda') or None
            cliente.segmento_trabalho = request.form.get('segmento_trabalho') or None
            cliente.endereco_fisica = request.form.get('endereco_fisica') or None

        # Pessoa Jurídica
        elif tipo_pessoa == "Jurídica":
            cliente.data_abertura = request.form.get('data_abertura') or None
            cliente.faturamento = request.form.get('faturamento') or None
            cliente.segmento_empresa = request.form.get('segmento_empresa') or None
            cliente.endereco_juridica = request.form.get('endereco_juridica') or None
            cliente.qtd_funcionarios = request.form.get('qtd_funcionarios') or None

        db.session.add(cliente)
        db.session.commit()

        flash('Cliente cadastrado com sucesso!')
        return redirect(url_for('cadastro'))

    return render_template('cadastro.html')
