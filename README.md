> **Ideia de máquina CTF: Sistema de Recarga do RU 🍽️💳**
> **Tema/Lore:**
> Um portal web da UnB para recarga de créditos do RU onde o aluno pode fazer upload da foto da carteirinha para ler o QR Code automaticamente (em vez de digitar a matrícula).
> **Vetor de Entrada (User):**
> * O backend usa uma ferramenta/script para extrair os dados do QR Code da imagem enviada.
> * O conteúdo do QR Code é processado sem sanitização pelo sistema operacional (Command Injection).
> * O jogador gera uma imagem de QR Code contendo um comando de reverse shell, faz o upload e ganha acesso inicial como o usuário da aplicação web (`user.txt`).
> 
> 
> **Escalação de Privilégios (Root):**
> A definir
