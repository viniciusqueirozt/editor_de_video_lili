# Estrutura das próximas rodadas da Lili

Diretriz do usuário de 24/10/2026. Substitui a prioridade anterior de usar as rodadas de produto para preparar autenticação. Este documento organiza trabalhos futuros; não cria ou reativa uma automação.

## Cinco rodadas e uma extra condicional

| Rodada | Foco | Exemplos de entregas |
| --- | --- | --- |
| 1 | Montagem e efeitos | Cortes, transições, efeitos visuais, marca d'água e controles da linha do tempo. |
| 2 | Legendas e composição | Legendas editáveis, tipografia, posicionamento, enquadramento e proporção do vídeo. |
| 3 | Áudio e exportação | Volume, fades, trilhas/efeitos sonoros, sincronismo, resolução, qualidade e formatos compatíveis. |
| 4 | Fluxo de trabalho e recursos de edição | Importação, exclusão, recuperação e outros obstáculos concretos para editar e entregar. |
| 5 | Segurança, contas e acesso | Investigar/corrigir falhas e melhorar login, convites, recuperação de acesso, sessões, identidade e permissões dos projetos. |
| Extra | Visual e pesquisa de mercado | Melhoria visual, acompanhada de pesquisa objetiva sobre concorrentes e formas de monetização. Somente se houver margem de uso e tempo. |

A distribuição dos temas nas quatro primeiras rodadas é orientativa: escolher os problemas mais úteis e viáveis do editor, sem obrigação de implementar um exemplo de cada linha. As quatro rodadas devem resultar em avanços de edição ou de seu fluxo, com comportamento concreto e testes. Não contabilizar apenas documentação ou infraestrutura de contas como recurso de edição entregue.

O usuário esclareceu que a quinta rodada também pode implementar melhorias de contas, pois elas controlam o acesso ao sistema. Isso inclui integrar com segurança as contas individuais do portal ao editor, login/logout, convites, recuperação de acesso, expiração/revogação de sessões, proprietários e compartilhamento autorizado. A quinta rodada procura problemas reais de segurança; corrigir os encontrados e registrar escopo e limitações da revisão. Não inventar uma falha para preencher a rodada. Todas as alterações continuam recebendo verificações básicas durante sua própria implementação. Uma falha crítica encontrada antes deve ser corrigida antes de expor o recurso, sem esperar a quinta rodada.

Contas individuais, compartilhamento e nuvem permanecem na esteira. A preparação existente não significa privacidade ativa. Contas, identidade e controle de acesso podem avançar na quinta rodada de segurança. Essas frentes não devem consumir as quatro rodadas de edição como prioridade padrão; dependências indispensáveis ou riscos críticos precisam ser explicitados no relatório.

## Extra: visual e mercado

Consultar fontes primárias atuais, como páginas oficiais de recursos, preços e licenças. Verificar modelos observáveis de receita, por exemplo assinatura, recursos premium, créditos ou serviços de edição, sem apresentar preços de venda como prova de lucro ou receita de um concorrente. Registrar links, data, diferenças relevantes e uma hipótese prática para a Lili. Pesquisa pública na internet não deve ser descrita como entrevista com clientes ou validação de demanda.

A pesquisa deve orientar uma melhoria visual útil. O usuário esclareceu que as entregas devem ter escopo normal e completo, sem limite artificial de dez minutos ou obrigação de serem pequenas. Não instalar serviços pagos, contratar APIs, iniciar cobranças, mudar preços ou enviar mídias pessoais a concorrentes. A logo permanece na ramificação própria. Manter funções gratuitas locais como prioridade do editor.

## Limites, horários e relatório

- Consultar os limites no início e novamente depois da implementação e dos testes de cada rodada. Conferir uso normal permitido, janela de cinco horas, semanal e horários de renovação. Os limites são compartilhados com os outros chats.
- Informar no chat o percentual restante real nas duas janelas, o horário da consulta e da renovação. Se a consulta falhar, declarar indisponível. Não estimar saldo final usando a consulta inicial nem chamar percentuais de contagem exata de tokens.
- Manter margens conservadoras: não iniciar rodada comum com menos de 20% na janela de cinco horas ou 15% no semanal. Extra somente com pelo menos 35% e 15%, respectivamente, e tempo para concluir, testar e registrar. No máximo uma extra por janela de cinco horas; não criar execução adicional para ela. Respeitar restrições mais específicas da agenda autorizada.
- Trabalho automático somente durante noite/madrugada, no horário de São Paulo, dentro das datas e horários autorizados. Nenhuma continuação automática pela manhã ou tarde. A agenda anterior foi encerrada e removida; uma próxima agenda precisa de autorização e configuração próprias.
- Relatório simples ao final: o que mudou, recursos novos, erros corrigidos, testes, o que está ativo, o que aguarda ativação, pendências e percentuais restantes consultados após o trabalho. Ao encerrar o conjunto, consolidar as entregas sem somar testes repetidos como novos.
- Sincronizar somente código, testes e documentação no GitHub autorizado. Percentuais/dados da conta, segredos, mídias e estado operacional privado ficam fora dos documentos versionados.
- Preservar projetos reais, originais e montagem aprovada. Usar dados sintéticos e simular respostas de IA nos testes. Não reiniciar serviços com possíveis envios/processamentos em andamento. Não anunciar Safari real validado sem teste humano.

## Cadência esclarecida em 24/10/2026

Demonstração atual: cinco rodadas sequenciais e extra logo depois, havendo limite. Rotina recorrente autorizada: todas as noites, exceto a noite de sexta-feira para sábado; uma rodada por hora, extra imediatamente após a quinta. A exclusão cobre sexta à noite e as primeiras horas de sábado, mantendo sábado à noite para domingo. A configuração e os horários da agenda devem respeitar São Paulo e encerrar antes da manhã.

## Aproveitamento de limite e escopo — ajuste de 24/10/2026

O usuário pediu pacotes mais completos por rodada, sem obrigação de mudanças pequenas. Planejar o conjunto para aproveitar aproximadamente 70% a 85% do uso total da janela de cinco horas, preservando margem antes de 90% para terminar, testar e registrar o pacote em curso. O consumo é compartilhado e não previsível com exatidão; a faixa é referência, sem garantia de atingir um número. Não gastar por gastar, repetir testes sem motivo, inflar respostas ou iniciar trabalho que possa ficar incompleto por limite.

Selecionar várias melhorias relacionadas e úteis por rodada e reavaliar o saldo entre elas. Reservar a revisão de segurança e a extra ao distribuir o orçamento, consultar reset real e semanal. Se os limites já estiverem altos por outros chats, reduzir o escopo e priorizar concluir as entregas iniciadas. Rotina noturna encerra antes das 5h, mesmo havendo saldo; nenhuma continuação automática durante o dia.

## Publicação e reaplicação

O usuário pediu publicar as melhorias ao final da extra. Incorporar revisão, testes, sincronização e checagem da ativação ao orçamento do ciclo, preservando serviços em uso. Processo genérico em elaboração em outputs/processo-reutilizavel-de-rodadas.md, para futuro relatório de transferência quando solicitado.
