# Primeira etapa: base de permissões por projeto — 22/10/2026

## Resultado concreto

lili/access.py implementa Principal e ProjectAccess. O servidor aceita um identity_resolver fornecido pelo código confiável de autenticação. Esse resolvedor ainda não foi integrado ao portal/gateway; a construção atual do servidor não o configura. Não há modo privado ativo no editor real, interface de compartilhamento ou migração de projetos nesta entrega.

Quando configurado, o servidor exige Principal válida por requisição, atribui o dono na criação e ignora owner_id enviado pelo cliente. Projetos sem dono explícito não ficam visíveis nesse modo. Autorizações são lidas do estado atual do projeto: view, edit, download_exports e download_sources. O dono tem todas; editar/baixar exige visualização, mas não concede administração. Apenas o dono vê/altera a lista de permissões e gerencia lixeira, restauração e exclusão de projeto.

## Cobertura da política HTTP

- Lista ativa filtrada pelo acesso; Lixeira visível somente ao proprietário.
- Projeto, contexto, miniaturas/prévias, mídia original, exportação, uploads, comandos, rascunho, IA e jobs passam pela autorização correspondente.
- /api/jobs/ID também confere o projeto de origem; conhecer um ID não concede acesso.
- GET/POST /api/projects/ID/sharing exclusivos do dono; POST recebe subject, permissions e expected_revision. Lista vazia revoga. Essa API retorna indisponível no modo legado, sem resolvedor de identidade.
- Metadados internos de acesso não entram no JSON público/contexto geral. Proprietário só é definido pela identidade autenticada na criação; não há troca de dono implícita.
- Compartilhamento não entra no histórico de montagem: Desfazer não devolve permissões já revogadas. Comandos registram a identidade confiável como autora em vez de aceitar o autor informado pelo navegador nesse modo.
- Resposta de negação por projeto é 404, tanto para ID inexistente quanto para projeto privado/sem autorização. Identidade ausente em modo individual retorna 401.

## Testes e verificação

Quatro testes HTTP novos usam identidades definidas por um resolvedor exclusivo do servidor sintético, nunca por cabeçalhos de autenticação inventados para a aplicação real. Cobrem duas contas/projetos, tentativas por IDs/headers falsos, mídia original versus prévia, download final separado do original, edição sem poder administrar, revogação, jobs, legado sem dono, sessão ausente, argumentos inválidos e Desfazer sem reautorizar colaboradores.

A suíte completa passou com 71 testes, sem chamadas reais de IA. Os servidores de teste usam diretórios temporários. Nenhuma conta, senha, sessão real ou projeto existente foi lido para obter credenciais ou modificado. O serviço real não foi reiniciado para esta base ainda não ativada.

## Próxima etapa necessária

Implementar a ligação segura portal → gateway → servidor: identidade comprovada no servidor, sessão expirada/revogada recusada e nenhuma confiança em IDs enviados pelo navegador. Definir associação dos projetos atuais por decisão explícita do proprietário. Conferir a identidade das contas convidadas e seu estado no diretório antes da interface de compartilhamento. A checagem de permissões ocorre no início de cada requisição; já ter iniciado uma transferência não permite prometer apagar bytes recebidos ou interromper instantaneamente toda tarefa em voo.

As rotas novas são uma base de integração, não uma promessa de isolamento no modo compartilhado atual. Não habilitar um resolvedor que simplesmente copie um header do cliente. Acesso local de manutenção e clientes CLI/MCP precisarão da mesma estratégia de identidade antes de anunciar privacidade completa.
