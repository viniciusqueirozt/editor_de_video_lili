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


## Transporte preparado — madrugada de 23/10/2026

lili/identity.py acrescenta assinador/verificador HMAC-SHA256 para futuras requisições do gateway ao editor. A identidade é vinculada a método, caminho/query, tamanho declarado, tipo de conteúdo, validade curta, nonce de uso único e audiência da instância. Campos duplicados, assinatura inválida, replay, tempo expirado/futuro e cache cheio são recusados. A audiência precisa ser nova por instância na futura ativação e a chave precisa ser compartilhada somente pelos processos confiáveis; o construtor não aceita chave curta nem texto livre no lugar de bytes.

Cinco testes focados passaram, incluindo um servidor HTTP real com o verificador ligado à política por projeto e replay concorrente com somente um vencedor. Não foram acessadas credenciais reais nem modificados serviços/projetos.

Este transporte **não autentica a conta do portal**, não foi ligado ao gateway real e não está ativo no servidor de produção. O próximo passo continua sendo provar a sessão individual no portal, entregá-la com segurança ao gateway e definir a migração dos proprietários. O assinador só pode receber uma Principal previamente autenticada, nunca um ID livre fornecido pelo cliente; cabeçalhos do navegador devem ser descartados antes de assinar.

Limites: cache de nonces em memória, com capacidade finita e recusa quando cheio. Audiência nova por instância e coordenação/rotação segura da chave serão necessárias na ativação. O conteúdo integral de uploads em streaming não é assinado: são vinculados apenas seus metadados. Essa peça assume o canal local entre processos gerenciados, não substitui HTTPS externo nem configura transporte remoto seguro por si só.

## Gateway opcional ligado ao transporte — 23/10/2026, 00h55

RemoteServer agora pode receber identity_resolver e IdentitySigner juntos, por construção em código confiável. No modo opcional, cada requisição exige uma Principal comprovada pelo resolvedor; não há fallback para login compartilhado, leitura da credencial compartilhada ou aceitação de um ID cru. A lista de cabeçalhos encaminhados descarta cookies, Authorization e afirmações de identidade vindas do navegador. O gateway assina uma nova afirmação local por requisição, com método, caminho e metadados do corpo efetivamente encaminhados.

Três testes novos com gateway e editor HTTP reais verificam criação atribuída à conta autenticada, separação de duas contas, cabeçalhos falsos, sessão ausente/revogada, retorno inválido/erro do resolvedor e divergência de chave. Dezesseis testes existentes de login remoto, identidade e permissões também passaram. O resolvedor nos testes usa somente sessões sintéticas mantidas pelo servidor; não implementa a autenticação real do portal.

**Preparado, sem ativação:** main() continua construindo o gateway no modo compartilhado atual. Falta a troca segura de sessão/ticket com o portal, consulta de expiração/revogação da conta e configuração coordenada do verificador no editor. O gateway opcional recusa entradas cross-site até existir um fluxo específico de entrada do portal; suas rotas legadas de login/setup/logout ficam indisponíveis nesse modo. Nenhuma dessas configurações foi aplicada aos serviços reais. Não há isolamento real anunciado nem migração automática de proprietários. Uma sessão que já iniciou uma transferência não é revalidada durante cada bloco.
