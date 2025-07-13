import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from package.models import Paciente, Medico, Consulta, Especialidade, Cartao, Dinheiro, Pix
from package.persistencia import (
    salvar_pacientes, salvar_medicos, salvar_especialidades, salvar_consultas,
    carregar_dados, carregar_consultas, carregar_especialidades, carregar_medicos, carregar_pacientes, salvar_pagamento
)
from package.utilitarios import encontrar_paciente, encontrar_medico

app = Flask(__name__)
app.secret_key = 'sua-chave-secreta-aqui'  # importante para session e flash

# Carregar dados globais uma vez na inicialização
consultas, pacientes, medicos, especialidades = carregar_dados()

CAMINHO_BANCO = 'banco.json'

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        try:
            with open(CAMINHO_BANCO, 'r') as f:
                usuarios = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            usuarios = []

        for usuario in usuarios:
            if usuario['email'].lower() == email.lower() and usuario['senha'] == senha:
                session['email'] = email
                session['tipo'] = usuario['tipo']
                if usuario['tipo'] == 'paciente':
                    # Redireciona para o menu do paciente após login bem-sucedido
                    return redirect(url_for('menu_paciente'))
                else:
                    # Redireciona para o menu do médico após login bem-sucedido
                    return redirect(url_for('menu_medico'))

        erro = "Email ou senha incorretos!"
    return render_template('login.html', erro=erro)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        tipo = request.form['tipo']
        novo_usuario = {"email": email, "senha": senha, "tipo": tipo}
        try:
            with open(CAMINHO_BANCO, 'r') as f:
                usuarios = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            usuarios = []
        usuarios.append(novo_usuario)
        with open(CAMINHO_BANCO, 'w') as f:
            json.dump(usuarios, f, indent=4)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/menu_paciente')
def menu_paciente():
    if 'email' not in session or session.get('tipo') != 'paciente':
        return redirect(url_for('login'))

    return render_template('menu_paciente.html')

@app.route('/menu_medico')
def menu_medico():
    # Verifica se o usuário está logado e se é um médico
    if 'email' not in session or session.get('tipo') != 'medico':
        return redirect(url_for('login'))

    # Para médicos, você também pode querer passar o objeto médico para o template
    medico = next((m for m in medicos if m.email == session['email']), None)
    if not medico:
        flash("Erro: Médico não encontrado na base de dados.")
        return redirect(url_for('logout'))

    return render_template('menu_medico.html', medico=medico)

@app.route('/cadastro_paciente', methods=['GET', 'POST'])
def cadastro_paciente():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        email = request.form['email']
        senha = request.form['senha']  # Supondo que o form tenha esse campo

        paciente = Paciente(nome, cpf, email)
        pacientes.append(paciente)
        salvar_pacientes(pacientes)

        # Agora salvando também no banco.json para login
        try:
            with open(CAMINHO_BANCO, 'r') as f:
                usuarios = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            usuarios = []

        novo_usuario = {"email": email, "senha": senha, "tipo": "paciente"}
        usuarios.append(novo_usuario)

        with open(CAMINHO_BANCO, 'w') as f:
            json.dump(usuarios, f, indent=4)

        return redirect(url_for('login'))

    return render_template('cadastro_paciente.html')


@app.route('/cadastro_medico', methods=['GET', 'POST'])
def cadastro_medico():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        crm = request.form['crm']
        especialidade_nome = request.form['especialidade']
        senha = request.form['senha']  # <-- Corrigido: antes estava pegando a especialidade

        # Verifica se a especialidade já existe
        especialidade = next((e for e in especialidades if e.nome.lower() == especialidade_nome.lower()), None)
        if not especialidade:
            especialidade = Especialidade(especialidade_nome)
            especialidades.append(especialidade)
            salvar_especialidades(especialidades)

        # Cria o médico (com CPF fictício caso não use CPF no formulário)
        medico = Medico(nome=nome, cpf='00000000000', email=email, crm=crm, especialidade=especialidade)
        medicos.append(medico)
        especialidade.adicionar_medico(medico)
        salvar_medicos(medicos)

        # Salvar no banco.json para login
        try:
            with open(CAMINHO_BANCO, 'r') as f:
                usuarios = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            usuarios = []

        novo_usuario = {"email": email, "senha": senha, "tipo": "medico"}
        usuarios.append(novo_usuario)

        with open(CAMINHO_BANCO, 'w') as f:
            json.dump(usuarios, f, indent=4)

        return redirect(url_for('login'))

    return render_template('cadastro_medico.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/voltar_menup')
def voltar_menup():
    return redirect(url_for('menu_paciente'))

