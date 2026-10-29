# Rodada 1 — legendas com prévia · noite de 28 para 29/10/2026

## Entrega

Retomada a frente de legendas que estava prevista após o áudio do ciclo anterior. Os três checkpoints anteriores continuam preservados; esta entrega não repete aquelas melhorias e não os considera publicados.

- Tocar uma legenda na timeline ou escolher **Editar com prévia** abre um painel próprio de texto, tempos e estilo. Criar pelo botão **+ No cursor** prepara um rascunho vazio: o texto “Nova legenda” não é mais gravado automaticamente no projeto.
- Entrada e saída aceitam segundos ou minutos:segundos com milissegundos. Há passo de quadro para o cursor, entrada/saída no cursor e movimento do bloco preservando sua duração.
- Preenchimento exige texto e pelo menos 0,1 s. Uma nova legenda respeita o próximo bloco; se já existir legenda naquele instante, abre a existente. Sobreposição, tempo inválido e texto longo impedem aplicar, com motivo explícito.
- Fontes locais existentes, tamanho e posição participam da prévia. **Ver no vídeo** leva ao meio da legenda e abre a prévia ampliada existente, preservando o rascunho. **Reproduzir legenda** limita a reprodução ao seu intervalo, inclusive ao atravessar um corte de vídeo.
- Opção explícita **Usar este estilo em todas as legendas** padroniza apenas fonte, tamanho e posição. Preserva texto, ID e tempos das outras legendas. A prévia do estilo em lote também é local.
- Aplicar salva um único comando; a padronização usa a substituição atômica da faixa, com revisão esperada. Desfazer/Refazer recuperam o conjunto. Remover uma legenda continua sendo reversível. Cancelar descarta experiências e restaura o cursor anterior.
- As regiões da faixa de legendas passam a ter 44 px de altura, em uma faixa de 50 px. O painel usa rolagem interna, ações fixas, inputs de 16 px e espaço da área segura. Isso foi conferido no código, não no Safari.

Os antigos campos rápidos do inspetor continuam disponíveis e salvam diretamente como antes; a experiência Aplicar/Cancelar pertence ao novo painel. Não foram adicionadas novas famílias de fontes, animação de palavras ou transcrição automática.

## Verificação

**17 arquivos JavaScript passaram**, incluindo um novo que executa os manipuladores reais em ambiente simulado. Cobre criação local, texto e estilo na prévia, sobreposição/limites, movimento e aparo precisos, encaminhamento à prévia ampliada, reprodução limitada, aplicação/remoção em comando único, padronização em lote preservando conteúdos, Cancelar, revisão antiga e falha de salvamento. Os testes existentes continuam cobrindo áudio, efeitos, transições, busca e importação. Repetições não contam como testes novos.

**Quatro testes Python distintos passaram**, dois novos: substituição de estilo em lote com histórico e falha atômica; exportação de legendas independentes com tempos/estilos e Desfazer/Refazer; duas regressões de independência da faixa e recuperação de áudio/legendas/configurações. O vídeo sintético exportado foi decodificado: sem texto antes da entrada, texto grande na região inferior e pequeno na superior em seus respectivos intervalos. SRT, duração e montagem preservados. Não houve alteração do backend nem necessidade de repetir a suíte completa.

Conferidos sintaxe, diff, IDs únicos no HTML e entrega de HTML/scripts sem cache pelo servidor sintético. Só cenas geradas localmente e identidades fictícias; nenhuma chamada real de IA, mídia pessoal ou alteração de projeto real.

## Demonstração e limite da revisão visual

Servidor isolado na porta 8771, dados em work/nightly-2026-10-28/data. A tentativa de revisão visual foi bloqueada porque o navegador integrado não conseguiu inicializar seus arquivos de execução; uma reinicialização do recurso também falhou. Não foram feitas interações bem-sucedidas no navegador, capturas de tela, testes de layout em viewport ou validação de Safari nesta rodada. O novo fluxo de abertura da prévia ampliada e seu layout ainda precisam de conferência visual real; os manipuladores e a exportação foram testados por automação local.

## Publicação e ativação

Checkpoint de código, testes e documentação preparado localmente. Sincronização dos checkpoints acumulados permanece para o encerramento da extra, ou após segurança se não houver extra, como autorizado.

A checagem de /api/health na porta 8765 não respondeu nesta execução; a demonstração antiga da 8770 também não respondeu. Nenhum processo real foi iniciado, parado ou reiniciado para esta entrega. Apenas o novo ambiente sintético foi iniciado. Não anunciar este recurso como ativo em produção: a versão real, os jobs/envios e a identidade dos serviços precisam ser conferidos no fechamento do ciclo antes de ativar. Gateway, portal, conector, endereço remoto, sessões e credenciais não foram modificados.

## Próximo passo

Na rodada de 00h55, retomar a conferência visual pendente se o navegador estiver disponível; depois escolher uma lacuna de exportação/entrega. Registrar o estado real do serviço para o fechamento, sem deslocar as rodadas de edição para contas. A quinta rodada continua destinada à segurança/acesso. Permanecem pendentes: arraste das legendas, divisão de fala, animação de palavras, mais fontes licenciadas e teste de Safari real. SRT preserva texto e tempos, mas não leva a tipografia do projeto.
