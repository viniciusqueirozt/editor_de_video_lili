# Esteira da Lili

## Entregue nesta versão

- Identidade visual da inicial nas telas do editor, painéis, linha do tempo e janelas.
- Menu de projeto compacto no celular.
- Exclusão permanente de projeto já na Lixeira, com confirmação digitada e bloqueio de processamentos. Remove apenas dados na pasta do projeto; arquivos fora dela permanecem.

## Prioridade de interação móvel — pesquisa de 24/10/2026

O usuário relatou falta de transições reais, aplicação ruim de efeitos, configurações confusas e dificuldade para parar no instante desejado. A próxima evolução de edição deve resolver esse fluxo antes de aumentar o formulário ou adicionar efeitos isolados.

Base de trabalho: [estudo detalhado do CapCut Mobile](capcut-mobile-estudo-interface-funcoes.md) e [índice pesquisável de referências](capcut-mobile-referencias.json). São 61 funções/fluxos, sete propostas próprias e 24 fontes, incluindo três tutoriais específicos de celular. A pesquisa não implementou esses recursos nem validou Safari real.

- [ ] P0: seleção e ferramentas contextuais; distinguir navegar, selecionar, aparar e reordenar. Revisitar F02–F08, P01/P03/P05.
- [ ] P0: pinça, cursor estável, controle fino por toque e quadro carregado; ímã temporal opcional. Revisitar F05–F08/F40, P01–P03. Avanço por quadro no telefone é proposta própria, não controle confirmado do CapCut.
- [ ] P0: catálogo visual e aplicação/cancelamento de efeitos, com intervalo próprio e manutenção do bloco. Revisitar F15–F18, P04/P06.
- [ ] P0: transição na junção, duração e prévia de duas tomadas. Começar por dissolução e passagem por cor; definir regra temporal e preservar voz/legendas/último quadro. Revisitar F11–F14, P07.
- [ ] P1: fluxo simples de música, gravação de narração, legendas e congelamento do quadro escolhido. Revisitar F31–F44 antes de escolher o pacote.

Antes de implementar, abrir a referência do Fxx na seção Mobile ou no minuto marcado do vídeo. Verificar plataforma e versão; separar documentação, amostragem visual, transcrição e proposta. Cada tarefa deve registrar os IDs consultados, comportamento da Lili, testes e estado de ativação. Efeitos elaborados permanecem após a base, conforme o catálogo do estudo.

### Primeira implementação após o estudo — 24/10/2026

Entregue parcialmente F05–F08/P01/P03: painel Precisão, posição digitável, passo de um quadro da montagem, aparo no cursor com Desfazer, busca que conserva o último destino, inspetor estável e pinça restrita à régua. Aparo por arraste conserva a saída escolhida e considera fades sonoros. Interface ativa após recarregar; Safari real pendente. Os dois itens P0 acima continuam abertos porque seleção contextual completa, pinça sobre todas as trilhas e ímã ainda faltam.

Relatório e verificação: [rodada de precisão](rodada-precisao-timeline-24-10-2026.md). Próxima prioridade de edição: transição real na junção e aplicação visual de efeitos.

### Noite de 24 para 25/10 — transições preparadas

Rodada 1 implementou passagem por preto/branco e corte seco ligados a IDs de cenas adjacentes, catálogo, duração, prévia local e Aplicar/Cancelar, com histórico e exportação. Testada em ambiente sintético; produção ainda sem a capacidade pair_transitions, aguardando fechamento do ciclo. Dissolução, sobreposição e aplicação em todas as junções continuam pendentes. F11/F12/F14/P04/P07 avançaram parcialmente; não marcar o P0 inteiro como concluído.

Detalhes e verificação: [rodada noturna de transições](rodada-noturna-2026-10-24-01-transicoes.md). Continuação: catálogo de aparências implementado na rodada 2 abaixo.

### Noite de 24 para 25/10 — aparências com rascunho

Rodada 2: catálogo de seis aparências locais mais Atual, miniaturas do vídeo, intensidade, comparação pausada, Quadro central, reprodução da cena e Aplicar/Cancelar. Usa os ajustes RGB existentes; fica disponível após recarregar, sem reinício. Publicação Git aguarda o fim do ciclo. Não é camada independente ou efeito temporizado; Original restaura os valores de cor e Desfazer recupera os anteriores. F15/F18/F20/P04/P06 avançaram parcialmente; os itens P0 completos permanecem abertos.

