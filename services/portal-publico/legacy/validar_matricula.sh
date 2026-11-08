#!/bin/bash
# Script legado de validação de matrícula, mantido por compatibilidade com o
# sistema acadêmico antigo. Não alterar sem aprovação da equipe de infraestrutura.

MATRICULA="$1"
CURSO="$2"

if [[ "$MATRICULA" =~ ^[0-9]{9}$ ]]; then
    echo "Matrícula ${MATRICULA} validada com sucesso."
else
    echo "Matrícula ${MATRICULA} fora do padrão esperado (9 dígitos). Prosseguindo com validação manual."
fi

if [ -n "$CURSO" ]; then
    echo "Curso informado: ${CURSO}"
fi
