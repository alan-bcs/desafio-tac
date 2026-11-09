# Kill Chain — Sistema de Recarga do RU

Documento de referência da cadeia de exploração completa. Estrutura validada; detalhes
de implementação fechados em `decisoes.md`.

## Status de Implementação da Kill Chain

| Etapa | Técnica | Status | Validação / Testes |
|---|---|---|---|
| 1 — Acesso inicial | Command Injection via QR Code | ✅ Implementada | `tests/test_decode_qr.py` e `tests/test_app_client.py` |
| 2 — Pivot interno | Descoberta de serviços internos | 🟡 Em progresso | Serviços integrados ao `Dockerfile` e `entrypoint.sh` |
| 3 — Exploração de serviço interno | IDOR na API administrativa | ✅ Implementada | `tests/test_idor_logica.py` e `tests/test_painel_client.py` |
| 4 — Escalação de privilégio | Race condition (symlink TOCTOU) | ⏳ A implementar | Especificação fechada em `decisoes.md` |

## Etapa 1 — Acesso Inicial (Command Injection via QR Code)

1. Jogador acessa a homepage institucional do RU (`http://localhost:8000`).
2. Faz enumeração com Gobuster e descobre o módulo experimental em `/beta` e o arquivo esquecido `/carterinha-teste.jpg`.
3. Analisa o QR Code da carteirinha com `zbarimg` e descobre o comando de teste deixado pelos desenvolvedores:
   `DISCENTE: CACHORRO|CPF: 000.000.000-00|MATRICULA: 00000000|NÍVEL: graduaCÃO|CURSO: CACHORRO; echo 'Leitura bem sucedida'`
4. Ao enviar a carteirinha de teste em `/beta`, a saída confirma a execução do comando (`Leitura bem sucedida`).
5. Jogador gera um novo QR Code substituindo o `echo` pelo payload de reverse shell.
6. Faz upload da carteirinha maliciosa no `/beta`.
7. Backend decodifica o QR Code e repassa o conteúdo para o script legado sem sanitização via shell.
8. Reverse shell cai no listener do jogador → shell como o usuário da aplicação web (`ru_web`).
9. **Flag 1** em `/home/ru_web/user.txt`.

## Etapa 2 — Enumeração e Pivot até o Painel de Gerenciamento

10. Com shell em `ru_web`, jogador enumera portas internas (`ss -tulpn`) e encontra dois
    serviços HTTP escutando só em `127.0.0.1`:
    - `127.0.0.1:8081` — Painel de Gerenciamento do RU (uso interno da equipe).
    - `127.0.0.1:9090` — API administrativa de operadores.
11. Jogador pode abrir túnel SSH local para visualizar o painel no navegador (não é
    tecnicamente obrigatório — a exploração da Etapa 3 funciona via `curl` direto do
    shell em `ru_web`; o túnel tem valor de enumeração/visualização).
12. No painel, encontra a função "Consulta de Operadores / Turnos", com um campo de ID
    para buscar dados de operadores na API interna.

## Etapa 3 — IDOR (Insecure Direct Object Reference)

13. O jogador descobre a API administrativa (`127.0.0.1:9090`) e lista os operadores
    cadastrados via `curl http://127.0.0.1:9090/api/v1/operadores`, que retorna IDs,
    usuários e cargos (sem credenciais).
14. Ao consultar cada operador individualmente via
    `curl http://127.0.0.1:9090/api/v1/operadores/<id>`, descobre que o endpoint
    retorna o objeto completo — incluindo o campo `chave_privada` — sem qualquer
    controle de autorização (IDOR clássico).
15. Iterando os IDs (1, 2, 3), encontra que o operador com ID 3 (`operador_caixa`)
    possui uma chave SSH privada ed25519 no campo `chave_privada`.
16. O jogador salva a chave SSH num arquivo local, atribui as permissões corretas
    (`chmod 600`) e estabelece conexão SSH
    (`ssh -p 2222 -i chave operador_caixa@localhost`) → **Flag 2** em
    `/home/operador_caixa/user.txt`.

## Etapa 4 — Escalação de Privilégio (Race Condition em job de conciliação)

17. Como `operador_caixa`, jogador enumera o que está rodando/agendado e encontra um
    processo de "conciliação noturna de caixa do RU" rodando como `root`, a cada 90s.
18. O script lê/escreve um arquivo temporário num diretório com permissão aberta, sem
    checagem segura de existência prévia (TOCTOU clássico: checa e depois abre, sem
    `O_NOFOLLOW`/sem resolver link antes).
19. Jogador planta um symlink malicioso nesse diretório antes da próxima execução.
20. O processo roda como root na próxima execução → o symlink é seguido → código/efeito
    controlado pelo jogador acontece com privilégio de root.
21. **Flag 3 (root)** em `/root/root.txt`.

## Variedade de técnica (requisito desta máquina)

| Etapa | Técnica | Distinta de Margaret/Anisio? |
|---|---|---|
| 1 | Command Injection (via conteúdo de QR Code) | Sim |
| 3 | IDOR (Insecure Direct Object Reference) | Sim |
| 4 | Race Condition / symlink TOCTOU | Sim — nenhuma reutiliza sudo-argument-injection |
