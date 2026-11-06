# Sistema de Recarga do RU — Boot2Root (03-ru)

Máquina Boot2Root em container Docker, desenvolvida para trabalho da disciplina de
Segurança Ofensiva. Narrativa: um portal fictício da UnB para recarga de créditos do
Restaurante Universitário (RU), onde o aluno faz upload da foto da carteirinha para
leitura automática do QR Code em vez de digitar a matrícula manualmente.

> Projeto standalone desta disciplina — não é o mesmo evento das máquinas anteriores
> (Margaret, do CTF Pink Hat; Anisio, do CTF WPOS/UnB). Dificuldade alvo: **maior**
> que as duas.

## Status

🚧 Em design/implementação. Ver [`docs/decisoes.md`](docs/decisoes.md) para o estado
atual das decisões técnicas e [`docs/kill-chain.md`](docs/kill-chain.md) para a cadeia
de exploração completa.

## Visão geral da kill chain

| Etapa | Técnica | Resultado |
|---|---|---|
| 1 — Acesso inicial | Command Injection via conteúdo de QR Code decodificado | Shell como `ru_web`, flag 1 |
| 2 — Pivot interno | Enumeração de porta interna + túnel SSH até painel de gerenciamento | Acesso ao painel interno |
| 3 — Exploração de serviço interno | SSRF via campo de endpoint editável no painel | Vazamento de credencial de `operador_caixa`, flag 2 |
| 4 — Escalação de privilégio | Race condition (symlink/TOCTOU) em job de conciliação de caixa rodando como root | Shell root, flag 3 |

Cada etapa usa uma técnica distinta das demais e distinta do que já foi usado nas
máquinas anteriores da disciplina (nenhuma reutiliza sudo-argument-injection).

## Estrutura do repositório

```text
03-ru/
├── deploy/                      # Dockerfile, entrypoint.sh, docker-compose.yml
├── services/
│   ├── portal-publico/          # App Flask pública — upload/leitura de QR Code (porta 8000, exposta)
│   ├── painel-gerenciamento/    # Serviço interno com o campo vulnerável a SSRF (porta 8081, 127.0.0.1)
│   └── admin-api/               # API interna sem autenticação, alvo do SSRF (porta 9090, 127.0.0.1)
├── privesc/                     # Daemon/script de "conciliação noturna de caixa" (root, intervalo 90s)
├── seed/
│   └── qrcodes/                 # QR Codes de exemplo/válidos para teste manual
├── tests/                       # Script de QA/exploit automatizado end-to-end
└── docs/                        # Decisões técnicas, guia de execução, histórico
```

## Como rodar (assim que implementado)

```bash
cd deploy
docker compose up --build -d
```

- Portal público: `http://localhost:8000`
- SSH (para `operador_caixa` após a Etapa 3): `ssh -p 2222 operador_caixa@localhost`

Para derrubar: `docker compose down`.

## Documentação

- [`docs/kill-chain.md`](docs/kill-chain.md) — cadeia de exploração completa, passo a passo, com justificativa de design de cada etapa.
- [`docs/decisoes.md`](docs/decisoes.md) — tabela de decisões técnicas (credencial, portas, usuários, intervalo de cron, etc.) com status e justificativa.
- [`docs/guia-execucao.md`](docs/guia-execucao.md) — passo a passo manual reproduzível para jogar a máquina do zero (a preencher conforme a implementação avança).
- [`docs/checklist-qa.md`](docs/checklist-qa.md) — checklist de validação final antes da entrega.

## Regras de design (resumo)

- Dificuldade vem de raciocínio e encadeamento — nunca de força bruta, arquivos escondidos aleatoriamente ou adivinhação cega.
- Cada vulnerabilidade tem um único caminho intencional de exploração.
- `root` dentro do container nunca significa acesso real ao host (sem `--privileged`, sem `docker.sock` montado, sem mounts sensíveis do host).
- Comentários em código shipado nunca descrevem a vulnerabilidade ou a técnica de exploração.