Verificação e limites: [rodada 2 de aparências](rodada-noturna-2026-10-24-02-aparencias.md). Próxima frente: posicionamento e aparo de áudio na linha do tempo, respeitando os limites existentes.

## Prioridade de execução — 24/10/2026

O usuário definiu quatro rodadas de recursos de edição, uma revisão dedicada de segurança e uma extra condicional para visual e pesquisa de concorrentes/monetização. Esta estrutura substitui a prioridade anterior de concentrar as rodadas em identidade e contas.

| Rodadas | Prioridade |
| --- | --- |
| 1 a 4 | Edição de vídeo: montagem, efeitos, transições, marca d'água, legendas, áudio, formato, exportação, importação, exclusão e melhorias práticas do fluxo. |
| 5 | Segurança e contas: procurar/corrigir falhas e melhorar login, convites, sessões, identidade, recuperação de acesso e permissões. |
| Extra, se houver margem | Melhoria visual e pesquisa objetiva de mercado, concorrentes e modelos de monetização. |

A divisão interna dos quatro temas é flexível conforme os problemas mais úteis de resolver. Contas individuais e permissões podem avançar na rodada de segurança, conforme esclarecimento do usuário. Compartilhamento e nuvem seguem planejados nas seções abaixo, sem ocupar por padrão as quatro rodadas de edição. Nuvem depende de identidade/permissões, escolha do destino e autorização antes de enviar arquivos.

Regras de execução e relatório: outputs/estrutura-das-rodadas.md. Consultar os limites depois dos testes e informar os percentuais restantes ao usuário ao final de cada rodada. A agenda anterior foi substituída por duas janelas da mesma rotina recorrente neste chat: 23h55 e 00h55–03h55, com extra após a última rodada e publicação ao final. Excluída sexta à noite para sábado; trabalho encerra antes das 5h.

## Projetos privados e compartilhamento

### Estado atual e migração

Base de autorização preparada em código e testes nesta etapa: identidade confiável injetada pelo servidor, proprietário por projeto, permissões separadas e revogação. A base só é aplicada quando há um resolvedor de identidade configurado na construção do servidor; não há configuração ativa no ambiente real nem opção de ativação pela interface.

As contas do portal são individuais, mas o editor em produção ainda usa um login compartilhado e não associa os projetos existentes a proprietários. Não há isolamento por usuário implementado; esconder cartões na interface não resolve isso. Será necessário integrar a identidade ao servidor do editor e conferir permissões em cada operação. Não apresentar o estado atual como ambiente privado entre colegas.

- Associar cada projeto a um proprietário identificado por ID estável, nunca apenas pelo nome exibido ou por e-mail enviado pelo navegador.
- Migrar os projetos existentes com associação explícita ao proprietário correto, preservando arquivos, montagem aprovada e histórico. Não atribuir ao primeiro visitante que entrar.
- Validar uma sessão individual no editor vinculada à conta autorizada; não reutilizar a senha do portal em outro serviço nem depender de um ID de usuário livremente informado pelo cliente.
- Separar a capacidade de administrar convites do portal da autorização para abrir material de todos os projetos. Acesso de suporte/administração ao conteúdo exige regra explícita e registro.

### Progresso da primeira etapa

- [x] Política de autorização no servidor e criação privada a partir de identidade autenticada fornecida pelo servidor.
- [x] Regras separadas de visualizar, editar, baixar final e baixar originais; só o dono gerencia permissões e exclusão de projeto.
- [x] Rotas de projeto, mídia, jobs e operações verificadas em testes com duas identidades; revogação bloqueia requisições seguintes.
- [x] Sem confiar em cabeçalhos/IDs de usuário enviados livremente pelo navegador; metadados de acesso fora do contexto público; Desfazer não restaura autorizações revogadas.
- [x] Preparar transporte local assinado, de validade curta e uso único, testado com a política por projeto; ainda sem ativação.
- [x] Preparar gateway opcional que exige identidade resolvida pelo servidor e assina requisições locais, sem fallback compartilhado; testado com sessões sintéticas, ainda inativo.
- [x] Preparar cliente de validação HTTPS de sessão opaca do editor, sem cache de autorização e com testes de integração usando portal simulado; endpoint do portal ainda pendente.
- [ ] Integrar identidade e sessão individual ao portal/gateway, incluindo expiração/revogação e validação da conta.
- [ ] Associar explicitamente os projetos existentes aos proprietários corretos; nunca atribuir ao primeiro visitante.
- [ ] Diretório de contas, confirmação de identidade/e-mail e interface de Compartilhar/Compartilhados comigo.
- [ ] Validar transporte real com duas contas e autorizações em todos os caminhos antes de ativar privacidade em produção.

