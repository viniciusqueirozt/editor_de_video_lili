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


## Nova agenda — 23/10/2026, 00h (São Paulo)

- Uma melhoria completa de base: transporte de identidade assinado para a futura ponte gateway → editor. HMAC vincula usuário, método, URL/query, metadados do corpo, instante, nonce e audiência da instância; validade de 30 segundos por padrão, tolerância futura limitada e memória de replay com limite e recusa segura.
- Cinco testes focados passaram: adulteração, instância diferente, campos duplicados, expiração/futuro, replay, cache cheio/expiração, replay concorrente e integração HTTP real com a autorização de projetos. Uma identidade B não lista o projeto de A. Sem inferência real de IA.
- Apenas preparado em código: não autentica sessão do portal nem liga o modo privado real. Nenhum serviço foi reiniciado, conta migrada, proprietário atribuído, credencial lida ou projeto real alterado. Sessões, túnel, conector e mídia preservados. Safari real não foi testado.
- Limites e coordenação futura de chave/audiência descritos em outputs/base-de-permissoes.md. O conteúdo inteiro de upload não é assinado, somente seus metadados; cache de replay não persiste em disco. Não apresentar esta peça isolada como isolamento de usuários já ativo.
- Próximo passo: autenticação individual comprovada do portal ao gateway, sem alterar a publicação/acesso externo nesta rodada; depois proposta explícita de associação dos projetos existentes aos donos corretos. Nenhuma melhoria extra nesta execução.

## Continuidade — 23/10/2026, 00h55 (São Paulo)

- Uma melhoria: ligação opcional do gateway ao transporte de identidade. Exige resolvedor confiável e assinador configurados juntos; cada requisição valida a identidade antes de gerar a prova local. Cabeçalhos/cookies do navegador não são encaminhados como identidade. Conta inválida ou erro de autenticação não recorre ao login compartilhado.
- Verificação: três testes HTTP novos e dezesseis testes existentes de gateway, transporte e permissões passaram. Cobrem criação pelo dono autenticado, duas contas, falsificação, revogação/expiração simulada, indisponibilidade do resolvedor e chave divergente. A credencial compartilhada é substituída por uma função que falha nos testes, comprovando que esse modo não a consulta. Sem IA real ou mídias pessoais.
- Estado: apenas preparado. O portal ainda não fornece a sessão individual ao gateway real; modo privado permanece inativo. Não houve reinício, alteração de credenciais/sessões reais, atribuição de proprietários ou mudança do túnel/conector. Safari real não testado.
- Limites: resolvedor sintético nos testes; a entrada cross-site é recusada nesse modo até implementar o fluxo específico de ticket. Revogação é conferida no início da requisição, sem promessa de interromper bytes em trânsito. main() permanece com a configuração atual.
- Próximo passo: troca de ticket de uso único e sessão verificada entre portal e gateway, com revogação e expiração comprovadas; depois proposta explícita dos donos dos projetos existentes. Nenhuma melhoria extra nesta execução.

## Continuidade — 23/10/2026, 01h55 (São Paulo)

- Uma melhoria de integração: resolvedor de sessão opaca do editor que consulta o portal por HTTPS em rota fixa. Recusa cookies ambíguos, exige resposta vinculada ao token, prazo válido e identidade comprovada; não reutiliza IDs livres nem guarda autorização em cache. Falha de rede ou revogação impede novas requisições no modo opcional.
- Verificação: 13 testes focados aprovados. Quatro testes unitários novos e um novo teste HTTP ligam o resolvedor ao gateway, assinatura local e autorização do editor com duas contas e revogação; portal inteiramente simulado. Inclui regressão do conector. Sem chamadas reais de IA ou ao portal.
- Estado: preparado, não ativado. O endpoint de validação ainda precisa ser implementado no portal publicado e o ticket de entrada/cookie ainda precisa ser criado. Contrato documentado em outputs/base-de-permissoes.md para a próxima etapa. Não há isolamento real anunciado nem associação de projetos existentes.
- Nenhum serviço reiniciado, acesso externo ampliado, sessão real alterada ou mídia pessoal usada. Link, conector, contas e projetos preservados. Limites: consulta por requisição pode acrescentar carga/latência; revogação não interrompe bytes já em trânsito. Safari real pendente.
- Próximo passo: implementar no portal a sessão do editor vinculada à sessão original e o endpoint do contrato, com testes de expiração/revogação; depois troca de ticket de uso único. Nenhuma melhoria extra nesta execução.

