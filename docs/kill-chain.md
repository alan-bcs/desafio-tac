# Kill Chain — Sistema de Recarga do RU

**Atualizado em:** 10/11/2026. Este documento descreve a cadeia pretendida e identifica o que já foi comprovado em ambiente real.

## Status de implementação

| Etapa | Técnica | Estado comprovado | Falta validar |
|---|---|---|---|
| 1 — Acesso inicial | Command injection via QR Code | Código e testes em camadas registrados anteriormente | Shell real `ru_web` no build final |
| 2 — Enumeração interna | Descoberta do painel e da API | Processos internos em execução; API consultável dentro do container | Descoberta natural por `ru_web` |
| 3 — Movimento lateral | IDOR → chave SSH → `operador_caixa` | API retorna chave; SSH com chave local funcionou; flag 2 lida | Extrair/transferir chave exclusivamente pelo caminho do jogador |
| 4 — Privesc | Symlink TOCTOU | Execução como root confirmada via shell SSH do operador | Leitura da flag root via exploit e teste repetido |

## Etapa 1 — Acesso inicial: command injection no QR Code

1. Jogador acessa o portal público do RU (`http://ALVO:8000`).
2. Enumera o módulo experimental `/beta` e a carteirinha de teste `/carterinha-teste.jpg`.
3. Analisa o QR Code e identifica que conteúdo controlado pode alcançar um comando de shell do fluxo legado.
4. Constrói e envia um QR Code que provoca execução de comando no backend.
5. Obtém shell com privilégios do usuário `ru_web` e lê **flag 1** em `/home/ru_web/user.txt`.

**Status:** desenho e testes de lógica anteriores; ainda não repetido ponta a ponta no container atual.

## Etapa 2 — Enumeração dos serviços internos

6. A partir da shell `ru_web`, o jogador investiga processos, arquivos e serviços HTTP internos.
7. Encontra painel de gerenciamento na porta `8081` e admin-API na porta `9090`, não publicadas no host.
8. Examina o painel/rotas e identifica consultas de operadores. A API pode ser acessada diretamente por HTTP **de dentro do container**; túnel SSH não é requisito para essa etapa.

**Status:** serviços observados em `ps aux` e API consultada dentro do container; falta validar descoberta sem conhecimento prévio das rotas.

## Etapa 3 — IDOR e autenticação SSH

9. `GET http://127.0.0.1:9090/api/v1/operadores` enumera os IDs 1, 2 e 3.
10. `GET /api/v1/operadores/<id>` retorna detalhes sem verificar autorização por objeto.
11. O registro ID 3 (`operador_caixa`) contém `chave_privada`, uma chave OpenSSH ed25519.
12. Jogador salva a chave preservando as quebras de linha, define permissão `0600` e a utiliza para autenticar como `operador_caixa` no SSH.
13. Lê **flag 2** em `/home/operador_caixa/user.txt`.

**Status:** API respondeu com chave privada válida em formato OpenSSH; autenticação SSH com a chave de desenvolvimento funcionou e a flag 2 foi lida. A comparação exata entre chave da resposta e arquivo local e o transporte da chave a partir de `ru_web` ainda devem ser testados.

**Nota de rede:** no laboratório, SSH está publicado em `127.0.0.1:2222` no Kali. Painel e API permanecem internos. Jogadores remotos exigirão configuração de publicação compatível com a plataforma.

## Etapa 4 — Escalação de privilégio por symlink TOCTOU

14. Como `operador_caixa`, o jogador observa `python3 -u /opt/conciliacao.py` executando como root.
15. Verifica que `/opt/conciliacao.py` é legível, `/opt/helper_conciliacao.sh` é protegido (`root:root`, modo `0700`) e `/var/ru/caixa` é gravável pelo grupo `operador_caixa`.
16. O job lê o conteúdo controlável de `/var/ru/caixa/dados.csv`, valida `conciliacao.tmp` com `lstat()` e exige que seja arquivo regular.
17. Após **15 segundos**, reabre o mesmo caminho com `open(..., 'w')`, seguindo eventual symlink colocado após a checagem.
18. O jogador substitui `conciliacao.tmp` por um symlink para `/opt/helper_conciliacao.sh` durante a janela e provoca escrita de conteúdo controlado nesse helper.
19. O job executa `/bin/bash /opt/helper_conciliacao.sh` como root. O teste via SSH gravou `/var/ru/prova_ssh.txt` com `uid=0(root) gid=0(root) groups=0(root)`.
20. O objetivo final do jogador é obter **flag 3** em `/root/root.txt`; a leitura dessa flag via exploit ainda precisa ser registrada.

**Temporização:** há 15 segundos entre verificação e uso, mais `sleep(90)` ao fim de cada iteração; portanto o intervalo entre inícios de ciclos normais é de aproximadamente 105 segundos, não exatamente 90.

## Cuidados antes de entregar

- Remover do script distribuído comentários que revelam explicitamente a TOCTOU.
- Garantir que `ru_web` não leia diretamente a chave SSH e que as flags não estejam acessíveis por caminhos alternativos.
- Recriar a instância após testes que sobrescrevem o helper.
- Testar a kill chain integralmente sem `docker exec` administrativo.
- Evitar distribuir scripts de solução ou material de desenvolvimento contendo flags/chaves junto da máquina destinada aos jogadores.

## Variedade técnica

| Etapa | Vulnerabilidade |
|---|---|
| 1 | Command injection via QR Code |
| 3 | IDOR / ausência de autorização por objeto |
| 4 | Race condition (symlink TOCTOU) |

As três técnicas são distintas e não reutilizam sudo-argument-injection.


## Nota sobre o provisionamento (versão atual)

O par de chaves de `operador_caixa` é gerado automaticamente no build Docker.
A API expõe a chave privada correspondente ao `authorized_keys` do operador,
sem depender de arquivos secretos no repositório. A descoberta inicial da API
ocorre pelo shell `ru_web` dentro do container; SSH forwarding só é opcional
**após** obter a credencial, e não é pré-requisito para a IDOR.
A exploração TOCTOU foi validada anteriormente por execução de `id` como root.
