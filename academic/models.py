from django.db import models


class Turma(models.Model):
    nome = models.CharField(
        max_length=100, unique=True
    )  # Ex: "2º Ano Técnico - Desenvolvimento de Sistemas"
    serie = models.CharField(max_length=50)
    ano_letivo = models.IntegerField(default=2026)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Aluno(models.Model):
    nome = models.CharField(max_length=255)
    numero_chamada = models.IntegerField(null=True, blank=True)
    ra = models.CharField(max_length=50, unique=True)  # Registro do Aluno
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name="alunos")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.ra})"


class NotaBimestral(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="notas")
    disciplina = models.CharField(max_length=100)
    bimestre = models.IntegerField()  # 1, 2, 3 ou 4
    nota = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    frequencia = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )  # Ex: percentual de presença
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("aluno", "disciplina", "bimestre")

    def __str__(self):
        return f"{self.aluno.nome} - {self.disciplina} (B{self.bimestre}): {self.nota}"
