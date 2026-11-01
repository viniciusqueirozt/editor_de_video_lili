# Conexão do portal — correção direta solicitada em 01/11/2026

## Problema observado

Editor e entrada local responderam em aproximadamente 0,06 s e 0,03 s; o teste do endereço externo atual levou aproximadamente 0,83 s e passou. Mesmo assim, o portal guardava um estado inativo, um pedido expirado e uma última comunicação antiga do conector. O processo do conector ainda existia. Isso não comprova que o computador estivesse desligado.

Havia três problemas concretos no código: o portal só rechecava endereços já marcados saudáveis, o conector aguardava operações lentas antes de renovar sua presença e a interface consultava a cada 15 segundos sem limite de espera ou proteção contra respostas fora de ordem. Não foi determinada com certeza a causa específica da parada de comunicação do processo anterior.

## Correções

- O conector renova a presença em um ciclo de três segundos; checagem externa e reconexão usam uma única tarefa de fundo, sem bloquear a presença nem permitir duas substituições locais simultâneas. Chamadas ao portal têm timeout de cinco segundos e teste externo de quatro. Estes são limites por operação, não garantia do tempo total de recuperação em qualquer rede.
- Pedidos/resultados expirados são descartados com segurança. Falha no envio do resultado permite repetir o envio sem repetir a reconexão. A ação remota continua restrita a reconnect.
- O portal volta a testar endereços inativos e preserva um link que se recuperou. A verificação remota tem timeout de 2,5 segundos, leitura limitada e não segue redirecionamentos. Há cooldown e coordenação pelo banco entre visitantes. Um resultado antigo não pode substituir um relatório ou pedido mais novo.
- Leases expirados deixam o estado de trabalho pendente no próximo poll do conector. A presença continua sendo independente do sucesso do link. Não há nova tabela nem migração de dados.
- Interface sem consultas sobrepostas, com limite de seis segundos para status e oito para outras ações. Resultados tardios não sobrescrevem uma recuperação nem atualizam uma sessão já encerrada. Reconexão atualiza a cada dois segundos; estado sem link, cinco; conectado, dez. Ao voltar à aba ou recuperar internet, pede nova verificação.
- Botão Verificar conexão agora com feedback de espera, tempos da última resposta do conector e do link e mensagem Conector sem resposta. O texto deixa claro que isso não confirma notebook desligado. Se a consulta falhar, o estado anterior fica identificado como não confirmado e o último link pode ser tentado.
- O pedido de reconexão continua único e compartilhado. Uma resposta perdida não é tratada como autorização para substituir novamente o túnel; a tela reconsulta o estado.

## Verificação

27 testes Python focados passaram, incluindo nove do conector (quatro novos) e regressões de identidade, gateway e entrada remota. O portal passou em 20 testes Node: 15 de servidor (seis novos) e cinco novos de polling. Incluem simulação de atraso real com abort de 2,5 segundos, link recuperado, concorrência, relatório antigo, heartbeat durante reconexão, expiração, timeout no navegador, erro de autorização e logout. Repetições não somadas.

TypeScript e build de produção passaram; diffs conferidos. Testes usam dados sintéticos e chaves de teste. Nenhuma chamada de IA, mídia pessoal ou leitura de senha real. Sem revisão visual desktop/Safari nesta entrega: runtime de controle de janelas continua com bloqueio já registrado. Testes de funções e publicação não substituem o teste no iPhone.

## Publicação e ativação

Portal publicado com sucesso pelo plugin Sites no mesmo endereço e com o mesmo público:
https://lili-portal-convites.vinicius-queirozt.chatgpt.site

- Versão 3: appgprj_6ad95236fe688191b78a2079f3fb85c6~appgver_0f2801bdd62081918435b90c96f360d0.
- Fonte do Site sincronizada: c921d7f294a855c56821bca78be3a75a8bca1ebb.
- Deployment concluído: appgdep_6ae7cd0cf8508191a4f23441835df9aa.
- Reiniciado somente o conector identificado, depois de verificar ausência de script de reconexão em andamento. O endereço local do túnel foi comparado antes/depois dessa atualização e preservado. Editor e gateway não foram reiniciados; credenciais e sessões preservadas.
- Duas leituras do banco real confirmaram healthy=1, job_state=idle e avanço contínuo de agent_seen/checked_at após ativar o conector. A leitura final tinha heartbeat de um segundo antes; o teste externo final passou em aproximadamente 0,20 s. A comunicação voltou a refletir o endereço atual do arquivo local, em vez do registro antigo do portal.

As contas individuais do editor e o backup em nuvem não foram ativados. O conector ainda precisa estar em execução; esta entrega não instala inicialização automática do Windows nem liga um notebook desligado.

## Continuidade

Esta foi uma correção direta autorizada pelo usuário durante o dia, não uma nova rodada automática nem a conclusão do ciclo noturno pendente. Fonte do portal publicada separadamente pelo Sites. O checkpoint do conector fica no repositório local da Lili junto aos checkpoints anteriores; a sincronização acumulada do GitHub e a ativação de backend de edição continuam pendentes do fechamento/revisão apropriados. Atualizar a página do portal para carregar a nova versão.
