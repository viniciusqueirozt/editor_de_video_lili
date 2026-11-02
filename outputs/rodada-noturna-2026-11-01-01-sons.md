# Rodada 1 — noite de 01 para 02/11/2026: sons da biblioteca e fades rápidos

## Recursos entregues

**Som no cursor.** Novo botão na biblioteca para arquivos prontos que contenham áudio, inclusive vídeos. Insere um bloco independente no instante escolhido, sem substituir narração ou música e sem adicionar outra imagem. Na primeira inserção, o trecho é limitado ao espaço restante do vídeo, preservando a fonte inteira para ajustes posteriores; há aviso quando isso acontece. Em seguida abre o painel do bloco para aparo, velocidade, posição, volume e proteção. É possível repetir para combinar vários efeitos sonoros/ambientes próprios, usando o mixer e o histórico já existentes.

**Suavização em um toque.** Dentro de Volume e suavização: Sem fades, Curtos e Suaves preenchem entrada/saída com até 0,2 ou 0,6 segundo. Cada fade é limitado à metade do trecho, inclusive em durações fracionárias e após mudar velocidade. São rascunhos: Aplicar salva; Cancelar descarta. Funcionam também para música e narração, com os campos manuais mantidos.

**Faixa Sons.** A faixa que reunia o som original agora usa nome que também acomoda sons avulsos. O estado vazio abre a biblioteca, seletores e mensagens dizem qual bloco está sendo editado. Sons já extraídos dos vídeos continuam no mesmo modelo/IDs e preservam a ligação de origem para histórico e ações sobre o som original.

## Consistência e recuperação

- O atalho local de silenciar originais preserva os sons avulsos adicionados pela biblioteca, além de música/narração e áudios protegidos. Som extraído de uma cena continua sendo original mesmo se a imagem for removida.
- A inserção é um comando reversível. Bloqueia toque duplicado, ausência de montagem, cursor no fim, mídia sem áudio/em processamento, limite de 200 blocos e troca de projeto/revisão durante espera na fila.
- Falha ao salvar mantém os dados da montagem e libera os botões para nova tentativa; o painel não abre como se a inserção tivesse dado certo. O posicionamento usa o cursor do momento do pedido.
- Atalhos de fades respeitam proteção do bloco e salvamento em andamento; não produzem soma de fades maior que o trecho por arredondamento.
- Biblioteca de efeitos pré-instalados não foi adicionada: o recurso usa arquivos importados pelo usuário. Nenhum pacote externo, API paga, download de modelos ou código Concat incorporado.

## Testes e revisão

Passaram **22 testes Python focados**, dos quais dois novos: mistura de sons avulsos na exportação e preservação desses sons pelo atalho de silenciar originais. Incluem oito testes de áudio independente, 11 de planejamento/atalhos com IA simulada e três exportações sintéticas (efeitos/música/narração). A exportação nova foi decodificada para medir a presença dos dois blocos de efeito nos intervalos esperados, silêncio final, duração da imagem e preservação dos bytes de origem. Não houve chamada real de IA nem uso de mídia pessoal.

Passaram **23 arquivos de testes JavaScript**, um novo para a biblioteca, com testes ampliados do painel de áudio. Exercitam funções reais e DOM/players simulados, cliques repetidos, fila, revisão/projeto alterados, limites, estado após erro, fades proporcionais, proteção e Cancelar. Repetições de testes não foram somadas. Sintaxe e diff verificados. Suíte Python inteira não repetida nesta rodada, pois o ajuste de backend é um filtro de categoria já coberto nos testes focados; não houve mudança de renderizador nem formato de estado.

Não houve validação visual desktop ou Safari real nesta rodada. O runtime de controle desktop estava indisponível nas tentativas anteriores; os testes de DOM não substituem revisão no aparelho. Fica pendente conferir visualmente o espaço dos botões na biblioteca e o painel de mixagem no iPhone.

## Estado de ativação e publicação

Editor 8765 e login remoto saudáveis. Atalhos de fades/nomes novos são servidos como frontend e ficam disponíveis ao atualizar a página, usando a API ativa. **Som no cursor e a distinção de sons avulsos no atalho de silenciar originais estão preparados, mas aguardam ativação do backend**: a versão real consultada ainda não anuncia library_sounds; o botão não é exposto antes dessa capacidade. Nenhum serviço reiniciado, projeto real editado ou sessão/túnel alterado nesta rodada.

Checkpoint local revisado; sincronização GitHub e ativação segura do backend no fechamento após segurança/extra, conforme a rotina autorizada. Não anunciar o ciclo inteiro concluído.

## Próximo pacote

Às 00h55, consultar saldo/reset e retomar a edição: revisar escolha e apresentação das junções de transição, especialmente a concentração de botões em timelines móveis com muitas cenas. Limitar a ampliação ao que possa ser testado e concluído; questões de licença/instalação do Concat e contas reais permanecem fora desta rodada de edição. Rodada de segurança/acesso continua reservada às 03h55.