## Continuidade — 23/10/2026, 02h55 (São Paulo)

- Uma melhoria de robustez independente da migração de contas: cancelamento explícito de upload pendente. POST /api/projects/ID/uploads/UPLOAD_ID/cancel com corpo {} e Client.cancel_upload removem somente o temporário .upload daquele envio, liberam a reserva de espaço e a vaga na fila. Arquivos concluídos/registrados não são alvo. Repetição após sucesso retorna 404, sem nova remoção.
- Operação compartilha o bloqueio de gravação/finalização, aguarda o bloco em curso e confere projeto, caminho, tipo de arquivo e ausência de redirecionamento por links. Falha de exclusão preserva a pendência para nova tentativa. Um temporário já ausente pode liberar a pendência sem tocar no arquivo final.
- Verificação: 16 testes focados de upload e autorização passaram. Casos novos cobrem bytes removidos, capacidade liberada, cancelamento concorrente com bloco, projeto errado, apenas visualização sem poder cancelar, erro de disco, caminho adulterado, arquivo final preservado e fluxo HTTP/cliente que desbloqueia a lixeira. Somente arquivos sintéticos.
- Estado: API/cliente preparados para o próximo início normal do editor, sem reiniciar serviços ou interferir em envios reais. Ainda não há botão de cancelamento, listagem de envios pendentes, expiração automática ou recuperação da fila após reinício. Não cancelar automaticamente uma importação por falha de rede. Safari real não testado.
- A integração individual do portal continua pendente/inativa conforme contrato da rodada anterior; nenhuma identidade ou dono de projeto foi inferido. Credenciais, sessões, conector, túnel, logo, originais e montagem aprovada preservados. Nuvem permanece planejada.
- Próximo passo: controle explícito de cancelamento na interface com confirmação do resultado; para contas individuais, implementar o endpoint de validação e o fluxo de ticket no portal em uma rodada própria. Nenhuma melhoria extra nesta execução.

## Última oportunidade da agenda — 23/10/2026, 03h55 (São Paulo)

- Uma melhoria: botão Cancelar envio na importação, com área de toque de 44 px. Para o lote antes do próximo bloco/arquivo, aguarda o bloco em andamento e cancela somente o temporário atual pela API; os arquivos anteriormente recebidos continuam preservados. Durante a finalização o botão fica desabilitado para evitar cancelar um arquivo já registrado.
- Falha de rede não provoca exclusão automática. Um cancelamento sem confirmação mantém o aviso e o botão para tentar novamente; novos envios ficam bloqueados enquanto essa pendência conhecida não for resolvida. Uma resposta 404 informa que o envio não está mais pendente, sem prometer liberação de espaço ou remoção de arquivo concluído.
- Verificação: oito cenários Node executam as funções reais da interface com rede simulada. Cobrem cancelamento durante bloco e criação, arquivos anteriores preservados, erro/repetição, falha de bloco, finalização, resposta perdida/404 e servidor antigo. Dezesseis testes Python focados de upload/permissões passaram, além de sintaxe JavaScript e diff. Sem chamada real de IA ou mídia pessoal.
- Ativação: o botão depende da capacidade upload_cancel informada por /api/health. Isso mantém a interface compatível com o processo antigo sem forçar reinício. API e capacidade entram no próximo início normal do editor; nenhum serviço real foi reiniciado ou envio real cancelado nesta rodada. Safari real e avaliação visual do botão no iPhone permanecem pendentes.
- Limites: a página ainda não recupera a lista de uploads após recarregar/fechar; pendências ficam somente em memória no servidor, sem expiração automática. Cancelamento pode aguardar o timeout do bloco atual se a conexão estiver instável. Nuvem e privacidade individual continuam pendentes, conforme esteira e contrato de autenticação.

### Melhoria extra única e encerramento — 23/10/2026, 04h (São Paulo)

- Reforço de segurança nos dois servidores: recusar cabeçalhos duplicados de origem, contexto de navegação, tipo do conteúdo, cookie e autorização, além do Host já protegido. Evita que camadas diferentes escolham valores distintos para autenticação ou validação da origem. Cookie único contendo vários pares normais continua permitido.
- Vinte testes focados passaram, abrangendo os dois servidores, login atual, transporte assinado e gateway com identidade. Dois testes novos cobrem campos duplicados com variação de maiúsculas/minúsculas e recusa HTTP antes de ler o corpo ou consultar autenticação. Apenas diretórios temporários e dados sintéticos. Estado da melhoria extra registrado somente no controle local ignorado pelo Git.
- Proteção preparada para os próximos inícios normais do editor/gateway; serviços reais não reiniciados. Nenhuma credencial real lida, sessão alterada ou ampliação de acesso externo. Não foram feitos testes de celular.
- Concluídas as cinco oportunidades e a única melhoria extra permitida. A automação foi removida no aplicativo; esta agenda não terá continuação durante manhã/tarde nem execução adicional após a madrugada.

