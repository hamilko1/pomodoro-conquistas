# Dicionário de dados

SGBD: **PostgreSQL 14+**. Projeto físico completo em [`schema.sql`](schema.sql).
Todos os instantes (`TIMESTAMP`) são gravados em **UTC**; a aplicação converte para o horário de Brasília ao exibir e ao agrupar por dia.

## Visão geral dos relacionamentos

| Relação | Cardinalidade | Regra de exclusão |
|---|---|---|
| `usuarios` → `materias` | 1 : N | Excluir o usuário exclui suas matérias (`CASCADE`) |
| `usuarios` → `sessoes_pomodoro` | 1 : N | `CASCADE` |
| `usuarios` → `metas` | 1 : N | `CASCADE` |
| `materias` → `sessoes_pomodoro` | 1 : N (opcional) | Excluir a matéria mantém a sessão, com `materia_id` nulo (`SET NULL`) |
| `materias` → `metas` | 1 : N (opcional) | A aplicação apaga as metas abertas da matéria e mantém as cumpridas (`SET NULL`) |
| `usuarios` ↔ `conquistas` | N : N | Tabela associativa `usuarios_conquistas`; `CASCADE` nos dois lados |

## `usuarios`

| Coluna | Tipo | Nulo | Restrições | Descrição |
|---|---|---|---|---|
| `id` | SERIAL | não | PK | Identificador |
| `nome` | VARCHAR(100) | não | | Nome de exibição |
| `email` | VARCHAR(150) | não | UNIQUE | E-mail de login (gravado em minúsculas) |
| `senha_hash` | VARCHAR(255) | não | | Hash da senha (Werkzeug); a senha nunca é armazenada |
| `data_cadastro` | TIMESTAMP | não | padrão: agora | Quando a conta foi criada |

Domínio: senha com no mínimo 8 caracteres (validado na aplicação).

## `materias`

| Coluna | Tipo | Nulo | Restrições | Descrição |
|---|---|---|---|---|
| `id` | SERIAL | não | PK | Identificador |
| `usuario_id` | INTEGER | não | FK → `usuarios.id` | Dono da matéria |
| `nome` | VARCHAR(80) | não | UNIQUE (`usuario_id`, `nome`) | Nome da matéria (único por usuário; a aplicação também ignora maiúsculas/minúsculas) |

## `sessoes_pomodoro`

| Coluna | Tipo | Nulo | Restrições | Descrição |
|---|---|---|---|---|
| `id` | SERIAL | não | PK | Identificador |
| `usuario_id` | INTEGER | não | FK → `usuarios.id` | Quem fez o ciclo |
| `materia_id` | INTEGER | sim | FK → `materias.id` | Matéria estudada (opcional) |
| `inicio` | TIMESTAMP | não | índice (`usuario_id`, `inicio`) | Quando o ciclo começou (hora do servidor) |
| `duracao_min` | SMALLINT | não | CHECK > 0 | Duração planejada, em minutos (1 a 180 na aplicação) |
| `tipo` | VARCHAR(12) | não | CHECK em (`foco`, `pausa_curta`, `pausa_longa`); padrão `foco` | Tipo de ciclo |
| `concluida` | BOOLEAN | não | padrão `FALSE` | Vira `TRUE` só quando o servidor confirma que o tempo passou |

## `metas`

| Coluna | Tipo | Nulo | Restrições | Descrição |
|---|---|---|---|---|
| `id` | SERIAL | não | PK | Identificador |
| `usuario_id` | INTEGER | não | FK → `usuarios.id`; índice | Dono da meta |
| `materia_id` | INTEGER | sim | FK → `materias.id` | Matéria da meta; nulo = vale qualquer matéria |
| `descricao` | VARCHAR(150) | não | | Texto da meta |
| `quantidade_alvo` | SMALLINT | não | CHECK > 0 | Quantidade de pomodoros de foco a concluir (1 a 500 na aplicação) |
| `prazo` | DATE | sim | | Último dia para cumprir (sessões depois do fim desse dia, em Brasília, não contam) |
| `data_criacao` | TIMESTAMP | não | padrão: agora (UTC) | Só contam pomodoros iniciados a partir deste instante |
| `concluida` | BOOLEAN | não | padrão `FALSE` | Meta cumprida |
| `data_conclusao` | TIMESTAMP | sim | | Quando foi cumprida |

O **progresso** da meta não é gravado: é calculado a partir de `sessoes_pomodoro` (focos concluídos, do mesmo usuário, depois de `data_criacao`, na matéria da meta, até o prazo).

## `conquistas` (catálogo)

| Coluna | Tipo | Nulo | Restrições | Descrição |
|---|---|---|---|---|
| `id` | SERIAL | não | PK | Identificador |
| `codigo` | VARCHAR(40) | não | UNIQUE | Código estável (ex.: `primeiro_foco`) |
| `nome` | VARCHAR(60) | não | | Nome da medalha |
| `descricao` | VARCHAR(200) | não | | Como conquistar |
| `icone` | VARCHAR(10) | não | | Emoji da medalha |
| `criterio_tipo` | VARCHAR(20) | não | CHECK em (`total_sessoes`, `sequencia_dias`, `sessoes_no_dia`, `metas_concluidas`, `hora_apos`, `hora_antes`) | Qual regra avaliar |
| `criterio_valor` | SMALLINT | não | CHECK > 0 | Valor a atingir (quantidade, dias ou hora) |

Significado dos critérios:

| `criterio_tipo` | Conquistada quando… |
|---|---|
| `total_sessoes` | o total de focos concluídos chega a `criterio_valor` |
| `sequencia_dias` | já houve `criterio_valor` dias seguidos com ao menos 1 foco |
| `sessoes_no_dia` | já houve `criterio_valor` focos concluídos no mesmo dia |
| `metas_concluidas` | o total de metas cumpridas chega a `criterio_valor` |
| `hora_apos` | algum foco terminou a partir das `criterio_valor` horas |
| `hora_antes` | algum foco terminou antes das `criterio_valor` horas |

## `usuarios_conquistas` (N:N)

| Coluna | Tipo | Nulo | Restrições | Descrição |
|---|---|---|---|---|
| `usuario_id` | INTEGER | não | PK composta; FK → `usuarios.id` | Quem ganhou |
| `conquista_id` | INTEGER | não | PK composta; FK → `conquistas.id` | Qual medalha |
| `data_obtencao` | TIMESTAMP | não | padrão: agora | Quando foi concedida |

A chave composta garante que cada medalha é concedida **uma única vez** por usuário.
