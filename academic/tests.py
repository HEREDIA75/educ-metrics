from django.test import TestCase
from django.db import IntegrityError
from decimal import Decimal
from academic.models import Turma, Aluno, NotaBimestral


class AcademicModelAndDatabaseTests(TestCase):

    def setUp(self):
        # Configuração inicial de dados de teste
        self.turma = Turma.objects.create(
            nome="Turma Teste - 2º Ano", serie="Ensino Médio", ano_letivo=2026
        )
        self.aluno = Aluno.objects.create(
            nome="Estudante de Teste",
            ra="123456789-SP",
            turma=self.turma,
            numero_chamada=10,
        )

    def test_criacao_aluno_e_turma(self):
        """Valida se a turma e o aluno foram criados corretamente."""
        self.assertEqual(self.turma.nome, "Turma Teste - 2º Ano")
        self.assertEqual(self.aluno.turma, self.turma)
        self.assertEqual(str(self.aluno), "Estudante de Teste (123456789-SP)")

    def test_trigger_validacao_nota_valida(self):
        """Valida que notas entre 0 e 10 são aceitas sem erros."""
        nota_obj = NotaBimestral.objects.create(
            aluno=self.aluno, disciplina="Matemática", bimestre=1, nota=Decimal("8.5")
        )
        self.assertEqual(nota_obj.nota, Decimal("8.5"))

    def test_trigger_validacao_nota_invalida(self):
        """Valida que a trigger do banco rejeita notas acima de 10."""
        with self.assertRaises((IntegrityError, Exception)):
            NotaBimestral.objects.create(
                aluno=self.aluno,
                disciplina="Matemática",
                bimestre=1,
                nota=Decimal("11.0"),
            )

    def test_view_analitica_desempenho(self):
        """Valida se a View vw_desempenho_alunos retorna os dados unidos corretamente."""
        NotaBimestral.objects.create(
            aluno=self.aluno,
            disciplina="Programação Back-End",
            bimestre=1,
            nota=Decimal("9.0"),
        )

        # Consulta direta à View criada via migração SQL
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT turma_nome, aluno_nome, disciplina, nota FROM vw_desempenho_alunos WHERE aluno_id = %s",
                [self.aluno.id],
            )
            row = cursor.fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "Turma Teste - 2º Ano")
        self.assertEqual(row[1], "Estudante de Teste")
        self.assertEqual(row[2], "Programação Back-End")
        self.assertEqual(float(row[3]), 9.0)
