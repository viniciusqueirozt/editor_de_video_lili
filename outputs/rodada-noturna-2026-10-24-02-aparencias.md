# Noite de 24 para 25/10/2026 — rodada 2: aparências com prévia

## Recursos entregues

O botão **Filtros**, no rodapé da linha do tempo, abre um catálogo da cena escolhida com miniaturas do próprio vídeo. Há seis aparências locais: Original, Suave, Vivo, Editorial, Preto e branco e Mais luz. A opção Atual mantém os valores já salvos e serve de referência; não é um sétimo efeito.

O fluxo separa experimentar de gravar:

- Escolher um cartão muda a imagem da prévia, sem escrever no projeto.
- Intensidade de 0 a 100% mistura os ajustes anteriores com a aparência escolhida. Arrastar repetidamente não acumula correções; 0% preserva o estado salvo e não cria uma alteração vazia.
- Ver antes/Ver ajustado pausa a reprodução para comparar o mesmo quadro. Aplicar fica desabilitado enquanto o usuário observa o estado anterior.
- Quadro central ajuda a avaliar a cor fora das bordas que podem estar em fade/transição. Reproduzir cena toca só a cena selecionada e para nela, sem avançar para a seguinte.
- Aplicar envia um único clip_update, com apenas brilho, contraste e saturação. Desfazer/Refazer recupera a edição. Os demais ajustes, bloco de roteiro, título, áudio e cortes permanecem.
- Cancelar/fechar restaura o cursor anterior e descarta a experiência. Trocar a cena pelo seletor também descarta o rascunho ainda não aplicado.
- Cenas com cor ajustada recebem um indicador discreto na linha do tempo. No painel estreito, Aplicar e Cancelar permanecem visíveis enquanto o catálogo pode rolar.

As miniaturas usam o mesmo cálculo RGB da prévia. A extração respeita o limite de 40 ms reservado pela API no fim do arquivo, inclusive com durações fracionárias e vídeos curtos; abrir o catálogo perto da saída não envia um instante inválido.

## Proteções e comportamento de erro

Uma cena protegida permite experimentar visualmente, mas não aplicar. A API existente continua conferindo proteção e revisão. Rascunho de uma revisão antiga não encobre o estado novo; o painel pede fechar e reabrir. Durante o salvamento os controles de edição ficam bloqueados. Falha não transforma uma prévia em edição salva.

A busca de quadros e a reprodução continuam usando o controle de carregamento. A confirmação aguarda a imagem ficar disponível. O fim da prévia da cena é tratado tanto no avanço normal quanto no evento de encerramento do vídeo, evitando mudar acidentalmente de tomada.

## Escopo e limitações

São **presets de correção de cor da cena inteira**, não uma pilha de efeitos independente. Aplicar grava os valores existentes em Luz e cor. Original restaura esses valores ao padrão e pode substituir correções manuais; a interface explica isso antes de aplicar. Atual/Cancelar não altera as correções, e Desfazer recupera os valores anteriores.

Remover um look de modo independente depois de outras correções, salvar o nome do preset, efeitos em intervalo próprio, camadas, desfoque, LUT, temperatura e grão continuam pendentes. Não foram anunciados como concluídos os critérios completos de F16/F17/F20. Nenhum catálogo pago ou conteúdo do CapCut foi copiado.

## Verificação

- **15 arquivos de testes JavaScript passaram.** O novo teste executa funções e handlers reais com DOM/rede simulados: seis aparências mais Atual, intensidade, não acumulação, comparação, proteção, revisão antiga, falha, troca de cena, envio de um comando, Cancelar, Quadro central, fim da reprodução e miniaturas no limite do arquivo.
- **Três testes Python focados passaram**, dos quais um é novo. O novo teste aplica as seis combinações de cor, confere os demais campos, título, bloco do roteiro, narração e legendas, desfaz/refaz e exporta um vídeo sintético de seis segundos. Os pixels das seis cenas são comparados com o cálculo de cor esperado, com tolerância de conversão/compressão. Os outros dois conferem limites/histórico e a exportação dessaturada já existentes.
- A suíte Python inteira não foi repetida: o backend e o exportador não mudaram nesta rodada. As 133 verificações da rodada anterior não são somadas aos testes novos desta entrega.
- Revisão desktop no projeto sintético da porta 8770: escolher Preto e branco, comparar, reproduzir, descartar, testar intensidade 0/100%, aplicar, desfazer e refazer. A prévia parou em aproximadamente 1,99 s ainda na cena 1, e a comparação não gravou comandos. Revisão 10 preservada durante as experiências, chegando a 13 após Aplicar/Desfazer/Refazer; somente a primeira cena mudou, com duração total de quatro segundos mantida.
- Catálogo aberto em 1,999 s de um arquivo de dois segundos: as sete miniaturas carregaram usando a posição permitida de 1,96 s. Sem erros/avisos no console da demonstração.
- Layout conferido em 320 × 740 e 390 × 844 no navegador desktop. Atalhos e botões de confirmação permaneceram dentro da tela com altura de 44 px. Isso não comprova Safari/iPhone real; aparelho, teclado/gestos e desempenho com gravações grandes continuam pendentes.
- Sintaxe e diff conferidos. Somente mídias e projetos sintéticos nos testes; sem inferências reais de IA, credenciais ou dados pessoais.

## Ativação e publicação

O novo fluxo usa a capacidade color_adjustments já existente. HTTP confirmou servidor real saudável e arquivos atualizados com no-store; o botão fica disponível ao recarregar o editor. Nenhum servidor real, gateway, conector ou túnel foi reiniciado. A produção continua sem pair_transitions da rodada anterior, que aguarda a ativação de backend no fechamento.

Esta rodada cria um checkpoint local de código, testes e documentação. A publicação dos commits no GitHub permanece reservada ao fim da extra — ou da segurança se não houver extra. Contas individuais, nuvem, logo, originais e montagem aprovada não foram alterados.

## Referências e próximo pacote

Revisitados F15/F18/F20 e P04/P06 do [estudo móvel](capcut-mobile-estudo-interface-funcoes.md). A [ajuda oficial, seção Mobile](https://www.capcut.com/help/effectss-not-applying-in-capcut) orienta biblioteca, confirmação e revisão visual; seu suporte a efeitos temporizados não significa que a Lili já os tenha.

Revisitada a transcrição local do [tutorial no iPhone, 22:07–22:41](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=1327s), que separa aparência dos ajustes. A paleta, valores RGB, mistura e fluxo de rascunho são decisões próprias da Lili. Não foram atribuídos ao CapCut esses presets ou algoritmos.

Rodada 3, às 01h55: melhorar o posicionamento de áudio na linha do tempo, avaliando primeiro movimentação de música/narração e aparo da música com prévia e salvamento previsível. Conferir os controles e limites existentes antes de escolher o pacote; não repetir este catálogo nem a rodada de transições. Guardar a publicação para o fechamento do ciclo e reavaliar limites antes de começar.
