# Rodada de melhorias — precisão da linha do tempo

Entrega de 24/10/2026, solicitada diretamente pelo usuário. Uma rodada de implementação; não representa um novo ciclo de cinco rodadas ou uma execução automática durante o dia.

## O que mudou

- **Precisão no corte:** botão na linha do tempo e acesso pelo contador abaixo da prévia. Reúne navegação, posição digitável e aparo no cursor. No desktop, abre ao lado do monitor; no layout estreito, como painel inferior com rolagem.
- **Um quadro por toque:** voltar/avançar na grade de 30 fps da montagem. As setas na linha do tempo usam a mesma grade; Shift + seta continua movendo um segundo. O passo é da montagem, não a promessa de percorrer cada quadro nativo de um original com taxa variável.
- **Tempo digitável:** aceita segundos com vírgula ou ponto (1,5) e minutos:segundos com até três casas decimais (00:01.500). Posição inválida ou além da duração apresenta erro sem mover o cursor.
- **Entrada/saída no cursor:** apara a cena selecionada, respeitando velocidade, proteção, duração mínima e fades de imagem/som. Usa o comando existente e seu histórico. Desfazer está disponível no próprio painel.
- **Pinça na régua:** dois dedos ampliam/reduzem a escala mantendo o tempo sob o ponto médio. O cursor anterior é restaurado quando o gesto se transforma em pinça. Soltar um dedo não transforma o dedo restante em uma busca acidental. As trilhas continuam com rolagem horizontal nativa; a pinça personalizada fica restrita à régua, sem bloquear o zoom do navegador no restante da página.
- **Estado da busca:** o painel distingue a posição pronta, a busca do quadro e o salvamento. O aparo fica bloqueado enquanto a prévia ainda busca a posição e durante o salvamento.

## Erros corrigidos

A busca dentro da mesma cena reconstruía o painel de ajustes a cada movimento. Agora os campos são preservados; uma mudança de cena ou atualização efetiva do projeto renova o painel.

Pedidos de busca sucessivos podiam usar callbacks antigos de carregamento e encerrar o estado de busca antes de alcançar a posição mais recente. A prévia agora mantém o último destino, aguarda a busca em curso e confere novamente a posição. Um evento antigo não encerra a busca atual; carregar somente metadados também não declara a imagem pronta.

Ao aparar a saída arrastando, o salvamento colocava o cursor no início da cena. Agora ele permanece imediatamente antes da nova saída, dentro da cena aparada. Ao cancelar ou soltar a borda sem alteração, volta à posição anterior. O limite de aparo por arraste também passa a considerar os fades do áudio original, além dos visuais.

## Como usar

1. Abra um projeto e toque em **Precisão**, no rodapé da linha do tempo, ou no contador abaixo do vídeo.
2. Digite a posição e toque em **Ir**, ou use **−1 quadro / +1 quadro**.
3. Aguarde **Posição pronta** e aplique **Entrada no cursor / Saída no cursor** quando o corte estiver correto.
4. Use **Desfazer última alteração** para revisar a escolha sem sair do painel.

A saída é o limite final do trecho; a prévia permanece imediatamente antes desse limite. Aparar encurta a sequência e aproxima as cenas seguintes. Narração, música e legendas preservam suas posições absolutas: o painel avisa que é necessário conferir o sincronismo após esse tipo de corte. Esta entrega não implementa retemporização automática dessas faixas.

## Verificação

- Sintaxe de app.js e timeline.js e git diff --check passaram.
- Os **13 arquivos de testes JavaScript** passaram, incluindo a nova cobertura de precisão. Os testes executam funções e handlers reais com vídeo/rede/DOM simulados: entrada inválida, 30 passos = um segundo, grade entre quadros, limites, velocidade, fades visuais/sonoros, proteção, buscas concorrentes, troca de cena/fonte, metadados sem imagem, pedido antigo de reprodução, preservação do inspetor, ancoragem da pinça e cancelamento dos ponteiros.
- Revisão no navegador desktop com projeto isolado sintético: posição 1,5 s, avanço para 1,533 s, aparo da saída, salvamento e Desfazer; posição 4 s na segunda cena a 1,25×, avanço para 4,033 s, aparo da entrada e Desfazer dentro do painel. A duração de sete segundos foi restaurada pelo histórico. Entrada inválida 99:99 recusada. A reprodução iniciada em 2,9 s atravessou a junção e chegou ao fim em 7 s, retornando ao estado pausado. Nenhum erro ou aviso foi capturado no console da aba de demonstração.
- HTTP local confirmou saúde dos servidores e entrega dos arquivos atualizados com Cache-Control: no-store nas portas 8765 e 8769. A interface entra após recarregar a página; não foi necessário reiniciar editor, gateway, conector ou túnel.
- Não houve alteração de backend/exportador: a suíte Python completa não foi repetida por esta mudança de interface. Nenhum projeto real, original, credencial ou sessão foi usado nos testes ou alterado. Sem chamadas de IA ou envio de mídia pessoal.

## Referências aplicadas e limites

A entrega usa F05–F08 e propostas P01/P03 do [estudo do CapCut Mobile](capcut-mobile-estudo-interface-funcoes.md), parcialmente. O conjunto P0 ainda não está concluído. O avanço por quadro e o contador digitável são decisões da Lili, não botões móveis atribuídos ao CapCut.

- **V01, navegação/pinça:** [Jefe Vilanova, trecho a partir de 03:23](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=203s), revisitado pela transcrição local do estudo. Inspiração para separar o gesto de navegação do aparo.
- **V02, escala/aparo:** [tutorial no iPhone a partir de 03:29](https://www.youtube.com/watch?v=o6tcF1JLlwo&t=209s), referência já indexada no estudo.
- **C16, aparo móvel:** [guia oficial, seção Using CapCut on the App (Android/iOS)](https://www.capcut.com/resource/free-video-edit). Revisita da seção móvel; outras seções não são evidência de interface no telefone.
- **Implementação web:** [MDN, seeked](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/seeked_event), [gestos de pinça com Pointer Events](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events/Pinch_zoom_gestures) e [touch-action](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/touch-action). Usadas para fila de busca, captura e cancelamento, mantendo a restrição do gesto à superfície apropriada.

**Safari e iPhone reais continuam pendentes**, incluindo pinça, teclado decimal, posição do painel com teclado aberto e desempenho com vídeos grandes. Os testes de ponteiros são simulações, não validação em aparelho. Não foi anunciada precisão de decodificação por quadro nativo/VFR nem ausência de latência em qualquer dispositivo.

## Ativação e próximo passo

Arquivos atualizados já são servidos pelo editor local; basta recarregar uma página aberta. Código, testes e documentação desta rodada seguem para o GitHub autorizado. Os estados de contas individuais, nuvem e correções anteriores do gateway permanecem conforme a esteira.

Próxima prioridade: transição real na junção de duas cenas, com duração e prévia visual, começando por dissolução e passagem por cor. Acompanhar com seletor visual e aplicação/cancelamento claros. Ímã temporal, pinça sobre todas as trilhas e reformulação completa das ferramentas contextuais continuam pendentes; não são entregas desta rodada.
