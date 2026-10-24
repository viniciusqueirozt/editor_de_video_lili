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

## Rodada 5 — Segurança e sessões

- Falha identificada: auth() lia o corpo do formulário enquanto segurava o bloqueio global das sessões. Um envio lento podia impedir outras requisições autenticadas. Leitura agora fora desse bloqueio, com limite próprio de dez segundos e recusa de corpo incompleto.
- Cookies de sessão duplicados dentro do mesmo cabeçalho, inválidos ou grandes demais são recusados. A assinatura/transporte individual existente continua separado e inativo em produção.
- Novo controle Segurança e sessões permite sair de todos os aparelhos do acesso remoto compartilhado, mediante requisição autenticada e validação de origem. Encerra inclusive a sessão atual e exige nova entrada. Não revoga automaticamente a conta do portal. Controle visível somente se o gateway anunciar suporte.
- Verificação: 18 testes focados de login, gateway individual e proteções HTTP passaram. Casos novos comprovam que formulário lento não bloqueia uma sessão válida, origem estrangeira não encerra sessões, duas sessões são revogadas e cookie ambíguo é recusado. Nenhuma conta/credencial/sessão real usada ou modificada.
- Ativação depende do próximo início normal do gateway. Não houve reinício ou encerramento de sessões reais. Não é auditoria integral nem conclusão do isolamento entre usuários.

## Extra — Finalização visual e pesquisa de mercado

- Janela de exportação com resumo de tela/resolução/arquivo e orientação prática de cada perfil. Entrega mais recente em destaque; anteriores recolhidas em histórico expansível, preservando a expansão nas atualizações. Etiquetas distinguem versão atual/anterior, com tamanho real e botão amplo de download.
- Links de download montados pela rota local validada, sem aceitar uma URL arbitrária retornada em metadados. Mensagens escapadas e progresso limitado ao intervalo válido.
- Teste Node das funções reais conferiu cartões, versões, tamanho, URL segura, erro escapado e histórico aberto. Sintaxe conferida. Avaliação visual no desktop e revisão final descritas abaixo; Safari real permanece pendente.
- Pesquisa em Shotcut, Kdenlive, CapCut, Clipchamp, Kapwing e VEED registrada em outputs/mercado-e-basico-da-lili.md, com fontes e prioridades. O básico ainda precisa de cor/luz, música independente, velocidade, dissolução e legendas temporizadas, entre outras lacunas. Não foi anunciado editor profissional completo.

## Ampliação dos pacotes a pedido do usuário

O usuário pediu entregas de escopo normal e maior aproveitamento da janela de cinco horas. O ciclo foi ampliado sem alterar a divisão de quatro frentes de edição, segurança e extra. Uso de 70%–85% é referência de planejamento; reservar margem antes de 90%, conferir limites entre pacotes e evitar gasto artificial. Dados da conta continuam somente no chat.

### Pacote visual ampliado

Brilho, contraste e saturação por cena, prévia ao ajustar e botão de restaurar a cor original. Prévia SVG e exportação usam os mesmos coeficientes RGB; a exportação real confirmou dessaturação e nível válido. São 19 testes de estado passando, teste Node dos coeficientes e teste FFmpeg focado. HDR, balanço de branco e correção seletiva continuam pendentes.
