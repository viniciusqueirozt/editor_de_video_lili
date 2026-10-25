# Rodada 3 — áudio no tempo certo · noite de 24 para 25/10/2026

## O que mudou para editar

- Tocar na faixa de música ou narração abre um painel próprio. Também há o atalho **Ajustar tempo e ouvir prévia** nos ajustes de cada áudio.
- O início pode ser digitado em segundos ou minutos:segundos, deslocado um quadro de cada vez ou alinhado ao cursor. O cursor tem navegação por slider, instante digitável e passo de quadro da montagem a 30 fps.
- Música pode ser aparada no cursor ou por entrada/saída digitadas. Ao aparar o início, a entrada no arquivo e a posição na montagem avançam juntas: o trecho restante permanece sincronizado. Aparar o fim preserva a entrada.
- Forma de onda tanto na música quanto na voz. O painel mostra o arquivo completo, o trecho utilizado e a posição correspondente ao cursor. A faixa da timeline representa somente os dados do trecho visível, inclusive quando a música começa no meio do arquivo.
- Volume, entrada/saída suaves e redução da música durante a voz ficam agrupados em uma seção de mixagem. Ouvir do cursor usa os ajustes provisórios na mistura; Aplicar grava um único comando, recuperável com Desfazer/Refazer. Cancelar descarta os ajustes e restaura a posição anterior.
- A interface explica quando o áudio começa após o vídeo ou ultrapassa seu fim. Um aparo que não comporta os fades fica indisponível; valores digitados inválidos impedem salvar e mostram o motivo. Uma revisão antiga não encobre o estado atualizado nem permite aplicar silenciosamente.
- Regiões de áudio têm área de toque de 44 px e faixas de 50 px. Corrigido o dimensionamento móvel para acomodar as duas faixas sem cortar os botões do rodapé.

## Referência utilizada

Reaproveitado o estudo já salvo de CapCut no celular, especialmente F39/F40 e [aula V01, 30:02–30:35](https://www.youtube.com/watch?v=dmVeTHBQxEc&t=1802s), sobre leitura de picos e alinhamento do som. Não houve nova busca repetida nem reprodução dos algoritmos proprietários. O desenho da Lili usa um painel de ajustes explícitos e as operações locais existentes.

## Verificação

- **16 arquivos de testes JavaScript passaram**, incluindo um novo que executa os manipuladores reais do painel, a mistura de prévia e os comandos com projeto/reprodução simulados. Cobertura de tempo digitado, passo de quadro, música aparada sem perder sincronismo, redução durante a voz, limites/fades, valores inválidos, revisão antiga, Cancelar, salvamento único e falha de gravação. Repetições durante o ajuste não contam como testes novos.
- **Quatro testes Python focados existentes passaram**: validação/histórico de música e narração, exportação de música com aparo/deslocamento/redução e narração com fades/deslocamento. As saídas sintéticas são decodificadas para medir duração e amplitude. Não foi acrescentado teste Python nesta rodada nem repetida a suíte completa: o backend não mudou.
- No navegador desktop, projeto isolado da porta 8770: música começava em 0,5 s, com entrada no arquivo em 1 s. Aparar início no cursor de 1,5 s resultou em entrada de 2 s e posição de 1,5 s; o fim permaneceu em 4 s. Aplicar, Desfazer e Refazer levaram a revisão 19 → 20 → 21 → 22. Narração, duração de 4 s e passagem por branco preservadas.
- Reprodução percorreu a montagem até o fim; experiência na narração foi cancelada sem gravação. Formas de onda carregadas e nenhum aviso/erro de console na revisão. Layouts de 320 × 740 e 390 × 844 conferidos: sem largura excedente, ações fixas do painel alcançáveis e rodapé inteiro. **Não é teste no Safari real**.
- Sintaxe e diff conferidos. Somente cores/tons gerados localmente, sem IA real, mídias pessoais ou alteração de projetos reais.

## Ativação e publicação

Frontend disponível após recarregar a página: os comandos narration_set/music_set e a API de forma de onda já existem no editor real. Conferidos /api/health (music_track e scene_audio_fades), HTML e scripts servidos sem cache na porta 8765. Nenhum serviço foi reiniciado; sessões, gateway, conector e túnel foram preservados.

Este é o checkpoint local da terceira rodada. Sincronização GitHub e fechamento da ativação do ciclo permanecem para o fim da extra, ou após a segurança se não houver extra. As transições da rodada 1 continuam aguardando ativação do backend; não confundir a disponibilidade deste painel com a ativação delas.

## Limites e próximo passo

Uma narração e uma música por projeto. A narração continua usando o arquivo inteiro, sem aparo/split neste painel. Ainda não há arraste temporal da faixa, ímã, marcadores de batida, crossfade sonoro entre clipes ou múltiplos efeitos sonoros simultâneos. A forma de onda é normalizada por arquivo: serve para localizar conteúdo, não mede volume absoluto entre arquivos. A prévia do navegador limita a voz a 100%; quando escolhido ganho maior, o painel explicita que a amplificação ocorre na exportação. O fim da montagem corta o áudio; não cria automaticamente um fade no ponto do corte.

Próxima rodada de edição: avaliar o fluxo de legendas e seus tempos/estilos, usando a mesma lógica de experiência, comparação e aplicação reversível onde houver lacuna real. Segurança/contas ficam na quinta rodada; nuvem e associação de donos permanecem dependentes das decisões já registradas.
