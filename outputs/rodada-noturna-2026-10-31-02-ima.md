# Rodada 2 — ímã opcional na timeline · noite de 31/10 para 01/11/2026

## Entrega

Em **Precisão**, o botão **Ímã: ligado/desligado** controla o encaixe durante o posicionamento pela régua e o arraste das bordas de vídeo. Começa desligado; a preferência é guardada somente neste navegador, sem mudar o projeto ou seu histórico.

O cursor e as bordas podem encaixar nos cortes da montagem, início/fim do vídeo e limites de narração, música e legendas dentro da montagem. Uma linha tracejada identifica o alvo durante o gesto. O alvo mais próximo vence, com preferência estável para os primeiros alvos em caso de empate.

O encaixe tem dois limites simultâneos: até 8 px e no máximo 150 ms. Assim o zoom não puxa o cursor para um ponto distante quando a timeline está muito reduzida. **Shift** ignora o ímã naquele arraste no computador. Tempos digitados, passos por quadro e botões de alinhamento exato permanecem livres, mesmo com o ímã ligado.

Nos aparos, a conversão entre posição da montagem e tempo da fonte respeita a velocidade. Um alvo que violaria duração mínima ou fades de imagem/áudio é ignorado. Também foi corrigido o arredondamento da borda para nunca passar da duração fracionária da fonte. Soltar continua enviando um único clip_update, recuperável pelo histórico existente; cancelar limpa a guia e restaura a posição conforme o comportamento anterior. A guia também é removida ao encerrar a busca e durante a pinça.

Esta entrega não arrasta blocos de áudio, não detecta batidas automaticamente e não cria marcadores manuais. Apenas usa limites que já existem nos metadados. Narração, música e legendas mantêm suas posições quando o vídeo é aparado, como antes; o restante do vídeo continua se aproximando após o aparo.

## Verificação

- **19 arquivos JavaScript passaram**, incluindo um teste novo das funções e dos manipuladores reais de régua/aparo. Cobrem geração dos alvos sem modificar dados, zoom, limites de distância, preferência opcional, falha do armazenamento local, Shift, guia, velocidade, fades, duração fracionária e salvamento em comando único. Os testes anteriores de pinça, busca, precisão e rascunhos continuaram passando. Repetições não são contadas como testes novos.
- **Quatro testes Python existentes e focados passaram**: fades/velocidade/som original, divisão inválida ou protegida atômica, fades visuais com histórico e duração/divisão após velocidade. Nenhuma alteração de backend nesta rodada; a suíte completa de 137 testes da rodada 1 não foi repetida nem somada a este subconjunto.
- Sintaxe, diff e IDs únicos no HTML conferidos. Editor real 8765 respondeu saudável e serviu HTML/JavaScript novos sem cache.
- Dados sintéticos em memória e comandos simulados para o gesto. Nenhum projeto real, original, credencial, sessão, serviço ou IA real foi usado como teste.

## Revisão visual retomada e ainda pendente

Foi lida a skill computer-use e tentada a inicialização desktop por @oai/sky no runtime Node fornecido. A inicialização falhou antes de listar apps, com erro de gravação dos arquivos do kernel. Nenhuma janela foi manipulada, imagem capturada ou teste visual concluído. A revisão anterior de legendas/exportação e a revisão visual deste ímã continuam pendentes; **não foi validado Safari real nem viewport móvel nesta execução**.

## Ativação e publicação

Mudança de frontend compatível com os comandos já ativos: disponível ao recarregar o editor e habilitar o ímã em Precisão. Não houve reinício de editor, gateway, conector ou túnel. A pré-validação de arquivos do backend da rodada 1 continua preparada, aguardando ativação segura no fechamento.

Checkpoint local após os cinco commits anteriores já preservados. Sincronização GitHub acumulada continua reservada ao fim da extra, ou após a segurança se a extra não ocorrer.

## Próximo pacote

Às 01h55, avaliar aparo não destrutivo da narração, que ainda usa o arquivo inteiro: manter compatibilidade com os projetos existentes e alinhar prévia, exportação, fades e redução da música. Retomar a revisão visual quando o runtime permitir, sem usar o celular do usuário. A quinta rodada mantém segurança/contas e o fechamento deve conferir jobs/envios antes de ativar backend e publicar.