Detalhes: outputs/base-de-permissoes.md. Os itens marcados não significam que o modo privado já esteja disponível para os usuários.

### Permissões por projeto

Padrão: privado. O proprietário decide a quem liberar e quais ações permitir.

| Permissão | Pode fazer | Não concede automaticamente |
| --- | --- | --- |
| Visualizar | Abrir o projeto e assistir às prévias autorizadas. | Editar, exportar, baixar originais ou compartilhar. |
| Baixar vídeo final | Baixar as entregas autorizadas. | Baixar gravações originais nem editar. |
| Baixar originais | Baixar as mídias liberadas pelo proprietário. | Editar ou redistribuir acesso. |
| Editar | Alterar roteiro, cortes, textos e áudio; gerar prévias/exports conforme regra do projeto. | Convidar outras pessoas, trocar proprietário ou excluir o projeto inteiro permanentemente. |
| Proprietário | Gerenciar projeto, convites e permissões; arquivar, restaurar ou excluir o projeto. | Acesso aos projetos de outros proprietários. |

Editar implica poder visualizar. Download de arquivos originais e compartilhamento ficam explícitos. O controle de download regula os endpoints e botões de originais/entregas; não promete impedir captura da tela ou gravação de algo que a pessoa consegue assistir.

- Convidar uma conta por e-mail; confirmar a identidade da pessoa antes de permitir material privado. O portal atual não verifica automaticamente a propriedade do e-mail, portanto essa parte precisa ser resolvida na implementação.
- Mostrar Proprietário, Privado / Compartilhado, pessoas com acesso, permissões e convites pendentes. Para o convidado, uma área Compartilhados comigo.
- Permitir alterar/revogar acesso e expirar convites. Revogação bloqueia novas leituras, downloads e alterações; links temporários também precisam de política de invalidação/expiração.
- Verificar autorização no servidor para listagem, contexto, mídia original/proxy/miniatura, áudio, uploads, jobs, exportação, histórico, lixeira, exclusão, MCP/CLI e futuros arquivos em nuvem. Conhecer um ID ou URL não concede acesso.
- Não implementar compartilhamento público irrestrito como padrão. Um link de revisão público, se solicitado futuramente, terá escopo, prazo e autorização próprios.

### Conflitos, revisão e auditoria

- Começar com edição coordenada: revisão atual, aviso de outra pessoa editando e bloqueio/lease por projeto quando necessário. Não prometer edição simultânea em tempo real nesta primeira etapa.
- Preservar histórico recuperável; identificar autor, data e natureza das alterações. Desfazer de uma pessoa não pode apagar silenciosamente o trabalho recente da outra.
- Registrar concessão/revogação, alterações relevantes, downloads e exclusões sem gravar senhas, tokens ou conteúdo sensível nos logs.
- Depois: comentários com marcação de tempo, pedidos de ajuste, versões de revisão e aprovação do vídeo final.

### Critérios de aceite para privacidade

Testar duas contas e dois projetos: nenhum usuário pode listar/abrir/baixar/editar/excluir o projeto do outro sem permissão, mesmo chamando a API diretamente ou adivinhando IDs. Conferir que visualizar não permite editar, baixar final não libera originais e revogar realmente interrompe o acesso. Incluir jobs em andamento, sessão expirada, identidade inválida e projetos migrados.

## Acabamento: transições, textos e som

### Transições

