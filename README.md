# Pomodoro com Conquistas

Aplicação web para estudar com a técnica Pomodoro e ganhar medalhas ao cumprir sessões e metas.
Projeto Integrador Transdisciplinar em Engenharia de Software II.

**Stack:** Python 3 · Flask · SQLAlchemy · PostgreSQL · Pytest · padrão MVC

## Estrutura (MVC)

```
app/
  models/        # Model: regras de dados e validação (Usuario, Materia, SessaoPomodoro, Meta, Conquista...)
  controllers/   # Controller: recebe a requisição e decide o que fazer (auth, main)
  templates/     # View: HTML renderizado com Jinja2
  static/css/    # Estilos
tests/           # Testes automatizados (Pytest)
docs/            # Documentação e schema.sql (projeto físico do banco)
config.py        # Configurações (lê o arquivo .env)
run.py           # Ponto de entrada
```

## Como rodar

1. Crie o banco no PostgreSQL:
   ```
   createdb pomodoro
   psql -d pomodoro -f docs/schema.sql
   ```
   (o `schema.sql` já cadastra as conquistas iniciais)

2. Crie o ambiente virtual e instale as dependências:
   ```
   python -m venv venv
   # Windows:  venv\Scripts\activate
   # Linux/Mac: source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure o ambiente: copie `.env.example` para `.env` e ajuste `DATABASE_URL` e `SECRET_KEY`.

4. Inicie a aplicação:
   ```
   flask --app run run --debug
   ```
   Acesse http://127.0.0.1:5000

> Sem PostgreSQL instalado, dá para testar rápido com SQLite:
> defina `DATABASE_URL=sqlite:///dev.db`, rode `flask --app run init-db` e `flask --app run seed`.

## Testes

```
python -m pytest
```

Os testes usam um banco SQLite em memória, então não precisam de PostgreSQL.

## Comandos úteis

| Comando | O que faz |
|---|---|
| `flask --app run init-db` | Cria as tabelas pelos modelos (alternativa ao schema.sql) |
| `flask --app run seed` | Cadastra as conquistas iniciais (sem duplicar) |

## Status

- [x] Cadastro, login e logout
- [ ] Timer pomodoro e registro de sessões
- [ ] Matérias e metas
- [ ] Concessão automática de conquistas
- [ ] Histórico e estatísticas
