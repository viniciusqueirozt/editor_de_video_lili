# Esteira da Lili

## Entregue nesta versão

- Identidade visual da inicial nas telas do editor, painéis, linha do tempo e janelas.
- Menu de projeto compacto no celular.
- Exclusão permanente de projeto já na Lixeira, com confirmação digitada e bloqueio de processamentos. Remove apenas dados na pasta do projeto; arquivos fora dela permanecem.

## Ordem de criação atualizada — 22/10/2026

Os itens abaixo são planejamento, não recursos disponíveis. O usuário pediu incluir projetos privados, compartilhamento e acabamento de vídeo. A preparação da nuvem continua na esteira, precedida pela identidade/permissões que deverão proteger esses dados.

| Etapa | Frente | Resultado esperado |
| --- | --- | --- |
| 1 | Identidade e privacidade | Cada pessoa vê apenas seus projetos e os compartilhados com ela. |
| 2 | Compartilhamento | Proprietário autoriza visualização, download e edição por projeto; pode revogar. |
| 3 | Edição e acabamento básico | Transições úteis, legendas editáveis, fontes e áudio com prévia/exportação consistentes. |
| 4 | Nuvem e arquivo | Cópia verificada, histórico, restauração e liberação local segura. |
| 5 | Estilo e colaboração avançados | Presets da Elisa, revisão por comentários e melhorias da montagem assistida. |

Entregar em incrementos pequenos. Não esperar todas as etapas para liberar funções prontas e testadas. A seleção do provedor de nuvem pode ocorrer em paralelo ao planejamento, sem enviar arquivos antes da configuração e autorização.

## Projetos privados e compartilhamento

### Estado atual e migração

As contas do portal são individuais, mas o editor ainda usa um login compartilhado e não associa projetos a proprietários. Não há isolamento por usuário implementado; esconder cartões na interface não resolve isso. Será necessário integrar a identidade ao servidor do editor e conferir permissões em cada operação. Não apresentar o estado atual como ambiente privado entre colegas.

- Associar cada projeto a um proprietário identificado por ID estável, nunca apenas pelo nome exibido ou por e-mail enviado pelo navegador.
- Migrar os projetos existentes com associação explícita ao proprietário correto, preservando arquivos, montagem aprovada e histórico. Não atribuir ao primeiro visitante que entrar.
- Validar uma sessão individual no editor vinculada à conta autorizada; não reutilizar a senha do portal em outro serviço nem depender de um ID de usuário livremente informado pelo cliente.
- Separar a capacidade de administrar convites do portal da autorização para abrir material de todos os projetos. Acesso de suporte/administração ao conteúdo exige regra explícita e registro.

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

- Cancelamento/expiração de uploads abandonados.
- Legendas locais, perfis de estilo e formatos adicionais de projeto.
- Inicialização do conector após reinício do Windows.
- Validação da interface no Safari real, além dos testes no notebook.