- Primeira biblioteca: corte seco já existente, dissolução, fade para preto/branco e transição simples de áudio entre cenas.
- Escolher transição na junção de duas cenas, com duração, prévia, remover, desfazer e opção de aplicar às junções compatíveis.
- Tratar duração insuficiente e reserva de quadros nas bordas sem repetir tomadas ou cortar falas silenciosamente. Recalcular o tempo total e sincronismo da narração quando houver sobreposição.
- Depois: movimentos de entrada/saída e presets discretos; evitar encher a edição de efeitos por padrão. A IA pode sugerir, mas mantém a escolha editável.

### Legendas e tipografia

- Faixa de legendas com texto e tempos editáveis, divisão/união, ajuste por frase e importação/exportação SRT/VTT.
- Transcrição local quando as dependências/modelos estiverem definidos; revisão humana de nomes e palavras. Não anunciar legenda automática antes de existir transcrição funcional.
- Pequeno catálogo de fontes com licença adequada para distribuição e vídeos comerciais, acentos em português e uso consistente na prévia e no FFmpeg.
- Controles: família, tamanho, peso quando suportado, cor, alinhamento, posição, fundo, contorno, sombra e área segura para Instagram/TikTok. Limitar texto às bordas do vídeo sem depender só de coordenadas da tela do celular.
- Presets legíveis e estilos próprios da Elisa; títulos simples, legendas e créditos. Depois, animação por palavra e destaque de termos, com opção de desligar.

### Música e efeitos sonoros

- Biblioteca inicial enxuta: ambiente, clique, pop, whoosh e pequenos acentos. Importar áudio próprio continua necessário.
- Catálogo com origem e licença de cada recurso; priorizar gravações próprias ou itens cuja licença permita uso e distribuição pretendidos. Não copiar bibliotecas do CapCut nem prometer uso comercial de sons sem conferência.
- Faixas separadas de narração, música e efeitos; arrastar/posicionar, cortar, duplicar, ajustar volume, silenciar e aplicar fades. Encaixar o efeito no corte/evento, com indicador de tempo.
- Controle de pico/clipagem e nivelamento; depois, reduzir música enquanto há fala e tratamento local de ruído. Prévia e exportação devem ter o mesmo comportamento.
- Depois: marcação de batidas, ajuste musical ao tempo e favoritos do criador.

## Necessidades complementares identificadas

- Organização: pastas/etiquetas, busca, duplicação de projeto e versões antes/depois, sem compartilhar mídias entre proprietários por acidente.
- Linha do tempo: encaixe nos cortes (snap), seleção múltipla de cenas, dividir/aparar/duplicar, reorganizar e controle explícito de ripple para não desalinhar áudio.
- Velocidade: aceleração/câmera lenta com duração recalculada, áudio compatível e narração preservada conforme escolha. Rampas de velocidade ficam para etapa posterior.
- Imagem: rotação, recorte, enquadramento, proporções, exposição, contraste, temperatura e saturação, com redefinição de ajustes e consistência no export.
- Entrega: presets de resolução/fps/qualidade, área segura, revisão de duração e áudio, nome de arquivo, fila de exportação e indicação inequívoca de export final desatualizado após editar o projeto.
- Robustez: autosave, recuperação, versão anterior, importação interrompida, cancelamento de uploads abandonados, armazenamento disponível e tarefas em segundo plano.
- Mobilidade: gestos e alvos de toque, linha do tempo com zoom e rolagem, teclado sem cobrir campos, acessibilidade e teste real no iPhone.
- Custo e privacidade: recursos locais sempre que viável; mostrar antes quando uma ação usa conta/limites do Codex ou envia dados para análise externa. Sem APIs pagas contratadas automaticamente.
- Produto comercial futuro: separação entre espaço pessoal/equipe, cotas, auditoria e política de retenção. Não transformar isso em promessa de infraestrutura gratuita ilimitada.

## Nuvem, backup e liberação local

Solicitação registrada em 22/10/2026. Ainda não implementada. Não há envio de dados nem backup remoto ativo.

### 1. Escolher o destino e conectar a conta

Avaliar o provedor com o usuário antes de integrar: espaço disponível, custo, tamanho dos vídeos, upload pelo notebook e permissão por projeto. Usar autenticação oficial com permissões mínimas; não pedir senhas no chat nem guardar tokens no Git. Nenhum plano pago deve ser contratado automaticamente.

