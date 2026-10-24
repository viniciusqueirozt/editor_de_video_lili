# Ciclo de demonstração da Lili — 24/10/2026

## Resultado para revisão

Publicado no GitHub e ativo no editor do notebook em 24/10/2026. Atualize a página do editor para carregar os novos controles. Código funcional publicado no commit 9903878; esta documentação registra a verificação posterior.

- Imagem e ritmo: fades para preto, brilho/contraste/saturação, velocidade 0,25×–4×, preenchimento/recorte, posição e espelhamento.
- Texto: títulos com fontes/tamanho/posição, faixa de legendas com tempos próprios e importação/download SRT, marca d'água de texto opcional.
- Som: música independente, aparo/início/volume/fades, redução opcional durante narração, fades do som original e proteção de picos na exportação.
- Montagem e entrega: fotos JPG/PNG/WebP como cenas, Desfazer/Refazer persistentes, prévia ampliada, tela vertical/quadrada/horizontal e quatro perfis MP4/H.264.
- Interface: quatro faixas visíveis no desktop, biblioteca com Usar como música, histórico de exportações e resumo de resolução/arquivo.
- Segurança publicada: correção de bloqueio por formulário lento, recusa de cookie ambíguo e revogação de todas as sessões. **Aguardam reinício do gateway**; sessões atuais foram preservadas. Contas individuais do editor ainda não estão ativas.

Validação: 124 testes Python e 12 arquivos de testes JavaScript passaram, com exportações FFmpeg reais de mídia sintética e revisão desktop. Prévia ampliada, música, Refazer e exportação usados na demonstração isolada. Safari/iPhone real pendente.

Rotina recorrente configurada neste chat: 23h55, 00h55, 01h55, 02h55 e 03h55, extra imediatamente ao final quando houver margem e publicação ao encerrar. Exceção sexta à noite para sábado; trabalho termina antes das 5h.

Os tópicos abaixo registram cada entrega durante o desenvolvimento. Menções a recurso preparado no começo do ciclo foram superadas pela ativação final do editor, exceto as correções do gateway explicitamente pendentes.


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

### Ritmo e velocidade no pacote visual

Velocidade constante de 0,25× a 4×, com duração da montagem, cursor, largura dos clipes, busca e aparo convertidos entre tempo da fonte e da montagem. Som original usa mudança de tempo com preservação de tom. A narração independente continua no tempo da montagem, com o aviso de duração existente. Fades são medidos em segundos da montagem; alterações incompatíveis são recusadas sem apagar os ajustes.

Verificação: 20 testes de estado passaram; Node conferiu durações/offsets e curva de fade. Três exportações reais a 0,5×, 2× e 4× confirmaram duração e tom próximo de 440 Hz. Não inclui speed ramp nem interpolação por IA.

### Pacote de legendas ampliado

Faixa de legendas independente das cenas, com início/fim/texto/estilo editáveis e blocos clicáveis na linha do tempo. Importação SRT com revisão explícita da substituição e download SRT com permissão de entrega. Conteúdo tratado como texto simples; limites de tamanho/quantidade, tempos válidos e ausência de sobreposição na mesma faixa. Desfazer restaura a faixa.

Prévia e exportação mostram a legenda pelo tempo da montagem, inclusive atravessando cortes; ficam legíveis durante fades da imagem. Legendas que ultrapassam a montagem são sinalizadas para revisão, sem deslocamento silencioso. Transcrição automática continua pendente.

Verificação: parser/roundtrip SRT e validações, edição atômica/Desfazer, permissões HTTP e Node de limites da prévia. Teste FFmpeg confirmou ausência/presença nos quadros antes, durante e depois do intervalo, inclusive após a junção de cenas. Somente projetos sintéticos.

### Pacote de áudio ampliado

Faixa independente de música, com seleção de arquivo importado, entrada/saída na fonte, início na montagem, volume e fades. Redução opcional para 25% do volume escolhido durante a narração adicional, na prévia e na exportação. A mistura exportada recebe limitador de picos; não é normalização por loudness nem detecção automática de fala no som original. Música que ultrapassa a montagem termina com o vídeo, com aviso no painel.

Atualizações parciais preservam os outros ajustes; Desfazer inclui música e exclusão de mídia avisa/remove/restaura seu uso. Verificação: 22 testes de estado, teste Node de envelope e intervalos e duas exportações sintéticas. Análise de frequência do arquivo exportado confirmou início, fim, corte da fonte e redução real da música durante a voz. Safari real pendente.


### Importação de fotos e recuperação do histórico

JPG, JPEG, PNG e WebP estáticos podem virar cenas, com até 30 segundos disponíveis na fonte para aparar na linha do tempo. Miniatura, prévia, quadros e exportação usam uma cópia preparada localmente. Orientação EXIF respeitada; transparência composta sobre preto. Original preservado byte a byte, sem envio externo. Fotos acima de 50 megapixels, lado acima de 16384 pixels, imagens animadas e arquivos ilegíveis são recusados; a cópia de trabalho é limitada a 4096 pixels por lado. HEIC, camadas de logotipo e animação da foto continuam pendentes.

