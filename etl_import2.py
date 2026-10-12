import os
import pandas as pd
import django

# Configurar o ambiente Django para interagir com os models
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
    Lê a planilha do Walkir Vergani e grava no PostgreSQL.
    """
    if not os.path.exists(caminho_arquivo):
        print(f"Erro: O arquivo {caminho_arquivo} não foi encontrado.")
        return

    xls = pd.ExcelFile(caminho_arquivo)
    print(f"\n[Walkir Vergani] Processando arquivo: {caminho_arquivo}")

    for sheet_name in xls.sheet_names:
        if "Página" in sheet_name:
            continue

        print(f"--- Processando Aba (Walkir): {sheet_name} ---")
        df = pd.read_excel(caminho_arquivo, sheet_name=sheet_name)

        if "Nome" not in df.columns:
            print(
                f"Aviso: Coluna 'Nome' não encontrada na aba {sheet_name}. Pulando..."
            )
            continue

        df = df.dropna(subset=["Nome"])

        turma_obj, _ = Turma.objects.get_or_create(
            nome=f"Walkir - {sheet_name}",
            defaults={"serie": "Ensino Médio / Técnico", "ano_letivo": 2026},
        )

        contador_alunos = 0
        for _, row in df.iterrows():
            nome_aluno = row.get("Nome")
            ra_aluno = str(row.get("RA", f"RA_WALKIR_{contador_alunos}_{sheet_name}"))

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

            raw_media = row.get("Média", None)
            media_final = parse_decimal(raw_media)

            if media_final is not None:
                NotaBimestral.objects.update_or_create(
                    aluno=aluno_obj,
                    disciplina=sheet_name,
                    bimestre=1,
                    defaults={"nota": media_final},
                )

        print(f"Sucesso: {contador_alunos} alunos processados.")


def processar_planilha_frugoli(caminho_arquivo):
    """
    Lê a planilha da Escola Maria José da Penha Frugoli e grava no PostgreSQL.
    """
    if not os.path.exists(caminho_arquivo):
        print(f"Erro: O arquivo {caminho_arquivo} não foi encontrado.")
        return

    xls = pd.ExcelFile(caminho_arquivo)
    print(f"\n[Maria José Frugoli] Processando arquivo: {caminho_arquivo}")
    print(f"Abas encontradas: {xls.sheet_names}")

    for sheet_name in xls.sheet_names:
        if "Página" in sheet_name:
            continue

        print(f"--- Processando Aba (Frugoli): {sheet_name} ---")
        df = pd.read_excel(caminho_arquivo, sheet_name=sheet_name)

        # Ajuste caso a coluna de nome tenha pequenas variações (ex: 'Nome do Aluno')
        coluna_nome = (
            "Nome"
            if "Nome" in df.columns
            else [c for c in df.columns if "nome" in str(c).lower()]
        )
        if not coluna_nome:
            print(
                f"Aviso: Coluna de identificação de nome não encontrada na aba {sheet_name}. Pulando..."
            )
            continue

        if isinstance(coluna_nome, list):
            coluna_nome = coluna_nome[0]

        df = df.dropna(subset=[coluna_nome])

        turma_obj, _ = Turma.objects.get_or_create(
            nome=f"Frugoli - {sheet_name}",
            defaults={"serie": "Ensino Fundamental / Médio", "ano_letivo": 2026},
        )

        contador_alunos = 0
        for _, row in df.iterrows():
            nome_aluno = row.get(coluna_nome)
            ra_aluno = str(row.get("RA", f"RA_FRUGOLI_{contador_alunos}_{sheet_name}"))

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

            # Procura por colunas de média ou notas genéricas
            raw_media = row.get("Média", row.get("Nota Final", None))
            media_final = parse_decimal(raw_media)

            if media_final is not None:
                NotaBimestral.objects.update_or_create(
                    aluno=aluno_obj,
                    disciplina=sheet_name,
                    bimestre=1,
                    defaults={"nota": media_final},
                )

        print(f"Sucesso: {contador_alunos} alunos processados.")


if __name__ == "__main__":
    # Processar ambas as escolas
    processar_planilha_walkir("Walkir-Vergani (12).xlsx")
    processar_planilha_frugoli("Maria Jose da Penha Frugoli Professora3.xlsx")
