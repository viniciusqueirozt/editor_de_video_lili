# Rodada 2 — noite de 01 para 02/11/2026: transições sem sobreposição de controles

## Problema e resultado

Em uma montagem longa ajustada à largura do celular, os botões de 44 px de todas as junções se sobrepunham: ocultavam a imagem e dificultavam escolher o par certo. A faixa agora mantém marcadores finos em todos os cortes e apresenta apenas os alvos de toque que cabem sem sobreposição, priorizando o encontro da cena selecionada. O zoom revela mais controles. Um aviso explica como ampliar ou abrir Transições para escolher qualquer corte; nenhum encontro deixa de estar acessível pelo seletor completo.

O painel oferece **Corte anterior/Próximo corte**, posição temporal e número do corte, miniaturas do fim da tomada que sai e do início da que entra, e quantidade de junções sem proteção para aplicação em lote. Assim é possível revisar uma sequência inteira sem tentar acertar botões sobrepostos na timeline. As miniaturas são referências das fontes; o botão de reprodução continua sendo a prévia do resultado composto.

## Regras de uso

- Alvos mantidos em 44 px e separados por pelo menos 48 px, sem reduzir a área de toque para caber mais botões. Nas bordas, posição visual limitada à área disponível; marcador fino conserva o instante exato do corte.
- Todos os cortes continuam no seletor. Navegação anterior/próximo respeita os limites, proteção e gravação em andamento.
- Trocar de corte descarta o rascunho não aplicado; isso é informado no painel. Explorar o catálogo ou navegar não grava revisão/histórico. Aplicar e Cancelar mantêm os comportamentos existentes.
- As duas miniaturas só são recriadas ao trocar projeto/revisão/par; arrastar a duração não dispara repetidamente extração de quadros.
- Abertura aguardando fila não migra para outro projeto. Painel antigo fica indisponível após revisão/projeto alterados; salvamento agora também passa a revisão ao comando enfileirado, evitando aplicar um pedido que ficou desatualizado enquanto aguardava.
- Botões de fechar e Escape ficam bloqueados durante salvamento, para não dar a impressão de que Cancelar desfez um comando já enviado. Estilos e navegação também não mudam durante esse período.
- Mensagem de conflito da fila usa alteração cancelada, pois a mesma proteção atende áudio e transições.

Não foram acrescentados estilos de transição nesta rodada: dissolução, preto/branco e corte seco continuam os existentes. Regra de duração, áudio, montagem aprovada, originais e renderizador permanecem preservados. Este pacote corrige seleção/aplicação dos efeitos antes de ampliar o catálogo.

## Referências revisitadas

Revisitados F11/F12/F13 e critérios P07 do estudo CapCut Mobile já registrado. A [ajuda oficial, seção Mobile](https://www.capcut.com/help/transitions-in-capcut) foi consultada em 02/11/2026: descreve acesso entre dois clipes, seleção e duração/confirmação; também cita dificuldade de enxergar o controle em zoom distante. A distribuição adaptativa dos alvos, navegação por cortes, miniaturas e proteção de revisão são soluções próprias da Lili. Não se atribui esse layout ao CapCut nem se afirma ter revisto vídeos nesta rodada.

Também aplicada a skill mobile-native: alvos de toque, fontes dos inputs preservadas, sem detectar aparelho pelo user agent, sem desativar zoom. A ausência de validação física é mantida explicitamente abaixo.

## Testes

Passaram **24 arquivos JavaScript**, um novo com funções reais do painel, disposição dos marcadores e fila de comandos real. Casos: 20 cenas em zoom distante e próximo, prioridade da seleção, espaçamento/bordas, ausência de duplicação ao redesenhar, acesso às 19 junções, limites, miniaturas escapadas, cache durante o slider, proteção, referência inválida, projeto/revisão alterados, espera na fila e bloqueio de Cancelar durante gravação.

Passaram **10 testes Python focados existentes**: nove de transições e uma integração com exportação/prévia sintética, pixels, duração e som medidos. Não somar repetições nem apresentar essa execução como suíte Python completa. Sintaxe e diff revisados. Nenhuma chamada real de IA ou mídia pessoal nos testes.

Validação visual desktop e Safari real continuam pendentes. A disposição geométrica foi verificada em testes de código/DOM simulado; isso não comprova comportamento do Safari nem leitura visual das novas miniaturas/botões. Runtime de controle desktop esteve indisponível nas tentativas anteriores, sem nova alegação de teste de janela nesta rodada.

## Estado e continuação

Frontend servido pelo editor atual, compatível com a capacidade pair_transitions já ativa; disponível ao atualizar a página. Editor e login remoto consultados saudáveis. Serviços, sessões e dados reais preservados, sem reinício. Checkpoint local para publicação acumulada após segurança/extra. Backend da rodada 1 continua pendente de ativação coordenada no fechamento.

Próximo pacote às 01h55: após consultar a janela renovada e a esteira, avançar uma lacuna de edição concluível, priorizando ampliação de transições realmente renderizáveis ou recursos de montagem. Não ativar Concat nem copiar código AGPL enquanto a decisão de reutilização permanecer pendente. Segurança/acesso continua às 03h55; finalizar o ciclo antes das 5h.