Teste de preservação detectou colisão entre nome da miniatura e JPG importado durante o desenvolvimento; corrigida usando sufixo próprio de miniatura antes da publicação. Verificação inclui orientação, transparência, arquivo inválido/animado/grande, download do original, quadros e exportação real com duração e cor esperadas.

Refazer complementa Desfazer com até 30 passos, botão próprio e Ctrl+Shift+Z/Ctrl+Y fora de campos de texto. Histórico persiste no projeto, incluindo música, legendas, formato e restauração/remoção de mídia. Uma edição nova após desfazer abre outro caminho e limpa os passos de refazer. Testes cobrem sequência, reabertura do armazenamento, visibilidade da mídia e proteção contra revisão desatualizada.

A revisão desktop encontrou e corrigiu a última faixa escondida pela altura da linha do tempo e a rolagem vertical indevida nas abas. Vídeo, narração, música e legendas agora aparecem em faixas próprias. A biblioteca oferece Usar como música. Validação humana no Safari permanece pendente.


### Acabamento de áudio e revisão ampliada

Fades independentes do som original por cena, em segundos da montagem, compatíveis com velocidade, corte, proteção e histórico. Limitador de picos também no som original exportado. Teste com fonte forte e velocidade 2× confirmou fades, duração final e picos abaixo do teto de tolerância após codificação AAC. O limitador não é medição/normalização de LUFS. Atualizações parciais da narração preservam volume, início e fades já escolhidos.

Ampliar prévia abre monitor com reprodução/busca e retorna ao mesmo cursor, pausando na troca. Revisão desktop confirmou abertura, legenda visível e retorno ao editor. O indicador agora mostra proporção/dimensões reais. Marca d'água opcional fica recolhida na exportação para tornar o fluxo de gerar vídeo mais direto. Botões Refazer e ajustes de música foram usados na demonstração isolada; navegador sem erros capturados na revisão.

## Verificação final do conjunto

Suíte Python: 124 testes passaram em 43,4 segundos. Os 12 arquivos de testes JavaScript passaram; incluem funções reais de prévia, duração, importação cancelável, áudio, cor, texto, cartões e perfis. Testes repetidos durante desenvolvimento não foram somados como casos novos. Revisão do diff e sintaxe passaram. Exportações usam FFmpeg real com imagens, tons e vídeos sintéticos. Demonstração isolada no loopback 8769, fora dos projetos reais. Capturas locais não versionadas em work/demo-cycle-24/.

Safari/iPhone real não testado. MP4/H.264 continua sendo o contêiner/codec de entrega; não houve integração de serviços pagos nem chamadas reais de IA. Montagem aprovada da Cora e originais preservados. Nuvem, isolamento individual ativo, transcrição automática, dissolução entre cenas e keyframes permanecem pendentes.

## Rotina recorrente

Configuradas duas janelas nativas da mesma rotina deste chat: abertura às 23h55 e continuação de 00h55 a 03h55 (São Paulo). Quatro rodadas de edição, quinta de segurança/acesso, extra de visual/mercado quando houver margem e publicação no encerramento. Excluída sexta à noite para sábado; sábado à noite para domingo permitido. Encerrar antes das 5h; sem melhoria automática manhã/tarde. Processo reutilizável em outputs/processo-reutilizavel-de-rodadas.md; percentuais e respostas da conta não são versionados.

## Publicação

A publicação final inclui sincronização GitHub e ativação segura do editor, após confirmar ausência de jobs e uploads. Gateway de acesso mantém sessões em memória e não deve ser reiniciado neste ciclo para não encerrar acessos existentes. Correções de segurança do gateway ficam no código publicado, aguardando próximo início; não apresentar a função de sair de todos os aparelhos como ativa antes disso. O registro da checagem efetiva segue abaixo após a ativação.


### Ativação conferida

Editor local reiniciado após confirmar todos os jobs concluídos, nenhum envio parcial e nenhuma mídia em preparo. Saúde HTTP confirmou onze novas capacidades. Os metadados dos três projetos reais mantiveram os mesmos hashes antes/depois; nenhuma mídia real foi usada nos testes. Gateway manteve seu processo original e o túnel permaneceu no mesmo endereço. Consulta externa sem credencial terminou na tela de login HTTP 200, sem erro de origem. Não houve login automatizado com conta real.

Somente código, testes e documentação sincronizados; demonstração, capturas, mídias, estado de orçamento e configurações ficaram ignorados pelo Git. Melhorias de segurança do gateway dependem da próxima reinicialização, pois a troca agora encerraria as sessões que ficam em memória.
