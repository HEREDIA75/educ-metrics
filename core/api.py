from ninja import NinjaAPI, Schema
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.routers.obtain import (
    obtain_pair_router,
)  # Router oficial para obter o token
from typing import List, Optional
from academic.models import Turma, Aluno
from django.db import connection
from django.http import HttpResponse
import csv

api = NinjaAPI(title="EduMetrics PRO API", version="1.0.0")

# Adiciona as rotas de JWT (ex: /api/token/pair e /api/token/refresh) diretamente na API
api.add_router("/token", obtain_pair_router)


# ==========================================
# Health Check (Público)
# ==========================================
@api.get("/health", summary="Verificar status do sistema")
def health_check(request):
    return {"status": "online", "system": "EduMetrics PRO API running successfully"}


# ==========================================
# Schemas
# ==========================================
class TurmaSchema(Schema):
    id: int
    nome: str
    serie: str
    ano_letivo: int


class AlunoSchema(Schema):
    id: int
    nome: str
    ra: str
    numero_chamada: Optional[int] = None
    turma_id: int


class DesempenhoViewSchema(Schema):
    turma_id: Optional[int] = None
    turma_nome: Optional[str] = None
    serie: Optional[str] = None
    aluno_id: Optional[int] = None
    aluno_nome: Optional[str] = None
    ra: Optional[str] = None
    disciplina: Optional[str] = None
    bimestre: Optional[int] = None
    nota: Optional[float] = None


# ==========================================
# Endpoints Protegidos por JWT
# ==========================================
@api.get(
    "/turmas",
    response=List[TurmaSchema],
    auth=JWTAuth(),
    summary="Listar turmas (Protegido)",
)
def listar_turmas(request):
    return Turma.objects.all()


@api.get(
    "/alunos",
    response=List[AlunoSchema],
    auth=JWTAuth(),
    summary="Listar alunos com filtro (Protegido)",
)
def listar_alunos(request, ra: Optional[str] = None):
    queryset = Aluno.objects.all()
    if ra:
        queryset = queryset.filter(ra__icontains=ra)
    return queryset


@api.get(
    "/relatorios/desempenho",
    response=List[DesempenhoViewSchema],
    auth=JWTAuth(),
    summary="Consultar View Analítica com Pesquisa Avançada (Protegido)",
)
def relatorio_desempenho(
    request,
    turma_nome: Optional[str] = None,
    disciplina: Optional[str] = None,
    aluno_nome: Optional[str] = None,
    nota_minima: Optional[float] = None,
):
    """
    Consulta avançada na View PostgreSQL 'vw_desempenho_alunos' com filtros dinâmicos de pesquisa no banco de dados.
    """
    query = """
        SELECT turma_id, turma_nome, serie, aluno_id, aluno_nome, ra, disciplina, bimestre, nota 
        FROM vw_desempenho_alunos 
        WHERE 1=1
    """
    params = []

    if turma_nome:
        query += " AND turma_nome ILIKE %s"
        params.append(f"%{turma_nome}%")

    if disciplina:
        query += " AND disciplina ILIKE %s"
        params.append(f"%{disciplina}%")

    if aluno_nome:
        query += " AND aluno_nome ILIKE %s"
        params.append(f"%{aluno_nome}%")

    if nota_minima is not None:
        query += " AND nota >= %s"
        params.append(nota_minima)

    query += " ORDER BY turma_nome, aluno_nome, disciplina, bimestre"

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return results


@api.get(
    "/relatorios/exportar-csv",
    auth=JWTAuth(),
    summary="Exportar relatório de desempenho em formato CSV",
)
def exportar_csv_desempenho(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        'attachment; filename="relatorio_desempenho_edumetrics.csv"'
    )

    writer = csv.writer(response, delimiter=";")
    writer.writerow(
        [
            "ID Turma",
            "Turma",
            "Série",
            "ID Aluno",
            "Aluno",
            "RA",
            "Disciplina",
            "Bimestre",
            "Nota",
        ]
    )

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT turma_id, turma_nome, serie, aluno_id, aluno_nome, ra, disciplina, bimestre, nota FROM vw_desempenho_alunos"
        )
        for row in cursor.fetchall():
            writer.writerow(row)

    return response
