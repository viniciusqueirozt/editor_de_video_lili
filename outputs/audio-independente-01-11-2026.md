# Som original separado da imagem — 01/11/2026

## Para usar

1. Atualize a página do editor depois da ativação desta entrega.
2. Adicione à sequência um vídeo pronto que contenha áudio: a imagem entra na trilha de vídeo e o som aparece na faixa **Som original**, alinhado ao trecho e à velocidade escolhidos.
3. Toque no bloco de som para abrir o painel. Ajuste entrada/saída da fonte, início na montagem, volume, fades e velocidade própria. Aplicar salva; Cancelar descarta o rascunho.
4. Use a alça ↔ para mover só o som; o ímã opcional também considera suas extremidades. No painel, Dividir no cursor, Duplicar e Remover atuam só no áudio. Cada ação pode ser desfeita/refeita.
5. Corte, mova, acelere ou remova a imagem sem reescrever o som já separado. As posições do áudio são absolutas; não há deslocamento automático ao cortar/reordenar imagem. Revise o sincronismo quando mudar a sequência.

## Projetos existentes

Abrir um projeto antigo não altera seus arquivos nem força uma migração. O som ainda ligado à imagem aparece em bloco tracejado; ao aplicar o primeiro ajuste, mover ou executar uma ação, a separação e a ação são salvas juntas em um passo de histórico. O botão Aplicar também permite separar sem alterar os valores. Cena protegida precisa ser desprotegida antes dessa conversão. Desfazer restaura a ligação anterior.

A inserção pela interface solicita separação automática; a API de comandos mantém comportamento legado para integrações que não enviam separate_audio=true. A primeira montagem assistida e o rascunho da interface também separam os sons novos. Se já existem blocos independentes, uma substituição visual assistida conserva esses sons em suas posições e evita introduzir outra cópia automaticamente. O atalho local de silenciar originais alcança áudios independentes sem mexer nos protegidos, na narração ou na música.

## Comportamento e proteção

- Separação usa referências aos arquivos existentes, sem duplicar WAVs ou modificar originais. A imagem deixa de reproduzir o som embutido para evitar duplicação.
- Volume/fades/velocidade do áudio são próprios. Fades sonoros transferidos ao bloco não impõem mais duração mínima ao aparo da imagem.
- Sobreposições de sons são apresentadas em linhas separadas dentro da faixa, com rolagem vertical limitada. Há seletor de blocos no painel, inclusive para sons fora da duração visível.
- Proteção individual impede mover, aparar, duplicar ou remover som sem desproteger. A primeira separação também respeita proteção da cena legada.
- Excluir só o bloco mantém a imagem silenciosa. É possível readicionar o som pelo botão nos ajustes da cena; duplicar uma imagem separada não duplica seu áudio.
- Ao remover um arquivo da biblioteca, o sistema considera seu uso por áudio mesmo quando a imagem já saiu da sequência. Exige confirmar remoção dos usos; áudio/cena protegidos bloqueiam a exclusão. Desfazer restaura o estado.
- Comandos validam revisão, IDs, fonte, limites, fades e velocidade; falhas não gravam uma alteração parcial. Rascunhos e arrastes verificam projeto/revisão antes de salvar.
- A prévia rápida permite ouvir ajustes locais. A reprodução da montagem com áudio independente usa prévia renderizada, que compartilha a mixagem da exportação; a primeira geração pode demorar. Versões salvas são reutilizadas por revisão.
- Avisos de exportação incluem sons que passam do fim do vídeo e referências indisponíveis. O arquivo final termina na duração da montagem visual; som excedente não aumenta o vídeo.
- Limites desta versão: até 200 blocos independentes, velocidade 0,25–4× e montagem de até 30 minutos. Não há vínculo automático posterior/ripple, agrupamento imagem-som nem atalhos para relincar todos os blocos.

## Correção adicional de estabilidade

Na primeira suíte completa ocorreu PermissionError ao substituir jobs.json no Windows. A gravação agora tenta novamente apenas falhas transitórias de permissão, com quatro esperas curtas e no máximo cinco tentativas; uma negação persistente continua sendo erro. Não se afirma qual processo causou o bloqueio observado. Testes simulam o conflito transitório e permanente e verificam preservação do arquivo anterior. A suíte seguinte passou.

## Verificação

- Suíte completa: 166 testes Python passaram. Depois da revisão, um teste de regressão adicional confirmou que fades do som separado não bloqueiam cortes curtos da imagem; passaram os oito testes focados de áudio e a integração foi repetida após essa correção. Total: 167 casos Python distintos verificados, sem somar repetições.
- Passaram 22 arquivos JavaScript; os testes novos exercitam handlers reais com DOM/players simulados: faixa/linhas, conversão legada, aplicação/cancelamento, volume, velocidade, aparo, arraste, revisão, bloqueios, falha de rede, espera por metadados, liberação de players e atalho dos avisos de exportação.
- Exportação sintética com vídeo/tom de teste decodificada para medir silêncio, início, fim e nível: sem som embutido duplicado; mover/dividir/duplicar/remover som conserva imagem e bytes originais. IA e identidades simuladas; nenhuma chamada de IA real nem mídia pessoal usada.
- Testes do bridge Concat são de protocolo simulado e ausência de motor, não de efeitos nativos ativos. Relatório separado: integracao-concat.md.
- Não houve validação visual desktop nem Safari real nesta entrega; o runtime de controle desktop estava indisponível na tentativa anterior. Testes de DOM não substituem essa revisão no aparelho.

## Ativação

Ativada com o código c65709d após conferir zero jobs pendentes, uploads parciais ou mídias em processamento. Reiniciado exclusivamente o editor 8765; gateway 8767, conector e túnel mantidos. Saúde/capacidade source_audio_clips, HTML/script novos e bloqueio de acesso não autenticado a projetos pelo gateway verificados. Página de login no mesmo túnel externo respondeu saudável. Concat segue ausente e editing_ready=false, conforme o estado real. Não foram editados projetos reais para testar.
