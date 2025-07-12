def encontrar_paciente(nome, pacientes):
    """
    Retorna o objeto paciente cujo nome corresponde ao nome informado.
    """
    for paciente in pacientes:
        if paciente.nome.lower() == nome.lower():  # Ignora diferença de maiúsculas/minúsculas
            return paciente
    return None


def encontrar_medico(nome, medicos):
    """
    Retorna o objeto médico cujo nome corresponde ao nome informado.
    """
    for medico in medicos:
        if medico.nome.lower() == nome.lower():  # Ignora diferença de maiúsculas/minúsculas
            return medico
    return None
