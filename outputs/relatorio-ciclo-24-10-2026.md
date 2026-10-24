# Ciclo de demonstração da Lili — 24/10/2026

Execução direta autorizada pelo usuário: quatro rodadas de edição, uma de segurança/contas e extra condicional. Rodadas em sequência nesta demonstração, sem limite artificial de tamanho; rotina noturna permanece separada. Percentuais da conta são informados no chat após cada rodada, sem versioná-los.

## Rodada 1 — Entrada e saída suaves por cena

- Controles de entrada/saída para preto em segundos, com zero para desativar. Prévia e exportação aplicam a mesma curva linear, sem mudar a duração da cena ou atrasar a narração. Inclui texto sobreposto.
- Validação impede valores inválidos ou efeitos cuja soma ultrapasse a cena. Cenas protegidas respeitadas; Desfazer recupera ajustes. Dividir preserva a entrada na metade esquerda e a saída na direita, recusando cortes incompatíveis com a duração do efeito.
- Verificação: 15 testes de estado passaram; um teste HTTP/FFmpeg real mediu os quadros escuros nas bordas e a duração preservada; curva da prévia conferida em Node. Dados sintéticos, sem IA real.
- Preparado para o próximo início normal do editor. Controles dependem de capacidade anunciada pelo servidor, preservando compatibilidade com o processo antigo. Não é dissolução entre duas cenas nem cria sobreposição temporal.

## Rodada 2 — Tipografia e posicionamento do texto

- Texto manual por cena com três fontes locais (Arial, Georgia e Consolas), três tamanhos e quatro posições: clássica, superior, central e inferior. Mantém a aparência clássica dos projetos antigos; cenas protegidas e Desfazer respeitados.
- Quebra de linhas determinística na prévia e na exportação, incluindo palavras longas e linhas vazias. Nenhuma fonte enviada a serviço externo. Se uma fonte opcional não existir no sistema, a exportação usa a fonte padrão local.
- Verificação: 16 testes de estado passaram; testes Python/Node de quebra e estilo e uma exportação FFmpeg real confirmaram texto claro na região inferior solicitada. Não é transcrição automática nem legenda palavra por palavra.
- Preparado para próximo início normal do editor, anunciado pela capacidade caption_styles. Safari real pendente.

## Rodada 3 — Formatos e exportação

- Montagem vertical 9:16, quadrada 1:1 ou horizontal 16:9, com prévia que respeita a proporção e Desfazer para a troca de formato. Mantém o vídeo inteiro com barras quando necessário.
- Quatro perfis MP4/H.264: prévia, equilibrado, entrega final e alta qualidade. Resoluções acompanham o formato; a janela mostra dimensões antes de gerar e tamanho real em MB ao concluir. Alta qualidade usa compressão menor, sem prometer recuperar detalhes ausentes no original.
- Texto grande ajusta seu tamanho máximo à altura disponível para formatos mais baixos. A fonte continua local.
- Verificação: 17 testes de estado e dois de perfis passaram; Node conferiu dimensões anunciadas. Exportações reais confirmaram 540×540, 1280×720 e 1080×1920, codec H.264, parâmetros dos perfis e tamanho do arquivo. MP4 continua sendo o formato de arquivo disponível; não foram adicionados MOV/WebM ou 4K.
- Preparado para próximo início normal do editor, com capacidade export_profiles. Safari real pendente.

## Rodada 4 — Enquadramento e marca d'água

- Cada cena pode mostrar o vídeo inteiro ou preencher a tela recortando bordas. Controles horizontal/vertical escolhem a região visível; espelhamento horizontal opcional. Os ajustes não alteram o arquivo original.
- Marca d'água de texto própria do projeto, até 40 caracteres, quatro cantos e opacidade configurável; vazia remove, Desfazer recupera. Mostrada na prévia e exportada, sem cobrança. Não é importação de logotipo em imagem. Permanece visível durante fades, como identificação da entrega.
- Verificação: 18 testes de estado passaram; Node conferiu estilos de prévia. Exportação real de padrão vermelho/azul confirmou o lado escolhido no recorte e os pixels da marca d'água no canto solicitado. Fonte sintética teve seu parâmetro de duração corrigido antes de concluir o teste.
- Preparado para próximo início normal do editor, com capacidade framing_watermark. Safari real pendente. O ajuste é estático por cena, sem rastreamento automático ou keyframes nesta entrega.
