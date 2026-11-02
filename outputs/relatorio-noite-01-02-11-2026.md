# Relatório da Lili — noite de 01 para 02/11/2026

Concluídas **quatro rodadas de edição, uma de segurança e uma extra de visual/pesquisa**. Código publicado no GitHub e ativo no notebook, acumulado funcional até **cef630b**. Não foram editados projetos reais para testar as entregas.

## Recursos e correções

| Rodada | Entrega | Resultado prático |
| --- | --- | --- |
| 1 — áudio | Som no cursor e atalhos de fade | Adicionar áudio próprio ou som de um vídeo como bloco independente, sem substituir música/narração. Editar trecho, posição, volume e fades. Atalhos Sem fades, Curtos e Suaves respeitam o tamanho do trecho. Silenciar originais preserva sons avulsos. |
| 2 — controles de transição | Junções sem botões sobrepostos e navegação | Alvos maiores distribuídos conforme o zoom; marcadores e seletor dão acesso a todos os cortes. Anterior/Próximo, tempo do corte e duas miniaturas ajudam a escolher a junção. Proteções contra troca de projeto e salvamento concorrente. |
| 3 — transições | Varredura esquerda/direita e deslizar esquerda/direita | Quatro estilos de movimento renderizados localmente, com prévia, aplicação individual/em lote e histórico. Preservam o relógio total da montagem e o som; não exigem serviços pagos nem código do Concat. |
| 4 — exportação | Nomes identificáveis e recuperação de saídas indisponíveis | Download usa nome do projeto, revisão, qualidade/resolução e identificador curto. Histórico detecta arquivo ausente, vazio ou com tamanho alterado e permite preparar nova exportação da montagem atual. Prévia revalida o arquivo e orienta em caso de falha. |
| 5 — segurança | Pedidos completos e JSON sem ambiguidades | Recusa corpo incompleto, campos duplicados, números não finitos e Unicode inválido; controla timeout de leitura JSON e overflow. Revisados testes de acesso/identidade/cookies existentes. |
| Extra — inicial/mercado | Quatro atalhos com escolha de projeto | Abrir arquivos, transições, legendas e entrega diretamente da inicial. São atalhos às ferramentas existentes, sem aplicar edição ou iniciar exportação automaticamente. Pesquisa de ofertas oficiais registrada. |

O som usa os arquivos importados pelo usuário; não foi criada uma biblioteca licenciada de efeitos sonoros. A checagem de exportação confirma presença e tamanho, não checksum nem decodificação integral. Preparar nova exportação não restaura automaticamente uma revisão antiga.

## Segurança: o erro que foi encontrado

Um teste isolado comprovou que a API anterior podia criar um projeto ao receber JSON válido menor que o tamanho declarado no pedido. A correção exige receber o corpo completo antes de interpretar e executar. Regressões diretas e via gateway verificaram a rejeição sem criar projeto. Isso foi uma falha de integridade da requisição, não uma demonstração de entrada sem senha. Uploads binários mantêm seus próprios tempos de envio.

Contas individuais reais continuam pendentes. Esta rodada não ativou isolamento entre usuários, não escolheu donos para projetos antigos e não alterou credenciais/sessões reais. A revisão não equivale a uma auditoria independente de todo o sistema.

## Testes e ativação

- Última suíte Python completa: **182 testes aprovados**. Verificação JavaScript final: **25 arquivos de testes aprovados**. Testes focados e repetições não foram somados como novos.
- Exportações e prévias sintéticas verificaram direção/movimento das quatro transições, quadros intermediários, duração, áudio e saída 1920 × 1080. Sons/fades, compatibilidade de histórico legado, downloads com Range/HEAD e falhas de arquivos também foram cobertos.
- Antes da ativação: zero jobs em fila/execução, zero mídias processando e zero uploads parciais. Reiniciado somente o editor, com identidade de processo conferida.
- Depois: saúde local aprovada e capacidades library_sounds, spatial_transitions e export_delivery ativas; inicial e scripts HTTP 200. Acesso sem login via gateway continuou bloqueado com 401, e o endereço remoto existente respondeu saudável.
- Gateway, conector e túnel mantidos em seus processos; nenhuma revogação de sessão foi executada. Não foi feito login real para testar a continuidade de uma sessão humana.
- Revisão visual desktop e Safari real **pendentes**. A tentativa de controle desktop falhou na inicialização do runtime, antes de controlar uma janela; testes automatizados não são validação visual em aparelho.

Uma frente paralela passou a alterar arquivos de legendas após a ativação e as verificações acima. Essas alterações ainda não versionadas não fazem parte das entregas/testes deste ciclo e foram preservadas, sem publicação ou reinício adicional por esta rodada. O frontend serve arquivos do diretório de trabalho; portanto, a checagem HTTP registrada corresponde ao instante de ativação, não à validação dessas alterações posteriores.

## Pesquisa e direção do produto

Consultadas ofertas oficiais de Clipchamp, CapCut e DaVinci Resolve para comparar recursos gratuitos e cobranças anunciadas. Isso não comprova receita, lucro ou demanda. Hipótese futura: manter edição local útil e avaliar cobrança por fluxos de trabalho/serviços opcionais. Nenhum plano, preço, assinatura ou serviço pago foi criado. Fontes e análise: [extra de visual e mercado](rodada-noturna-2026-11-01-extra-atalhos-mercado.md).

A Lili segue com código próprio e objetivo de código fechado. Não foi incorporado código AGPL do Concat nem ativado seu motor; separação por API/MCP não foi tratada como isenção de licença. [Análise do Concat](integracao-concat.md). Rust/wgpu, transcrição local, remoção de fundo e backup em nuvem permanecem propostas, com licenças, desempenho e autorização a validar: [arquitetura local](arquitetura-local-e-automacao-02-11-2026.md).

## Como revisar

1. Recarregue a inicial e escolha um projeto nos quatro atalhos; confirme que cada um abre a ferramenta esperada.
2. Em um projeto de teste, importe som e use **Som no cursor**. Abra o bloco e experimente os atalhos de fade.
3. Abra Transições, navegue entre junções e compare os quatro novos estilos pela prévia renderizada e pela exportação.
4. Exporte e confira o nome do download e os dados da entrega. Não é necessário apagar arquivos reais para testar a recuperação.

Próximos passos: revisão humana do visual/Safari e da suavidade percebida nas mídias reais; ajustar o que essa revisão identificar. Contas individuais/portal, backup em nuvem e motor de IA local são frentes separadas ainda pendentes. Não há continuação automática pela manhã/tarde; futuras rodadas seguem apenas nas noites autorizadas.

Relatórios completos por etapa: [áudio](rodada-noturna-2026-11-01-01-sons.md), [controles](rodada-noturna-2026-11-01-02-transicoes.md), [movimento](rodada-noturna-2026-11-01-03-movimento.md), [entrega](rodada-noturna-2026-11-01-04-entrega.md), [segurança](rodada-noturna-2026-11-01-05-seguranca.md), [extra](rodada-noturna-2026-11-01-extra-atalhos-mercado.md).
