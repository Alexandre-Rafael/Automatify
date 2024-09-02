from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from maquina_turing import MaquinaTuring, carregar_maquina_turing_de_json
from graphviz import Digraph
import json
import os
import random
import tempfile

app = Flask(__name__)
app.secret_key = 'admin'

DATA_FILE = 'data/automatos.json'

def garantir_diretorio_e_arquivo():
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({"AFD": [], "AFN": []}, f, indent=4)

def salvar_resultados_em_json(aceitas_ambos, rejeitadas_ambos):
    resultado = {
        "aceitas_ambos": aceitas_ambos,
        "rejeitadas_ambos": rejeitadas_ambos
    }
    with open('resultado_equivalencia.json', 'w') as f:
        json.dump(resultado, f, indent=4)
    print("Resultados salvos em resultado_equivalencia.json")

def carregar_automatos():
    garantir_diretorio_e_arquivo()
    with open(DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"AFD": [], "AFN": []}

def salvar_automato(tipo, automato):
    automatos = carregar_automatos()
    automatos[tipo].append(automato)
    with open(DATA_FILE, 'w') as f:
        json.dump(automatos, f, indent=4)

def gerar_imagem_automato(estados, alfabeto, transicoes, est_inicial, estados_finais, tipo):
    dot = Digraph(comment=f'{tipo}')
    dot.attr(rankdir='LR')

    for estado in estados:
        shape = 'doublecircle' if estado in estados_finais else 'circle'
        dot.node(estado, shape=shape)

    for estado, trans in transicoes.items():
        for simbolo, prox_estados in trans.items():
            for prox_estado in prox_estados:
                dot.edge(estado, prox_estado, label=simbolo)

    dot.node('', shape='none')
    dot.edge('', est_inicial)

    filename = f'{tipo}_automato'
    dot.render(f'static/{filename}', format='png', cleanup=True)
    return f'{filename}.png'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/criar_automato/<tipo>', methods=['GET', 'POST'])
def criar_automato(tipo):
    etapa = 1
    estados = []
    alfabeto = []
    est_inicial = ''
    estados_finais = []
    transicoes = {}

    if request.method == 'POST':
        if 'salvar_dados' in request.form:
            estados = request.form['estados'].split()
            alfabeto = request.form['alfabeto'].split()
            est_inicial = request.form['est_inicial']
            estados_finais = request.form['estados_finais'].split()

            if est_inicial not in estados:
                erro = "O estado inicial deve estar entre os estados definidos."
                return render_template('criar_automato.html', tipo=tipo, etapa=1, erro=erro, estados=request.form['estados'], alfabeto=request.form['alfabeto'], est_inicial=est_inicial, estados_finais=request.form['estados_finais'])
            for estado in estados_finais:
                if estado not in estados:
                    erro = "Todos os estados finais devem estar entre os estados definidos."
                    return render_template('criar_automato.html', tipo=tipo, etapa=1, erro=erro, estados=request.form['estados'], alfabeto=request.form['alfabeto'], est_inicial=est_inicial, estados_finais=request.form['estados_finais'])

            etapa = 2
            return render_template('criar_automato.html', tipo=tipo, etapa=etapa, estados=estados, alfabeto=alfabeto, est_inicial=est_inicial, estados_finais=estados_finais, transicoes=transicoes)

        elif 'salvar_transicoes' in request.form:
            estados = request.form['estados'].split()
            alfabeto = request.form['alfabeto'].split()
            est_inicial = request.form['est_inicial']
            estados_finais = request.form['estados_finais'].split()

            for estado in estados:
                for simbolo in alfabeto:
                    trans = request.form.get(f'trans_{estado}_{simbolo}')
                    if trans:
                        prox_estados = trans.split()
                        for prox_estado in prox_estados:
                            if prox_estado not in estados:
                                erro = f"A transição {estado} -> {simbolo} leva a um estado inválido: {prox_estado}."
                                return render_template('criar_automato.html', tipo=tipo, etapa=2, erro=erro, estados=estados, alfabeto=alfabeto, est_inicial=est_inicial, estados_finais=estados_finais, transicoes=transicoes)
                        if estado not in transicoes:
                            transicoes[estado] = {}
                        transicoes[estado][simbolo] = prox_estados

            etapa = 3
            automato = {
                "estados": estados,
                "alfabeto": alfabeto,
                "est_inicial": est_inicial,
                "estados_finais": estados_finais,
                "transicoes": transicoes
            }
            salvar_automato(tipo.upper(), automato)
            imagem = gerar_imagem_automato(estados, alfabeto, transicoes, est_inicial, estados_finais, tipo.upper())
            return render_template('criar_automato.html', tipo=tipo, etapa=etapa, imagem=imagem)

    return render_template('criar_automato.html', tipo=tipo, etapa=etapa)

