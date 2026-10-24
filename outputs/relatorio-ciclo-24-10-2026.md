# Ciclo de demonstração da Lili — 24/10/2026

Execução direta autorizada pelo usuário: quatro rodadas de edição, uma de segurança/contas e extra condicional. Rodadas em sequência nesta demonstração, sem limite artificial de tamanho; rotina noturna permanece separada. Percentuais da conta são informados no chat após cada rodada, sem versioná-los.

## Rodada 1 — Entrada e saída suaves por cena

- Controles de entrada/saída para preto em segundos, com zero para desativar. Prévia e exportação aplicam a mesma curva linear, sem mudar a duração da cena ou atrasar a narração. Inclui texto sobreposto.
- Validação impede valores inválidos ou efeitos cuja soma ultrapasse a cena. Cenas protegidas respeitadas; Desfazer recupera ajustes. Dividir preserva a entrada na metade esquerda e a saída na direita, recusando cortes incompatíveis com a duração do efeito.
- Verificação: 15 testes de estado passaram; um teste HTTP/FFmpeg real mediu os quadros escuros nas bordas e a duração preservada; curva da prévia conferida em Node. Dados sintéticos, sem IA real.
- Preparado para o próximo início normal do editor. Controles dependem de capacidade anunciada pelo servidor, preservando compatibilidade com o processo antigo. Não é dissolução entre duas cenas nem cria sobreposição temporal.
