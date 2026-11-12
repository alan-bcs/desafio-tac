# Histórico de Decisões Técnicas — Sistema de Recarga do RU

**Atualizado em:** 10/11/2026. Este documento registra o design implementado e distingue decisões de validações realizadas.

| # | Decisão | Configuração atual | Justificativa / observação |
|---|---|---|---|
| 1 | Credencial da etapa 3 | Chave privada SSH ed25519 em `services/admin-api/dados/chave_operador_caixa.pem` | Vazamento permite autenticação como conta de automação |
| 2 | Acesso à API interna | Consulta HTTP a partir da shell `ru_web`; túnel é opcional | Não requer SSH antes de obter a chave |
| 3 | Intervalo da conciliação | `time.sleep(15)` dentro do job, seguido de `time.sleep(90)` ao final do ciclo | A janela TOCTOU é de 15 s; o início de ciclos normais fica separado por aproximadamente 105 s, mais tempo de processamento |
| 4 | Agendamento | Processo Python em loop iniciado como root pelo `entrypoint.sh` | Não utiliza cron |
| 5 | Race condition | Symlink TOCTOU sobre `/var/ru/caixa/conciliacao.tmp` | Checagem com `lstat()` e reabertura com `open(..., 'w')` após pausa |
| 6 | Destino privilegiado | `/opt/helper_conciliacao.sh`, root:root `0700` | O job root escreve no caminho temporário e depois executa o helper com Bash |
| 7 | Usuário web | `ru_web` | Executa o portal público |
| 8 | Usuário SSH | `operador_caixa` | Conta não privilegiada, UID 1001 no teste |
| 9 | Painel | Porta 8081, interna | Não publicada no Compose |
| 10 | Admin-API | Porta 9090, interna | Não publicada no Compose |
| 11 | Portal | Porta 8000, publicada no host | Entrada do desafio |
| 12 | SSH | Porta 22 interna, publicada como `127.0.0.1:2222` no host | Configuração de teste local; ajustar conforme plataforma de entrega |
| 13 | IDOR | `GET /api/v1/operadores/<id>` sem autorização por objeto | ID 3 devolve campo `chave_privada` |
| 14 | Autenticação SSH | Somente chave pública; login root e autenticação por senha desabilitados na configuração adicionada | `authorized_keys` recebe `chave_operador_caixa.pub` |
| 15 | Flags | Três flags independentes | A terceira é a flag root |

## Flags atuais

| Marco | Arquivo | Valor configurado |
|---|---|---|
| Etapa 1 | `/home/ru_web/user_ru_web.txt` | `FLAG{RU_qr_c0de_nao_e_so_pra_leitura_7f3a1c}` |
| Etapa 3 | `/home/operador_caixa/user_operador.txt` | `FLAG{RU_1d0r_ssh_operador_6b2f9a}` |
| Etapa 4 | `/root/root.txt` | `FLAG{RU_t0ct0u_syml1nk_r00t_9c4e2b}` |

A flag do operador foi lida em uma sessão SSH real. A flag root foi provisionada e sua leitura direta foi negada ao operador; sua recuperação **via exploit** ainda não foi demonstrada no teste relatado.

## Estado de implementação e evidências

### Etapa 1 — Command Injection

O portal e seus testes unitários/de integração Flask constam da versão anterior da documentação. A cadeia de QR Code até uma shell real `ru_web` ainda deve ser revalidada no container atual.

### Etapa 2 — Serviços internos

Os processos de painel (`/opt/painel/app.py`) e API (`/opt/admin-api/app.py`) apareceram em `ps aux`. Uma requisição HTTP feita **de dentro** do container retornou dados do operador 3; no Kali, `127.0.0.1:9090` não respondeu, como esperado para porta não publicada. Falta playtest da descoberta natural dessas rotas por `ru_web`.

### Etapa 3 — IDOR e SSH

A API retorna três operadores em endpoints de listagem/detalhe e, no detalhe do ID 3, inclui a chave privada OpenSSH. Foi gerado um par ed25519 para a conta `operador_caixa`; a chave pública foi instalada em `/home/operador_caixa/.ssh/authorized_keys`. O Dockerfile instala `openssh-server`, o entrypoint inicia `sshd` e o Compose publica `127.0.0.1:2222:22`. Login SSH bem-sucedido como UID 1001 e leitura da flag do operador confirmados. A identidade byte a byte entre resposta da API e arquivo local é esperada pelo código, mas o teste `cmp` sugerido ainda não foi apresentado.

### Etapa 4 — TOCTOU

O job root `/opt/conciliacao.py` lê `/var/ru/caixa/dados.csv`, valida que `conciliacao.tmp` é regular via `lstat()`, espera 15 segundos e reabre o mesmo caminho para escrita. Como `operador_caixa` controla o diretório, pode trocar o arquivo por symlink para `/opt/helper_conciliacao.sh`, que o job executa depois. O teste realizado exclusivamente via shell SSH criou `/var/ru/prova_ssh.txt` com `uid=0(root) gid=0(root) groups=0(root)`. Isso demonstra execução de comandos como root, não uma shell root interativa nem a leitura da flag final.

## Pendências antes de distribuir

1. Recriar o container para restaurar o helper após o teste de overwrite e confirmar estado limpo.
2. Remover os comentários explícitos sobre TOCTOU do script distribuído.
3. Auditar permissões: `ru_web` não deve ler a chave privada diretamente; conferir também caminhos alternativos para as flags.
4. Repetir a exploração da etapa 4 e comprovar recuperação da flag root.
5. Testar a cadeia completa desde a aplicação web, incluindo descoberta do painel/API e extração real da chave.
6. Decidir se o SSH deve ficar acessível pela rede dos jogadores: o binding atual `127.0.0.1:2222` serve ao laboratório local, não necessariamente a jogadores remotos.
7. Revisar a exposição de serviços e flags antes de publicar a imagem ou o repositório. Os valores de flag e a chave privada constam do material de desenvolvimento e não devem ser distribuídos como solução ao jogador.


## Provisionamento de credenciais (atualização)

A chave SSH de `operador_caixa` é **gerada automaticamente no Docker build**
(`ssh-keygen -t ed25519`), em vez de ser copiada do computador do autor.
A privada fica em `/opt/admin-api/dados/chave_operador_caixa.pem` com
permissão `0600`, proprietário root; a pública correspondente é instalada no
`authorized_keys` do operador. A API, iniciada como root, consegue ler a privada
para expô-la pelo endpoint vulnerável. Não commitar `.pem`.
O SSH está publicado em `127.0.0.1:2222` no host para testes locais.
Os serviços HTTP internos usam bind em `127.0.0.1` **dentro do container**.
A etapa 4 foi validada por execução de `id` como root via symlink TOCTOU;
a leitura da flag root e o teste integrado desde o QR Code ainda estão pendentes.