### 2. Cópia verificável do projeto

Enviar gravações originais importadas, áudios, roteiro, metadados da montagem e vídeo final escolhido. Prévias e caches podem ser recriados e não precisam ocupar a nuvem por padrão. Manifesto de arquivos com tamanho e hash, cópias por revisão e histórico separado da sincronização. Excluir localmente não deve apagar o último backup remoto automaticamente.

### 3. Envio em segundo plano

Fila persistente, progresso, retomada de transferências interrompidas, novas tentativas com espera e tratamento de cota/espaço insuficiente. Mudanças durante o upload geram nova revisão; uma cópia só recebe o estado Verificada depois de conferir os arquivos e o manifesto no destino. Não mostrar Backup ativo enquanto houver falha ou pendência.

### 4. Arquivar na nuvem e liberar o notebook

Ação explícita disponível apenas após cópia íntegra verificada. Guardar no notebook uma referência pequena ao projeto arquivado, miniatura e localização remota. Liberar arquivos grandes, proxies e exports locais com confirmação. Não usar uma pasta de sincronização como garantia de backup: a exclusão pode se propagar.

### 5. Restaurar para editar

Baixar os arquivos necessários para o notebook, validar os hashes e abrir a mesma montagem. Mostrar estado Arquivado / Baixando / Pronto para editar. O processamento continua no notebook; a hospedagem do portal não passa a armazenar nem editar os vídeos.

### Critérios para considerar o backup pronto

- Restaurar um projeto sintético completo e comparar montagem e arquivos.
- Simular conexão interrompida, cota esgotada, reinício do notebook e revisão concorrente.
- Confirmar que nenhuma remoção local ocorre com backup pendente ou divergente.
- Documentar retenção, recuperação e exclusão definitiva remota separadamente.

## Outras pendências

- Cancelamento explícito preparado na API, cliente e botão da interface; aparece somente quando o servidor anuncia suporte após início normal. Falta listar/recuperar pendências após recarregar a página e expirar/recuperar a fila após reinício.
- Legendas locais, perfis de estilo e formatos adicionais de projeto.
- Inicialização do conector após reinício do Windows.
- Validação da interface no Safari real, além dos testes no notebook.

## Segurança preparada — madrugada de 23/10/2026

Recusa de cabeçalhos de segurança duplicados nos dois servidores, com testes de regressão do login e da identidade. Entra nos próximos inícios normais dos processos, sem reinício automático nesta agenda. A preparação de contas individuais continua separada da ativação real; ver outputs/base-de-permissoes.md.

## Base de edição e mercado — 24/10/2026

Avaliação detalhada e próximos blocos em outputs/mercado-e-basico-da-lili.md. Priorizar cor/luz e fontes do iPhone, trilha musical/áudio, velocidade e dissolução sincronizada, legendas temporizadas/SRT e composição com fotos/logotipos/keyframes. As quatro rodadas deste ciclo prepararam fades, estilos de texto, formatos/perfis e enquadramento/marca de texto; detalhes de testes e ativação em outputs/relatorio-ciclo-24-10-2026.md.


## Ciclo manual ampliado de 24/10/2026

Código e verificações detalhados em outputs/relatorio-ciclo-24-10-2026.md. Recursos implementados: fades visuais, luz/cor, velocidade constante, enquadramento/espelhamento, marca de texto, estilos de títulos, legendas independentes com SRT, formatos e perfis MP4, música independente com redução durante narração e limitador da mistura, fotos estáticas e Refazer. Editor publicado e ativo ao final da revisão; gateway segue com ativação de suas correções pendente para preservar sessões. Verificação detalhada no relatório.

Próximas lacunas: dissolução entre cenas com prévia coerente, keyframes, fotos/logotipos em camadas, HDR/SDR, transcrição local e biblioteca de efeitos sonoros licenciados. Contas individuais integradas e nuvem não foram ativadas por este ciclo.


## Áudio — rodada 3 da noite de 24/10