### Revisão rápida desta madrugada

1. **Cancelamento de importação:** API/cliente e botão prontos e testados; aguardam próximo início normal do editor. O botão fica oculto enquanto /api/health não anunciar suporte — o processo atual foi consultado e ainda não anuncia. Evita ativar uma interface incompatível ou reiniciar durante envios.
2. **Contas privadas:** transporte assinado, ponte opcional do gateway e cliente de validação de sessão preparados. Ainda faltam endpoint e ticket no portal, configuração real e associação explícita dos projetos aos proprietários. O editor continua no modo compartilhado atual; não prometer isolamento individual.
3. **Segurança:** nova recusa de cabeçalhos ambíguos testada. Nenhum serviço, túnel, conector, credencial, sessão, mídia pessoal, logo ou montagem aprovada foi alterado nesta agenda.
4. **Próxima revisão humana:** quando não houver importações/processamentos, conferir um reinício normal para ativar as melhorias locais e testar Cancelar envio com arquivo descartável. Safari real continua pendente. Depois retomar integração do portal e decisão dos proprietários; nuvem permanece planejada.

Código, testes e documentação sincronizados no GitHub; estado operacional, dados privados e mídias ficaram fora do versionamento.


## 24/10/2026 — ciclo manual ampliado, autorizado diretamente

Conjunto de quatro frentes de edição, segurança e extra concluído/publicado. Relatório completo em outputs/relatorio-ciclo-24-10-2026.md. Editor ativo com recursos novos de imagem/ritmo, áudio/música, legendas/SRT, fotos, Refazer, prévia ampliada e perfis de saída. Gateway preservado; correções dele publicadas com ativação pendente do próximo início. Validação: 124 testes Python, 12 arquivos JavaScript e revisão desktop sintética. Originais/projetos reais preservados; Safari real pendente. Agenda recorrente autorizada configurada, excluindo sexta à noite para sábado e sem execução automática manhã/tarde. Próxima rodada deve escolher lacuna nova da esteira e consultar limites reais; não repetir as entregas deste ciclo.

## Rodada direta solicitada pelo usuário — 24/10/2026

Precisão da linha do tempo implementada: posição digitável, passo por quadro, aparo no cursor com Desfazer, fila de busca que preserva o último destino e pinça limitada à régua. Corrigidos reconstrução do inspetor durante a navegação, retorno ao início após aparar saída e limite de aparo que ignorava fades sonoros. Treze arquivos de testes JavaScript passaram, com revisão desktop em projeto sintético e conferência HTTP dos arquivos ativos. Nenhum serviço reiniciado, projeto real ou credencial alterado. Safari real, ímã, pinça em todas as trilhas e transições entre tomadas continuam pendentes. Relatório: [rodada de precisão](rodada-precisao-timeline-24-10-2026.md). Esta foi uma rodada direta, não o início de um novo ciclo automático diurno.

## Noite de 24 para 25/10/2026 — rodada 1, transições na junção

Passagens por preto/branco e corte seco implementados com par explícito, catálogo visual, duração, prévia limitada ao encontro e Aplicar/Cancelar sem gravar experiências. Preservam o tempo da montagem e as posições de áudio/legendas; não são dissolução nem crossfade sonoro. Histórico, cenas protegidas, alterações de adjacência e velocidade conferidos. Passaram 133 testes Python e 14 arquivos JavaScript; exportações sintéticas tiveram pixels, duração e áudio medidos. Revisão desktop e viewport estreito feita; Safari real pendente. Servidor sintético na porta 8770 com capacidade ativa; editor real saudável na 8765 ainda sem pair_transitions. Checkpoint local, publicação/ativação reservadas ao fechamento da extra ou da segurança. Nenhum serviço real reiniciado, projeto real, sessão ou credencial alterado. Relatório: [rodada 1](rodada-noturna-2026-10-24-01-transicoes.md). Próximo pacote de 00h55: catálogo e aplicação/cancelamento de efeitos reversíveis por cena.

## Noite de 24 para 25/10/2026 — rodada 2, aparências e comparação

