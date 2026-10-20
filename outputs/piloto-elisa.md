# Piloto de edição assistida para a Elisa

Proposta atualizada com os formatos, destinos e preferências informados pelo usuário. As regras de estilo ainda dependem da análise de vídeos e da validação da Elisa.

Uma primeira versão local já foi construída e os nove arquivos originais do passeio foram recebidos. O Codex preparou e exportou uma montagem visual editável com esse material. Ver [estado da versão 0.1](versao-0.1.md). As etapas seguintes deste documento distinguem a direção prevista do que já foi entregue.

## Contexto confirmado

- Formatos: vlogs, rotinas, bastidores, conteúdo lowfi, reviews promocionais, propaganda, ensaios publicitários, depoimentos e trends.
- Durações: curtos de 15 a 30 segundos; médios de 1 minuto e 30 segundos a 3 minutos; ocasionais de 4 a 5 minutos.
- Destino principal: Instagram; secundário: TikTok.
- Captura e edição atuais: iPhone 15 Pro Max e CapCut.
- Preferência de revisão: avaliar tanto pedidos por mensagem quanto ajustes manuais no CapCut.
- Processo informado: roteiro → gravação → montagem visual → gravação da narração → união do vídeo com a voz. O roteiro do passeio na Catedral já foi recebido e está em [Roteiro e plano de montagem](roteiro-cora-catedral.md).
- Direção proposta após a referência externa: permitir IA e ajustes manuais no mesmo projeto, com revisão no iPhone; o CapCut permanece como alternativa a comparar. Ver [Direção de produto](direcao-produto.md).
- Referências fornecidas: @elisabottelhoat, @elisabottelho e @cora.agatinha. O usuário informa que a Elisa gravou e editou os vídeos desses perfis. Isso não significa que todos os trabalhos tenham as mesmas regras de edição.

Na consulta inicial, foi possível abrir a página pública de @elisabottelhoat, mas a tentativa de abrir um Reel exigiu login. Depois, o usuário forneceu dois arquivos finalizados locais: IMG_7019_vlog cora 2.MOV e IMG_6447_vlog cora.MOV. Suas imagens, metadados e transcrições automáticas foram analisados localmente. Os resultados estão em [Análise das referências](analise-referencias-elisa.md), com um [perfil descritivo inicial](perfil-vlog-elisa.v0.1.json) sujeito à aprovação da Elisa. Não inferir o estilo a partir da página do perfil.

## Perfis de edição propostos

Estes grupos organizam os testes; não descrevem conclusões sobre o estilo real da Elisa.

| Grupo | O que o piloto deve avaliar |
| --- | --- |
| Vlogs, rotina, bastidores e lowfi | Preservação de espontaneidade, pausas intencionais, som ambiente e continuidade; cortes automáticos não devem eliminar toda hesitação |
| Reviews, promocionais falados e depoimentos | Sentido das falas, seleção de tomadas, demonstração do produto, legendas e requisitos do briefing |
| Campanhas, ensaios e trends | Ordem de planos, relação com música, sincronismo e efeitos específicos; começar após validar o fluxo básico |

Manter um perfil geral da Elisa com variações por formato e cliente. A proporção do quadro, a duração e as áreas reservadas para texto devem ser confirmadas por trabalho; não presumir que todo material seja vertical ou aceite o mesmo corte nas duas plataformas.

## Resultado esperado

A Elisa grava no iPhone, recebe uma primeira edição e revisa pelo celular. O sistema deve reduzir o tempo de trabalho manual e preservar as escolhas criativas que ela aprovar. A qualidade e a economia de tempo ainda precisam ser medidas em vídeos reais.

## Fluxo proposto

1. Enviar os arquivos originais e um briefing: objetivo, público, duração desejada, falas obrigatórias, referências e restrições do cliente.
2. O computador recebe os arquivos e mantém os originais intactos.
3. A análise relaciona roteiro e imagens dos brutos para propor a seleção e a sequência de cenas. A transcrição entra quando houver fala disponível, sem substituir a análise visual.
4. O Codex aplica um plano de edição no Concat e preserva versões relevantes do projeto.
5. O sistema gera uma prévia leve da montagem visual para revisão no iPhone.
6. A Elisa pede ajustes e grava a narração. O sistema propõe ajustes de duração para acomodar a voz sem perder as escolhas já aprovadas.
7. Aplicar texto, música e acabamento aprovados. Pedidos por mensagem e os futuros controles manuais devem atuar no mesmo projeto. A entrega final depende da aprovação da Elisa.

O acesso pelo celular e a transferência de arquivos ainda precisam ser implementados e testados. A existência de conversas sincronizadas não demonstra que este computador já possa ser comandado pelo telefone. Para o piloto, o computador executa a edição; ela pode revisar as prévias pelo celular, com você conduzindo o Codex enquanto validamos o processo.

## Preservação do estilo

Começar com três a cinco vídeos finalizados que a Elisa considere representativos. De preferência, obter também os brutos de um deles.

Criar um perfil explícito e revisável, sem treinar um modelo no primeiro piloto:

- Ritmo, pausas intencionais, cortes e escolha de tomadas.
- Fontes, cores, posição, animação e quantidade de texto.
- Enquadramento, aproximações, transições e efeitos recorrentes.
- Cor, exposição e aparência de pele.
- Música, relação entre voz e trilha e uso de som ambiente.
- Abertura, encerramento e exigências por cliente ou tipo de trabalho.

Separar hábitos recorrentes de escolhas específicas de cada vídeo. As regras precisam de aprovação da Elisa e devem registrar as correções dela; alterações futuras não devem modificar trabalhos anteriores.