@app.route('/voltar_menum')
def voltar_menum():
    return redirect(url_for('menu_medico'))

@app.route('/marcar_consulta')
def marcar_consulta():
    especialidades_nomes = sorted(set(e.nome for e in especialidades))
    return render_template('marcar_consulta.html',
                           especialidades=especialidades_nomes,
                           medicos=medicos)

@app.route('/confirmar_consulta', methods=['POST'])
def confirmar_consulta():
    global consultas, pacientes, medicos, especialidades

    nome_paciente = request.form['paciente']
    nome_medico = request.form['medico']
    data = request.form['data']
    hora = request.form['horario']
    data_hora = f"{data} {hora}"

    paciente = encontrar_paciente(nome_paciente, pacientes)
    medico = encontrar_medico(nome_medico, medicos)

    if not paciente or not medico:
        flash("Paciente ou médico não encontrado.")
        return redirect(url_for('marcar_consulta'))

    # Verifica se o horário está disponível para o médico
    for c in consultas:
        if c.medico.nome == medico.nome and c.data_hora == data_hora and c.status == "Agendada":
            flash("Esse horário já está ocupado para o médico selecionado.")
            return redirect(url_for('marcar_consulta'))

    nova_consulta = Consulta(data_hora, paciente, medico, "Agendada")
    nova_consulta.agendar()
    consultas.append(nova_consulta)
    salvar_consultas(consultas)

    flash("Consulta agendada com sucesso!")
    return redirect(url_for('marcar_consulta'))

@app.route('/consultas_paciente')
def consultas_paciente():
    if 'email' not in session or session.get('tipo') != 'paciente':
        return redirect(url_for('login'))

    paciente = next((p for p in pacientes if p.email == session['email']), None)
    if not paciente:
        flash("Paciente não encontrado.")
        return redirect(url_for('menu_paciente'))

    consultas_pac = [c for c in consultas if c.paciente.nome == paciente.nome]
    return render_template('consultas_paciente.html', consultas=consultas_pac, nome=paciente.nome)

@app.route('/consultas_medico/<nome>')
def consultas_medico(nome):
    medico = encontrar_medico(nome, medicos)
    if not medico:
        flash("Médico não encontrado.")
        return redirect(url_for('marcar_consulta'))

    consultas_med = [c for c in consultas if c.medico.nome == medico.nome]
    return render_template('consultas_medico.html', consultas=consultas_med, nome=medico.nome)

@app.route('/horarios_disponiveis')
def horarios_disponiveis():
    nome_medico = request.args.get('medico')
    data = request.args.get('data')  # yyyy-mm-dd

    consultas, pacientes, medicos, _ = carregar_dados()
    medico = encontrar_medico(nome_medico, medicos)

    # Se faltar info, retorna vazio
    if not medico or not data:
        return jsonify([])

    try:
        dia_semana = datetime.strptime(data, "%Y-%m-%d").weekday()
    except ValueError:
        return jsonify([])

    # Segunda a sexta = 0 a 4
    if dia_semana > 4:
        return jsonify([])

    # Horários fixos: manhã e tarde
    horarios_totais = ["08:00", "09:00", "10:00", "11:00", "12:00",
                       "14:00", "15:00", "16:00", "17:00", "18:00"]

    # Verifica quais horários já estão ocupados
    ocupados = [
        c.data_hora.split()[1] for c in consultas
        if c.medico.nome == medico.nome and c.data_hora.startswith(data) and c.status == "Agendada"
    ]

    # Remove os horários ocupados
    horarios_livres = [h for h in horarios_totais if h not in ocupados]
    return jsonify(horarios_livres)

@app.route('/cancelar_consulta', methods=['GET']) # Esta é a rota que estava faltando!
def cancelar_consulta():
    if 'email' not in session or session.get('tipo') != 'paciente':
        return redirect(url_for('login'))

    paciente_logado = next((p for p in pacientes if p.email == session['email']), None)
    if not paciente_logado:
        flash("Paciente não encontrado.", "error")
        return redirect(url_for('menu_paciente'))

    consultas_agendadas = [
        c for c in consultas
        if c.paciente and c.paciente.email == paciente_logado.email and c.status == "Agendada"
    ]
    
    return render_template('cancelar_consulta.html', consultas_agendadas=consultas_agendadas)


