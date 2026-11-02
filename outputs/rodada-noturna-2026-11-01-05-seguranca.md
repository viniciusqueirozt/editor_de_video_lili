# Rodada 5 — noite de 01 para 02/11/2026: integridade dos pedidos e revisão de acesso

## Falha reproduzida e correção

A API lia o tamanho informado em Content-Length, mas não verificava se todos esses bytes tinham chegado antes de interpretar o JSON. Em servidor sintético, um pedido declarou bytes extras, enviou um objeto válido menor e encerrou o lado de envio; a versão anterior respondeu HTTP 201 e criou o projeto. Não houve teste desse comportamento contra projetos reais. É uma falha de integridade da requisição, não uma demonstração de acesso sem login.

Agora a API exige corpo completo antes de interpretar ou aplicar qualquer ação. Conteúdo incompleto retorna erro sem alteração; leitura JSON usa timeout de inatividade de até dez segundos, restaura o timeout anterior e trata interrupção como erro de envio. Essa regra é para comandos/metadados JSON: não encurta o timeout dos uploads binários. A proteção no editor também cobre o caso de o gateway interromper o encaminhamento depois de receber apenas parte do corpo.

## Endurecimento complementar

- Campos JSON duplicados, inclusive dentro de args/objetos internos, são recusados para evitar interpretações ambíguas.
- JSON deve ser objeto UTF-8 com strings Unicode válidas; surrogates isolados escapados, constantes NaN/Infinity e números que virem infinito também são recusados.
- Conversão de inteiro excessivamente grande passa a retornar erro de validação, em vez de erro interno por overflow.
- Mensagens ao cliente não incluem corpo da solicitação, caminhos, cookies ou segredos. Não foram criadas rotas administrativas, portas públicas ou permissões adicionais.

## Acesso e contas: escopo conferido

Revisados código e testes das proteções de Host/Origin, enquadramento HTTP, cookies/sessões, gateway, prova de identidade e permissões por projeto. Os testes existentes de falsificação, revogação e separação de identidades sintéticas permanecem aprovados. Isso não é auditoria independente de todo o sistema nem prova de ausência de outras falhas.

Contas individuais reais continuam **não ativadas**: endpoint/fluxo de sessão do portal, integração coordenada e migração de proprietários seguem pendentes. Não atribuímos projetos legados ao primeiro visitante nem anunciamos isolamento real. O login compartilhado atual e suas sessões permanecem preservados. Não foram lidos auth.json/credenciais reais; testes de autenticação usam somente arquivos e sessões sintéticos isolados. Não se alterou nem reiniciou gateway, conector ou túnel.

## Verificação

O teste de regressão primeiro falhou na implementação anterior (201 em vez de rejeição), confirmando o comportamento. Após a correção, pedidos truncados diretos e encaminhados pelo gateway foram recusados, com confirmação de que nenhum projeto foi criado. Testes adicionais cobrem chaves duplicadas, números não finitos, Unicode inválido, valor inteiro excessivo e restauração do timeout. A exceção de desconexão exibida pelo Windows durante um encerramento sintético não tornou o teste inválido; os casos terminaram aprovados.

Passaram **182 testes Python na suíte completa**, seis novos nesta rodada. Também passaram 33 testes focados de HTTP/acesso/identidade/sessão e 24 arquivos JavaScript; não somar essas repetições ao total. Suíte completa justificada pela mudança central no parser usado por comandos, uploads de metadados e planejamento. Nenhuma inferência real de IA, mídia pessoal ou teste de Safari real. Diff revisado.

## Ativação e fechamento

Correção preparada para ativar ao reiniciar exclusivamente o editor após conferir trabalhos/envios. Ela não exige reiniciar o gateway nem invalidar sessões reais. Publicação no GitHub e ativação das capacidades das rodadas 1/3/4 continuam no fechamento desta execução, após extra caso haja tempo/saldo. Até essa checagem, não anunciar correção ativa ou ciclo encerrado.

Próximo passo operacional: consultar novamente os limites e o relógio, verificar extra ainda não usada na janela e decidir um pacote de visual/pesquisa que caiba antes das 5h com margem para testes, publicação e ativação. Caso não caiba, publicar após esta rodada; nunca prolongar para manhã/tarde.


## Estado final após publicação

Entrega publicada e código ativo no editor no fechamento de 02/11/2026, acumulado até cef630b. Reinício somente do editor após ausência de jobs/uploads/processamento; gateway, conector, túnel e sessões preservados. Verificadas saúde e capacidades HTTP, bloqueio sem login e endereço remoto saudável. A indicação anterior de ativação pendente é histórica. Revisão visual desktop e Safari real continuam pendentes. Ver [relatório consolidado](relatorio-noite-01-02-11-2026.md) para verificações, limitações e próximo passo.