Implementado painel de música/voz com rascunho, início preciso, alinhamento ao cursor, aparo sincronizado da música, volume/fades/redução, forma de onda de música e voz e aplicação única reversível. Frontend disponível após recarregar pela API já ativa, sem reiniciar serviços; sincronização no encerramento do ciclo. Validação/limites em outputs/rodada-noturna-2026-10-24-03-audio.md. Pendentes: arraste das faixas, ímã/batidas, aparo/split da narração, múltiplos sons e biblioteca licenciada. Uma música e uma narração continuam sendo os limites atuais. Safari real não validado.


## Legendas — rodada 1 da noite de 28/10

Código/testes preparados para painel de rascunho de texto, tempo e estilo, criação sem placeholder gravado, movimento/aparo precisos, padronização opcional da tipografia em lote e aplicação reversível. Reutiliza caption_add/update/remove e captions_replace, sem backend novo. Testes de prévia e exportação sintética passaram; revisão visual bloqueada pela inicialização do navegador, sem validação de Safari. Editor real 8765 não respondeu: ativação pendente, sem alteração dos serviços reais. Relatório/pendências: outputs/rodada-noturna-2026-10-28-01-legendas.md. Priorizar retomar a revisão visual e conferir ativação ao fechar a noite; depois entrega/exportação, arraste/divisão de legendas e fontes licenciadas. Não contar os três checkpoints ainda locais do ciclo anterior como publicados.


## Entrega/exportação — rodada 1 da noite de 31/10

Implementados avisos concretos com atalhos de revisão, bloqueio de fontes indisponíveis antes de gerar job e envio mais robusto contra cliques duplicados, trocas de projeto e respostas incertas da rede. Frontend já servido; pré-validação nova do backend preparada para ativação segura no fechamento. Sem reinício de serviços. Suíte final de 137 testes Python e 18 arquivos JavaScript aprovados; detalhes de tentativas/limites em outputs/rodada-noturna-2026-10-31-01-exportacao.md. Pendentes: revisão visual desktop/Safari, estimativa/checagem de espaço para saída, nome de arquivo e tratamento HDR/SDR. Quatro checkpoints anteriores continuam preservados e sem sincronização; publicar junto ao fechar a extra/segurança desta noite.


## Precisão — rodada 2 da noite de 31/10

Implementado ímã opcional em Precisão para régua e bordas de vídeo, com alvos dos cortes/áudios/legendas, guia, limites de distância, Shift e preferência local. Digitação e passos por quadro livres. Proteções de fades/velocidade preservadas e arredondamento na duração fracionária corrigido. Frontend servido; 19 arquivos JavaScript e quatro testes Python focados aprovados. Revisão visual não concluída por falha do runtime de controle desktop; Safari real pendente. Detalhes: outputs/rodada-noturna-2026-10-31-02-ima.md. Permanecem pendentes arraste de faixas, batidas/marcadores e aparo da narração. Não se alterou a ativação pendente do backend de exportação nem a publicação acumulada do ciclo.


## Narração — rodada 3 da noite de 31/10

Aparo não destrutivo da fonte de voz preparado no modelo, painel, prévia, waveform, ímã, avisos e exportação. Rascunho, restauração do arquivo inteiro, fades limitados ao trecho e histórico preservados; compatibilidade com projetos antigos sem start/end. Corrigido posicionamento de áudio reproduzido em teste sintético por reconstrução de timestamps após atraso. Suíte final: 139 testes Python e 19 arquivos JavaScript aprovados; detalhes e falhas anteriores em outputs/rodada-noturna-2026-10-31-03-narracao.md. Aparo de voz ainda depende da capacidade narration_trim no próximo início seguro do servidor; não ativo na produção consultada. Não houve reinício nem sincronização GitHub nesta rodada. Permanecem pendentes revisão visual/Safari, movimentação direta e divisão das faixas, múltiplos sons e biblioteca licenciada. O ímã da rodada 2 está implementado; batidas e marcadores manuais continuam pendentes.


## Movimento de áudio — rodada 4 da noite de 31/10

