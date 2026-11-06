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

## Flags atuais

| Etapa | Local | Valor |
|---|---|---|
| 1 | `/home/ru_web/user.txt` | `FLAG{RU_qr_c0de_nao_e_so_pra_leitura_7f3a1c}` |

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
- Etapas 2, 3 e 4: ainda não implementadas.

## Pendências para fechar durante a implementação

- Caminho exato do arquivo/symlink alvo da race condition da Etapa 4 (ex.: escrita em
  `/etc/cron.d/...` vs. `/root/.ssh/authorized_keys` vs. outro alvo) — decidir ao
  implementar `privesc/`, documentando aqui depois.
- Texto exato do payload/"dica" de homologação no campo vulnerável do painel (Seção
  5.2 das lições anteriores: confirmar a falha, nunca nomear a técnica).
- Conteúdo final do `# TODO` plausível a deixar no código do admin-api e do painel.
