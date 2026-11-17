# Publicar no Render (plano gratuito)

O arquivo [`render.yaml`](../render.yaml) na raiz do repositório descreve tudo: o banco PostgreSQL e o site.

## Passo a passo
1. Garanta que o código está no GitHub (`git push`).
2. Crie uma conta em https://render.com e conecte o GitHub.
3. No painel: **New +** → **Blueprint** → escolha o repositório `pomodoro-conquistas` → **Apply**.
4. Aguarde o build e o primeiro deploy (alguns minutos). Ao subir, o próprio comando de inicialização cria as tabelas e cadastra as conquistas.
5. Abra o endereço `https://pomodoro-conquistas.onrender.com` (o nome exato aparece no painel) e crie uma conta de teste.

Variáveis de ambiente (já definidas no `render.yaml`): `DATABASE_URL` (do banco criado), `SECRET_KEY` (gerada pelo Render), `TRUST_PROXY=1` (cookies seguros atrás do HTTPS do Render) e `PYTHON_VERSION`.

## Limitações do plano gratuito
- **O site dorme após ~15 minutos sem acesso** e a primeira visita seguinte leva cerca de 1 minuto para carregar. Abra o endereço uma vez antes de pedir para os colegas testarem, e avise-os da demora inicial.
- **O banco gratuito expira** (as fontes consultadas em 2026 divergem entre 30 e 90 dias; confira o prazo no painel do banco). Faça os testes e grave o vídeo dentro do prazo e não dependa desse banco para guardar dados importantes.
- Se precisar de um banco sem expiração, crie um PostgreSQL gratuito em outro provedor (por exemplo Neon ou Supabase), apague o bloco `databases` do `render.yaml` e, em **Environment**, defina `DATABASE_URL` com a URL do novo banco.

## Atualizações
Cada `git push` na branch `main` dispara um novo deploy automático.
