# Pomodoro com Conquistas

Aplicação web para estudar com a técnica Pomodoro e ganhar medalhas ao cumprir sessões e metas.
Projeto Integrador Transdisciplinar em Engenharia de Software II.

**Stack:** Python 3 · Flask · SQLAlchemy · PostgreSQL · Pytest · padrão MVC

## Estrutura (MVC)

```
app/
  models/        # Model: regras de dados e validação (Usuario, Materia, SessaoPomodoro, Meta, Conquista...)
  controllers/   # Controller: recebe a requisição e decide o que fazer (auth, timer/sessões, matérias, metas, conquistas, estatísticas)
  templates/     # View: HTML renderizado com Jinja2
  static/css/    # Estilos
  static/js/     # Timer do navegador (timer.js)
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

## Documentação

- [Manual de uso](docs/manual_de_uso.md)
- [Dicionário de dados](docs/dicionario_de_dados.md) e [projeto físico do banco](docs/schema.sql)
- Diagramas: [casos de uso](docs/diagramas/casos_de_uso_pomodoro.png) e [classes](docs/diagramas/diagrama_classes_pomodoro.html)
- [Guia de publicação no Render](docs/guia_de_deploy.md)
- [Testes e laudo de qualidade](docs/testes/README.md)

## Status

- [x] Cadastro, login e logout
- [x] Timer pomodoro e registro de sessões
- [x] Matérias e metas com progresso
- [x] Concessão automática de conquistas
- [x] Estatísticas
- [ ] Testes com usuários e laudo de qualidade
