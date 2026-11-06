# Checklist de QA Final

Validar antes de considerar a máquina pronta para entrega.

## Build e infraestrutura

- [ ] `docker compose up --build -d` sobe sem erros, todos os serviços saudáveis.
- [ ] `docker compose down` derruba limpo.
- [ ] Nenhum `--privileged`, `docker.sock` montado, ou mount sensível do host no
      `docker-compose.yml`.
- [ ] Scripts de infraestrutura (`entrypoint.sh`, provisionamento) com permissão
      `0700 root:root`.

## Isolamento de rede

- [ ] Painel de gerenciamento (`8081`) e admin-api (`9090`) só respondem em
      `127.0.0.1` dentro do container — inacessíveis da rede externa.
- [ ] Apenas porta `8000` (portal público) e `2222` (SSH) expostas no host.

## Etapa 1 — Command Injection

- [ ] Payload sobrevive ao ciclo QR Code → decodificação → shell sem corrupção de
      caracteres especiais (`;`, `|`, `` ` ``, espaços, aspas).
- [ ] `shell=True`/`os.system` embrulha corretamente bashismos se usados
      (`bash -c '...'`).
- [ ] Reverse shell cai como `ru_web`, não como root.
- [ ] Flag 1 presente e legível em `/home/ru_web/user.txt`.

## Etapa 2/3 — Pivot e SSRF

- [ ] Túnel SSH opcional funciona, mas não é obrigatório para completar a etapa.
- [ ] SSRF aceita o endpoint interno e retorna a credencial corretamente formatada.
- [ ] Validação (se houver) do campo de endpoint é consistente com a dificuldade
      pretendida (documentar bypass esperado, se aplicável).
- [ ] Chave SSH vazada funciona para autenticar como `operador_caixa`.
- [ ] Flag 2 presente e legível em `/home/operador_caixa/user.txt`.

## Etapa 4 — Race condition

- [ ] Ciclo completo testado de ponta a ponta: plantar symlink → aguardar execução
      (90s) → confirmar escalada.
- [ ] Processo roda como root e herda PATH/ambiente esperado (sem falha silenciosa).
- [ ] Exploit é reproduzível de forma consistente (não depende de timing
      excessivamente apertado).
- [ ] Flag 3 (root) presente e legível em `/root/root.txt`.

## Código e documentação

- [ ] Nenhum comentário no código shipado descreve a vulnerabilidade ou a técnica de
      exploração (no máximo `# TODO` genérico e plausível).
- [ ] Eventuais dicas confirmam a existência de uma falha, sem nomear a técnica.
- [ ] Flags consistentes entre filesystem da imagem, script de QA (`tests/`), e
      qualquer metadado de plataforma.
- [ ] README, kill-chain, decisões e guia de execução atualizados e consistentes
      entre si.

## Variedade de técnica

- [ ] Confirmado: Command Injection, SSRF e Race Condition são tecnicamente distintas
      entre si.
- [ ] Confirmado: nenhuma reutiliza sudo-argument-injection (técnica de
      Margaret/Anisio).
