# Rodada 1 — revisão e envio da exportação · noite de 31/10 para 01/11/2026

## O que mudou

A tela de exportação passa a apontar problemas concretos antes da entrega: fala que ultrapassa o vídeo, narração/música começando depois do fim, fade da música terminando fora da montagem, legendas fora da duração e ausência de áudio audível pelos metadados. Cada aviso tem um atalho ao ajuste correspondente. Avisos permitem gerar mesmo assim; montagem vazia e mídias usadas indisponíveis impedem o envio pela interface.

O servidor também verifica as fontes usadas por vídeo, narração e música antes de criar um job: exige mídia pronta/ativa e arquivo original existente, além da imagem preparada no caso de fotos. Recusa HTTP 409 sem ocupar a fila, alterar a montagem ou criar uma exportação já condenada a falhar. Mídia removida, inclusive ausente do JSON público, recebe a mesma orientação de revisão.

Corrigido o envio repetido por cliques enquanto o primeiro pedido aguarda a fila de salvamento ou a rede. O pedido mantém projeto/qualidade selecionados e usa a revisão já salva após a fila. Trocar de projeto antes do envio cancela aquela intenção, evitando exportar o projeto errado. Resposta atrasada da fila de um projeto não aparece em outro.

Se o pedido foi enviado mas a consulta da fila falha, a interface explica que ele pode ter sido recebido e mantém a nova tentativa bloqueada até conseguir consultar o estado. Não repete POST automaticamente. O servidor continua sendo a autoridade sobre revisão e exclusividade da exportação.

## Verificação

- **18 arquivos JavaScript passaram**, incluindo teste novo dos manipuladores reais de envio com rede/fila simuladas. Casos: áudio cortado, legenda fora do vídeo, silêncio, mídia indisponível, atalhos de revisão, clique duplicado, qualidade capturada, revisão após salvamento, troca de projeto, resposta incerta e fila atrasada. Não se contam repetições como testes novos.
- **Suíte final completa: 137 testes Python aprovados**, incluindo um novo teste HTTP que recusa mídia em processamento/com erro/removida e arquivo ausente antes de criar jobs. A suíte foi justificada pela mudança no caminho compartilhado de exportação. Também cobriu fotos, voz, música, legendas, transições e perfis; renderizações usaram mídias sintéticas. Os três testes focados de perfis executados antes estão incluídos no total, não são somados a ele.
- A primeira execução completa revelou um problema na asserção nova: o cliente converte HTTPError em ValueError. O teste passou a exercitar o HTTP diretamente; isso também expôs o caso de mídia removida ausente do JSON, agora tratado explicitamente. Houve ainda uma divergência de amplitude e um timeout de importação em dois testes existentes; ambos passaram isoladamente e na execução completa final, sem alteração nesses testes ou no processamento de áudio. A causa dessas duas falhas pontuais não foi determinada; acompanhar estabilidade.
- Sintaxe, diff e IDs únicos no HTML conferidos. Editor real 8765 respondeu saudável e entregou o novo JavaScript sem cache. Nenhuma mídia pessoal, conta, sessão ou chamada real de IA foi usada para testes.

## Ativo e preparado

**Frontend servido pelo editor real**, disponível ao recarregar a página. **Checagem de arquivos no backend preparada**, aguardando início seguro do processo no fechamento do ciclo. Nenhum serviço, gateway, conector ou túnel foi reiniciado nesta rodada.

O checkout começou com quatro commits locais ainda não sincronizados. Esta entrega conserva esses checkpoints; publicação acumulada fica para o encerramento da extra, ou após segurança se não houver extra. Não anunciar que o GitHub já recebeu essas mudanças.

## Pendências e limites

A revisão visual anterior de legendas foi retomada como pendência, mas não concluída: nesta execução não há controle do navegador integrado exposto. Não houve inspeção visual desktop, validação de viewport ou Safari real; os testes JavaScript executam funções em ambiente simulado. Os ajustes visuais desta tela também precisam de revisão no navegador.

A verificação da interface usa metadados, não analisa se o arquivo contém silêncio real. A checagem de existência no servidor é preventiva, não reserva nem bloqueia os arquivos contra alterações externas depois dela. Não verifica espaço livre para a saída, cor HDR/SDR, direitos de músicas nem legibilidade visual. Falha de rede em POST não prova se o servidor recebeu a solicitação; a fila é consultada antes de liberar outra tentativa. Sem idempotência persistente entre recargas da página. Não foram criados novos formatos/codecs/fps nesta entrega.

Próxima rodada, 00h55: retomar a revisão visual quando houver ferramenta disponível e avançar os controles de montagem (encaixe/precisão e manipulação de faixas) conforme lacuna real. Na segurança/fechamento, verificar jobs/envios e identidade do processo antes de ativar o backend; preservar sessões do gateway e publicar os checkpoints acumulados.
