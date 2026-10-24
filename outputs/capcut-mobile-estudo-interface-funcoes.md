# CapCut Mobile: estudo de interação e catálogo de funções para a Lili

Consulta: **24/10/2026**, horário de São Paulo. Pesquisa solicitada diretamente pelo usuário durante o dia. Escopo: **aplicativo de celular, iPhone/Android**. Esta entrega é documentação e planejamento; não anuncia novas transições ou mudanças de interação já implementadas.

## 1. Resultado principal

A lacuna mais urgente é o modo de editar: selecionar o elemento certo, enxergar a ferramenta correspondente, experimentar visualmente e ajustar no tempo sem perder o quadro. A Lili acrescentou recursos, mas seu painel de propriedades ainda concentra muitas decisões. A falta de transição real entre duas cenas permanece: fade para preto aplicado a uma cena não é dissolução entre duas tomadas.

Prioridade proposta: **navegação e posicionamento fino → escolha visual de efeitos/transições → transições e efeitos temporizados consistentes → outros recursos**. Não ampliar primeiro uma lista de efeitos escondidos no mesmo formulário.

## 2. Método, evidência e limites

- **D — documentação:** centro de ajuda e guias do domínio oficial capcut.com; somente seções explicitamente móveis. O material consultado é ajuda e guias por assunto, não um manual único versionado.
- **T — tutorial:** análise das transcrições públicas disponibilizadas pelo próprio YouTube, com instantes para revisita. As transcrições automáticas podem errar termos; foram cruzadas com documentação e imagens quando relevantes.
- **V — amostragem visual:** quadros/trechos inspecionados no navegador confirmaram telefone, barra inferior, linha do tempo e catálogo. V01 em torno de 03:26; V02 em 05:23 e 14:08; V03 em 03:50. Não foi reprodução integral contínua de todos os minutos, nem teste do aplicativo em um iPhone real.
- **L — leitura local:** análise de web/app.js, web/timeline.js e relatórios da versão publicada da Lili. Observação de código não equivale a teste no Safari.
- **P — proposta:** decisões próprias para a Lili e critérios de aceite. Não atribuir ao CapCut algoritmos, garantias de precisão, política de sobreposição ou botões não confirmados.