## Verificação técnica realizada

O código público foi baixado para a pasta de trabalho e comparado com a tag v0.2.7.

- A documentação e o código da branch principal incluem o servidor MCP embutido e o argumento `concat --mcp`.
- O código da tag v0.2.7 consultada não contém esse argumento nem o crate `concat-mcp`. Não assumir que o instalador dessa versão ofereça a integração MCP descrita na documentação atual.
- A primeira decisão de implementação é testar a API JSON-RPC da versão publicada ou preparar uma compilação fixada em um commit com MCP. Nenhuma das integrações foi executada nesta sessão.
- Não foi confirmada uma exportação de projeto do Concat que continue totalmente editável no CapCut do iPhone.
- Um MP4 finalizado permite novos cortes e sobreposições, mas não preserva as faixas e os elementos independentes da edição original.
- Ainda não foram testados decodificação, cor, orientação, áudio e exportação com os arquivos reais do iPhone da Elisa. Testar especialmente HDR caso ela grave nesse formato.

Referência do código consultado: `79116bd0f9a103c633d888603ad27890e929dbdc`.

## Duas formas de revisão a avaliar

| Forma | Benefício | Ponto a validar |
| --- | --- | --- |
| Prévia e pedidos de ajuste | Mantém a Elisa no celular e permite refazer a edição a partir do projeto | Clareza dos pedidos, tempo de resposta e necessidade de controles manuais |
| Finalização no CapCut | Aproveita a ferramenta que ela já conhece | Intercâmbio de projeto não confirmado; revisar apenas o MP4 limita alterações |

Para a opção CapCut, testar inicialmente uma montagem base sem legendas gravadas na imagem e sem trilha misturada, caso ela prefira finalizar esses elementos manualmente. Isso preserva mais liberdade para sobreposições, mas continua sendo um vídeo renderizado, sem recuperar os clipes originais e suas margens em uma timeline independente. Uma exportação com clipes e faixas editáveis exige validação própria.

Comparar os dois caminhos com o mesmo trabalho. Registrar quais correções exigiram a timeline e quais foram resolvidas com um pedido simples. Se a maior parte dos ajustes for texto, música e encerramento, avaliar um fluxo híbrido; se envolver troca e duração de cenas, medir o custo das novas versões geradas pelo Codex.

Uma interface móvel própria pode oferecer prévia, comentários por tempo e aprovação. Ela deve vir depois da validação da edição com material real. Não é necessário reproduzir uma timeline completa para testar o valor do serviço.

## Primeiro teste

Usar um trabalho que já tenha sido entregue e seus arquivos originais. Gerar uma edição sem copiar manualmente cada corte do resultado final. A Elisa compara as versões e aponta onde o sistema acertou ou perdeu sua intenção.

Proposta de sequência:

1. Review ou depoimento falado: escolher um exemplar curto, com briefing e brutos disponíveis, para testar sentido, cortes, legendas e áudio.
2. Rotina, vlog ou bastidor: testar seleção de cenas e preservação da naturalidade.
3. Publicidade ou trend: testar sincronismo e acabamento mais específico.

Para começar, basta obter os arquivos completos do primeiro trabalho. As demais referências podem ser acrescentadas progressivamente. Os links dos perfis ficam como catálogo; a análise de edição precisa de vídeos que possam ser reproduzidos integralmente com áudio.

Registrar:

- Tempo total de trabalho ativo da Elisa, incluindo transferência, revisão e correções.
- Tempo de processamento, separadamente.
- Quantidade e natureza dos ajustes solicitados.
- Aprovação de ritmo, texto, som, imagem e atendimento ao briefing.
- Custo por vídeo e estabilidade da execução.

Definir a meta de economia de tempo depois de medir o processo atual. Não prometer uma porcentagem de automação antes do teste.

## Caminho para produto

Validar primeiro com a Elisa; repetir em trabalhos diferentes; só então adicionar acesso remoto estável, fila de trabalhos, autenticação, armazenamento por cliente e cobrança. Escolher o Concat como motor depende dos resultados dos testes.

Antes de comercializar, avaliar as obrigações da licença AGPL do Concat, os termos das integrações de IA e os direitos dos materiais utilizados. A assinatura atual do usuário não deve ser tratada como infraestrutura comercial já disponível para outros clientes.

## Próximos insumos

1. Revisão da primeira montagem visual feita com os nove originais já recebidos do passeio na Catedral.
2. Briefing desse trabalho e estimativa do tempo que ela levou para editar.
3. O que a Elisa considera especialmente bem resolvido nesse vídeo e quais ajustes ela faz com mais frequência. A ordem entre roteiro, montagem e voz já foi informada.
4. Narração separada para ajustar a montagem final. Progressivamente, outras referências até cobrir os grupos de conteúdo. A preferência final de revisão será decidida depois da comparação dos dois caminhos.

## Fontes

- Repositório: https://github.com/jub0t/Concat
- MCP na branch principal: https://github.com/jub0t/Concat/blob/main/docs/MCP.md
- Versão publicada consultada: https://github.com/jub0t/Concat/releases/tag/v0.2.7
- Código de lançamento da versão publicada: https://github.com/jub0t/Concat/blob/v0.2.7/src/crates/concat/src/launch.rs
- Licença: https://github.com/jub0t/Concat/blob/main/LICENSE
- Perfis informados pelo usuário: https://www.instagram.com/elisabottelhoat/ ; https://www.instagram.com/elisabottelho/ ; https://www.instagram.com/cora.agatinha/
