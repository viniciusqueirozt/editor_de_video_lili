# Processo reutilizável de desenvolvimento por rodadas

Documento de procedimento em elaboração, a pedido do usuário em 24/10/2026. Pode servir de base a um relatório de transferência para outro projeto quando solicitado. Não cria automação, não autoriza despesas e não copia dados da Lili para outro produto.

## 1. Definir o contrato do ciclo

Registrar objetivo do produto, usuários, áreas prioritárias, horários permitidos, duração/frequência e o que exige decisão humana. Separar quantidade de rodadas de quantidade de recursos: uma rodada deve comportar um pacote coerente de melhorias de escopo normal. Datas e exceções pertencem à agenda do projeto, nunca a uma regra universal presumida.

Na Lili: quatro rodadas de edição, uma de segurança/contas, extra de visual e mercado se houver margem. Execução manual atual em sequência; à noite uma por hora e extra logo após a quinta. Excluir sexta à noite e madrugada de sábado; não trabalhar automaticamente de manhã/tarde. Esses detalhes precisam ser redefinidos ao replicar em outro projeto.

## 2. Ler o estado antes de escolher trabalho

Conferir instruções locais, Git, esteira, relatório anterior, serviços e limitações conhecidas. Distinguir código preparado, funcionalidade testada e recurso realmente ativo. Não contar documentação ou componentes não integrados como função pronta para o usuário. Preservar modificações de outros chats.

## 3. Distribuir orçamento por percentual

Consultar o uso normal permitido, janela de cinco horas, semanal e horários reais de renovação. Trabalhar com percentual da conta, sem convertê-lo em número exato de tokens. O usuário informou uso exclusivo durante seus períodos reservados, mas verificar os limites reais continua necessário.

Referência de planejamento: aproveitar cerca de 70%–85% do uso total da janela, preservando margem antes de 90% para terminar a entrega em curso. Não é garantia nem licença para consumir artificialmente. Se a janela já começou parcialmente usada, o orçamento é apenas a diferença disponível. Reservar testes, segurança, revisão, relatório e publicação antes de distribuir pacotes de produto. Um reset no meio do ciclo exige uma nova leitura e nova identificação da janela.

Ajustar o tamanho dos pacotes conforme consumo observado e tempo restante. Não parar automaticamente após uma alteração pequena se ainda houver trabalho útil e margem. Também não iniciar uma grande dependência perto do esgotamento. Consultar novamente entre pacotes e obrigatoriamente depois da implementação/testes de cada rodada. Se os limites estiverem indisponíveis, não estimar nem comprar créditos; preservar o checkpoint e informar a limitação quando relevante.

Manter uma só extra por janela autorizada, com estado operacional privado identificado pelo reset. Nunca usar orçamento semanal como se renovasse a cada cinco horas. Percentuais reais e respostas da conta ficam no chat ou no controle privado autorizado, fora de documentação versionada, segredos e logs públicos.

## 4. Escolher e concluir pacotes

Priorizar valor, criticidade, frequência de uso, dependências e consistência. Definir um resultado observável para cada pacote e critérios de aceite antes de alterar código. Resolver a função de ponta a ponta quando viável: estado, servidor, interface, prévia/saída e recuperação de erro. Não fragmentar artificialmente em muitas entregas para aumentar a contagem.

Se houver uma falha crítica, corrigir antes de expor o recurso; a rodada específica de segurança não substitui verificações básicas nas demais. Preservar uma margem de tempo suficiente para terminar e revisar, respeitando a janela de horário autorizada mesmo que sobrem créditos.

## 5. Testar com propósito

Usar dados sintéticos e serviços/identidades simulados. Nunca usar mídias pessoais, credenciais reais ou inferência paga como conveniência de teste. Verificar regras, erros e estado inalterado em falhas; para renderização, gerar e medir artefato real; para interface, executar as funções reais e revisar o resultado no navegador.

Rodar testes focados durante a implementação. Usar suíte completa quando alterações compartilhadas justificarem, como mudanças no modelo de estado, tempo, exportação e autenticação. Não repetir a suíte completa sem nova mudança ou incerteza relevante. Conferir se testes novos foram realmente descobertos/executados e se asserções medem comportamento, não apenas repetem a implementação.

Registrar número real de testes/cenários, origem dos dados e limitações. Navegador desktop ou emulação não comprovam Safari/iPhone real. Separar validação automatizada, visual no desktop e teste humano no aparelho.

## 6. Revisar e criar checkpoint

Conferir o diff e os arquivos a versionar. Não incluir dados pessoais, segredos, mídias, dependências, estado do orçamento ou arquivos temporários. Criar commits revisáveis de código, testes e documentação. Uma entrega com testes falhando não está concluída; ajustar ou registrar bloqueio concreto sem anunciar sucesso.

## 7. Publicar ao fechar a extra

A pedido do usuário, publicação é etapa obrigatória de fechamento após a extra — ou após a última rodada executada se não houver extra. Sincronizar o GitHub autorizado, disponibilizar o resultado e verificar o que está ativo. Antes de reiniciar serviços, conferir jobs e envios; nunca interromper processamento ou invalidar sessões silenciosamente para marcar ativação como concluída.

Para mudanças de acesso externo, dados, cobrança ou implantação que ultrapassem a autorização atual, preparar primeiro um resultado revisável e explicitar a decisão necessária. Caso parte da ativação deva aguardar, registrar exatamente qual parte, por quê e como retomar. Um ambiente isolado de demonstração não deve ser confundido com produção.

## 8. Encerrar com relatório simples e completo

Informar: melhorias por pacote, recursos novos, correções de erro/segurança, testes realizados, publicação, estado ativo/preparado e pendências. Após os testes e ao final da rodada, consultar e apresentar os percentuais restantes das duas janelas e horários da leitura/renovação. Não somar repetições de testes como novos testes.

Ao final do conjunto, consolidar as entregas em linguagem de produto e manter detalhes técnicos em documento vinculado. Registrar aprendizado para escolher os próximos pacotes e calibrar o orçamento com evidência. Não estender agenda ou continuar em horário proibido por haver limite sobrando.
