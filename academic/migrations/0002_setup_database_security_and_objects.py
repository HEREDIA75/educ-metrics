from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("academic", "0001_initial"),
    ]

    operations = [
        # 1. Função de Auditoria para Atualização Automática de timestamps (Corrigida)
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION atualizar_timestamp_modificacao()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS atualizar_timestamp_modificacao CASCADE;",
        ),
        # 2. Trigger para garantir integridade na tabela de notas (Validação de Intervalo 0 a 10)
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION validar_faixa_nota()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.nota IS NOT NULL AND (NEW.nota < 0.0 OR NEW.nota > 10.0) THEN
                    RAISE EXCEPTION 'A nota %.2f é inválida. Deve estar entre 0.0 e 10.0.', NEW.nota;
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS trg_valida_nota ON academic_notabimestral;
            CREATE TRIGGER trg_valida_nota
                BEFORE INSERT OR UPDATE ON academic_notabimestral
                FOR EACH ROW
                EXECUTE FUNCTION validar_faixa_nota();
            """,
            reverse_sql="DROP TRIGGER IF EXISTS trg_valida_nota ON academic_notabimestral;",
        ),
        # 3. View Analítica de Desempenho (Inner Joins Otimizados para Relatórios)
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE VIEW vw_desempenho_alunos AS
            SELECT 
                t.id AS turma_id,
                t.nome AS turma_nome,
                t.serie,
                a.id AS aluno_id,
                a.nome AS aluno_nome,
                a.ra,
                n.disciplina,
                n.bimestre,
                n.nota
            FROM academic_aluno a
            INNER JOIN academic_turma t ON a.turma_id = t.id
            LEFT JOIN academic_notabimestral n ON n.aluno_id = a.id;
            """,
            reverse_sql="DROP VIEW IF EXISTS vw_desempenho_alunos;",
        ),
    ]
