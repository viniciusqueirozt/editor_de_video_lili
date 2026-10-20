# Linha do tempo e acesso pelo celular

A interface agora tem régua, cursor de reprodução, zoom, clipes com largura proporcional ao tempo, miniaturas do trecho e uma faixa com a forma de onda real da narração. Clique na régua para buscar um momento; selecione um clipe e arraste suas bordas para aparar. O botão **Dividir** ou a tecla **S** corta no cursor. **Ctrl+Z** desfaz. As setas na régua avançam um quadro; Shift com seta avança um segundo. A montagem aprovada da Cora foi preservada.

Dividir, aparar, reordenar e remover atualizam o mesmo projeto usado pela exportação e pelo Codex. As cenas protegidas continuam protegidas. A duração mínima de um trecho é 0,1 segundo. A reprodução ainda troca proxies de mídia no navegador; pode haver uma pequena pausa no carregamento entre arquivos. A exportação é feita nos arquivos importados.

## iPhone como site-app

Foi preparada uma PWA com ícone, modo de janela independente e instruções no botão de celular. Depois de ativar o endereço HTTPS, abrir no Safari, entrar no estúdio e usar **Compartilhar → Adicionar à Tela de Início**. O notebook deve permanecer ligado, conectado e com o editor rodando. Não há edição offline; instalação, gestos e reprodução ainda precisam ser testados em um iPhone real.

Não é necessário comprar um domínio para o piloto. Um [Quick Tunnel da Cloudflare](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/) fornece um endereço HTTPS temporário. O endereço muda ao recriar o túnel, não tem garantia de disponibilidade e serve para teste. Para uso habitual e comercial, escolher endereço estável e infraestrutura apropriada.

O gateway de acesso exige login para abrir projetos, mídias, comandos e exportações. A senha é guardada somente como hash com sal; as sessões usam cookies HttpOnly, SameSite e Secure no acesso HTTPS. Há limitação de tentativas e verificação da origem das alterações. O editor original permanece em loopback. O túnel deve apontar apenas para a porta **8767**, do gateway autenticado; nunca para a porta 8765 do editor.

No PowerShell, dentro do projeto:

```powershell
.\acesso-remoto.ps1 -Modo Preparar
```

Criar usuário e senha no notebook em `http://127.0.0.1:8767/auth/setup`. O cadastro só é oferecido localmente e não substitui uma conta já criada. Depois:

```powershell
.\acesso-remoto.ps1 -Modo Ativar
```

O ativador baixa o cloudflared do repositório oficial da Cloudflare, confere o SHA-256 publicado e abre um túnel para o gateway. Ele só permite a ativação após o cadastro. Mantenha o link e a senha com as pessoas autorizadas a usar o estúdio. O login deste piloto dá acesso a todos os projetos; ainda não há permissões por cliente ou contas separadas.

Para encerrar o acesso externo:

```powershell
.\acesso-remoto.ps1 -Modo Desativar
```

Vídeos são enviados em blocos de 8 MiB e reconstituídos sem alterar seus bytes. Uma repetição do bloco já recebido não duplica os dados. O limite por arquivo continua 2 GiB. O envio não retoma após recarregar a página ou reiniciar o servidor; nesses casos, reenviar o arquivo. Não foi medido o desempenho com arquivos grandes ou internet móvel.

## Concat

O motor atual continua FFmpeg. O Concat oferece um editor nativo e recursos que podem ser aproveitados numa integração futura, mas seu código não foi incorporado. A [documentação MCP atual](https://github.com/jub0t/Concat/blob/main/docs/MCP.md) ainda informa que o agente edita seus próprios projetos e que editar ao vivo o projeto aberto na janela está planejado. O site publicado e a branch principal também descrevem estágios distintos da integração; não presumir que o instalador publicado ofereça os mesmos recursos da branch principal.

Para esta correção, manter a interface web e o estado compartilhado já existentes evitou uma migração de motor, formato de projeto e aplicativo. Ainda não foi comparado desempenho de exportação com o Concat. Uma adoção posterior deve validar importação, cortes, títulos, áudio, prévia, exportação e continuidade entre edição manual e agente.

## Verificação desta etapa

Testes de divisão com duração preservada, campos e desfazer; proteção de cenas; limites de corte; forma de onda; envio em blocos; senha, sessão, origem, bloqueio de tentativas e acesso não autenticado. No navegador, divisão, desfazer, aparo por arrasto e reprodução até o final foram exercitados em projeto isolado. Acesso externo e uso em iPhone dependem da ativação e do teste com os aparelhos.