def testar_palavra_afn(afn, palavra):
    est_inicial = afn["est_inicial"]
    estados_finais = afn["estados_finais"]
    transicoes = afn["transicoes"]
    estados_atuais = {est_inicial}

    for simbolo in palavra:
        novos_estados = set()
        for estado in estados_atuais:
            if simbolo in transicoes.get(estado, {}):
                novos_estados.update(transicoes[estado][simbolo])
        if not novos_estados:
            return False
        estados_atuais = novos_estados

    return any(estado in estados_finais for estado in estados_atuais)

def testar_palavra_afd(afd, palavra):
    estado_atual = afd["est_inicial"]
    transicoes = afd["transicoes"]
    estados_finais = afd["estados_finais"]

    for simbolo in palavra:
        if simbolo in transicoes.get(estado_atual, {}):
            estado_atual = transicoes[estado_atual][simbolo][0]
        else:
            return False

    return estado_atual in estados_finais

@app.route('/testar/<tipo>', methods=['GET', 'POST'])
def testar_palavra(tipo):
    automatos = carregar_automatos()
    if request.method == 'POST':
        palavra = request.form["palavra"]
        automato = automatos[tipo.upper()][-1]

        if tipo.upper() == "AFN":
            reconhecida = testar_palavra_afn(automato, palavra)
        else:
            reconhecida = testar_palavra_afd(automato, palavra)

        resultado_teste = f"A palavra '{palavra}' foi {'reconhecida' if reconhecida else 'não reconhecida'}."
        return render_template('testar_palavra.html', tipo=tipo, resultado_teste=resultado_teste)

    return render_template('testar_palavra.html', tipo=tipo)

@app.route('/testar_equivalencia', methods=['GET'])
def testar_equivalencia():
    automatos = carregar_automatos()

    if len(automatos["AFD"]) + len(automatos["AFN"]) >= 2:
        automato1 = None
        automato2 = None

        if len(automatos["AFD"]) >= 2:
            automato1 = automatos["AFD"][-2]
            automato2 = automatos["AFD"][-1]
        elif len(automatos["AFN"]) >= 2:
            automato1 = automatos["AFN"][-2]
            automato2 = automatos["AFN"][-1]
        elif len(automatos["AFD"]) >= 1 and len(automatos["AFN"]) >= 1:
            automato1 = automatos["AFD"][-1]
            automato2 = automatos["AFN"][-1]

        alfabeto = automato1["alfabeto"]
        n_palavras = 50
        max_length = 5

        palavras_geradas = set()
        while len(palavras_geradas) < n_palavras:
            palavra = ''.join(random.choices(alfabeto, k=random.randint(1, max_length)))
            palavras_geradas.add(palavra)
        palavras_geradas = list(palavras_geradas)

        aceitas_ambos = []
        rejeitadas_ambos = []
        for palavra in palavras_geradas:
            resultado_automato1 = testar_palavra_afd(automato1, palavra) if "AFD" in automato1 else testar_palavra_afn(automato1, palavra)
            resultado_automato2 = testar_palavra_afd(automato2, palavra) if "AFD" in automato2 else testar_palavra_afn(automato2, palavra)

            if resultado_automato1 and resultado_automato2:
                aceitas_ambos.append(palavra)
            elif not resultado_automato1 and not resultado_automato2:
                rejeitadas_ambos.append(palavra)

        resultado = "AFN e AFD são equivalentes" if len(aceitas_ambos) + len(rejeitadas_ambos) == n_palavras else "AFN e AFD não são equivalentes"

        return render_template(
            'testar_equivalencia.html',
            resultado=resultado,
            aceitas_ambos=aceitas_ambos,
            rejeitadas_ambos=rejeitadas_ambos
        )
    else:
        erro = "Não há autômatos suficientes para testar a equivalência."
        return render_template('testar_equivalencia.html', erro=erro)

