# Lili — melhorias noturnas de 20/10/2026

## Escopo autorizado

Trabalhar em funções e segurança enquanto o usuário dorme, poupar tokens e usar funções locais gratuitas. Sem depender do iPhone. Não prometer paridade completa com CapCut em uma noite. A montagem automática usa limites da conta Codex e não é IA ilimitada gratuita. Não alterar a montagem aprovada da Cora, originais ou credenciais. Não abrir novas portas nem trocar o túnel.

## Pesquisa inicial (fontes oficiais)

- [Shotcut — recursos](https://www.shotcut.org/features/): referência para filtros de áudio/vídeo e edição local. Priorizar controles simples que também funcionem na exportação.
- [Kdenlive](https://kdenlive.org/): referência para edição não linear, áudio e títulos/legendas.
- [Kdenlive — proxies](https://docs.kdenlive.org/en/project_and_asset_management/project_settings/proxy_settings.html): versões leves para editar e originais para exportar; a Lili já segue essa arquitetura.
- [OpenShot — recursos](https://www.openshot.org/features/): referência de ferramentas de edição em software livre.

As referências orientam prioridades de produto; seu código e suas marcas não foram incorporados. Não repetir pesquisa geral a cada rodada.

## Primeira rodada

- Duplicação de cenas: operação `clip_duplicate` e botão Duplicar. Insere cópia após a seleção; preserva o original protegido e cria cópia destravada para ajustes. Desfazer usa o histórico existente.
- Segurança HTTP: validação comum ao editor e gateway antes de ler/encaminhar requisições. Rejeita Content-Length duplicado, tamanho inválido, Transfer-Encoding e Host duplicado. Limita o corpo a 2 GB; os limites menores por endpoint continuam valendo.
- Conexões têm prazo de inatividade de 120 segundos, para não manter leituras abandonadas indefinidamente.
- Verificação: 33 testes passaram, incluindo pedidos HTTP ambíguos rejeitados por ambos os servidores antes da leitura do corpo, além da duplicação com preservação de cena protegida e Desfazer. Sintaxe JavaScript verificada.
- Ativação: editor e gateway reiniciados após confirmar ausência de jobs em andamento. Credenciais e túnel preservados; sessões do gateway em memória foram encerradas, exigindo novo login. Evitar novos reinícios do gateway sem necessidade nas próximas rodadas.

## Agenda e economia

Solicitadas cinco rodadas por hora neste mesmo chat. Uma melhoria completa por rodada, cerca de 10 minutos de esforço. Parar após as cinco execuções; não prolongar agenda. Não fazer novas chamadas de IA reais se testes simulados verificarem a mudança. Testar apenas o que mudou e a suíte completa quando necessário.

## Próximas prioridades

1. Recuperação básica entregue na rodada de 21/10. Snapshots manuais e backup dos vídeos permanecem como escopo futuro, sem prometer recuperação além do último espelho válido.
2. Melhorias úteis de áudio: fades e nível, sempre com prévia e exportação consistentes.
3. Velocidade e ajustes visuais; não adicionar controle que só altere a prévia.
4. Legendas locais: verificar dependências existentes antes de prometer automação ou baixar modelos.
5. Integridade de reenvios e contagem inteira de bytes entregue em 21/10 às 20h. Permanecem pendentes uploads abandonados, limites de concorrência/recursos e auditoria adicional do processamento de IA.

Não é auditoria completa de segurança. iPhone/Safari real continua pendente. Registrar cada entrega concreta abaixo e remover itens já resolvidos da lista.

## Novo trabalho autorizado pelo usuário: portal fixo

Foi preparado um portal em Sites, por convite e com e-mail/senha próprios. Ver outputs/portal-acesso.md para identidade e estado exato. A conta administradora depende de cadastro humano; o Site está temporariamente privado. Não iniciar lili.portal_agent nem regenerar suas chaves/pepper durante as rodadas noturnas. Não alterar o túnel saudável. A liberação pública e a ativação do conector serão concluídas depois do primeiro cadastro, neste chat.


## Rodada de continuidade — 21/10/2026

- Implementada recuperação automática do estado do projeto por `project.json.bak`. Cada salvamento grava o principal e o espelho por substituição atômica, com flush e fsync. O espelho contém a última gravação concluída, incluindo mídia importada, histórico, narração e proteções.
- Se o principal estiver ausente, truncado, ilegível ou com estrutura principal inválida, a leitura tenta a cópia. Confere o identificador para não recuperar outro projeto. Projetos com apenas a cópia continuam aparecendo na lista.
- A leitura de recuperação não sobrescreve nada. O editor desktop informa a recuperação; a próxima alteração salva o estado recuperado. Projetos antigos sem cópia continuam funcionando e passam a ter espelho no próximo salvamento.
- Limite: falha entre a substituição do principal e a do espelho pode deixar a cópia um salvamento atrás. Não é histórico de versões nem backup dos arquivos de vídeo. Ambos ilegíveis retornam erro 422; nenhum arquivo é apagado. A validação confere identidade e estrutura principal, sem pretender detectar toda corrupção semântica interna.
- Verificação: suíte completa com 38 testes passou antes do sexto caso de recuperação; os seis testes focados de recuperação passaram, incluindo falha entre gravação do principal e do espelho. Sem chamadas reais de IA. Sintaxe de app.js e diff verificados. Safari real continua pendente.
- Ativação: o editor estava desligado (porta 8765 recusou conexão). Foi iniciado somente o editor local com a versão testada; saúde e listagem dos três projetos confirmadas. Gateway, sessões e túnel não foram alterados. O espelho de projetos antigos será criado no próximo salvamento normal; nenhum salvamento foi forçado na montagem aprovada. Código, testes e este relatório seguem para o GitHub autorizado.
- Próximo passo: áudio/fades, garantindo prévia e exportação consistentes; ou auditar envios abandonados se for menor. A recuperação básica já foi entregue, sem ampliar esta rodada para snapshots manuais ou exportação de backups de mídia.


## Rodada de continuidade — 21/10/2026, 20h (Brasília)

- Uma melhoria de segurança e confiabilidade dos uploads: reenvios só são confirmados após ler e comparar todo o bloco com os bytes já recebidos. Conteúdo diferente retorna 409; reenvio truncado retorna 400. Nenhum desses casos altera os bytes nem avança o progresso.
- Tamanho do arquivo, tamanho do bloco e posição do bloco precisam representar quantidades inteiras de bytes. Posições fracionárias, inclusive valores que antes seriam arredondados, são rejeitadas. O protocolo normal do navegador continua enviando inteiros e aceitando reenvios idênticos.
- Verificação: quatro testes de upload e cinco de integração passaram; foi acrescentado um quinto teste de upload para tamanhos declarados inválidos, com repetição apenas da suíte focada de upload. A integração verifica pelo HTTP rejeição 409/400 seguida de importação bem-sucedida com arquivo idêntico ao original. A mesma suíte também cobre exportação, narração e MCP existentes. Sem inferência real de IA nem nova pesquisa geral.
- Ativação: código preparado para o próximo início do editor. Não reiniciar o servidor nesta rodada: um upload ainda em trânsito pode não aparecer na lista de jobs, e o usuário utilizou recentemente o acesso remoto. Gateway, sessões, credenciais, endereço externo e projetos reais não foram modificados.
- Limites: não implementa limpeza/expiração de envios abandonados, retomada após reinício do servidor ou comparação dos vídeos após processamento. O limite de pendências e o modelo de concorrência existentes continuam. Safari real pendente.
- Próximo passo: manter a prioridade de áudio/fades para função útil de edição, ou expiração/cancelamento de uploads em uma rodada separada. Não ampliar esta entrega nem criar novas agendas.


## Rodada de continuidade — 21/10/2026, 21h (Brasília)

- Adicionadas Entrada suave e Saída suave da narração, em segundos, no painel de áudio. Zero desativa. Aplicação local, sem API paga ou inferência do Codex.
- O backend rejeita valores negativos, não finitos, booleanos, durações maiores que o áudio e soma dos fades maior que sua duração; erro mantém a revisão anterior. Desfazer restaura os valores. Projetos antigos sem esses campos usam zero.
- Prévia aplica a curva linear ao tempo da narração, incluindo atraso e busca. Exportação aplica afade antes do atraso, terminando a saída no fim do arquivo de áudio. Se a montagem terminar antes da voz, permanece o aviso existente: prolongar as cenas para ouvir o final completo.
- Verificação: 14 testes de estado e seis de integração passaram. A nova integração exporta mídia sintética e mede a energia do áudio no silêncio inicial, entrada, meio, saída e silêncio final. Teste Node da lógica real da prévia cobre fades, atraso/busca e narração antiga; sintaxe JavaScript e diff também conferidos. Sem chamadas reais de IA, sem mídia pessoal nos testes.
- Ativação pendente do próximo início normal do editor, para preservar possíveis uploads em andamento. Não houve reinício, mudança de gateway/sessões/túnel ou alteração da montagem aprovada. Portal continua aguardando cadastro humano, sem ativação do conector. Safari real e avaliação visual dos novos controles permanecem pendentes.
- Limites: os fades são apenas da narração adicional. Não são transições entre cenas nem fades individuais dos sons originais. O navegador continua limitado a ganho de 100% na prévia; ganho legado acima de 100% é aplicado pela exportação, como antes.
- Próximo passo: em rodada separada, controles de velocidade com exportação consistente ou limite/expiração de uploads abandonados. Não ampliar esta entrega.


## Rodada de continuidade — 21/10/2026, 22h (Brasília)

- Proteção de espaço livre no protocolo de upload em blocos usado pela interface. Antes de criar um envio, considera o tamanho ainda pendente de todos os projetos e mantém margem de 256 MiB no disco do projeto. Não pré-aloca os vídeos nem apaga arquivos.
- Antes de gravar cada novo bloco, verifica novamente o espaço disponível. Se insuficiente, retorna 507 sem consumir o bloco, alterar os bytes recebidos ou avançar o progresso; reenvios idênticos já gravados continuam funcionando. Se a consulta de espaço falhar, retorna 503 sem expor o caminho local.
- Verificação: oito testes focados de upload e seis de integração passaram. Casos novos simulam disco cheio, orçamento compartilhado entre projetos, contagem apenas dos bytes restantes e retomada após liberar espaço. Não foi preenchido nenhum disco real. Sem inferência de IA, pesquisa ou arquivos pessoais nos testes.
- Limites: é uma checagem preventiva, não reserva exclusiva no sistema operacional. Outro processo ainda pode ocupar disco durante a gravação. A margem não garante espaço para proxies, exportações ou todos os dados do Windows. O endpoint legado de upload direto não recebeu essa proteção nesta rodada. Uploads abandonados continuam contabilizados até concluir ou reiniciar; limpeza/cancelamento permanecem para trabalho separado.
- Ativação no próximo início normal do editor: nenhum serviço reiniciado para preservar envios em trânsito. Originais, montagem aprovada, credenciais, sessões e link remoto preservados. Safari real permanece pendente.
- Atualização de contexto: o usuário concluiu e liberou o portal entre as rodadas. O conector foi ativado e verificado no atendimento anterior; ver outputs/portal-acesso.md. Esta rodada não alterou o portal nem o túnel.
- Próximo passo: cancelamento/expiração segura de envios abandonados ou controles de velocidade consistentes com exportação, em uma rodada separada. Não prolongar a agenda existente.


## Última rodada da agenda — 21/10/2026, 23h (Brasília)

- Completa a proteção de espaço no endpoint legado de upload direto, usado pelo cliente local/MCP. Verifica tamanho declarado antes de criar o temporário e repete a checagem antes de cada bloco de até 1 MiB, preservando margem de 256 MiB.
- Falta de espaço retorna HTTP 507. O temporário de um envio direto incompleto é removido pelo fluxo de limpeza já existente; nenhum arquivo é registrado na biblioteca. O arquivo de origem enviado pelo cliente não é alterado. Diferentemente do envio em blocos, o envio direto não oferece retomada de uma transferência parcial.
- Oito testes de integração passaram: novos testes HTTP verificam recusa antes da criação e falha após o primeiro MiB, sem temporário ou mídia registrada; os demais continuam cobrindo importação, reenvio, exportação, fades e proteções HTTP. Usados somente projetos sintéticos isolados. Diff conferido; nenhuma chamada real de IA.
- Limites: checagem preventiva, sem reserva exclusiva de disco. O envio direto não participa do orçamento compartilhado em memória dos envios em blocos. Outros processos podem ocupar espaço entre checagem e escrita. Não garante espaço para proxies/exportações nem implementa cancelamento/expiração de pendências.
- Código preparado para o próximo início normal do editor. Nenhum servidor, gateway, conector ou túnel foi reiniciado. Originais, montagem aprovada, credenciais, sessões e endereço remoto preservados. Safari real continua pendente.
- A agenda de cinco execuções encerra aqui, sem novas automações. Próximos trabalhos registrados para retomada pelo usuário: cancelamento/expiração segura de uploads, velocidade com prévia/exportação consistentes, inicialização do conector após reiniciar Windows e teste real de Safari. Não são entregas desta rodada.