Movimentação direta de música/narração implementada por alça de toque, com encaixe de ambas as extremidades, cancelamento, comando único e proteção da fila por projeto/revisão. Usa a API já existente, frontend servido e disponível ao recarregar. Testes: 20 arquivos JavaScript e seis Python focados passaram; produção saudável, sem reinício. Detalhes: outputs/rodada-noturna-2026-10-31-04-mover-audio.md. Revisão visual desktop e Safari permanecem pendentes por bloqueio do runtime de controle. Não há rolagem automática nas bordas nem divisão/múltiplos blocos de áudio; trechos longos podem terminar fora da montagem com aviso. Publicação acumulada e ativação do aparo de voz/pré-validação de fontes continuam reservadas ao fechamento desta noite. Prioridade seguinte: segurança/acesso/contas e publicação.


## Correção direta de conexão — 01/11/2026

Portal versão 3 publicado e conector atualizado: presença independente da reconexão, recuperação de estado inativo, limites de espera, consultas serializadas e indicação de última comunicação. Estado saudável e heartbeat recente confirmados no banco real. Editor/gateway preservados, sem ativar backend de edição pendente. Relatório em outputs/correcao-conexao-portal-01-11-2026.md. Testes de servidor/poller e build passaram; Safari real e inicialização automática do conector continuam pendentes. Não conta como rodada noturna de segurança/extra.


## Conversa e dissolução — entrega direta de 01/11/2026

Conversa contextual por projeto, histórico, pedidos sucessivos sobre a revisão atual e preservação de ajustes existentes implementados. Atalhos locais de dissolução e silenciar som original não chamam Codex. Dissolução real com duração da timeline preservada, aplicação em lote nas junções desprotegidas, prévia fiel renderizada e manutenção dos tempos dos fades. Código 3119048 publicado e ativo após início seguro apenas do editor; gateway/conector/túnel e sessões preservados. Backend de narração/pré-validação de fontes antes pendente também ativo. Suíte final de 147 testes Python e 21 arquivos JavaScript passou, incluindo exportação 1080 × 1920 e pixels/áudio sintéticos. Relatório: outputs/conversa-e-dissolucoes-01-11-2026.md. Revisão visual/Safari pendente; composição de camadas, wipes/zoom/keyframes, crossfade sonoro, contas integradas e nuvem permanecem pendentes. Esta entrega direta não conclui a rodada noturna de segurança/extra.


## Entrega direta — som independente e preparação Concat, 01/11/2026

Implementados blocos de som original separados na inserção pela interface, painel de trecho/posição/velocidade/volume/fades/proteção, arraste, dividir/duplicar/remover, histórico e mixagem/exportação sem duplicar o áudio embutido. Projetos antigos não são convertidos só por abrir: a primeira ação de áudio separa em um comando reversível. Montagem assistida conserva sons já independentes ao trocar imagens. Relatório: [áudio independente](audio-independente-01-11-2026.md). Código c65709d ativado após checagem sem jobs/envios pendentes; capacidade confirmada, gateway/conector/túnel mantidos. Safari/visual desktop reais pendentes.

Concat: referência fixada, inventário de módulos e ponte MCP de descoberta somente leitura preparados. Motor nativo não instalado; editing_ready=false. Catálogo de efeitos, transcrição, máscaras, keyframes e renderização Concat NÃO estão ativos na Lili. Em 02/11/2026, o usuário determinou definir a licença antes de copiar código; não autorizou relicenciar a Lili nem torná-la código aberto. Implementações próprias e análise técnica podem continuar sem incorporar código do Concat. Próximo passo da integração: definir reutilização/distribuição, disponibilizar build compatível e validar o adaptador em projetos sintéticos, preservando a interface/motor existentes até equivalência comprovada. Referências e critérios: [integração Concat](integracao-concat.md).


## Noite de 01 para 02/11 — rodada 1, sons da biblioteca

Preparados Som no cursor para áudios próprios/som de vídeos sem substituir música ou voz, inserção limitada ao espaço restante, edição do bloco e proteções da fila. Atalho de silenciar originais passa a preservar sons avulsos. Fades rápidos Sem/Curto/Suave no painel, com rascunho e limites pelo trecho; faixa renomeada Sons e atalho da faixa vazia à biblioteca. Passaram 22 testes Python focados (dois novos) e 23 arquivos JavaScript (um novo), com áudio sintético exportado e medido. Frontend dos fades servido; inserção e filtro de categoria aguardam capacidade library_sounds no backend. Sem reinício, GitHub acumulado no fechamento; editor/login remoto saudáveis. Visual desktop/Safari real pendentes. Relatório: [rodada de sons](rodada-noturna-2026-11-01-01-sons.md). Próximo pacote às 00h55: junções/controles de transição, após conferir orçamento.


