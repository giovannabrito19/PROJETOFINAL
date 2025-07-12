import json
from abc import ABC, abstractmethod

class Pessoa:
    def __init__(self, nome, cpf, email):
        self.nome = nome
        self.cpf = cpf
        self.email = email


    def exibir_dados(self):
        print(f'Nome: {self.nome}')
        print(f'CPF: {self.cpf}')
        print(f'Email: {self.email}')


class Consulta:
    def __init__(self, data_hora, paciente, medico, status):
        self.data_hora = data_hora
        self.paciente = paciente
        self.medico = medico
        self.status = status

    def agendar(self):
        self.medico.consultas.append(self)

        self.status = "Agendada"

    def cancelar_consulta(self):
        if self in self.medico.consultas:
            self.medico.consultas.remove(self)

        self.status = "Cancelada"


    def to_dict(self):
        return {
            'data_hora': self.data_hora,
            'paciente': self.paciente.nome,
            'medico': self.medico.nome,
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data, pacientes, medicos):
        paciente = next((p for p in pacientes if p.nome == data["paciente"]), None)
        medico = next((m for m in medicos if m.nome == data["medico"]), None)
        if paciente and medico:
            return cls(data["data_hora"], paciente, medico, data["status"])
        return None



class Paciente(Pessoa):
    def __init__(self, nome, cpf, email):
        super().__init__(nome, cpf, email)


    def infos(self):
        print(f'Nome: {self.nome}')
        print(f'CPF: {self.cpf}')
        print(f"Email: {self.email}")


    def to_dict(self):
        return {
            "nome": self.nome,
            "cpf": self.cpf,
            "email": self.email

        }

    @classmethod
    def from_dict(cls, data, consultas):
        return cls(
            data["nome"],
            data["cpf"],
            data["email"]
        )



class Especialidade:
    def __init__(self, nome):
        self.nome = nome
        self.medicos = []

    def adicionar_medico(self, medico):
        if medico not in self.medicos:
            self.medicos.append(medico)


    def listar_medicos(self):
        print(f"Médicos com especialidade em {self.nome}:")
        for medico in self.medicos:
            print(f"- Dr(a). {medico.nome} (CRM: {medico.crm})")
    
        return {
            "nome": self.nome,
            "medicos": [medico.nome for medico in self.medicos]
        }

    def to_dict(self):
        return {
            "nome": self.nome,
            "medicos": [medico.nome for medico in self.medicos]
        }


    @classmethod
    def from_dict(cls, data):
        return cls(data["nome"])


class Medico(Pessoa):
    def __init__(self, nome, cpf, email, crm, especialidade):
        super().__init__(nome, cpf, email)
        self.crm = crm
        self.especialidade = especialidade
        self.consultas = []

    def listar_consultas(self):
        for consulta in self.consultas:
            print(f"{consulta.data_hora} com {consulta.paciente.nome}")

    def to_dict(self):
        return {
            "nome": self.nome,
            "cpf": self.cpf,
            "email": self.email,
            "crm": self.crm,
            "especialidade": self.especialidade.to_dict()
        }

    @classmethod
    def from_dict(cls, data, especialidades):
        nome_esp = data["especialidade"]["nome"]
        especialidade = next((e for e in especialidades if e.nome == nome_esp), None)
        if not especialidade:
            especialidade = Especialidade(nome_esp)
            especialidades.append(especialidade)
        medico = cls(
            data["nome"],
            data["cpf"],
            data["email"],
            data["crm"],
            especialidade
        )
        especialidade.adicionar_medico(medico)
        return medico

class Pagamento(ABC):
    def __init__(self, valor, data, consulta):
        self.valor = valor
        self.data = data
        self.consulta = consulta

    @abstractmethod
    def processar_pagamento(self):
        pass


class Cartao(Pagamento):
    def __init__(self, valor, data, consulta, numero_cartao):
        super().__init__(valor, data, consulta)
        self.numero_cartao = numero_cartao

    def processar_pagamento(self):
        print(f"Processando pagamento de R${self.valor:.2f} no cartão ****{self.numero_cartao[-4:]}")


class Dinheiro(Pagamento):
    def processar_pagamento(self):
        print(f"Pagamento de R${self.valor:.2f} em dinheiro realizado na data {self.data}")


class Pix(Pagamento):
    def __init__(self, valor, data, consulta, chave_pix):
        super().__init__(valor, data, consulta)
        self.chave_pix = chave_pix

    def processar_pagamento(self):
        print(f"Pagamento de R${self.valor:.2f} via PIX para {self.chave_pix}")

class Usuario:
    def __init__ (self,nome, user, senha):
        self.nome = nome
        self.user = user
        self.senha = senha

    def to_dict(self):
        return {"nome": self.nome, "user": self.user, "senha": self.senha}

    @staticmethod
    def from_dict(data):
        return Usuario(data["nome"], data["user"], data["senha"])
     