@app.route('/converter_afn_afd', methods=['GET', 'POST'])
def converter_afn_afd():
    automatos = carregar_automatos()
    if request.method == 'POST':
        afn = automatos["AFN"][-1]
        afd_estados = []
        afd_transicoes = {}
        afd_estados_finais = set()
        queue = [(afn["est_inicial"],)]
        visitados = set()

        while queue:
            estados_atuais = queue.pop(0)
            novo_estado = ''.join(estados_atuais)

            if novo_estado not in visitados:
                visitados.add(novo_estado)
                afd_estados.append(novo_estado)

                if any(estado in afn["estados_finais"] for estado in estados_atuais):
                    afd_estados_finais.add(novo_estado)

                for simbolo in afn["alfabeto"]:
                    novos_estados_alcancados = set()
                    for estado in estados_atuais:
                        if simbolo in afn["transicoes"].get(estado, {}):
                            novos_estados_alcancados.update(afn["transicoes"][estado][simbolo])

                    if novos_estados_alcancados:
                        novo_estado_destino = ''.join(sorted(novos_estados_alcancados))
                        if novo_estado not in afd_transicoes:
                            afd_transicoes[novo_estado] = {}
                        afd_transicoes[novo_estado][simbolo] = [novo_estado_destino]
                        queue.append(tuple(sorted(novos_estados_alcancados)))

        afd = {
            "estados": afd_estados,
            "alfabeto": afn["alfabeto"],
            "est_inicial": afn["est_inicial"],
            "estados_finais": list(afd_estados_finais),
            "transicoes": afd_transicoes
        }

        salvar_automato("AFD", afd)
        imagem = gerar_imagem_automato(afd_estados, afn["alfabeto"], afd_transicoes, afn["est_inicial"], list(afd_estados_finais), "AFD")
        return render_template('converter_afn_afd.html', imagem=imagem)

    return render_template('converter_afn_afd.html')

@app.route('/minimizar_afd', methods=['GET', 'POST'])
def minimizar_afd():
    automatos = carregar_automatos()
    if request.method == 'POST':
        afd = automatos["AFD"][-1]
        estados = afd["estados"]
        alfabeto = afd["alfabeto"]
        est_inicial = afd["est_inicial"]
        estados_aceitacao = afd["estados_finais"]
        transicoes = afd["transicoes"]

        def sao_distinguiveis(est1, est2, particao):
            for simbolo in alfabeto:
                prox_est1 = transicoes.get(est1, {}).get(simbolo, [None])[0]
                prox_est2 = transicoes.get(est2, {}).get(simbolo, [None])[0]
                if prox_est1 is None or prox_est2 is None:
                    return True
                if particao.get(prox_est1) != particao.get(prox_est2):
                    return True
            return False

        particao = {estado: str(1) if estado in estados_aceitacao else str(0) for estado in estados}
        alteracao = True

        while alteracao:
            alteracao = False
            novo_grupo = max(map(int, particao.values())) + 1
            for est1 in estados:
                for est2 in estados:
                    if est1 != est2 and particao[est1] == particao[est2]:
                        if sao_distinguiveis(est1, est2, particao):
                            particao[est2] = str(novo_grupo)
                            alteracao = True
                            novo_grupo += 1

        estados_min = set(particao.values())
        d_trans_min = {}
        est_inicial_min = particao[est_inicial]
        estados_aceitacao_min = {particao[estado] for estado in estados_aceitacao}

        for estado, trans in transicoes.items():
            for simbolo, prox_estados in trans.items():
                prox_estado = prox_estados[0]
                if prox_estado is not None:
                    particao_estado = particao[estado]
                    particao_prox_estado = particao[prox_estado]
                    if particao_estado not in d_trans_min:
                        d_trans_min[particao_estado] = {}
                    d_trans_min[particao_estado][simbolo] = [particao_prox_estado]

        afd_min = {
            "estados": list(estados_min),
            "alfabeto": alfabeto,
            "est_inicial": est_inicial_min,
            "estados_finais": list(estados_aceitacao_min),
            "transicoes": d_trans_min
        }

        salvar_automato("AFD", afd_min)
        imagem = gerar_imagem_automato(list(estados_min), alfabeto, d_trans_min, est_inicial_min, list(estados_aceitacao_min), "AFD_Minimizado")
        return render_template('minimizar_afd.html', imagem=imagem)

    return render_template('minimizar_afd.html')

@app.route('/testar_mt', methods=['GET', 'POST'])
def testar_mt():
    resultado = None  # Definido como None por padrão
    erro = None

    if request.method == 'POST':
        if 'mt_arquivo' in request.files and request.files['mt_arquivo'].filename != '':
            mt_arquivo = request.files['mt_arquivo']
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(mt_arquivo.read())
                session['mt_arquivo_path'] = temp_file.name

        if 'mt_arquivo_path' in session:
            palavra_entrada = request.form['palavra_entrada']
            try:
                mt = carregar_maquina_turing_de_json(session['mt_arquivo_path'])
                resultado_execucao = mt.executar(palavra_entrada)

                resultado = {
                    "aceito": "Sim" if resultado_execucao['aceito'] else "Não",
                    "resultado_fita": resultado_execucao['resultado_fita']
                }

            except Exception as e:
                erro = f"Erro ao processar a Máquina de Turing: {e}"

    return render_template('testar_mt.html', resultado=resultado, erro=erro)

if __name__ == "__main__":
    app.run(debug=True)
