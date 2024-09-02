import json

class MaquinaTuring:
    def __init__(self, estados, alfabeto, alfabeto_fita, simbolo_branco, transicoes, estado_inicial, estado_aceitacao, estado_rejeicao):
        self.estados = estados
        self.alfabeto = alfabeto
        self.alfabeto_fita = alfabeto_fita
        self.simbolo_branco = simbolo_branco
        self.transicoes = transicoes
        self.estado_inicial = estado_inicial  # Certifique-se de que este atributo seja corretamente atribuído
        self.estado_aceitacao = estado_aceitacao
        self.estado_rejeicao = estado_rejeicao
        self.fita = {}
        self.posicao_cabecote = 0

    def inicializar_fita(self, palavra_entrada):
        for i, char in enumerate(palavra_entrada):
            self.fita[i] = char
        # Preencher o restante da fita com o símbolo de branco
        self.fita[len(palavra_entrada)] = self.simbolo_branco

    def passo(self):
        simbolo_atual = self.fita.get(self.posicao_cabecote, self.simbolo_branco)
        if (self.estado_atual, simbolo_atual) in self.transicoes:
            proximo_estado, escrever_simbolo, direcao = self.transicoes[(self.estado_atual, simbolo_atual)]
            print(f"Estado atual: {self.estado_atual}, Símbolo atual: {simbolo_atual}")
            print(f"Próximo estado: {proximo_estado}, Escrever: {escrever_simbolo}, Direção: {direcao}")
            self.fita[self.posicao_cabecote] = escrever_simbolo
            self.estado_atual = proximo_estado
            if direcao == 'R':
                self.posicao_cabecote += 1
            elif direcao == 'L':
                self.posicao_cabecote -= 1
            print(f"Fita após passo: {self.obter_resultado_fita()}")
        else:
            print(f"Transição não encontrada para o estado {self.estado_atual} com símbolo {simbolo_atual}")
            return False
        return True

    def executar(self, palavra_entrada):
        # Resetar estado atual e posição do cabeçote para o estado inicial e posição inicial
        self.estado_atual = self.estado_inicial
        self.posicao_cabecote = 0
        self.fita = {}

        print(f"Iniciando execução para a palavra de entrada: {palavra_entrada}")

        self.inicializar_fita(palavra_entrada)
        while self.estado_atual not in [self.estado_aceitacao, self.estado_rejeicao]:
            if not self.passo():
                print("Erro: Transição não encontrada")
                break
        resultado = {
            'aceito': self.estado_atual == self.estado_aceitacao,
            'resultado_fita': self.obter_resultado_fita()
        }
        print(f"Resultado da execução: {resultado}")
        return resultado


    def obter_resultado_fita(self):
        # Converte a fita de volta em uma string
        return ''.join(self.fita[i] for i in range(len(self.fita)))

def carregar_maquina_turing_de_json(caminho_json):
    with open(caminho_json, 'r') as f:
        mt_dados = json.load(f)
    return MaquinaTuring(
        estados=mt_dados["estados"],
        alfabeto=mt_dados["alfabeto"],
        alfabeto_fita=mt_dados["alfabeto_fita"],
        simbolo_branco=mt_dados["simbolo_branco"],
        transicoes={(t[0], t[1]): (t[2], t[3], t[4]) for t in mt_dados["transicoes"]},
        estado_inicial=mt_dados["estado_inicial"],
        estado_aceitacao=mt_dados["estado_aceitacao"],
        estado_rejeicao=mt_dados["estado_rejeicao"]
    )