## Noite de 01 para 02/11 — rodada 2, escolher transições

Controles de junção distribuídos sem sobreposição com alvos de 44 px, marcadores em todos os cortes e acesso completo por seletor. Painel com Anterior/Próximo, número/tempo, duas miniaturas reutilizadas durante ajustes e contagem de junções desprotegidas. Abertura/salvamento protegidos por projeto/revisão e Cancelar bloqueado durante gravação. Nenhum estilo novo nesta rodada. Passaram 24 arquivos JavaScript (um novo) e dez testes Python focados existentes, incluindo exportação sintética medida. Frontend servido e compatível com API ativa; sem reinício/GitHub acumulado até o fechamento. Visual desktop/Safari pendentes. Relatório: [rodada de transições](rodada-noturna-2026-11-01-02-transicoes.md). Próximo pacote às 01h55: lacuna de montagem/transições conforme orçamento renovado.


## Diretriz de licenciamento — 02/11/2026

O usuário definiu que a Lili deve manter código fechado. Não incorporar, portar ou traduzir código AGPL do Concat, incluindo módulos, efeitos/shaders e wrappers. Usar referências funcionais para desenvolvimento próprio e avaliar componentes diretamente de suas fontes com licença compatível, preservando avisos e conferindo dependências/modelos. Concat via MCP não será ativado como motor supondo que processo separado elimina obrigações. O bridge de consulta continua apenas preparado; nenhuma licença do projeto foi alterada. Candidatos e limitações registrados em [integração Concat](integracao-concat.md). Antes da distribuição comercial, conferir também o build/encoders do FFmpeg e demais recursos embarcados. Esta diretriz vale nas próximas rodadas automáticas; não é um novo pacote de edição nem conclusão de auditoria jurídica.


## Proposta arquitetural recebida — 02/11/2026

Analisada a especificação core/app/Rust/wgpu/ONNX do usuário e adaptada à base existente. Direção: controle simples por PWA, automações locais com prévia/histórico, workers opcionais e código próprio fechado; manter timeline para ajustes finos. Separação por API não é exceção de licença. RVM GPL-3.0 não adotado como componente permissivo; SAM 2 Apache-2.0 é candidato a prova técnica. whisper.cpp é motor independente, não um modelo ONNX; animação por palavra exige render próprio e validação de tempos. Aceleração wgpu não substitui codecs nem garante desempenho total da GPU.

Sequência proposta: ação local completa → transcrição/legendas → cortes de pausas com revisão → recorte assistido → benchmark de GPU e worker Rust onde justificar → avaliar app nativo por necessidade. Uploads, API, estado e MCP atuais reaproveitados. Nenhum modelo/toolchain instalado, serviço ou projeto real alterado; não se anuncia esses recursos ativos. Build FFmpeg local declarou GPL e encoders de hardware compilados, com auditoria de distribuição e operação/qualidade ainda pendentes. Detalhes, referências e critérios de aceite: [arquitetura local e automação](arquitetura-local-e-automacao-02-11-2026.md). Esta é análise solicitada diretamente, sem substituir as rodadas automáticas de edição ou segurança.


## Noite de 01 para 02/11 — rodada 3, varredura e deslize

Quatro tipos preparados: varredura esquerda/direita e deslizar esquerda/direita, no compositor local, sem código Concat. Duração total/som preservados, prévia renderizada e aplicação individual/em lote com histórico/proteções. Cards dependem de spatial_transitions: backend real ainda sem a capacidade, portanto novos estilos aguardam ativação no fechamento. Passaram 171 testes Python na suíte e 24 arquivos JavaScript, com quatro exports/prévias sintéticos decodificados para direção, movimento, som e duração, mais saída 1920 × 1080. Sem soma de repetições, IA real ou mídia pessoal. Editor/login remoto saudáveis, sem reinício; GitHub acumulado. Visual desktop/Safari pendentes. Relatório: [rodada de movimento](rodada-noturna-2026-11-01-03-movimento.md). Próximo pacote às 02h55: entrega/exportação conforme lacuna e orçamento.
