# Kill Chain — Sistema de Recarga do RU

Documento de referência da cadeia de exploração completa. Estrutura validada; detalhes
de implementação fechados em `decisoes.md`.

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

7. Com shell em `ru_web`, jogador enumera portas internas (`ss -tulpn`) e encontra um
   serviço HTTP escutando só em `127.0.0.1:8081` — o "Painel de Gerenciamento do RU"
   (uso interno da equipe).
8. Jogador pode abrir túnel SSH local para visualizar o painel no navegador (não é
   tecnicamente obrigatório — o pivot da Etapa 3 também funciona via `curl` direto do
   shell em `ru_web`; o túnel tem valor de enumeração/visualização).
9. No painel, encontra a função "Verificar integração com o Sistema Acadêmico", com um
   campo de endpoint editável (pensado só para testes de homologação, nunca travado).

## Etapa 3 — SSRF até o serviço administrativo oculto

10. Jogador descobre (testando o campo, ou enumerando mais portas internas) um
    terceiro serviço, sem autenticação nenhuma, em `127.0.0.1:9090` — API interna de
    "gerenciamento de operadores", nunca pensada para ser exposta externamente.
11. Jogador usa o campo vulnerável do painel para apontar pra esse serviço:
    `endpoint=http://127.0.0.1:9090/admin/credenciais`
12. O painel do RU faz a requisição por ele (SSRF) e devolve na tela a chave SSH
    privada do usuário `operador_caixa`.
13. Jogador salva a chave, ajusta permissão (`chmod 600`) e acessa via SSH
    (`ssh -p 2222 operador_caixa@localhost -i chave`) → **Flag 2** em
    `/home/operador_caixa/user.txt`.

## Etapa 4 — Escalação de Privilégio (Race Condition em job de conciliação)

14. Como `operador_caixa`, jogador enumera o que está rodando/agendado e encontra um
    processo de "conciliação noturna de caixa do RU" rodando como `root`, a cada 90s.
15. O script lê/escreve um arquivo temporário num diretório com permissão aberta, sem
    checagem segura de existência prévia (TOCTOU clássico: checa e depois abre, sem
    `O_NOFOLLOW`/sem resolver link antes).
16. Jogador planta um symlink malicioso nesse diretório antes da próxima execução.
17. O processo roda como root na próxima execução → o symlink é seguido → código/efeito
    controlado pelo jogador acontece com privilégio de root.
18. **Flag 3 (root)** em `/root/root.txt`.

## Variedade de técnica (requisito desta máquina)

| Etapa | Técnica | Distinta de Margaret/Anisio? |
|---|---|---|
| 1 | Command Injection (via conteúdo de QR Code) | Sim |
| 3 | SSRF | Sim |
| 4 | Race Condition / symlink TOCTOU | Sim — nenhuma reutiliza sudo-argument-injection |
