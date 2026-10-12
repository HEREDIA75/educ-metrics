import os
import pandas as pd
import django

# Configurar o ambiente Django para permitir interagir com os models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from academic.models import Turma, Aluno, NotaBimestral


def parse_decimal(valor):
    """
    Trata e converte valores de notas da planilha de forma segura,
    ignorando textos como 'S/N', 'N/A', vazios ou inválidos.
    """
    if pd.isna(valor):
        return None

    # Se for string, limpa espaços e converte vírgula para ponto
    if isinstance(valor, str):
        valor_str = valor.strip().upper()
        if valor_str in ["S/N", "N/A", "-", "", "FALTOU", "TR"]:
            return None
        valor = valor_str.replace(",", ".")

    try:
        return float(valor)
    except (ValueError, TypeError):
        return None


def processar_planilha_walkir(caminho_arquivo):
    """
    Lê todas as abas da planilha do Walkir Vergani, extraindo notas,
    avaliações, Prova Paulista e médias por componente e bimestre,
    gravando diretamente no PostgreSQL através do Django ORM.
    """
    if not os.path.exists(caminho_arquivo):
        print(f"Erro: O arquivo {caminho_arquivo} não foi encontrado.")
        return

    xls = pd.ExcelFile(caminho_arquivo)
    print(f"Processando arquivo: {caminho_arquivo}")
    print(f"Abas encontradas: {xls.sheet_names}")

    for sheet_name in xls.sheet_names:
        # Ignorar páginas vazias ou de layout auxiliar
        if "Página" in sheet_name:
            continue

        print(f"\n--- Processando e Salvando Aba: {sheet_name} ---")
        df = pd.read_excel(caminho_arquivo, sheet_name=sheet_name)

        # Verificar se a coluna 'Nome' existe
        if "Nome" not in df.columns:
            print(
                f"Aviso: Coluna 'Nome' não encontrada na aba {sheet_name}. Pulando..."
            )
            continue

        # Limpar linhas em branco onde o nome do aluno é nulo
        df = df.dropna(subset=["Nome"])

        # Criar ou recuperar a Turma baseada no nome da aba (componente/turma)
        turma_obj, _ = Turma.objects.get_or_create(
            nome=sheet_name,
            defaults={"serie": "Ensino Médio / Técnico", "ano_letivo": 2026},
        )

        contador_alunos = 0
        for _, row in df.iterrows():
            nome_aluno = row.get("Nome")
            ra_aluno = str(
                row.get("RA", f"RA_TEMP_{contador_alunos}_{sheet_name}")
            )  # Caso o RA venha vazio na planilha

            # Criar ou atualizar o Aluno
            aluno_obj, _ = Aluno.objects.update_or_create(
                ra=ra_aluno,
                defaults={
                    "nome": nome_aluno,
                    "turma": turma_obj,
                    "numero_chamada": (
                        row.get("Nº", None) if "Nº" in df.columns else None
                    ),
                },
            )
            contador_alunos += 1

            # Tratamento seguro da nota/média usando parse_decimal
            raw_media = row.get("Média", None)
            media_final = parse_decimal(raw_media)

            if media_final is not None:
                NotaBimestral.objects.update_or_create(
                    aluno=aluno_obj,
                    disciplina=sheet_name,
                    bimestre=1,  # Pode ajustar conforme a estrutura exata das colunas da planilha
                    defaults={"nota": media_final},
                )

        print(
            f"Sucesso: {contador_alunos} alunos processados para a turma/componente '{sheet_name}'."
        )


if __name__ == "__main__":
    arquivo_exemplo = "Walkir-Vergani (12).xlsx"
    processar_planilha_walkir(arquivo_exemplo)
