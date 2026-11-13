# Ficha de Apresentação do Desafio 🍽️💳

---

### **Nome do Desafio:**
**Sistema de Recarga do RU (03-ru)**

---

### **Sinopse / Contextualização:**
A Diretoria de Gestão do Restaurante Universitário (RU) da Universidade de Brasília (UnB) está prestes a implementar um novo sistema unificado de autoatendimento e recarga de créditos para os campi. A promessa é reduzir as filas quilométricas no horário de pico do almoço através da modernização digital do atendimento aos estudantes.

O portal encontra-se em fase final de homologação técnica e testes de usabilidade com a comunidade acadêmica. Contudo, em meio à pressa para colocar a novidade no ar antes do início do semestre letivo, a equipe de desenvolvimento cometeu deslizes na segregação de ambientes, no controle de permissões e no saneamento de dados manipulados pelos serviços internos de conciliação.

Sua missão como pentester é auditar a segurança desse novo ecossistema: explorar o portal partindo da perspectiva de um usuário externo, descobrir caminhos para a rede interna da operação e escalar privilégios até assumir o controle total (root) da infraestrutura do RU.

*Bom apetite e boa exploração!*

---

### **Nível de Dificuldade Estimado:**
**Médio**  
*(Requer enumeração web metódica, inspeção de serviços internos e análise de lógica de sistemas em Linux).*

---

### **Flags:**
* **Quantidade de Flags:** 3 flags
  * `user_ru_web.txt` (Acesso inicial ao servidor web)
  * `user_operador.txt` (Movimentação lateral para a operação)
  * `root.txt` (Controle administrativo do sistema)
* **Formato Esperado:** `TAC{...}`

---

### **Como Executar o Desafio:**

#### 1. Imagem Docker Oficial:
* **Docker Hub:** `desafiotac/ru-machine:1.0` *(ou ghcr.io/<usuario>/ru-machine:1.0)*
* **Arquitetura:** `linux/amd64`

#### 2. Arquivo `docker-compose.yml` de Distribuição:
Crie um arquivo `docker-compose.yml` com o conteúdo abaixo:

```yaml
services:
  ru-machine:
    image: leanddro13/ru-machine:1.0
    container_name: ru-machine
    ports:
      - "8000:8000"
      - "2222:22"
    restart: unless-stopped
```

#### 3. Inicialização em Comando Único:
```bash
docker compose up -d
```

Após o container subir:
* Acesse o portal em: `http://localhost:8000` *(ou no IP da máquina/VM onde o container estiver rodando)*.
* Serviço SSH disponível na porta: `2222`.

---

### **Regras de Escopo:**
* A exploração deve ocorrer **estritamente pela rede** (portas `8000` e `2222`).
* É proibido o uso de `docker exec`, `docker cp`, inspeção de camadas/imagens no host ou qualquer atalho que ignore a simulação de pentest real.
* Todo o cenário está contido no ambiente do container.
