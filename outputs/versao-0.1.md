# Lili 0.1 — primeira versão funcional

## O que foi construído

Interface local em português, com biblioteca de mídia, roteiro, prévia vertical, sequência editável, ajustes de entrada/saída, troca de tomadas, títulos, volumes, proteção de cenas e desfazer. O projeto é salvo em disco e pode ser editado pelo Codex por CLI ou MCP.

A exportação usa os arquivos originais importados e produz MP4/H.264 com áudio AAC. A narração pode ser acrescentada depois da montagem. Cada exportação mantém a revisão utilizada, mesmo se o projeto receber novos ajustes durante o processamento.

## Primeira montagem com os arquivos recebidos

- Arquivos de origem: 1.mp4 a 9.mp4, fornecidos pelo usuário.
- Seleção preparada pelo Codex após inspeção visual dos arquivos e comparação com o roteiro e as referências da Elisa.
- 16 cenas, aproximadamente 35,7 segundos.
- Abertura, preparação do passeio, catedral, exploração, atividade com o livro e encerramento.
- Título breve na abertura, planos com durações variáveis e uma sequência curta de detalhes da atividade.
- Sem narração e sem trilha: é uma montagem visual para a Elisa revisar antes de gravar a voz.
- Projeto separado da sequência técnica criada com vídeos já finalizados.

As cópias dos brutos recebidas têm 576 × 1024 de exibição após aplicar a rotação dos metadados. A exportação em 1080 × 1920 amplia esses arquivos; não recupera detalhe de uma gravação em resolução maior.

## O que já pode ser feito

Abrir o estúdio em http://127.0.0.1:8765 neste computador, escolher o projeto **Cora na Catedral · primeira montagem**, assistir à sequência, selecionar uma cena e ajustar seus detalhes. Também é possível importar outros arquivos, criar projetos e acrescentar a narração.

A aba Pedidos registra ajustes para o Codex. O agente precisa ler e executar esses pedidos em uma sessão ativa. A integração MCP implementada foi testada pelo protocolo; o carregamento das ferramentas no cliente depende de ele ler a configuração local.

## Limites desta entrega

- A primeira montagem ainda depende da avaliação criativa da Elisa. Não foi medida economia de tempo no processo dela.
- Não há agente autônomo executando os pedidos da interface.
- O rascunho por etiquetas não faz análise visual automática dos brutos.
- O processamento atual é FFmpeg; não há conexão operacional com o Concat.
- Sem legendas automáticas, trilha independente, gradação de cor, estabilização ou transições elaboradas nesta primeira versão.
- O acesso está restrito ao computador. Ainda faltam conexão autenticada para o iPhone e testes em aparelho real.
- O CapCut não recebe uma timeline editável deste sistema.

## Verificação

Testes automatizados de estado, persistência, proteção de cenas, revisões, processamento, narração, títulos, orientação e MCP. A interface foi aberta e inspecionada no navegador; a proteção e o desfazer foram exercitados com o projeto de teste. A montagem real foi exportada e amostras da imagem resultante foram verificadas.

## Próximo ciclo

Revisar a seleção de cenas com a Elisa, receber a narração e ajustar o ritmo final. Em seguida, medir o tempo de revisão e priorizar os controles e a conexão móvel necessários para que ela use o fluxo pelo iPhone.

## Atualização — áudio da edição final

A pedido do usuário, o áudio de IMG_7019_vlog cora 2.MOV foi extraído para M4A por cópia dos pacotes AAC, sem recompressão. A igualdade dos dados de áudio foi verificada por hash. A faixa tem aproximadamente 35,7 segundos e contém toda a mixagem do vídeo final, incluindo eventual música e efeitos; não houve isolamento de voz.

O arquivo foi importado para o mesmo projeto como faixa de narração, a partir de zero segundo e com volume de 100%. As 16 cenas e seus ajustes foram preservados. Uma nova cópia com áudio foi exportada para revisão do sincronismo; a montagem visual anterior foi mantida.
