# Histórico de Decisões Técnicas

Tabela de decisões fechadas para a máquina "Sistema de Recarga do RU", com
justificativa. Atualizar sempre que uma decisão mudar por feedback de playtesting
(recalibrar tem prioridade sobre defender o plano original).

| # | Decisão | Valor fechado | Justificativa |
|---|---|---|---|
| 1 | Formato da credencial vazada (Etapa 3) | Chave SSH privada | Mais realista para conta de operador de sistema/automação; caminho único de exploração (sem brute force de senha) |
| 2 | Barreira no túnel (Etapa 2) | Sem barreira extra — túnel é opcional, só para visualização | SSRF funciona via `curl` direto do shell de `ru_web`; exigir cookie de sessão seria gating artificial, não realista |
| 3 | Intervalo do job de conciliação (Etapa 4) | 90 segundos | Meio-termo entre esperar demais (2 min) e não dar tempo de reagir (1 min) |
| 4 | Mecanismo de agendamento (Etapa 4) | Daemon/loop simulado (`while true; sleep 90`), supervisionado no `entrypoint.sh` | Cron real tem granularidade mínima de 1 min; daemon dá controle exato de 90s e facilita debug, sem denunciar ao jogador que não é cron real |
| 5 | Tipo de race condition (Etapa 4) | Symlink TOCTOU clássico | Mais rico tecnicamente que overwrite direto; eleva a dificuldade frente a Margaret/Anisio |
| 6 | Quantidade/formato de flags | 3 flags simples, standalone (sem fragmento de gateway) | Trabalho de disciplina, evento diferente de Margaret/Anisio |
| 7 | Usuário da aplicação web | `ru_web` | — |
| 8 | Usuário pivotado via SSH | `operador_caixa` | — |
| 9 | Porta do painel de gerenciamento | `8081`, bind `127.0.0.1` apenas | Não pode vazar para fora do container |
| 10 | Porta do admin-api | `9090`, bind `127.0.0.1` apenas | Não pode vazar para fora do container |
| 11 | Porta do portal público | `8000`, exposta no host via compose | Ponto de entrada do jogador |
| 12 | Porta SSH | `2222` mapeada no host | Usada após a Etapa 3 |
| 13 | Validação do campo de endpoint no painel (Etapa 3) | Bloqueio fraco: recusa string `"localhost"`, não recusa `"127.0.0.1"` | Bypass clássico de SSRF; dá uma camada extra de raciocínio sem tornar a etapa impossível |

## Flags atuais

| Etapa | Local | Valor |
|---|---|---|
| 1 | `/home/ru_web/user.txt` | `FLAG{RU_qr_c0de_nao_e_so_pra_leitura_7f3a1c}` |
| 2 | `/home/operador_caixa/user.txt` | Ainda não definida — depende da configuração do SSH/usuário (ver pendências) |

Definida em `deploy/entrypoint.sh` e usada como valor esperado em
`tests/exploit_etapa1.py`. Atualizar os dois juntos se o valor mudar (regra 5.8).

## Status de implementação

- **Etapa 1 — Command Injection via QR Code: implementada.**
  - Testada em 3 camadas (regra 5.9): lógica de decode isolada
    (`tests/test_decode_qr.py`, ✅ 8/8 payloads sobrevivem ao ciclo QR intactos),
    `app.test_client()` do Flask (`tests/test_app_client.py`, ✅ injection confirmada),
    e `requirements.txt` do portal validado em venv isolado (✅ instala limpo).
  - **Não validada em container real nesta sessão**: o build da imagem
    (`docker compose build`) precisa puxar `python:3.11-slim` do Docker Hub, e a
    rede desta sessão de design bloqueia esse registro por política
    (`403` em `registry-1.docker.io`). Rodar `docker compose up --build -d` em
    `deploy/` e depois `python3 tests/exploit_etapa1.py` num ambiente com acesso
    normal à internet antes de dar a Etapa 1 como fechada.
- **Etapa 3 — SSRF: implementada, de forma standalone (não depende da Etapa 2).**
  - `services/painel-gerenciamento` expõe o campo de endpoint vulnerável
    (`/verificar-integracao`) com a validação fraca descrita na decisão #13.
  - `services/admin-api` expõe `/admin/credenciais` sem autenticação, servindo o
    conteúdo de `dados/chave_operador_caixa.pem` — hoje um **placeholder**, não
    uma chave real (ver pendências).
  - Testada em 2 camadas: lógica isolada contra a admin-api real
    (`tests/test_ssrf_logica.py`, ✅), e `app.test_client()` do painel fazendo a
    SSRF de verdade contra a admin-api rodando como processo real
    (`tests/test_painel_client.py`, ✅ bloqueio de `localhost` confirmado, ✅
    bypass via `127.0.0.1` confirmado, ✅ credencial vazada).
  - Validado visualmente (screenshot) rodando os dois serviços localmente fora
    do Docker — a integração final no Dockerfile/entrypoint compartilhado ainda
    não foi feita (depende da Etapa 2 existir para fazer sentido o container
    único).
  - **Não valida ainda**: acesso SSH real com a chave vazada (isso é
    propositalmente responsabilidade de quem for fazer a Etapa 2 e/ou a parte
    de usuário/SSH da Etapa 4 — ver pendências).
- Etapas 2 e 4: ainda não implementadas.

## Pendências para fechar durante a implementação

- Caminho exato do arquivo/symlink alvo da race condition da Etapa 4 (ex.: escrita em
  `/etc/cron.d/...` vs. `/root/.ssh/authorized_keys` vs. outro alvo) — decidir ao
  implementar `privesc/`, documentando aqui depois.
- Conteúdo final do `# TODO` plausível a deixar no código do admin-api e do painel.
- **Handoff Etapa 3 → Etapa 2/4 (quem for configurar o SSH do `operador_caixa`):**
  1. Gerar o par de chaves SSH real (ex. `ssh-keygen -t ed25519 -f operador_caixa -N ""`).
  2. Substituir o conteúdo de `services/admin-api/dados/chave_operador_caixa.pem`
     pela chave **privada** real (nenhum código muda, só o arquivo).
  3. Criar o usuário `operador_caixa` no container, com `/home/operador_caixa` e
     `~/.ssh/authorized_keys` contendo a chave **pública** correspondente.
  4. Configurar e subir o `sshd` no container, expor a porta `2222:22` no
     `docker-compose.yml` (já deixada comentada em `deploy/docker-compose.yml`).
  5. Criar `/home/operador_caixa/user.txt` com a flag 2 e atualizar a tabela
     "Flags atuais" acima.
  6. Integrar `painel-gerenciamento` e `admin-api` no `Dockerfile`/`entrypoint.sh`
     compartilhado, com bind em `127.0.0.1` apenas (hoje os dois serviços sobem
     soltos, em `0.0.0.0`, só para teste standalone fora do container).
