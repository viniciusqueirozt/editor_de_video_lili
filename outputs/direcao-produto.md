# Direção de produto — edição por IA com ajustes manuais

Proposta derivada das necessidades do usuário, das duas referências da Elisa, do processo informado e da demonstração pública indicada. Uma primeira versão local já foi implementada com FFmpeg, interface editável, CLI e MCP; ver [estado da versão 0.1](versao-0.1.md). Acesso direto pelo iPhone e integração com o Concat ainda não estão implementados. As seções abaixo registram a direção do produto e os requisitos a validar.

## Experiência desejada

A Elisa usa o iPhone para enviar roteiro e gravações, revisar uma montagem proposta pela IA e escolher entre pedir mudanças por mensagem e ajustar elementos manualmente. As duas formas de interação devem atuar no mesmo projeto e preservar o trabalho aprovado.

O Codex pode conduzir os primeiros testes no computador. Um produto com acesso direto pelo telefone exigirá uma interface própria e uma conexão autenticada ao processamento, cuja implementação e operação ainda precisam ser definidas.

## Referência externa consultada

Na demonstração pública indicada, identificada visualmente como IA Edit Pro, foi possível observar uma prévia e uma timeline no navegador. Aproximadamente entre 2min05s e 3min33s, o apresentador demonstra limpeza de uma gravação falada, revisão, aprovação e uma segunda etapa de legendas e acabamento, além de pedir outro estilo de legenda. A promessa de automação total pertence à oferta comercial. Não foram inspecionados código, funcionamento interno ou um teste independente do produto. A amplitude dos ajustes manuais e o funcionamento no iPhone não foram comprovados nesta análise.

Fontes: [página com o vídeo demonstrativo](https://snaiperdash.com/v/creator-factory-academy/pagina-de-vendas) e [publicação indicada pelo usuário](https://www.instagram.com/p/DemE7CtgU1v/).

## Aplicação ao trabalho da Elisa

O exemplo demonstrado inclui limpeza de fala e acabamento de uma gravação diante da câmera. Os vídeos recebidos da Elisa combinam várias cenas, narração e seleção de momentos. O primeiro fluxo deve relacionar roteiro e tomadas disponíveis, preservando a identidade observada nessas escolhas.

Processo confirmado: roteiro → gravação → montagem visual → gravação da narração → união e ajuste final.

Fluxo proposto para o produto: roteiro e brutos → montagem assistida → revisão visual → narração → ajuste de ritmo e acabamento → aprovação e exportação.

## Primeira versão funcional a validar

| Parte | Comportamento esperado |
| --- | --- |
| Entrada | Receber roteiro e arquivos de um trabalho e indicar o progresso de transferência |
| Catálogo | Relacionar cenas, ações e assuntos aos blocos do roteiro; indicar lacunas |
| Montagem | Criar uma primeira sequência com cortes e durações variáveis |
| Revisão por mensagem | Interpretar pedidos associados a cenas ou posições de tempo e apresentar uma nova versão |
| Revisão manual | Permitir escolher outra tomada, ajustar início/fim, reordenar cenas e alterar texto e volumes |
| Narração posterior | Receber a voz gravada e propor os ajustes de duração necessários |
| Preservação | Manter versões anteriores e respeitar cenas ou elementos fixados pela Elisa |
| Entrega | Gerar prévia leve e exportação final a partir do mesmo estado de projeto |

A interface manual deve começar pelos controles necessários aos ajustes reais da Elisa. Formas de interação no iPhone precisam de teste em aparelho; não foi produzido protótipo visual neste estágio.

## Decisões técnicas propostas

- Manter uma representação estruturada da edição: arquivos de origem, trechos utilizados, ordem, durações, textos, áudio e versões.
- Converter pedidos da IA e ações manuais em alterações nessa mesma representação.
- Registrar elementos fixados pela Elisa e solicitar revisão quando uma mudança depender de alterar uma escolha fixada.
- Usar o Concat como motor candidato e verificar que a prévia e a exportação correspondem ao projeto. A compatibilidade com a representação proposta ainda exige um adaptador e teste.
- Tratar gravações como conteúdo a analisar; somente o briefing e as ações autorizadas do usuário definem as instruções do trabalho.

O MCP documentado no código do Concat permite editar projetos do agente, mas a edição ao vivo do projeto aberto na janela é descrita como planejada. Portanto, não tratar uma conexão MCP como solução pronta de sincronismo entre IA e interface manual. A versão publicada v0.2.7 consultada também não contém o comando `--mcp` do código mais recente. [Documentação MCP consultada](https://github.com/jub0t/Concat/blob/main/docs/MCP.md).

## Convivência com o CapCut

O CapCut continua como alternativa para finalizar os primeiros testes e como opção de revisão a comparar. O objetivo proposto para o produto é oferecer os ajustes essenciais na própria interface móvel, com o mesmo projeto usado pela IA. A transferência de uma timeline completa para o CapCut permanece sem validação.

## Critério para avançar

Começar pelo [roteiro do passeio na Catedral](roteiro-cora-catedral.md) e os brutos correspondentes. Avaliar se a primeira montagem ajuda a Elisa, quais ajustes ela faz e quais precisam de controle manual. A seguir, testar a narração posterior e a geração da versão final. Medir tempo ativo, satisfação com o estilo, retrabalho e custo de processamento antes de ampliar formatos ou comercializar.