@app.route('/cancelar_consulta_post', methods=['POST'])
def cancelar_consulta_post():
    if 'email' not in session or session.get('tipo') != 'paciente':
        return redirect(url_for('login'))

    paciente_logado = next((p for p in pacientes if p.email == session['email']), None)
    if not paciente_logado:
        flash("Paciente não encontrado.", "error")
        return redirect(url_for('menu_paciente'))

    consulta_index = request.form.get('consulta_id')
    
    if not consulta_index:
        flash("Por favor, selecione uma consulta para cancelar.", "warning")
        return redirect(url_for('cancelar_consulta'))

    try:
        consulta_index = int(consulta_index)
    except ValueError:
        flash("Seleção de consulta inválida.", "error")
        return redirect(url_for('cancelar_consulta'))

    # Re-filtrar as consultas agendadas para o paciente para garantir que o índice é correto
    consultas_do_paciente = [
        c for c in consultas
        if c.paciente and c.paciente.email == paciente_logado.email and c.status == "Agendada"
    ]

    # ESTE É O BLOCO DE LÓGICA QUE DEVE EXISTIR APENAS UMA VEZ
    if 0 <= consulta_index < len(consultas_do_paciente):
        consulta_para_cancelar = consultas_do_paciente[consulta_index]
        
        # Encontre a consulta original na lista global 'consultas'
        for i, c in enumerate(consultas):
            # Cuidado com a comparação de objetos. É melhor comparar IDs ou atributos únicos.
            # Se 'Consulta' tiver um ID único, use-o. Senão, compare data/hora/medico/paciente.
            # Usando atributos para comparação, já que não temos ID único no modelo atual.
            if (c.data_hora == consulta_para_cancelar.data_hora and
                c.medico.nome == consulta_para_cancelar.medico.nome and
                c.paciente.nome == consulta_para_cancelar.paciente.nome and
                c.status == "Agendada"): # Importante: apenas cancelar se ainda estiver agendada
                
                # Chamando o seu método 'cancelar_consulta'
                consultas[i].cancelar_consulta() 
                salvar_consultas(consultas) # Salva as alterações no banco de dados
                flash("Consulta cancelada com sucesso!", "success")
                break
        else:
            flash("Erro: Consulta não encontrada ou já cancelada na base de dados.", "error")
    else:
        flash("Seleção de consulta inválida ou consulta não encontrada.", "error")

    return redirect(url_for('cancelar_consulta'))

def carregar_medicos():
    try:
        with open("medicos.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@app.route("/visualizar_medicos", methods=["GET", "POST"])
def visualizar_medicos():
    medicos = carregar_medicos()

    # Obter todas as especialidades únicas
    especialidades = sorted(set(m['especialidade']['nome'] for m in medicos))  # ✅ certo


    especialidade_selecionada = request.form.get("especialidade")
    if especialidade_selecionada:
        medicos_filtrados = [m for m in medicos if m['especialidade']['nome'] == especialidade_selecionada]

    else:
        medicos_filtrados = []

    return render_template("visualizar_medicos.html",
                           especialidades=especialidades,
                           medicos=medicos_filtrados,
                           selecionada=especialidade_selecionada)


@app.route("/pagamento", methods=["GET", "POST"])
def pagamento():
    if 'email' not in session or session.get('tipo') != 'paciente':
        return redirect(url_for('login'))

    # Pega o paciente pelo e-mail da sessão
    paciente = next((p for p in pacientes if p.email == session['email']), None)

    if not paciente:
        flash("Paciente não encontrado.")
        return redirect(url_for('menu_paciente'))

    # Filtra consultas do paciente logado
    consultas_paciente = [c for c in consultas if c.paciente.email == paciente.email and c.status == "Agendada"]

    if request.method == "POST":
        consulta_index = int(request.form["consulta"])
        forma_pagamento = request.form["forma"]
        data_pagamento = datetime.now().strftime("%d/%m/%Y")

        if 0 <= consulta_index < len(consultas_paciente):
            consulta_escolhida = consultas_paciente[consulta_index]
            valor = 200.0

            if forma_pagamento == "cartao":
                numero_cartao = request.form["numero_cartao"]
                pagamento = Cartao(valor, data_pagamento, consulta_escolhida, numero_cartao)
            elif forma_pagamento == "pix":
                chave_pix = request.form["chave_pix"]
                pagamento = Pix(valor, data_pagamento, consulta_escolhida, chave_pix)
            else:
                flash("Forma de pagamento inválida.")
                return redirect(url_for("pagamento"))

            pagamento.processar_pagamento()
            salvar_pagamento(pagamento)
            consulta_escolhida.status = "Paga"
            salvar_consultas(consultas)
            flash("Pagamento realizado com sucesso!", "success")
            return render_template("pagamento_confirmado.html", pagamento=pagamento)
        else:
            flash("Consulta selecionada inválida.", "error")
            return redirect(url_for("pagamento"))

    return render_template("pagamento.html", consultas=consultas_paciente)


if __name__ == '__main__':
    app.run(debug=True)
