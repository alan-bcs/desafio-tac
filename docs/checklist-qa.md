# Checklist de QA Final

Validar antes de considerar a máquina pronta para entrega.

## Build e infraestrutura

- [ ] `docker compose up --build -d` sobe sem erros, todos os serviços saudáveis.
- [ ] `docker compose down` derruba limpo.
- [x] Nenhum `--privileged`, `docker.sock` montado, ou mount sensível do host no
      `docker-compose.yml`.
- [x] Scripts de infraestrutura (`entrypoint.sh`, provisionamento) com permissão
      `0700 root:root`.

## Isolamento de rede

- [ ] Painel de gerenciamento (`8081`) e admin-api (`9090`) só respondem em
      `127.0.0.1` dentro do container — inacessíveis da rede externa.
- [ ] Apenas porta `8000` (portal público) e `2222` (SSH) expostas no host.

## Etapa 1 — Command Injection

- [x] Payload sobrevive ao ciclo QR Code → decodificação → shell sem corrupção de
      caracteres especiais (`;`, `|`, `` ` ``, espaços, aspas) — `tests/test_decode_qr.py`.
- [x] Injeção confirmada na lógica do Flask via `app.test_client()` —
      `tests/test_app_client.py`.
- [x] `requirements.txt` do portal instala limpo em venv isolado.
- [ ] **Pendente**: validar em container real (`docker compose up --build` +
      `tests/exploit_etapa1.py`) — não foi possível nesta sessão por bloqueio de
      rede ao Docker Hub (ver `docs/decisoes.md`).
- [ ] Reverse shell cai como `ru_web`, não como root (confirmar no container real).
- [ ] Flag 1 presente e legível em `/home/ru_web/user.txt` (confirmar no container real).

## Etapa 2/3 — Pivot e IDOR

- [ ] Túnel SSH/pivot para alcançar a API interna (`9090`) ou painel restrito funciona conforme o planejado (pendente container real).
- [x] Endpoint vulnerável a IDOR permite consultar registros/perfis de outros usuários sem validar o token/sessão do requisitante (`tests/test_idor_logica.py`).
- [x] Enumeração de identificadores (IDs sequenciais) expõe a chave/credencial de `operador_caixa` (`tests/test_idor_logica.py` e `tests/test_painel_client.py`).
- [ ] Chave SSH vazada funciona para autenticar como `operador_caixa` (pendente setup do sshd no container).
- [ ] Flag 2 presente e legível em `/home/operador_caixa/user.txt`.

## Etapa 4 — Race condition

- [ ] Ciclo completo testado de ponta a ponta: plantar symlink → aguardar execução
      (90s) → confirmar escalada.
- [ ] Processo roda como root e herda PATH/ambiente esperado (sem falha silenciosa).
- [ ] Exploit é reproduzível de forma consistente (não depende de timing
      excessivamente apertado).
- [ ] Flag 3 (root) presente e legível em `/root/root.txt`.

## Código e documentação

- [x] Nenhum comentário no código shipado descreve a vulnerabilidade ou a técnica de
      exploração (no máximo `# TODO` genérico e plausível).
- [ ] Eventuais dicas confirmam a existência de uma falha, sem nomear a técnica.
- [ ] Flags consistentes entre filesystem da imagem, script de QA (`tests/`), e
      qualquer metadado de plataforma.
- [x] README, kill-chain, decisões e guia de execução atualizados e consistentes
      entre si.

## Variedade de técnica

- [x] Confirmado: Command Injection, IDOR e Race Condition são tecnicamente distintas
      entre si.
- [x] Confirmado: nenhuma reutiliza sudo-argument-injection (técnica de
      Margaret/Anisio).
