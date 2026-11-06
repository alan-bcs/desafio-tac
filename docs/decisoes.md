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

## Pendências para fechar durante a implementação

- Caminho exato do arquivo/symlink alvo da race condition da Etapa 4 (ex.: escrita em
  `/etc/cron.d/...` vs. `/root/.ssh/authorized_keys` vs. outro alvo) — decidir ao
  implementar `privesc/`, documentando aqui depois.
- Texto exato do payload/"dica" de homologação no campo vulnerável do painel (Seção
  5.2 das lições anteriores: confirmar a falha, nunca nomear a técnica).
- Conteúdo final do `# TODO` plausível a deixar no código do admin-api e do painel.
