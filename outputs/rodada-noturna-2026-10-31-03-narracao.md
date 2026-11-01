# Rodada 3 — aparo não destrutivo da narração · noite de 31/10 para 01/11/2026

## Recursos

O painel **Narração no tempo certo** passa a oferecer entrada e saída no arquivo, além do início na montagem. É possível digitar os tempos, aparar no cursor e voltar a **Usar arquivo inteiro**. Aparar o início avança a entrada e a posição juntas, preservando a sincronização do restante da fala; aparar o fim mantém a entrada. Restaurar o arquivo inteiro mantém a posição na montagem e os fades escolhidos: confira a prévia antes de aplicar.

As experiências ficam no rascunho: Cancelar descarta, Aplicar envia um único comando e Desfazer/Refazer recupera o intervalo. Arquivos originais ficam intactos. A restauração do intervalo inteiro também está disponível para música. Não há divisão da voz em vários blocos nem edição de várias narrações nesta entrega.

Prévia, forma de onda da timeline, limites do ímã, aviso de fala fora do vídeo, fades e redução da música usam a duração do trecho escolhido. Fades maiores que o intervalo impedem o salvamento, com aviso para corrigir. Ajustar volume ou posição depois preserva o intervalo. Projetos/históricos antigos sem entrada/saída continuam usando o arquivo inteiro; não houve migração de projetos reais.

## Correção na exportação

Um teste novo com tons sintéticos reproduziu uma exportação em que a fala começava antes da posição solicitada, embora o filtro de atraso estivesse presente. Foi acrescentada a reconstrução dos timestamps pelo número de amostras depois do atraso, tanto na voz quanto na música. O teste mede o conteúdo selecionado, o silêncio antes/depois, fades e recuperação do volume da música. Não se atribui uma causa upstream comprovada ao FFmpeg nem se promete corrigir todo caso possível de sincronismo.

Referência técnica consultada para os filtros de atraso e timestamps: [documentação oficial de filtros do FFmpeg](https://www.ffmpeg.org/ffmpeg-filters.html). A validação desta implementação usa artefatos realmente exportados; não se baseia apenas na descrição dos filtros.

## Verificação

- **139 testes Python passaram na suíte final**, incluindo dois testes novos: regras/validação atômica/histórico e exportação integrada. A suíte completa foi justificada pela alteração compartilhada no modelo e no renderizador.
- O teste integrado usa vídeo e tons gerados localmente. Mede frequências para confirmar qual trecho foi usado, posição, fades, redução da música, duração final e compatibilidade com narração antiga sem start/end. Confere montagem e bytes do original preservados.
- **19 arquivos JavaScript passaram**. Foram ampliados três arquivos existentes para testar rascunho de narração, compatibilidade com servidor antigo, aparo, prévia e parada no limite, redução musical, restauração, Aplicar/Cancelar, avisos e alvos do ímã. Nenhum arquivo JavaScript novo nesta rodada.
- Antes da correção dos timestamps, o teste novo de áudio falhou de forma intermitente; a primeira suíte também teve timeout em um teste existente com IA simulada. Depois da correção, três execuções focadas do caso novo e o caso de música existente passaram, seguidos da suíte completa sem falhas. Repetições não contam como testes novos. O timeout isolado não recebeu uma correção específica nesta rodada; acompanhar caso reapareça.
- Sintaxe e diff conferidos. Editor real 8765 respondeu saudável, ainda sem a capacidade narration_trim. Não houve chamada real de IA, uso de mídia pessoal ou alteração de serviços, sessões e credenciais.

## Ativação e limites

**Código preparado; aparo de narração ainda não ativo em produção.** Os controles ficam ocultos até /api/health anunciar narration_trim, evitando oferecer um ajuste que o processo antigo não exporta. O backend novo e a pré-validação de fontes da rodada 1 aguardam ativação segura no fechamento da noite. Nenhum reinício nesta rodada.

Revisão visual desktop continua pendente pelo bloqueio já registrado na inicialização do runtime de controle de janelas. Não houve nova tentativa nem teste de Safari real. Os testes de manipuladores e de áudio não substituem essa revisão.

Checkpoint local; sincronização GitHub acumulada reservada ao fim da extra, ou após a segurança se a extra não ocorrer. Contas individuais e nuvem continuam com o estado pendente descrito na esteira.

## Próxima frente

Às 02h55, avaliar movimentação direta das faixas de áudio na timeline, mantendo posição precisa, rascunho reversível, limites do projeto e compatibilidade com servidor ativo. Retomar a revisão visual quando o runtime permitir. Às 03h55 permanecem segurança/contas, eventual extra e publicação/ativação verificadas antes das 5h.