Os três tutoriais principais são V01 (português, 2023), V02 (iPhone, 2024; YouTube apresentou dublagem/transcrição pt) e V03 (CapCut Mobile, inglês, 2025). O mais antigo serve para gestos e estrutura, não para provar catálogo/preços atuais. Fontes e disponibilidade foram consultadas nesta data; nomes, região e planos podem mudar. [Ajuda oficial sobre mudanças de UI](https://www.capcut.com/help/capcut-ui-update-changes).

Não foram usados tutoriais de computador como evidência do fluxo móvel. Páginas que misturam plataformas foram restritas à subseção do telefone. Uma página intitulada de efeitos móveis manda importar do computador; outra mistura CapCut e Alight Motion. Essas passagens não foram usadas como instrução. Também há documentação divergente sobre exportar SRT no celular; isso **não foi confirmado** como comportamento universal. A função SRT da Lili continua sendo independente dessa incerteza.

Transcrições integrais ficaram apenas em work/capcut-research-2026-10-24/, ignorado pelo Git, como material temporário de análise. Não foram copiados vídeos, bibliotecas de efeitos ou cursos. Este relatório resume fatos e desenvolve propostas próprias, sem republicar as transcrições.

## 3. Diagnóstico da Lili e comparação de fluxo

Leitura local nesta data; confirmar em testes de interação antes de classificar uma causa de falha no celular.

| Situação na Lili | Fluxo de referência móvel | Mudança proposta |
| --- | --- | --- |
| Formulário extenso da cena com vários efeitos e propriedades | Ferramentas variam conforme o elemento selecionado; V01 03:40–04:16 | Barra contextual e painel inferior por tarefa; preservar seleção e cursor. |
| Fade por cena, sem um objeto de transição entre duas tomadas | Controle na junção abre um catálogo; C02 e V02 13:50–14:49 | Selecionar a junção, escolher miniatura, ajustar duração, assistir e aplicar. |
| Efeitos atuais sem bloco temporal independente | Duração do efeito pode ser aparada numa faixa; C03 e V02 12:55–13:45 | Faixa de efeitos com alvo, intervalo e ações visíveis. |
| Zoom por botões/slider; navegação e busca com caminhos separados | Pinça e deslocamento da timeline; V01 03:23–03:39 e V02 03:29–04:04 | Gesto de pinça mais modos de precisão; um eixo temporal consistente. |
| pointermove de busca chama seekTo; seleção chama markSelection/renderInspector | A tarefa é permanecer no quadro escolhido para editar | Investigar reconstrução do painel e carga de seeks; não afirmar medição de desempenho sem perfilar. |
| Passo de 1/30 s existe por teclado, não como controle fino de toque | Gestos móveis ajudam aproximação; botões quadro a quadro não foram confirmados nesta pesquisa | Criar controles próprios de um quadro, contador e confirmação do quadro carregado. |
| Recorte visual estima limites por fades da imagem; validação do áudio é separada no backend | Alça deve indicar o limite efetivo antes de soltar | Conferir todos os limites de áudio/imagem/transição e avisar durante o gesto, sem falhar só ao salvar. |

Referências de código: web/timeline.js (pointerTime, beginTrim, moveTrim, setTimelineZoom e atalhos); web/app.js (seekTo, markSelection, renderInspector, updatePlayer). A inspeção não modificou esses arquivos.

## 4. Fluxos de interface propostos

### 4.1 Transição

Toque na junção → painel inferior com nome das duas cenas → cartões de transição → prévia do encontro → duração por slider e leitura numérica → Aplicar ou Cancelar. Incluir Sem transição, recentes/favoritas e aplicação a todos explicitamente separada. Cartões animam quando solicitados, não todos ao mesmo tempo. A duração máxima depende das duas cenas e do modelo de tempo; desabilitar escolhas inválidas com motivo legível.

### 4.2 Efeito

Selecione o vídeo/camada → Efeitos → categoria/busca → toque no cartão → prévia temporária → intensidade → Aplicar. O resultado vira um bloco na faixa Efeitos. Tocar no bloco abre Ajustar, Substituir, Duplicar e Excluir; suas bordas editam o intervalo. Filtro de cor, transição e animação de texto ficam em grupos distintos, com o elemento afetado sempre identificado.

### 4.3 Instante preciso

Pause → amplie a régua com pinça ou botão → deslize a trilha sob um ponto de referência → refine por quadro/contador → confirme o quadro carregado → corte/defina a borda. O ímã ajuda a aproximar cortes, mas pode ser desligado. Proteger cena, pausar cursor e congelar imagem têm ações distintas. Este conjunto fino é proposta para a Lili, não uma descrição integral do CapCut.

### 4.4 Configurações

Tela normal: mídia e ferramentas principais. Com cena selecionada: Cortar, Dividir, Velocidade, Som, Ajustar imagem, Animar. Na junção: Transição. No texto: Conteúdo, Estilo, Tempo, Animação. No áudio: Aparar, Volume, Fades, Remover. No efeito: Ajustar, Substituir, Duplicar, Excluir. Configurações de projeto/exportação permanecem separadas das propriedades da cena.

## 5. Catálogo detalhado e rastreável

Cada Fxx é uma função ou fluxo encontrado, com fonte, estado local, proposta e critério para criação. **P0:** usabilidade/transição/tempo urgente; **P1:** básico de edição; **P2:** expansão após a base; **P3:** elaborado. O estado local é o da pesquisa, não uma promessa sobre versões futuras.


### Navegação e montagem


<a id="f01"></a>

#### F01 — Importar e começar uma montagem · P1

**Encontrado:** Novo projeto abre a seleção de mídias do aparelho; os arquivos escolhidos entram na edição.

**Revisitar:** [C21](https://www.capcut.com/resource/capcut-tutorial-for-beginners), [C16](https://www.capcut.com/resource/free-video-edit).

**Na Lili hoje:** Importação local existente, inclusive fotos estáticas.

**Aplicação proposta:** Mostrar selecionados, ordem de entrada e progresso; distinguir adicionar à biblioteca de inserir na montagem.

**Aceite:** Seleção de três arquivos deve comunicar destino e ordem antes de confirmar.


<a id="f02"></a>

#### F02 — Ferramentas conforme a seleção · P0

**Encontrado:** Selecionar um elemento muda as ferramentas inferiores disponíveis.

**Revisitar:** [V01 · 03:40–04:16](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=220s).

**Na Lili hoje:** Painel Cena concentra muitos grupos; existem abas de narração, música e legendas.

**Aplicação proposta:** Uma barra contextual curta: vídeo, texto, áudio, efeito ou junção; um painel inferior por tarefa.

**Aceite:** Selecionar música não deve abrir campos de recorte de imagem; voltar deve recuperar o contexto.


<a id="f03"></a>

#### F03 — Reproduzir, pausar e ampliar a prévia · P0

**Encontrado:** Prévia, contador e reprodução ficam próximos; há ampliação do monitor.

**Revisitar:** [V01 · 02:17–03:05](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=137s).

**Na Lili hoje:** Prévia ampliada existente.

**Aplicação proposta:** Manter cursor e seleção ao ampliar; mostrar quando o quadro solicitado ainda está carregando.

**Aceite:** Pausar e ampliar não podem trocar o instante ou perder o enquadramento.


<a id="f04"></a>

#### F04 — Desfazer e refazer acessíveis · P1

**Encontrado:** As duas ações ficam próximas da reprodução, disponíveis durante a edição.

**Revisitar:** [V01 · 02:38–02:56](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=158s), [V03 · 17:14–17:28](https://www.youtube.com/watch?v=KVws1GVHoA0&t=1034s).

**Na Lili hoje:** Histórico persistente e botões existentes.

**Aplicação proposta:** Manter os botões visíveis no telefone, informar a ação recuperada e desfazer uma confirmação inteira.

**Aceite:** Uma aplicação de efeito seguida de Desfazer deve restaurar tudo; Refazer deve recuperar o mesmo resultado.


<a id="f05"></a>

#### F05 — Percorrer a linha do tempo · P0

**Encontrado:** Arrastar a linha permite explorar o vídeo em relação ao indicador de reprodução.

**Revisitar:** [V01 · 03:23–03:39](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=203s).

**Na Lili hoje:** Régua e cursor arrastáveis; também existe barra de busca separada.

**Aplicação proposta:** No telefone, testar trilha rolando sob cursor central; separar navegar, selecionar e mover um clipe.

**Aceite:** Ao soltar o dedo, manter o instante escolhido; um toque para selecionar não deve reposicionar o vídeo inesperadamente.


<a id="f06"></a>

#### F06 — Zoom por pinça na linha do tempo · P0

**Encontrado:** O gesto muda a escala temporal, permitindo enxergar uma região menor ou a montagem inteira.

**Revisitar:** [V01 · 03:23–03:39](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=203s), [V02 · 03:29–04:04](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=209s).

**Na Lili hoje:** Zoom por botões e slider; gesto de dois dedos não implementado em timeline.js.

**Aplicação proposta:** Adicionar pinça ancorada no ponto tocado e atalhos Ajustar/Detalhar, preservando a posição.

**Aceite:** O mesmo corte deve continuar sob o ponto de referência depois de ampliar/reduzir.


<a id="f07"></a>

#### F07 — Aparar pelas bordas · P0

**Encontrado:** Selecionar um clipe revela alças nas extremidades para ajustar entrada e saída.

**Revisitar:** [C16](https://www.capcut.com/resource/free-video-edit), [V02 · 04:33–04:52](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=273s).

**Na Lili hoje:** Alças e campos de segundos existem.

**Aplicação proposta:** Alças com área de toque maior, quadro da borda em revisão e controles finos separados do arraste.

**Aceite:** Aparar fim deve exibir o último quadro que permanecerá, inclusive com velocidade diferente de 1×.


<a id="f08"></a>

#### F08 — Dividir no cursor · P0

**Encontrado:** Posicionar o indicador dentro de um clipe e acionar a divisão gera dois trechos.

**Revisitar:** [V02 · 04:53–05:23](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=293s), [C16](https://www.capcut.com/resource/free-video-edit).

**Na Lili hoje:** Divisão existente; precisão por teclado disponível no desktop.

**Aplicação proposta:** Botão Dividir sempre reconhecível quando uma cena estiver selecionada; mostrar o instante exato.

**Aceite:** Um cursor parado não pode saltar para o início da cena ao abrir a ferramenta.


<a id="f09"></a>

#### F09 — Remover, copiar e reorganizar trechos · P1

**Encontrado:** A edição combina seleção, remoção e deslocamento/cópia dos elementos na montagem.

**Revisitar:** [V01 · 07:32–11:05](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=452s), [V01 · 15:02–15:29](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=902s).

**Na Lili hoje:** Remover, duplicar e reordenar existentes; arraste usa também mecanismo HTML draggable.

**Aplicação proposta:** Oferecer operações contextuais claras e reordenação por toque prolongado no telefone.

**Aceite:** Arrastar para navegar não pode reordenar; excluir um trecho deve ser recuperável.


<a id="f10"></a>

#### F10 — Proporção e enquadramento · P1

**Encontrado:** Há escolha de proporção e manipulação da imagem na prévia.

**Revisitar:** [V02 · 02:00–03:27](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=120s), [C13](https://www.capcut.com/resource/free-video-overlay-effects).

**Na Lili hoje:** Três formatos e enquadramento estático existentes.

**Aplicação proposta:** Separar Tela da montagem de Enquadrar esta cena; permitir reposicionar visualmente com limites.

**Aceite:** Mudar 9:16 para 1:1 deve mostrar corte/barras antes da confirmação, sem deformar a imagem.


### Transições


<a id="f11"></a>

#### F11 — Transição na junção entre cenas · P0

**Encontrado:** O acesso nasce no pequeno controle entre dois clipes adjacentes.

**Revisitar:** [C02](https://www.capcut.com/help/transitions-in-capcut), [V02 · 13:50–14:20](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=830s), [V01 · 12:32–12:58](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=752s).

**Na Lili hoje:** Há fade por cena; não existe transição real entre duas tomadas.

**Aplicação proposta:** Criar alvo de toque em cada junção e abrir catálogo ligado ao par correto; corte seco continua opção.

**Aceite:** A junção entre cenas 2 e 3 deve afetar esse par; projeto com uma única cena deve explicar a indisponibilidade.


<a id="f12"></a>

#### F12 — Escolher duração e confirmar transição · P0

**Encontrado:** O painel oferece escolha visual e ajuste de duração, com confirmação.

**Revisitar:** [C02](https://www.capcut.com/help/transitions-in-capcut), [V02 · 14:22–14:49](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=862s).

**Na Lili hoje:** Fades usam campos numéricos no painel de cena.

**Aplicação proposta:** Miniaturas, reprodução do encontro e slider com número legível; Aplicar/Cancelar sem gravar cada toque exploratório.

**Aceite:** Cancelar preserva o projeto; Aplicar grava uma operação e permite Desfazer.


<a id="f13"></a>

#### F13 — Aplicar uma transição a vários cortes · P1

**Encontrado:** O tutorial apresenta aplicação ao corte atual ou a todos os cortes.

**Revisitar:** [V02 · 14:22–14:37](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=862s).

**Na Lili hoje:** Não disponível.

**Aplicação proposta:** Aplicar a todos deve ser ação explícita, mostrar quantas junções serão alteradas e respeitar restrições.

**Aceite:** Não tocar nas cenas protegidas silenciosamente nem gerar uma operação de histórico para cada junção.


<a id="f14"></a>

#### F14 — Catálogo de famílias de transição · P0

**Encontrado:** A demonstração mostra categorias e cartões; há mistura de itens gratuitos e Pro.

**Revisitar:** [V02 · 13:50–14:49](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=830s).

**Na Lili hoje:** Sem biblioteca de transições entre cenas.

**Aplicação proposta:** Começar com dissolver, passar por preto/branco, deslizar e wipe; categorias curtas, Sem transição e favoritas.

**Aceite:** Nome e miniatura devem antecipar o resultado; item não implementado não pode parecer disponível.


### Efeitos e imagem


<a id="f15"></a>

#### F15 — Encontrar um efeito visual · P0

**Encontrado:** O menu de efeitos abre uma biblioteca de efeitos de vídeo; há busca e opções de ajuste.

**Revisitar:** [C03](https://www.capcut.com/help/effectss-not-applying-in-capcut), [C04](https://www.capcut.com/resource/special-effects-apps).

**Na Lili hoje:** Não há catálogo visual equivalente.

**Aplicação proposta:** Cartões com miniatura animada sob demanda, categorias legíveis, busca e recentes; mostrar somente efeitos executáveis.

**Aceite:** Encontrar um desfoque não deve exigir entender filtros FFmpeg ou campos técnicos.


<a id="f16"></a>

#### F16 — Efeito com início e fim próprios · P0

**Encontrado:** Um efeito pode aparecer como elemento temporal, movido e aparado na trilha.

**Revisitar:** [C03](https://www.capcut.com/help/effectss-not-applying-in-capcut), [V02 · 12:55–13:45](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=775s), [C20](https://www.capcut.com/resource/motion-blur-effect).

**Na Lili hoje:** Ajustes visuais atuais valem pela cena inteira; não há trilha independente de efeitos.

**Aplicação proposta:** Criar faixa Efeitos, blocos selecionáveis e alças; explicitar se o alvo é uma cena, camada ou imagem composta.

**Aceite:** Efeito de 2 a 4 segundos deve aparecer só nesse intervalo na prévia e no arquivo final.


<a id="f17"></a>

#### F17 — Ajustar, substituir, duplicar e excluir efeito · P0

**Encontrado:** A documentação do app descreve ações de manutenção no efeito selecionado.

**Revisitar:** [C05](https://www.capcut.com/resource/blur-a-video-app).

**Na Lili hoje:** Sem objeto independente de efeito.

**Aplicação proposta:** Barra contextual do bloco com quatro ações claras e um controle de intensidade quando aplicável.

**Aceite:** Substituir mantém intervalo por padrão; excluir não apaga a cena; duplicar pode ser desfeito.


<a id="f18"></a>

#### F18 — Parâmetros específicos do efeito · P1

**Encontrado:** Desfoque e outros efeitos oferecem parâmetros próprios, em vez de uma configuração única universal.

**Revisitar:** [C05](https://www.capcut.com/resource/blur-a-video-app), [C20](https://www.capcut.com/resource/motion-blur-effect).

**Na Lili hoje:** Brilho, contraste e saturação têm sliders.

**Aplicação proposta:** Expor intensidade primeiro e esconder ajustes avançados; unidades legíveis e botão Restaurar.

**Aceite:** Um efeito sem parâmetro de direção não deve mostrar campo de direção; zero/neutralidade precisa ser previsível.


<a id="f19"></a>

#### F19 — Correção de luz e cor · P1

**Encontrado:** O ajuste móvel inclui controles como brilho, contraste, saturação e temperatura.

**Revisitar:** [V02 · 22:09–22:42](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=1329s), [V03 · 02:53–03:56](https://www.youtube.com/watch?v=KVws1GVHoA0&t=173s).

**Na Lili hoje:** Brilho, contraste e saturação ativos; temperatura não implementada.

**Aplicação proposta:** Agrupar correção em Ajustar imagem, com comparação original e redefinição por grupo.

**Aceite:** A comparação deve preservar o instante; preview e exportação precisam concordar, com atenção a HDR/SDR.


<a id="f20"></a>

#### F20 — Filtros de aparência · P1

**Encontrado:** O tutorial usa filtros e controle de intensidade para mudar o aspecto da imagem.

**Revisitar:** [V02 · 22:07–22:41](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=1327s).

**Na Lili hoje:** Há correção básica, mas não presets de aparência.

**Aplicação proposta:** Separar corrigir a imagem de aplicar um look; filtros locais reversíveis, com intensidade e Sem filtro.

**Aceite:** Remover o look não deve remover correções manuais ou mudar a duração do vídeo.


<a id="f21"></a>

#### F21 — Isolar uma cor / HSL · P2

**Encontrado:** O tutorial demonstra tratamento seletivo de cor no telefone.

**Revisitar:** [V03 · 00:49–01:36](https://www.youtube.com/watch?v=KVws1GVHoA0&t=49s).

**Na Lili hoje:** Sem HSL seletivo.

**Aplicação proposta:** Adicionar depois da base: faixa de cor e intensidade, sem transformar o controle de cor comum em um formulário longo.

**Aceite:** A pele e as cores não selecionadas devem ser avaliadas; não prometer seleção perfeita de objetos.


<a id="f22"></a>

#### F22 — Camada de ajuste sobre várias cenas · P2

**Encontrado:** O exemplo estende uma camada de correção para afetar mais clipes.

**Revisitar:** [V03 · 02:53–03:56](https://www.youtube.com/watch?v=KVws1GVHoA0&t=173s).

**Na Lili hoje:** Correção por cena; sem camada global temporizada.

**Aplicação proposta:** Implementar camada de ajuste com intervalo próprio e ordem de composição visível.

**Aceite:** Aparar a camada deve limitar o look ao intervalo, sem copiar valores ocultos em todas as cenas.


<a id="f56"></a>

#### F56 — Vinheta · P2

**Encontrado:** O ajuste móvel demonstrado inclui escurecimento das bordas.

**Revisitar:** [V02 · 22:27–22:34](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=1347s).

**Na Lili hoje:** Sem vinheta dedicada.

**Aplicação proposta:** Preset local com intensidade e comparação, preservando o centro e os textos sobrepostos.

**Aceite:** A vinheta não deve recortar a imagem nem escurecer a legenda por acidente.


<a id="f57"></a>

#### F57 — Grão · P2

**Encontrado:** A aula apresenta grão entre os ajustes de aparência.

**Revisitar:** [V02 · 22:30–22:41](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=1350s).

**Na Lili hoje:** Sem grão dedicado.

**Aplicação proposta:** Grão discreto com intensidade; definir como o ruído será reproduzido na prévia e exportação.

**Aceite:** Exportar novamente a mesma versão não deve produzir um efeito inexplicavelmente diferente.


<a id="f58"></a>

#### F58 — Ajuste automático da imagem · P2

**Encontrado:** O tutorial menciona uma opção de correção automática após os controles manuais.

**Revisitar:** [V02 · 22:41–22:57](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=1361s).

**Na Lili hoje:** Correção manual básica; sem ajuste automático.

**Aplicação proposta:** Comparação com original e aplicação optativa; avaliar consistência entre tomadas antes de automatizar.

**Aceite:** Preservar valores anteriores e Desfazer; não alterar imagens aprovadas sem ação explícita.


<a id="f61"></a>

#### F61 — Desfoque de movimento · P2

**Encontrado:** O guia móvel descreve efeito com parâmetros e intervalo temporal editável.

**Revisitar:** [C20](https://www.capcut.com/resource/motion-blur-effect).

**Na Lili hoje:** Não implementado.

**Aplicação proposta:** Começar por efeito limitado e reversível; avaliar custo de prévia, qualidade e ghosting.

**Aceite:** Não usar simples desfoque espacial e anunciar como equivalente a todo motion blur do concorrente.


### Camadas e movimento


<a id="f23"></a>

#### F23 — Animação de entrada e saída de um elemento · P1

**Encontrado:** Animações são aplicadas ao elemento; não equivalem ao encontro de duas tomadas.

**Revisitar:** [V01 · 11:07–12:32](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=667s), [V03 · 08:59–09:34](https://www.youtube.com/watch?v=KVws1GVHoA0&t=539s).

**Na Lili hoje:** Fades por cena e texto, sem biblioteca de animações.

**Aplicação proposta:** Separar Entrada, Saída e Durante para textos/imagens; duração coerente com o elemento.

**Aceite:** Uma animação de título não pode alterar a narração ou virar transição entre vídeos.


<a id="f24"></a>

#### F24 — Keyframes de escala e posição · P2

**Encontrado:** Marcar dois instantes com enquadramentos diferentes produz movimento entre eles.

**Revisitar:** [C10](https://www.capcut.com/resource/how-to-zoom-in-on-video), [V03 · 04:16–05:23](https://www.youtube.com/watch?v=KVws1GVHoA0&t=256s).

**Na Lili hoje:** Posição e espelhamento estáticos; sem keyframes.

**Aplicação proposta:** Começar por escala, posição e opacidade; adicionar, selecionar, navegar e remover pontos.

**Aceite:** Reabrir deve preservar pontos; exportação deve manter o mesmo enquadramento em cada instante.


<a id="f25"></a>

#### F25 — Curvas de suavização · P2

**Encontrado:** O exemplo de zoom troca a curva entre pontos para suavizar o movimento.

**Revisitar:** [V03 · 04:36–05:23](https://www.youtube.com/watch?v=KVws1GVHoA0&t=276s).

**Na Lili hoje:** Não disponível.

**Aplicação proposta:** Oferecer Linear, Suave e entradas/saídas simples antes de um editor complexo de curvas.

**Aceite:** A curva deve modificar o percurso temporal sem deslocar os keyframes.


<a id="f26"></a>

#### F26 — Movimento de câmera simulado · P2

**Encontrado:** Reposicionamentos em keyframes geram deslocamento lateral em um vídeo existente.

**Revisitar:** [V03 · 05:24–06:02](https://www.youtube.com/watch?v=KVws1GVHoA0&t=324s).

**Na Lili hoje:** Reposicionamento por cena é estático.

**Aplicação proposta:** Preset de pan/zoom discreto, com início e fim editáveis; alertar quando o recorte expõe bordas.

**Aceite:** Não deve aparecer barra inesperada nem haver salto na borda do efeito.


<a id="f27"></a>

#### F27 — Sobreposição e B-roll · P1

**Encontrado:** Adicionar uma sobreposição cria mídia em outra camada; pode ser aparada e posicionada.

**Revisitar:** [C13](https://www.capcut.com/resource/free-video-overlay-effects), [V01 · 17:28–24:59](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=1048s).

**Na Lili hoje:** Uma trilha principal de vídeo; fotos entram como cenas, não como overlays.

**Aplicação proposta:** Adicionar imagem/vídeo acima da trilha principal, com intervalo, escala e posição próprios.

**Aceite:** Adicionar um logo não deve substituir a cena; ocultar a camada deve revelar a imagem de baixo.


<a id="f28"></a>

#### F28 — Mistura e opacidade de camadas · P2

**Encontrado:** A documentação e a aula apresentam transparência e modos de mistura.

**Revisitar:** [C13](https://www.capcut.com/resource/free-video-overlay-effects), [V03 · 10:55–11:26](https://www.youtube.com/watch?v=KVws1GVHoA0&t=655s).

**Na Lili hoje:** Sem composição visual de múltiplas camadas.

**Aplicação proposta:** Começar por opacidade normal; modos de mistura depois, com miniatura e nome descritivo.

**Aceite:** PNG transparente deve manter transparência; usar uma foto como cena continua sendo operação distinta.


<a id="f29"></a>

#### F29 — Remover fundo / recorte do sujeito · P3

**Encontrado:** A aula demonstra remoção automática do fundo e recomposição sobre outra imagem.

**Revisitar:** [V03 · 10:20–10:54](https://www.youtube.com/watch?v=KVws1GVHoA0&t=620s).

**Na Lili hoje:** Não implementado.

**Aplicação proposta:** Avaliar motor local e qualidade em cabelo/pelo; manter original e permitir desfazer.

**Aceite:** Não anunciar resultado automático confiável para a Cora sem amostras adequadas e medição de tempo.


<a id="f30"></a>

#### F30 — Adesivos e elementos gráficos · P2

**Encontrado:** O editor permite inserir e posicionar elementos sobre o vídeo.

**Revisitar:** [V02 · 17:01–17:21](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=1021s), [V03 · 10:55–11:26](https://www.youtube.com/watch?v=KVws1GVHoA0&t=655s).

**Na Lili hoje:** Sem catálogo ou camada gráfica independente.

**Aplicação proposta:** Biblioteca própria pequena, com licença registrada, importação local e favoritos.

**Aceite:** Nenhum recurso do catálogo CapCut ou patrocinador deve ser copiado para a Lili sem licença.


<a id="f60"></a>

#### F60 — Guias de alinhamento na imagem · P2

**Encontrado:** Um elemento gráfico encaixa no centro da tela com uma guia de alinhamento.

**Revisitar:** [V01 · 14:25–14:36](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=865s).

**Na Lili hoje:** Posição configurada por sliders; sem guias de arraste de overlay.

**Aplicação proposta:** Adicionar guias de centro/bordas ao futuro editor de camadas; manter separado do ímã temporal.

**Aceite:** Centralizar um texto não deve deslocar seu instante na montagem.


### Texto e legendas


<a id="f31"></a>

#### F31 — Texto manual e estilo · P1

**Encontrado:** Texto pode ser inserido, editado e transformado na prévia.

**Revisitar:** [V02 · 16:01–17:00](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=961s), [V01 · 12:59–15:09](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=779s).

**Na Lili hoje:** Títulos por cena e legendas temporizadas com estilos básicos.

**Aplicação proposta:** Camada de texto com tipografia, alinhamento, cor, contorno e fundo; controles visuais simples.

**Aceite:** Texto deve permanecer legível na área segura e preservar caracteres acentuados.


<a id="f32"></a>

#### F32 — Modelos de texto reutilizáveis · P1

**Encontrado:** Há modelos que aceitam troca de texto sem refazer todo o desenho.

**Revisitar:** [V01 · 11:44–12:22](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=704s), [V02 · 16:18–17:00](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=978s).

**Na Lili hoje:** Não há modelos salvos de estilo.

**Aplicação proposta:** Salvar Estilo da Elisa e kit de títulos próprios, usando fontes locais/licenciadas.

**Aceite:** Aplicar um estilo não deve sobrescrever as palavras nem alterar tempos das legendas.


<a id="f33"></a>

#### F33 — Legendas automáticas · P1

**Encontrado:** O app oferece idioma e geração, seguida da edição das caixas de legenda.

**Revisitar:** [C07](https://www.capcut.com/help/how-to-recognise-subtitles).

**Na Lili hoje:** Edição manual e SRT ativos; transcrição automática pendente.

**Aplicação proposta:** Preferir transcrição local viável; escolher fonte de voz e idioma, com progresso e revisão.

**Aceite:** Nenhum áudio deve ser enviado a uma API externa sem escolha/autorização; geração não pode apagar revisão manual sem confirmar.


<a id="f34"></a>

#### F34 — Corrigir e dividir uma legenda · P1

**Encontrado:** Selecionar uma legenda permite corrigir seu conteúdo e dividir no instante escolhido.

**Revisitar:** [C08](https://www.capcut.com/help/split-the-subtiltes), [C09](https://www.capcut.com/help/auto-captions-in-capcut).

**Na Lili hoje:** Tempos/textos editáveis; divisão específica de legenda não implementada.

**Aplicação proposta:** Lista de frases sincronizada com vídeo; dividir/juntar e aparar sem repetir ajustes de estilo.

**Aceite:** O corte deve preservar legibilidade e sincronismo; não duplicar frases nem criar sobreposição acidental.


### Áudio


<a id="f35"></a>

#### F35 — Música do aparelho e biblioteca · P1

**Encontrado:** O fluxo aceita áudio e permite escolher trecho para a montagem.

**Revisitar:** [V01 · 27:01–30:01](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=1621s), [C16](https://www.capcut.com/resource/free-video-edit).

**Na Lili hoje:** Música independente ativa, com aparo e offset numéricos.

**Aplicação proposta:** Selecionar com escuta curta, forma de onda e alças; explicitar substituir música ou adicionar outra faixa.

**Aceite:** Uma música não pode virar narração automaticamente; mostrar origem/licença das faixas fornecidas.


<a id="f36"></a>

#### F36 — Extrair som de um vídeo · P1

**Encontrado:** A opção de extração gera áudio editável separado da imagem.

**Revisitar:** [C15](https://www.capcut.com/resource/audio-extractor-from-mp4).

**Na Lili hoje:** Arquivos de vídeo com som podem ser usados como fonte; extração como ação dedicada não existe.

**Aplicação proposta:** Ação Extrair áudio cria faixa ligada à fonte; explicitar se o som original ficará mudo.

**Aceite:** Evitar tocar duas cópias do mesmo áudio; manter alinhamento inicial e permitir separar depois.


<a id="f37"></a>

#### F37 — Gravar narração vendo a montagem · P1

**Encontrado:** O app oferece gravação pelo microfone dentro do projeto.

**Revisitar:** [C14](https://www.capcut.com/resource/how-to-add-voice-in-a-video).

**Na Lili hoje:** Importa narração; não grava voz no navegador.

**Aplicação proposta:** Gravar no cursor, contagem curta, escuta e nova tomada; verificar permissões e codecs do Safari real.

**Aceite:** Gravação recusada ou interrompida não pode perder a montagem; ouvir a tomada antes de substituir a anterior.


<a id="f38"></a>

#### F38 — Efeitos sonoros · P1

**Encontrado:** A área de áudio apresenta uma biblioteca de sons/efeitos.

**Revisitar:** [C14](https://www.capcut.com/resource/how-to-add-voice-in-a-video).

**Na Lili hoje:** Sem biblioteca de SFX e sem várias faixas livres de áudio.

**Aplicação proposta:** Sons locais/licenciados com busca, categorias, pré-escuta e volume; alinhar no cursor.

**Aceite:** Um efeito curto deve poder ser movido e aparado sem substituir música ou narração.


<a id="f39"></a>

#### F39 — Volume e fades de áudio · P1

**Encontrado:** Selecionar áudio dá acesso ao volume e às suavizações nas extremidades.

**Revisitar:** [C15](https://www.capcut.com/resource/audio-extractor-from-mp4), [V01 · 29:17–29:28](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=1757s).

**Na Lili hoje:** Volume e fades ativos para música, voz e som da cena.

**Aplicação proposta:** Mostrar os fades na própria região de áudio e oferecer slider com leitura clara.

**Aceite:** Alterar entrada suave da música não deve modificar o fade visual; exportação deve evitar picos.


<a id="f40"></a>

#### F40 — Alinhar som pela forma de onda · P0

**Encontrado:** A aula usa picos da música para escolher cortes e alinhar momentos; descreve encaixe no alinhamento.

**Revisitar:** [V01 · 30:02–30:35](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=1802s).

**Na Lili hoje:** Forma de onda da narração; música sem onda e sem arraste temporal.

**Aplicação proposta:** Forma de onda nas faixas relevantes; ímã temporal opcional para cortes, cursor e marcadores.

**Aceite:** Com ímã desligado, permitir ajuste fino; não confundir guia de centro da imagem com encaixe na timeline.


<a id="f41"></a>

#### F41 — Melhorar voz / reduzir ruído · P2

**Encontrado:** O tutorial demonstra processamento de voz em um controle do clipe.

**Revisitar:** [V03 · 12:12–12:45](https://www.youtube.com/watch?v=KVws1GVHoA0&t=732s).

**Na Lili hoje:** Sem tratamento de ruído dedicado.

**Aplicação proposta:** Avaliar filtro local com comparação e intensidade; não tratar limiter como remoção de ruído.

**Aceite:** Testar preservação de consoantes e som ambiente desejado; tempo de processamento deve ficar claro.


<a id="f59"></a>

#### F59 — Harmonizar volumes entre clipes · P2

**Encontrado:** O tutorial apresenta uma opção para aproximar níveis de áudio de vários clipes.

**Revisitar:** [V02 · 21:07–21:35](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=1267s).

**Na Lili hoje:** Volumes individuais e limitador; sem análise de loudness entre clipes.

**Aplicação proposta:** Medir antes de sugerir ganho; mostrar quais cenas mudarão e preservar escolhas protegidas.

**Aceite:** Não chamar limiter de normalização; comparar percepção de volume sem saturar ou apagar ambiente desejado.


### Ritmo e entrega


<a id="f42"></a>

#### F42 — Velocidade normal e curvas · P1

**Encontrado:** No celular, o menu de velocidade separa valor constante e curva.

**Revisitar:** [C11](https://www.capcut.com/resource/how-to-speed-up-a-video), [C12](https://www.capcut.com/resource/how-to-do-velocity-on-capcut).

**Na Lili hoje:** Velocidade constante 0,25× a 4× ativa; sem rampa.

**Aplicação proposta:** Manter Normal simples e adicionar Curva depois de modelo temporal consistente e prévia.

**Aceite:** Mudança de ritmo deve comunicar duração final e efeito sobre voz/legendas; nunca cortar fala silenciosamente.


<a id="f43"></a>

#### F43 — Congelar um quadro · P1

**Encontrado:** O guia móvel descreve escolher o quadro e aplicar congelamento, com duração ajustável.

**Revisitar:** [C17](https://www.capcut.com/resource/freeze-frame-final-cut-pro).

**Na Lili hoje:** Importação de foto existe; congelamento de quadro do vídeo não.

**Aplicação proposta:** Ação Congelar quadro cria trecho estático do instante aprovado, com duração explícita.

**Aceite:** Congelar o aceno deve segurar a pessoa, sem avançar para o mato do take seguinte. É diferente de proteger a cena.


<a id="f44"></a>

#### F44 — Exportar com parâmetros claros · P1

**Encontrado:** O fluxo do telefone leva a configurações de resolução e taxa de quadros e então à saída.

**Revisitar:** [C21](https://www.capcut.com/resource/capcut-tutorial-for-beginners), [V02 · 22:58–23:49](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=1378s), [C11](https://www.capcut.com/resource/how-to-speed-up-a-video).

**Na Lili hoje:** MP4/H.264 com quatro perfis; 30 fps fixos no motor atual.

**Aplicação proposta:** Resumo antes de gerar, FPS explicado, estimativa distinta de tamanho final e prévia curta de validação.

**Aceite:** Não prometer 4K/60 fps ou MOV enquanto não implementados; saída deve refletir a versão e os efeitos escolhidos.


<a id="f55"></a>

#### F55 — Encerramento padrão e marca do aplicativo · P1

**Encontrado:** Os tutoriais antigos mostram remoção do encerramento inserido pelo app.

**Revisitar:** [V01 · 01:26–01:40](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=86s), [V03 · 00:34–00:48](https://www.youtube.com/watch?v=KVws1GVHoA0&t=34s).

**Na Lili hoje:** A Lili não acrescenta encerramento de marca; marca de texto é opcional.

**Aplicação proposta:** Manter exportação sem marca obrigatória; deixar identidade do cliente como escolha explícita.

**Aceite:** Nenhum vídeo deve receber logo/encerramento da Lili por surpresa. Não assumir regras atuais de planos CapCut a partir desses vídeos.


### Recursos elaborados


<a id="f45"></a>

#### F45 — Templates de montagem · P2

**Encontrado:** A aula mostra modelos para substituir conteúdos preservando uma estrutura pronta.

**Revisitar:** [V03 · 01:37–02:52](https://www.youtube.com/watch?v=KVws1GVHoA0&t=97s).

**Na Lili hoje:** Montagem por roteiro/IA e rascunho; sem template visual salvo.

**Aplicação proposta:** Modelos próprios de vlog/review, com espaços explícitos e prévia antes de aplicar.

**Aceite:** Escolher modelo não deve apagar montagem aprovada sem confirmação; não importar template proprietário do concorrente.


<a id="f46"></a>

#### F46 — Tracking de texto ou objeto · P3

**Encontrado:** A aula define alvo e manda acompanhar seu movimento.

**Revisitar:** [V03 · 09:35–10:19](https://www.youtube.com/watch?v=KVws1GVHoA0&t=575s).

**Na Lili hoje:** Sem tracking.

**Aplicação proposta:** Futuro: alvo editável, progresso e correção manual; validar em animais e câmera de mão.

**Aceite:** Se perder o alvo, sinalizar e permitir corrigir, sem afirmar que o resultado está pronto.


<a id="f47"></a>

#### F47 — Desenho e escrita por cima do vídeo · P2

**Encontrado:** Há ferramenta de desenho, e a aula combina escrita com animação de revelação.

**Revisitar:** [V02 · 17:19–17:55](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=1039s), [V03 · 09:01–09:34](https://www.youtube.com/watch?v=KVws1GVHoA0&t=541s).

**Na Lili hoje:** Sem desenho/camada vetorial.

**Aplicação proposta:** Começar por setas/círculos; guardar traços editáveis e duração própria.

**Aceite:** Alterar duração do desenho não deve alterar a cena ou rasterizar o original.


<a id="f48"></a>

#### F48 — Câmera 3D · P3

**Encontrado:** O tutorial apresenta uma opção de movimento tridimensional.

**Revisitar:** [V03 · 08:37–09:00](https://www.youtube.com/watch?v=KVws1GVHoA0&t=517s).

**Na Lili hoje:** Não existe.

**Aplicação proposta:** Somente após camadas/keyframes; protótipo separado para avaliar custo e qualidade.

**Aceite:** Não colocar como disponível no catálogo inicial sem prévia/exportação correspondentes.


<a id="f49"></a>

#### F49 — Movimento flutuante de uma camada · P3

**Encontrado:** A aula ajusta movimento aplicado a um elemento sobreposto.

**Revisitar:** [V03 · 11:27–12:11](https://www.youtube.com/watch?v=KVws1GVHoA0&t=687s).

**Na Lili hoje:** Sem animação de overlays.

**Aplicação proposta:** Preset próprio discreto de oscilação, com amplitude e velocidade, respeitando área segura.

**Aceite:** A camada deve continuar legível e dentro da tela; intensidade zero remove o movimento.


<a id="f50"></a>

#### F50 — Retoque de rosto · P3

**Encontrado:** A aula usa ferramentas de retoque e suavização.

**Revisitar:** [V03 · 13:41–14:33](https://www.youtube.com/watch?v=KVws1GVHoA0&t=821s).

**Na Lili hoje:** Sem retoque.

**Aplicação proposta:** Avaliar somente após requisitos essenciais; desligado por padrão e sujeito à escolha da criadora.

**Aceite:** Comparação deve revelar o que mudou; não alterar rostos silenciosamente.


<a id="f51"></a>

#### F51 — Realçar palavras em uma imagem · P3

**Encontrado:** O exemplo combina bloco de cor, recorte, animação e mistura para destacar texto.

**Revisitar:** [V03 · 14:33–15:24](https://www.youtube.com/watch?v=KVws1GVHoA0&t=873s).

**Na Lili hoje:** Sem camadas/mesclagem necessárias.

**Aplicação proposta:** Primeiro um marcador gráfico simples; composições elaboradas dependem de overlays e máscaras.

**Aceite:** Realce não deve cobrir a palavra nem mudar o conteúdo; é composição, não legenda automática.


<a id="f52"></a>

#### F52 — Barras de cinema · P2

**Encontrado:** Um efeito adiciona barras à imagem durante um intervalo.

**Revisitar:** [V03 · 15:24–15:45](https://www.youtube.com/watch?v=KVws1GVHoA0&t=924s).

**Na Lili hoje:** Proporções de tela existentes; não há efeito letterbox próprio.

**Aplicação proposta:** Oferecer preset separado de formato de exportação; alertar sobre perda de área útil.

**Aceite:** Adicionar barras não pode mudar 9:16 para 16:9 sem avisar.


<a id="f53"></a>

#### F53 — Vídeo dentro de letras · P3

**Encontrado:** A técnica da aula combina texto, keyframes e composição de vídeos.

**Revisitar:** [V03 · 15:45–16:49](https://www.youtube.com/watch?v=KVws1GVHoA0&t=945s).

**Na Lili hoje:** Dependências de composição ausentes.

**Aplicação proposta:** Guardar como referência de efeito composto, depois de máscaras e keyframes.

**Aceite:** Não apresentar como um filtro simples que já funciona no render atual.


<a id="f54"></a>

#### F54 — Teleprompter · P3

**Encontrado:** O tutorial apresenta leitura guiada do roteiro durante captura.

**Revisitar:** [V03 · 16:50–17:13](https://www.youtube.com/watch?v=KVws1GVHoA0&t=1010s).

**Na Lili hoje:** Roteiro no projeto; sem captura guiada.

**Aplicação proposta:** Separar modo Gravar do modo Editar; priorizar narração própria antes desse recurso.

**Aceite:** Não solicitar câmera/microfone para editar um vídeo existente.


## 6. Propostas próprias para resolver a reclamação de precisão


### P01 — Posicionamento fino no telefone

Contador editável mm:ss:quadro ou mm:ss.mmm, botões de um quadro e passos maiores por pressão contínua. Esta combinação é proposta para a Lili; não foi confirmada como interface móvel do CapCut.

**Aceite:** A 30 fps, avançar um quadro deve somar exatamente 1/30 s no modelo, sem arredondar repetidamente. Ao exibir dois decimais, não confundir leitura com precisão interna. **Relacionadas:** F05, F06, F07, F08.


### P02 — Ímã temporal controlável

Encaixar em corte/cursor/início-fim de legenda com distância calculada em pixels; botão para desligar e indicação do alvo. A fala de alinhamento em V01 não comprova os detalhes desse algoritmo.

**Aceite:** Não puxar o cursor para um alvo distante quando o zoom mudar; prioridade ao ajuste manual fino. **Relacionadas:** F40, F60.


### P03 — Quadro solicitado versus quadro carregado

Manter o cursor estável ao soltar e mostrar carregamento até o player alcançar o instante. Evitar redesenhar o formulário inteiro em todo movimento.

**Aceite:** Busca rápida deve terminar na última solicitação; resposta atrasada de outra cena não pode substituir a seleção atual. **Relacionadas:** F03, F05, F07.


### P04 — Aplicação de efeito em rascunho

Escolher e ajustar em estado temporário; Aplicar grava uma alteração, Cancelar restaura. A confirmação visível foi observada, mas a implementação interna do CapCut não é conhecida.

**Aceite:** Fechar/cancelar a seleção não muda revisão nem histórico do projeto; falha do servidor não deixa parte do efeito aplicada. **Relacionadas:** F12, F15, F16, F17.


### P05 — Nomes distintos para travar

Pausar no instante, encaixar na régua, proteger escolhas e congelar quadro devem ter nomes e controles diferentes.

**Aceite:** Proteger uma cena não congela sua imagem; congelar não bloqueia edição de outras cenas. **Relacionadas:** F03, F07, F43.


### P06 — Catálogo executável e próprio

Biblioteca inicial local e gratuita, com presets, miniaturas e parâmetros versionados. Não extrair assets, fontes, modelos ou shaders proprietários do concorrente.

**Aceite:** Cada cartão disponível precisa ter preview e exportação testados; planejados vão para a esteira, não para botões falsos. **Relacionadas:** F14, F15, F30, F45.


### P07 — Mesma regra de tempo na prévia e render

Uma especificação única deve definir clipes, sobreposições, efeitos e transições. O cálculo interno do CapCut não foi inferido dos vídeos.

**Aceite:** Mudanças de duração devem explicitar efeito sobre voz/legendas e último quadro; não deslocar a narração aprovada silenciosamente. **Relacionadas:** F11, F12, F16, F42, F43, F44.


## 7. Transições: catálogo inicial e decisões de tempo

As fontes comprovam o seletor e a edição da duração; a seleção abaixo é recomendação de produto para vlogs/reviews da Elisa, **não um ranking de uso medido** e não uma cópia dos presets proprietários.

| Etapa | Efeito | Comportamento esperado na Lili | Dependência |
| --- | --- | --- | --- |
| Base | Corte seco / Sem transição | Troca imediata, reversível e claramente selecionável | Junções e catálogo. |
| Base | Dissolver / cross dissolve | Mistura progressiva de duas tomadas | Dois quadros/fontes no intervalo e política de sobreposição. |
| Base | Passar por preto / branco | A saída e a entrada encontram a cor escolhida | Definir duração total e distribuição entre os lados. |
| Base | Deslizar / empurrar | Deslocamento direcional legível | Direção, recorte e composição. |
| Base | Wipe / revelar | Uma imagem revela a outra | Máscara simples e direção. |
| Depois | Zoom, desfoque, giro, flash, glitch | Escolha editorial, com intensidade quando fizer sentido | Preview/render coerentes, custo e teste de qualidade. |

O modelo interno do CapCut não foi determinado. Para a Lili, escolher e documentar antes de codificar: transição com sobreposição encurtando a montagem ou uso de material adicional preservando os cortes. Se houver sobreposição de duração d em cada junção, um modelo possível é duração total = soma das durações dos clipes − soma das sobreposições. Isso é uma definição possível da Lili, **não uma afirmação sobre o CapCut**. Sobreposições que disputam o mesmo clipe curto também precisam de validação conjunta.

Narração, legendas e música exigem política explícita quando o total mudar. Preservar a fala aprovada e o último aceno tem prioridade sobre aplicar um efeito. Prévia deve compor as duas imagens no mesmo intervalo que o FFmpeg; uma animação CSS parecida não comprova render correto. Começar por dissolução e passagem por cor, com testes sintéticos de pixels, duração e áudio.

## 8. Ordem de criação sugerida

| Entrega | Itens para revisar antes | Resultado revisável |
| --- | --- | --- |
| 1 — Navegação precisa no telefone | F02–F08, F40; P01–P03/P05 | Gestos distinguíveis, busca estável, contador e ajuste fino por toque. |
| 2 — Nova aplicação de efeitos | F15–F18; P04/P06 | Catálogo e confirmação com estado temporário, ações de manutenção e intervalo visível. |
| 3 — Transições reais | F11–F14; P07 | Seletor na junção, dissolução/passagem por cor, duração e exportação sincronizadas. |
| 4 — Acabamento básico | F19/F20/F23/F31–F44/F56–F59 | Texto/áudio mais fáceis, looks próprios, narração e último quadro sob controle. |
| 5 — Movimento e composição | F24–F30/F45–F54/F60–F61 | Overlays, keyframes e recursos elaborados após as dependências. |

As entregas são dependências de produto, não uma nova automação ou obrigação de uma entrega inteira caber em uma noite. Pesquisa de mercado não substitui teste com a Elisa. Nesta etapa não foi instalado o CapCut nem testado o Safari real.

## 9. Como usar as referências no desenvolvimento

1. Localizar o Fxx e a proposta Pxx da tarefa.
2. Abrir o link do guia na subseção Mobile ou o YouTube já no instante indicado; a faixa final é limite de revisão, não garantia de que o botão aparece exatamente no primeiro quadro.
3. Conferir data, plataforma e eventual mudança de rótulo/catálogo antes de reproduzir o fluxo. Vídeos de 2023/2024 podem ensinar gestos ainda úteis sem representar a UI atual.
4. Escrever a regra da Lili, incluindo cancelamento, histórico, cenas protegidas, áudio e dados legados. Não inferir o código interno do concorrente.
5. Criar preview e exportação com a mesma semântica; usar projeto sintético. Registrar teste desktop e deixar Safari real pendente até teste humano.
6. Atualizar o estado do Fxx ou adicionar nota datada quando implementar; não reescrever uma proposta antiga como se já estivesse pronta.

O arquivo **capcut-mobile-referencias.json** guarda os IDs, URLs, localizadores, instantes, prioridades, estado local e aceites de forma pesquisável. As referências estão incorporadas ao repositório; não dependem de favoritos de um navegador ou da memória deste chat.

## 10. Índice de fontes para revisita

Todas consultadas em 24/10/2026. Descrições são resumos próprios. URLs preservam inclusive grafias peculiares do site oficial para evitar links inventados.


- **C01** — [Centro de ajuda CapCut](https://www.capcut.com/help). Localizador: Índice de ajuda; consultar a subseção Mobile de cada artigo.


- **C02** — [Transições: localização e condições](https://www.capcut.com/help/transitions-in-capcut). Localizador: How to Use Transitions in CapCut on Mobile.


- **C03** — [Aplicação e duração de efeitos](https://www.capcut.com/help/effectss-not-applying-in-capcut). Localizador: How to Add Effects in CapCut on Mobile.


- **C04** — [Catálogo e ajuste de efeitos no app](https://www.capcut.com/resource/special-effects-apps). Localizador: How to add video effects with this best video effects app.


- **C05** — [Desfoque e ações de um efeito](https://www.capcut.com/resource/blur-a-video-app). Localizador: How to create app blur videos with the CapCut app.


- **C06** — [Prévia e edição divergentes](https://www.capcut.com/help/editing-not-match-displayed). Localizador: CapCut Mobile App (iOS / Android). Limite: Usar diagnóstico de resultado; não reproduzir recomendações de limpeza de dados na Lili..


- **C07** — [Reconhecimento de legendas](https://www.capcut.com/help/how-to-recognise-subtitles). Localizador: CapCut Mobile App (iOS/Android).


- **C08** — [Dividir legendas](https://www.capcut.com/help/split-the-subtiltes). Localizador: CapCut Mobile App (iOS / Android).


- **C09** — [Corrigir legendas automáticas](https://www.capcut.com/help/auto-captions-in-capcut). Localizador: CapCut Mobile App (iOS / Android).


- **C10** — [Zoom com keyframes no celular](https://www.capcut.com/resource/how-to-zoom-in-on-video). Localizador: How to zoom in on a video edit with the CapCut mobile app.


- **C11** — [Velocidade no iPhone](https://www.capcut.com/resource/how-to-speed-up-a-video). Localizador: How to speed up a video on an iPhone using CapCut.


- **C12** — [Curvas e auto velocity móvel](https://www.capcut.com/resource/how-to-do-velocity-on-capcut). Localizador: Method 3. How to make a velocity edit on CapCut mobile app.


- **C13** — [Sobreposição no celular](https://www.capcut.com/resource/free-video-overlay-effects). Localizador: How to use video overlays on a phone: CapCut mobile app.


- **C14** — [Gravar voz, voz sintética e efeitos sonoros](https://www.capcut.com/resource/how-to-add-voice-in-a-video). Localizador: Way 2: Using record audio tool; Way 3: Using a sound tool.


- **C15** — [Extrair e editar áudio no app](https://www.capcut.com/resource/audio-extractor-from-mp4). Localizador: Here are the steps for extracting audio with the CapCut mobile app.


- **C16** — [Fluxo básico no app](https://www.capcut.com/resource/free-video-edit). Localizador: Using CapCut on the App (Android/iOS).


- **C17** — [Congelar quadro no celular](https://www.capcut.com/resource/freeze-frame-final-cut-pro). Localizador: How to freeze frame on Phone with CapCut. Limite: Página também contém Final Cut Pro e desktop; somente a seção Phone foi aproveitada..


- **C18** — [Mudanças de localização dos controles](https://www.capcut.com/help/capcut-ui-update-changes). Localizador: Why Did Feature Locations or the UI Change After I Updated CapCut?.


- **C19** — [Catálogo pode mudar ou perder efeitos](https://www.capcut.com/help/ai-templates-and-effects). Localizador: CapCut Mobile App (iOS/Android).


- **C20** — [Desfoque de movimento no celular](https://www.capcut.com/resource/motion-blur-effect). Localizador: CapCut mobile editing app / Add motion blur effect & edit.


- **C21** — [Introdução oficial ao telefone](https://www.capcut.com/resource/capcut-tutorial-for-beginners). Localizador: How to use CapCut for beginners on a mobile phone.


- **V01** — [CAPCUT - Como EDITAR VÍDEOS do Zero pelo CELULAR — Jefe Vilanova](https://www.youtube.com/watch?v=dmVeTHBQxEc). Localizador: Publicado em 20/04/2023; 34:27; capítulos e transcrição pt automática. Limite: Amostragem visual da interface móvel em torno de 03:26; transcrição analisada. Interface antiga: revalidar nomes e disponibilidade..


- **V02** — [CapCut App Video Editing Tutorial - How To Edit Videos On iPhone! — Justin Brown / Primal Video](https://www.youtube.com/watch?v=o6tcF1JLlwo). Localizador: Publicado em 06/03/2024; 25:13; transcrição pt disponibilizada pelo YouTube. Limite: YouTube mostrou dublagem automática em português. Amostras visuais em 05:23 e 14:08 confirmam telefone e catálogo; não é tutorial desktop..


- **V03** — [20 CapCut Mobile Effects to COMPLETELY Change your Editing — Matt Loui](https://www.youtube.com/watch?v=KVws1GVHoA0). Localizador: Publicado em 20/10/2025; 17:28; transcrição en automática. Limite: Amostragem visual em 03:50 confirma camada de ajuste no telefone. Publicidade externa ignorada; recursos gratuitos/Pro não foram auditados em conta real..


## 11. Roteiro de revisita dos 20 tópicos do tutorial móvel V03

Este mapa cobre os tópicos técnicos do vídeo; o trecho de patrocínio e a oferta de curso não são funções do editor. Os instantes vieram dos capítulos/transcrição, sem promessa de que o recurso continue gratuito ou com o mesmo nome.

| Ponto do vídeo | Catálogo deste estudo |
| --- | --- |
| [00:34 — encerramento/marca](https://www.youtube.com/watch?v=KVws1GVHoA0&t=34s) | F55 |
| [00:49 — cor seletiva](https://www.youtube.com/watch?v=KVws1GVHoA0&t=49s) | F21 |
| [01:37 — modelos](https://www.youtube.com/watch?v=KVws1GVHoA0&t=97s) | F45 |
| [02:53 — camada de ajuste](https://www.youtube.com/watch?v=KVws1GVHoA0&t=173s) | F22 |
| [03:58 — zoom suave](https://www.youtube.com/watch?v=KVws1GVHoA0&t=238s) | F24/F25 |
| [05:24 — movimento de câmera](https://www.youtube.com/watch?v=KVws1GVHoA0&t=324s) | F26 |
| [06:02 — B-roll e animação](https://www.youtube.com/watch?v=KVws1GVHoA0&t=362s) | F23/F27 |
| [08:37 — câmera 3D](https://www.youtube.com/watch?v=KVws1GVHoA0&t=517s) | F48 |
| [09:01 — desenho](https://www.youtube.com/watch?v=KVws1GVHoA0&t=541s) | F47 |
| [09:36 — rastreamento](https://www.youtube.com/watch?v=KVws1GVHoA0&t=576s) | F46 |
| [10:20 — remoção de fundo](https://www.youtube.com/watch?v=KVws1GVHoA0&t=620s) | F29 |
| [10:55 — elementos gráficos](https://www.youtube.com/watch?v=KVws1GVHoA0&t=655s) | F28/F30 |
| [11:27 — flutuação](https://www.youtube.com/watch?v=KVws1GVHoA0&t=687s) | F49 |
| [12:15 — voz](https://www.youtube.com/watch?v=KVws1GVHoA0&t=735s) | F41 |
| [13:41 — retoque](https://www.youtube.com/watch?v=KVws1GVHoA0&t=821s) | F50 |
| [14:33 — realce de palavras](https://www.youtube.com/watch?v=KVws1GVHoA0&t=873s) | F51 |
| [15:24 — barras](https://www.youtube.com/watch?v=KVws1GVHoA0&t=924s) | F52 |
| [15:45 — vídeo nas letras](https://www.youtube.com/watch?v=KVws1GVHoA0&t=945s) | F53 |
| [16:50 — teleprompter](https://www.youtube.com/watch?v=KVws1GVHoA0&t=1010s) | F54 |
| [17:14 — desfazer](https://www.youtube.com/watch?v=KVws1GVHoA0&t=1034s) | F04 |

## 12. O que ficou sem confirmação

- Versão/build específico do CapCut instalado por Elisa; nenhuma conta/aparelho dela foi acessado.
- Lista completa atual de efeitos gratuitos/Pro por país, licenças de assets e disponibilidade offline.
- Botões de avanço de um quadro, editor numérico de timecode e chave específica de ímã na UI móvel atual. São propostas da Lili quando indicadas acima.
- Motor/algoritmo de busca de frames, render de transições, política exata de handles e eventual ripple usado internamente pelo CapCut.
- Exportação SRT universal no app móvel; fontes variam por região/versão e algumas páginas se contradizem.
- Tutorial não prova ganho de produtividade ou qualidade: validar tarefas curtas com Elisa, especialmente corte final, legenda e entrada da narração.

## 13. Verificação desta entrega

Verificação estática executada: 61 IDs de funções únicos, sete propostas próprias, 24 fontes, referências existentes, URLs oficiais de documentação, IDs de vídeo válidos e intervalos crescentes dentro da duração de cada vídeo. Todo Fxx tem proposta, aceite e âncora no relatório. Links Markdown, JSON e diff conferidos. Transcrições confirmadas como ignoradas pelo Git. A suíte do editor não foi executada, pois esta entrega não muda código. Publicação restrita à documentação, sem transcrições completas, mídia ou dados privados.
