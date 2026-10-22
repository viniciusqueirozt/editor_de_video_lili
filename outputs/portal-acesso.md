# Portal fixo da Lili

Endereço provisionado: https://lili-portal-convites.vinicius-queirozt.chatgpt.site

## Fluxo

1. Administrador cria convites de uso único, com validade de 48 horas e vinculados ao e-mail autorizado.
2. Convidado cadastra e-mail, senha própria e código. O código é consumido atomicamente; uso simultâneo não cria duas contas.
3. Após login, o portal mostra o estado compartilhado do túnel e o botão Abrir editor quando o link está ativo.
4. Se o link estiver inativo e o conector do notebook estiver online, Reconectar estúdio cria um único pedido compartilhado. O banco bloqueia pedidos simultâneos.
5. O conector faz duas verificações do endereço. Se ele já voltou a funcionar, mantém o link. Caso continue inativo, reinicia somente o processo do túnel gerenciado e usa o inicializador existente.
6. O notebook informa o endereço e o resultado ao portal. Todos os usuários passam a visualizar esse mesmo estado.

## Segurança e limites

- Portal em Sites, com dados estruturados em D1; não hospeda as gravações. O editor e suas mídias continuam no notebook e protegidos pelo login existente.
- Contas próprias por e-mail/senha. Convites armazenados como hash; sessões em cookie HttpOnly/Secure/SameSite=Strict. Senhas com salt e derivação PBKDF2-HMAC-SHA256, mais segredo de servidor separado do banco.
- Não implementa confirmação automática da propriedade do e-mail, envio de mensagens ou recuperação de senha por e-mail. O administrador compartilha o código manualmente por um canal privado. Não foi contratado serviço de e-mail.
- API verifica sessão/permissão e Origin em alterações, limita tentativas de login e reconexão e impede URLs de destino arbitrárias.
- A chave do conector fica em arquivo privado ignorado pelo Git e no ambiente secreto do Site. Nunca vai para o navegador. O notebook aceita apenas a ação fixa reconnect; não recebe código, comandos livres nem caminhos enviados por visitantes.
- O conector faz conexões HTTPS de saída. Não adiciona portas públicas. Sem conector, energia ou internet no notebook, o portal permanece acessível, mas não consegue ligar o computador nem criar um túnel.
- Detectar queda leva alguns segundos; durante a tentativa o botão fica bloqueado. O lease vence em 180 segundos para permitir nova tentativa se o conector travar. Só uma instância local do conector pode gerenciar o túnel.
- O endereço fixo depende da disponibilidade e dos limites da hospedagem Sites; não equivale a garantia de hospedagem gratuita ilimitada.

## Ativação inicial

O Site foi criado privado para o proprietário configurar a conta administradora. Nessa única etapa a plataforma pode pedir login ChatGPT para proteger o bootstrap. Os convidados usarão as contas próprias depois da abertura do portal.

Após o proprietário cadastrar e-mail e senha diretamente na tela: desativar ALLOW_SETUP no ambiente, publicar a revisão desse ambiente e mudar o acesso do Site para público (somente a página de entrada; os dados seguem sob a autenticação própria). Iniciar o conector com `iniciar-portal.ps1 -Background` e verificar status/link reais. A chave já foi provisionada; não regenerá-la desnecessariamente. Não ler a senha do usuário nem inventar uma conta administradora.

O acesso externo antigo permanece funcionando enquanto o portal é preparado. Não substituir nem encerrar o túnel saudável para testar esta funcionalidade.

## Fonte e verificação

- Código do portal: checkout gerenciado pelo Sites em work/sites/lili-portal, com identidade em .openai/hosting.json. A fonte é sincronizada pelo helper oficial no repositório do próprio Site.
- Identidade: appgprj_6ad95236fe688191b78a2079f3fb85c6. Não criar outro Site para continuar o trabalho.
- Nove testes do portal cobrem bootstrap, autorização, convites, corrida de pedidos, dispositivo offline, revogação, limites de login, destinos de túnel e tamanho de corpo/expiração de convite.
- Quatro testes do conector usam chamadas simuladas; nenhum túnel real foi reiniciado para teste.
- Build e tela desktop verificados. Safari real e reconexão real pelo portal dependem da conclusão da conta administradora e da ativação pública.

## Estado da publicação

- Versão privada publicada com sucesso: appgprj_6ad95236fe688191b78a2079f3fb85c6~appgver_6d10745a19f48191936fe5e02a174495.
- Commit da fonte no Sites: 6d7b7ba88ed70ed5d8d806e3d29264c9e7a952c1.
- Ambiente de bootstrap: ALLOW_SETUP ainda habilitado. PASSWORD_PEPPER e DEVICE_KEY estão em ambiente secreto. Nunca regenerar o pepper após criar contas, pois isso invalidaria a verificação das senhas existentes.
- Conector preparado, porém ainda não iniciado: a camada privada do Sites bloqueia o acesso anônimo do dispositivo. Aguardar o proprietário criar a conta, desabilitar o bootstrap, aplicar o ambiente e liberar a página pública com autenticação própria antes de iniciar o conector.
- A tela nativa de login ChatGPT foi aberta apenas para a configuração privada do proprietário. Nenhum e-mail ou senha real foi preenchido pelo agente. O usuário deve usar a conta proprietária do Sites para essa etapa única; as contas convidadas depois são próprias da Lili.
- Oito testes iniciais e o nono caso de limites/expiração passaram; quatro testes Python passaram. A prova visual de cadastro é da prévia local com dados vazios, não de uma conta real criada.
