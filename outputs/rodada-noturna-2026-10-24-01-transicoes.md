# Noite de 24 para 25/10/2026 — rodada 1: transições entre cenas

## Resultado

Duas novas passagens visuais na junção de duas cenas: **por preto** e **por branco**, com corte seco para remover. O controle fica no encontro dos clipes e também no botão Transições, que permite escolher o par mesmo quando a linha do tempo está muito reduzida.

O painel oferece cartões visuais, duração com número legível e reprodução limitada ao encontro. A prévia é um rascunho local: escolher estilo, mexer no controle ou reproduzir não grava comandos. Aplicar salva uma alteração, com Desfazer/Refazer; Cancelar e fechar descartam a experiência e restauram o cursor anterior. No layout estreito, Aplicar/Cancelar permanecem visíveis enquanto o conteúdo interno pode rolar.

## Regra de tempo e proteção

- Metade da duração atua antes do corte e metade depois. Não há sobreposição, remoção ou criação de quadros na montagem; os cortes originais permanecem. Não é dissolução entre imagens, que segue pendente.
- Duração entre 0,1 e 3 segundos, limitada pela menor cena na velocidade atual. Duas junções em torno da mesma cena não ocupam mais que a duração disponível.
- Narração, música, legendas e duração total mantêm suas posições; não foi adicionado crossfade de áudio. Títulos da cena passam pela cor, enquanto legendas temporizadas e marca d'água ficam acima, como na exportação.
- O servidor confere adjacência, tipo, duração e proteção das duas cenas antes de gravar. Edições em uma cena vizinha também não podem remover/encurtar indiretamente uma transição ligada a cena protegida; é necessário desproteger. Erro mantém o projeto intacto; a revisão continua obrigatória.
- A transição pertence aos IDs do par, não ao número da cena. Reordenar, remover, duplicar ou dividir pode separar o par: nesse caso a passagem deixa de existir naquela junção, sem migrar para cenas diferentes. Desfazer restaura a escolha anterior. Encurtar/acelerar uma cena limita a duração da passagem ao espaço disponível.
- Projetos e históricos antigos sem o campo de transições continuam abrindo e podem desfazer/refazer.

## Verificação

**133 testes Python passaram**, incluindo nove testes novos: oito de regras/histórico e um de integração com duas exportações reais. A suíte completa foi justificada pela alteração compartilhada do estado, histórico e exportador; as execuções focadas anteriores não são somadas novamente.

As exportações sintéticas por preto e por branco tiveram os pixels medidos antes, no encontro e depois do corte; a duração final e a presença da narração durante o encontro foram verificadas. As regras cobrem comando inválido sem gravação parcial, cenas protegidas, par não adjacente, remoção/reordenação, limite com velocidade, duas junções e histórico legado.

Os **14 arquivos JavaScript** passaram, incluindo curvas das duas metades, velocidade, rascunho sem alteração do projeto, descarte e revisão antiga. Ajustado o DOM simulado do teste de precisão para a nova consulta do catálogo. Sintaxe dos scripts e git diff --check passaram.

Revisão no navegador com projeto isolado de dois vídeos de cor e tom sintéticos: escolher e reproduzir sem salvar, Cancelar, Aplicar, Desfazer e Refazer. A revisão permaneceu 7 durante a experiência e chegou a 10 após Aplicar/Desfazer/Refazer; o vídeo manteve quatro segundos. O slider foi ajustado de 0,50 para 0,51 s; a prévia parou sozinha em aproximadamente 2,45 s, já na segunda cena. Sem erros/avisos no console da demonstração.

Layout conferido também com viewport de 390 × 844 no navegador desktop, com alvos de 44 px e confirmação visível. Isso não equivale a teste no iPhone: **Safari real, gestos e desempenho com gravações grandes permanecem pendentes**.

## Estado de ativação

Preparado e testado no servidor isolado da porta 8770. O servidor real na porta 8765 continua saudável e ainda não anuncia pair_transitions. A interface esconde os controles novos quando essa capacidade não existe, evitando oferecer uma operação a um processo antigo.

Nenhum serviço de produção foi reiniciado nesta rodada. Gateway, sessões, conector, portal, túnel, endereço remoto, originais e montagem aprovada foram preservados; sem uso de mídia pessoal ou chamadas reais de IA.

Checkpoint local de código/testes/documentação ao concluir a rodada. Publicação no GitHub e ativação serão feitas no fechamento da extra, ou após segurança se a extra não ocorrer, conforme o contrato do ciclo. Antes de ativar: conferir jobs, uploads e a identidade do processo; preservar o gateway e as sessões. Não anunciar esta passagem como ativa no editor real até confirmar a capacidade.

## Referências e próxima rodada

Revisitados F11/F12/F14 e P04/P07 do [estudo do CapCut Mobile](capcut-mobile-estudo-interface-funcoes.md). O [guia oficial, seção Mobile](https://www.capcut.com/help/transitions-in-capcut) orienta acesso pela junção, seleção, duração e confirmação. A política de tempo e o rascunho são decisões próprias da Lili, sem atribuí-las ao concorrente.

O render usa [fade do FFmpeg](https://ffmpeg.org/ffmpeg-filters.html#fade), com direção, início, duração e cor definidos pelo par. Não foram baixadas bibliotecas de efeitos de terceiros.

Para 00h55: continuar a aplicação visual de efeitos reversíveis por cena, com comparação e Aplicar/Cancelar, evitando ampliar o formulário antigo. Dissolução e transições com sobreposição exigem uma política de tempo e prévia específica; não improvisar redução da duração ou deslocar a narração aprovada. Aplicar a todas as junções segue pendente. Não repetir a entrega de precisão nem esta passagem por cor.
