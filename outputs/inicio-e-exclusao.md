# Página inicial e exclusões recuperáveis — 22/10/2026

## Pesquisa de interfaces

Foram consultadas fontes oficiais, sem adicionar serviços ou dependências:

| Referência | Padrão observado | Aplicação na Lili |
| --- | --- | --- |
| [CapCut: editar projetos existentes em desktop, web e celular](https://www.capcut.com/help/modify-history-task) | Acesso aos projetos e retomada pela área inicial; edição em espaço próprio. | Início com recentes, busca, novo projeto e continuar edição. |
| [Canva: criar e editar vídeos](https://www.canva.com/en_au/help/creating-and-editing-videos/) | Entrada pela página inicial para criar vídeo, seguida do ambiente de edição. | Criação curta com nome e roteiro opcional; abertura direta da linha do tempo. |
| [DaVinci Resolve, visão oficial](https://www.blackmagicdesign.com/products/davinciresolve) | Organização das tarefas em áreas de mídia, corte, edição, cor, áudio e entrega. | Navegação por propósito, adaptada à Lili: Projetos, Edição com IA, Conexão e Preferências. Sem reproduzir a complexidade de um editor profissional. |

A síntese é uma decisão de produto, não um teste comparativo de desempenho ou pesquisa com usuários. Não foram copiadas telas, marcas ou recursos pagos. A inicial usa fundo claro, navegação escura, acento verde e cartões compactos; o editor mantém seu ambiente escuro.

## Exclusão em massa de arquivos

No editor: Arquivos → Selecionar → marcar arquivos ou Selecionar todos → Excluir selecionados. Uma confirmação lista exemplos dos nomes e quantas cenas/faixas sairão da montagem. Arquivos em processamento não podem ser selecionados; cenas protegidas bloqueiam a exclusão do lote inteiro.

A operação media_remove_many é atômica: valida todos os identificadores e usos antes de salvar. Exige revisão atual e confirmação de remoção dos usos. Não exclui parte de um lote se houver erro. Um único Desfazer restaura biblioteca, cortes e narração. Também disponível na ferramenta lili_edit do MCP.

Os arquivos vão para a Lixeira do projeto. Restauração individual retorna o arquivo à biblioteca; Desfazer recupera os usos removidos. Originais permanecem no notebook. Não esvazia a Lixeira nem libera espaço em disco.

## Exclusão de projetos inteiros

Disponível no botão de lixeira de cada cartão da inicial e no botão Excluir projeto no cabeçalho do editor. Exige confirmação, revisão atual e ausência de uploads pendentes/preparação de mídias. Projetos excluídos saem da lista ativa e têm acesso por API, mídia e edição bloqueado. Lixeira da inicial → Restaurar projeto recupera o mesmo projeto, arquivos, montagem e histórico. Nenhuma pasta é apagada ou movida fisicamente; o estado é salvo junto do espelho de recuperação existente.

Não há exclusão permanente nesta entrega. Um upload abandonado ainda pode bloquear a exclusão do projeto; cancelamento/expiração de uploads fica para uma entrega futura. A exclusão de um projeto inteiro é uma decisão explícita, mesmo que ele contenha cenas protegidas; a proteção das cenas bloqueia a exclusão de mídias individuais/em lote.

## Página inicial funcional

- / abre a inicial; /editor?project=ID abre o editor. Projetos existentes continuam com os mesmos identificadores.
- Recentes com miniaturas, duração da montagem, contagem de arquivos e data. Busca por nome, atualização e continuação do projeto usado neste navegador.
- Novo projeto aceita nome/roteiro e abre diretamente no editor. Nenhum projeto é criado automaticamente ao abrir a inicial vazia.
- Edição com IA explica o fluxo real e mostra a presença do CLI; não promete login/limites disponíveis nem dispara inferência ao consultar status. Atalho ao último projeto abre o painel de IA, sem iniciar a edição.
- Conexão reúne portal fixo, endereço atual e instruções para iPhone.
- Preferências permitem cartões/lista, ordenação por data/nome e restauração desses valores. Persistem apenas neste navegador e não alteram outros usuários.
- Legendas automáticas, perfil de estilo, novos formatos e backup externo aparecem identificados como Planejado, sem simular execução.
- CSS móvel inclui navegação inferior, áreas seguras, controles de toque e campos com tamanho adequado. Sem proibir zoom. Safari real desta interface ainda precisa ser validado.

## Verificação e ativação

- Suíte completa: 60 testes passaram. Em seguida, dois novos testes HTTP de rotas/ciclo de vida foram acrescentados; a suíte focada de integração passou com dez testes. Cinco testes novos de exclusão/recuperação estão incluídos na suíte completa. Lógica de áudio da prévia e sintaxe de ambos os scripts verificadas no Node.
- Navegador desktop em porta isolada e projetos sintéticos: exclusão/restauração de projeto, exclusão dos três arquivos com confirmação, montagem vazia e recuperação completa com Desfazer, criação com roteiro, abertura do editor, exclusão dentro do editor com retorno à Lixeira e preferências persistidas após recarregar.
- Provas locais: outputs/lili-inicio-projetos.png (inicial real, somente leitura), outputs/lili-inicio-preferencias.png e outputs/lili-exclusao-em-massa.png (ambiente sintético). Imagens não seguem para o GitHub.
- Ativado com reinício somente do servidor local após confirmar ausência de jobs e arquivos de upload recentes. Gateway, sessões, túnel e conector não foram reiniciados. Identificadores e revisões dos três projetos reais foram comparados antes/depois e permaneceram iguais; montagem aprovada preservada.
- Rotas reais da inicial/editor verificadas. API remota sem login continua retornando 401. Nenhum consumo de IA ou serviço pago foi necessário.

## Pendências práticas

Reteste visual/gestual no iPhone, exclusão permanente com confirmação própria se desejada, cancelamento de uploads abandonados e configurações por projeto. Cada recurso Planejado precisa de implementação própria; esta tela não o torna disponível.