Seis aparências locais com miniaturas mais referência Atual, intensidade sem acumular correções, comparação que pausa o quadro, atalho Quadro central e reprodução limitada à cena. Aplicar salva um único comando RGB; Cancelar restaura o cursor sem gravar. Proteção/revisão antiga/falha de salvamento cobertas; miniaturas respeitam o limite de extração perto do fim do arquivo. São presets de cor da cena inteira, com Original explicitamente restaurando os ajustes; camadas e remoção independente de look permanecem pendentes. Passaram 15 arquivos JavaScript e três testes Python focados, um novo com seis aparências exportadas/pixels medidos e preservação de metadados, áudio e legendas. Revisão desktop e viewport estreito feita; Safari real pendente. Frontend disponível após recarregar usando a API já ativa; produção não reiniciada e transições da rodada 1 ainda aguardam capacidade. Checkpoint local, publicação ao fechamento do ciclo. Relatório: [rodada 2](rodada-noturna-2026-10-24-02-aparencias.md). Próximo pacote às 01h55: edição direta de posicionamento/aparo de áudio, após conferir as lacunas reais e o saldo.


## Noite de 24 para 25/10/2026 — rodada 3, áudio no tempo certo

Painel próprio ao tocar música/narração: início digitável, passos de quadro, alinhamento ao cursor, aparo de música preservando sincronismo, navegação precisa, forma de onda nas duas faixas e mixagem em prévia local com Aplicar/Cancelar. Salvamento único, Desfazer/Refazer e avisos de duração/fades; corrigido espaço móvel das faixas e rodapé. Passaram 16 arquivos JavaScript e quatro testes Python focados existentes, com exportações sintéticas e medição de áudio. Revisão desktop em exemplo isolado e larguras de 320/390 px; Safari real pendente. Frontend compatível com API já ativa, disponível após recarregar; serviços e sessões preservados. Checkpoint local, sincronização no encerramento do ciclo. Transições da rodada 1 ainda aguardam backend; não anunciar tudo ativo. Relatório: [rodada 3](rodada-noturna-2026-10-24-03-audio.md). Próximo pacote às 02h55: conferir edição de legendas e simplificar ajustes reversíveis de tempo/estilo onde necessário.


## Noite de 28 para 29/10/2026 — rodada 1, legendas com prévia

Retomada a frente pendente após o áudio: painel de legenda com rascunho, texto/tempos/estilo, aparo e movimento precisos, prévia ampliada, reprodução limitada, validação de sobreposição, Aplicar/Cancelar e padronização opcional de estilo da faixa em um único comando reversível. Novas legendas não gravam texto provisório antes de aplicar. Passaram 17 arquivos JavaScript e quatro testes Python distintos, dois novos, com vídeo sintético decodificado para medir tempos/posição do texto e SRT. Não houve teste visual bem-sucedido: navegador integrado não inicializou; layout, fluxo visual ampliado e Safari real pendentes. Servidor sintético 8771 ativo. Editor real 8765 não respondeu à checagem; produção não foi iniciada/reiniciada, e não se anuncia ativação. Três commits anteriores preservados; sincronização acumulada no fechamento do ciclo. Relatório: [rodada 1 de 28/10](rodada-noturna-2026-10-28-01-legendas.md). Próximo pacote: retomar revisão visual pendente e avançar exportação/entrega conforme lacuna real; conferir serviços com segurança no fechamento.


## Noite de 31/10 para 01/11/2026 — rodada 1, revisão e envio da exportação

Avisos de fala/música/legendas fora da duração e silêncio pelos metadados, com atalhos ao ajuste. Bloqueio de mídia indisponível na interface e checagem de fontes no servidor antes de criar job. Corrigidos cliques duplicados, troca de projeto enquanto aguarda salvamento, retorno atrasado de fila e mensagem após resposta incerta. Passaram 18 arquivos JavaScript e a suíte final de 137 testes Python; repetições não somadas. Duas falhas pontuais de testes existentes na primeira suíte não se reproduziram isoladamente nem no conjunto final; acompanhar estabilidade, sem anunciar correção de áudio inexistente. Frontend servido na 8765; backend novo aguarda ativação segura no fechamento. Serviços reais preservados, publicação acumulada pendente. Revisão visual de legendas e exportação continua pendente, sem Safari real validado. Relatório: [rodada 1 de 31/10](rodada-noturna-2026-10-31-01-exportacao.md). Próximo pacote às 00h55: revisão visual se disponível e controles de montagem/precisão.
