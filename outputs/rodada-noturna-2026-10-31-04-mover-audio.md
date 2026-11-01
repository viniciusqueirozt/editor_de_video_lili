# Rodada 4 — mover áudio diretamente na timeline · noite de 31/10 para 01/11/2026

## Como usar

Música e narração ganham uma alça **↔** no início da faixa. Arraste a alça para posicionar; solte para salvar. Um toque na alça ou na forma de onda continua abrindo o painel de tempos e mixagem. Pelo teclado, o botão também abre esse painel, com posição digitável e passos por quadro.

A alça tem 44 × 44 px e assume o gesto apenas nessa área. O restante da forma de onda mantém o comportamento nativo de rolagem; não foi necessário bloquear gestos da página inteira nem desativar o zoom. Hover é limitado a mouse preciso; há feedback de pressão e foco visível. Em trechos muito estreitos a alça pode ocupar mais largura que a representação do áudio para conservar a área de toque. A duração sonora continua sendo a do trecho.

Durante o movimento, início/fim aparecem no rodapé e a faixa mostra a posição provisória. A forma de onda usa a parte visível do trecho quando seus dados já estão disponíveis. A reprodução fica pausada. Soltar usa a posição final do ponteiro, mesmo se o último evento de movimento não tiver sido entregue. Não há salvamento por pixel percorrido.

## Encaixe e limites

O ímã opcional em **Precisão** alinha tanto o início quanto o fim do áudio aos cortes e limites das outras faixas/legendas. Os limites da própria faixa não viram alvos, evitando prendê-la à posição anterior. Reutiliza o limite conjunto de 8 px e 150 ms; Shift ignora o encaixe no computador.

O arraste mantém pelo menos 0,1 segundo do áudio dentro da montagem e respeita o máximo de posição aceito pelos comandos existentes. Se o trecho se estender além do vídeo, o rodapé avisa: não se corta a fonte nem se aumenta o vídeo automaticamente. Áudios que já começam depois da montagem continuam acessíveis pelo botão de ajustes existente. Não há rolagem automática nas bordas nesta entrega; amplie/role a timeline antes de arrastar ou use o painel preciso para deslocamentos longos.

## Recuperação e proteção da edição

- Esc, cancelamento do ponteiro, perda de captura, outra interação de ponteiro, ocultar a página, perder foco ou reconstruir a timeline cancelam o gesto sem comando.
- Movimentos pequenos são tratados como toque. Voltar à posição original não cria entrada no histórico. Arraste cancelado ou concluído não deve abrir o painel pelo clique gerado ao soltar.
- Soltar envia somente media_id e offset em um comando de narração ou música, preservando fonte, aparo, fades, volumes e demais trilhas. O histórico existente permite Desfazer/Refazer.
- A fila confere projeto e revisão novamente antes do envio. Se outra edição/troca ocorrer enquanto o movimento aguarda, ele é descartado em vez de ser aplicado à montagem errada. O servidor continua verificando a revisão enviada.
- Um novo arraste fica bloqueado durante o salvamento. Em conflito, recarrega o estado informado pelo servidor; se a conexão falhar, mostra erro, remove a posição provisória e mantém os metadados locais sem confirmar um salvamento desconhecido. Não promete que uma resposta perdida significa que o servidor não salvou.

## Verificação

**20 arquivos de testes JavaScript passaram**, incluindo um novo que executa os manipuladores reais de áudio e a função real de salvamento serializado. Cobre toque versus arraste, posição ao soltar, fonte preservada, comando único, início/fim no ímã, Shift, limites, rolagem durante o gesto, cancelamentos, captura indisponível, alça removida, reconstrução real da timeline, projeto/revisão/fonte alterados, edição concorrente na fila, envio em andamento, conflito e indisponibilidade de rede.

**Seis testes Python existentes e distintos passaram**, focados em atualização parcial e histórico de música/narração, Refazer após recarregar e três exportações de áudio com posição, aparo, fades e redução musical medidos em material sintético. Não houve alteração de backend nesta rodada; a suíte de 139 testes da rodada anterior não foi repetida nem somada ao subconjunto. Repetições de testes não contam como casos novos.

Sintaxe, diff e 284 IDs únicos do HTML conferidos. A produção 8765 respondeu saudável e serviu os arquivos JS/CSS modificados com no-store. Nenhum serviço foi reiniciado, nenhuma mídia pessoal foi usada e não houve chamada real de IA, acesso a credenciais ou alteração de projeto real.

## Ativação e revisão visual

Frontend servido, disponível ao recarregar com os comandos já existentes. Não exige backend novo. O aparo de narração da rodada 3 e a pré-validação de fontes da rodada 1 continuam aguardando ativação segura no fechamento; narration_trim ainda não foi anunciado pelo processo real consultado.

Tentativa de retomar o controle desktop por @oai/sky falhou novamente antes de iniciar, com erro de gravação dos arquivos do kernel. Não houve captura de tela, interação visual ou teste de Safari/iPhone. Os testes verificam funções, HTML e estilos; sensação do arraste, rolagem real, foco e leitura no aparelho continuam pendentes. A entrega não deve ser anunciada como validada no celular.

Checkpoint local; sincronização GitHub acumulada permanece para o fim da extra ou depois da segurança caso a extra não ocorra. Projetos, originais, Cora aprovada, sessões, gateway, portal, conector, túnel e logo preservados.

## Próximo passo

Às 03h55, revisar segurança/acesso/contas com identidades e serviços simulados, sem ativar isolamento individual incompleto nem migrar proprietários. Depois, avaliar a única extra com o saldo consultado e o tempo disponível. Fechar com publicação acumulada, conferência de jobs/envios antes de qualquer ativação, saúde/capacidades e resumo do que está efetivamente ativo, sempre antes das 5h.
