# Concat como complemento da Lili — 01/11/2026

## Estado real desta entrega

Foi estudada uma cópia de referência do Concat, commit `f0c0169628c61de7311f7fc15ee5be82dd611d2e` (workspace declara 0.2.8). A cópia permanece ignorada pelo Git em work/inspiration/Concat-reference. Nenhum código, logotipo, instalador, modelo de IA ou arquivo pessoal foi incorporado a partir dela.

A Lili continua renderizando com FFmpeg. O Concat é um aplicativo nativo Rust/Slint com bibliotecas próprias; não é um componente JavaScript que possa ser colocado diretamente no navegador. A implementação entregue prepara descoberta pelo protocolo público MCP, sem anunciar efeitos disponíveis antes de executá-los. O motor Concat não está instalado nos caminhos conhecidos do notebook; não foi compilado nem executado nesta entrega. Rust e as bibliotecas de desenvolvimento necessárias também não estão prontos no ambiente consultado.

## Implementado e verificável

- lili/concat_bridge.py: identifica instalação conhecida ou caminho absoluto LILI_CONCAT definido pelo responsável no notebook; não pesquisa um executável genérico chamado concat no PATH.
- GET /api/concat/status: informa instalação, protocolo, commit de referência e editing_ready=false.
- POST /api/concat/inspect: inicialização MCP, listagem paginada das ferramentas anunciadas, consulta concat_version e effects_list quando disponíveis. Corpo do navegador não escolhe métodos/comandos.
- Processo próprio, headless, diretório isolado work/concat-engine, ambiente reduzido, CONCAT_MCP_ROOTS restrito para escritas pelo motor (não é sandbox do sistema operacional), prazo de resposta, limites de mensagem/paginação e encerramento do processo. A consulta é recusada enquanto há jobs pendentes; não abre projetos reais, não importa mídias, não salva montagem, não exporta e não toca no processo gráfico do Concat.
- Ausência do motor é uma resposta normal. Erros de inicialização/protocolo são tratados sem mostrar caminhos internos ao cliente. Recursos de edição do Concat continuam indisponíveis até integração e testes reais.
- Separação independente de som/imagem entregue na própria Lili, com implementação original e exportação FFmpeg; não é chamada ao Concat. Detalhes no relatório de áudio desta data.

## Inventário para complementar a base existente

As capacidades da coluna Concat foram identificadas em documentação/tipos/código; não foram validadas executando seu aplicativo. Disponibilidade via MCP varia: localizar código na aplicação não garante uma ferramenta pronta no servidor MCP.

| Área | Base atual da Lili | Complemento encontrado no Concat e trabalho necessário | Referências |
| --- | --- | --- | --- |
| Cortes e histórico | Dividir, aparar, duplicar, reordenar e Desfazer/Refazer | Comandos em lote, ripple, merge e congelamento; mapear sem alterar sincronismo por surpresa | C02, C03 |
| Trilhas | Sequência visual, som original independente, narração e música | Composição com várias camadas, overlays, picture-in-picture e várias timelines; exige modelo/controles além do motor | C01, C03 |
| Som original | Blocos independentes: posição, trecho, velocidade, fades e proteção | Comparar modelo de áudio e comandos para futura tradução de projetos | C03 |
| Efeitos e aparências | Presets e ajustes RGB da cena inteira | Catálogo por pacote, parâmetros e intensidade; não presumir IDs nem disponibilidade por GPU | C04 |
| Transições | Dissolução e passagem por preto/branco com prévia renderizada | Outras transições do catálogo; traduzir duração/overlap para preservar voz, legendas e último quadro | C04, C05 |
| Animação | Ajustes constantes por cena | Keyframes, interpolação e curvas para transformação, opacidade, volume e parâmetros | C02, C03 |
| Cor | Brilho, contraste, saturação e presets reversíveis | LUTs e pacotes de cor; prévia e exportação devem usar os mesmos valores | C04 |
| Títulos | Texto, posição e estilo básico | Estilo por palavra, presets e camadas; verificar fontes e layout no render | C02, C06 |
| Legendas | Edição manual/SRT, tempos, estilos, prévia e exportação | Transcrição Whisper local e colocação de legendas; modelos dependem de instalação/licença própria | C02, C07 |
| Voz sintética | Não criada automaticamente; narração da Elisa preservada | TTS local e clonagem existem no módulo de fala; uso/clonagem somente quando solicitado, sem ativar por padrão | C07 |
| Limpeza de áudio | Mix, volume, fades, limiter e redução musical | Denoise/enhancement, normalização e efeitos de voz; conferir comando exposto, modelos e latência | C01, C03, C07 |
| Máscaras e fundo | Enquadramento/espelhamento e composição básica | Segmentação, pincel, máscaras e remoção de fundo; requer modelos e desempenho verificado | C02, C08 |
| Estabilização | Sem estabilização dedicada | clip_stabilize documentado; validar crop, recursos e efeitos no tempo | C02 |
| Velocidade | Velocidade constante e áudio ajustável separadamente | Curvas, propriedades animadas e comportamento de freeze; preservar limites da fonte | C03, C05 |
| Exportação | Perfis locais FFmpeg e checagem de fontes | API de exportação com progresso/cancelamento; codecs/resoluções dependem do build e hardware, não só da opção mostrada | C02, C09 |
| Templates | Roteiro e montagem assistida | Listagem/instanciação de templates; tradução precisa de modelo de projeto e direitos dos materiais | C02 |
| Automação | Chat contextual, atalhos locais, comandos e revisões | MCP/JSON-RPC do Concat, schemas anunciados e edit_apply; não permitir execução arbitrária vinda do navegador ou do modelo | C02, C10 |
| GPU e prévia | Renderização FFmpeg e prévia de montagem | Compositor GPU e frame composto; verificar no notebook e manter fallback funcional | C05, C09 |
| Conta, celular e portal | Interface web, gateway e portal existentes | A interface nativa do Concat não substitui login, sessões, permissões e UI móvel da Lili | C02, C11 |

## Como transformar a preparação em integração real

1. Definir a forma de reutilização/licença antes de copiar ou distribuir código do Concat dentro da Lili. Em 02/11/2026, o usuário escolheu expressamente **definir a licença antes de copiar código**. Não houve autorização para relicenciar a Lili ou torná-la código aberto. Até essa definição, continuar implementações próprias e análise técnica sem incorporar código do Concat.
2. Disponibilizar build oficial compatível e registrar versão/checksum; testar descoberta real, dependências e ferramentas disponíveis em projeto sintético. Não baixar todos os modelos por padrão.
3. Criar adaptador Lili → projeto Concat em pasta de trabalho: IDs, fontes, fontes tipográficas, enquadramento, posições, velocidade, áudio, legendas, fades, junções e locks. Rejeitar mapeamento incompleto em vez de perder efeitos silenciosamente.
4. Renderizar uma cópia sintética sem alterar a origem, medir duração/som/pixels e comparar com a prévia. Testar falha, cancelamento, reinício e ausência de GPU.
5. Expor no editor somente recursos comprovados nesse build. Aplicar com rascunho/Cancelar, expected_revision, histórico e fallback quando possível. Não trocar automaticamente o motor de projetos existentes.
6. Ampliar em pacotes: transições/efeitos → títulos/keyframes → camadas → modelos locais. Manter cada capacidade documentada como preparada, testada ou ativa.

## Licença e marca

O workspace declara AGPL-3.0-or-later. Essa licença admite uso comercial; não é uma proibição de vender um produto. Reutilização e distribuição/modificação trazem obrigações de licença e disponibilização do código correspondente, inclusive condições específicas para versões modificadas usadas pela rede. O alcance de um produto combinado depende da arquitetura/distribuição: não foi assumido que um processo separado resolve automaticamente todas as obrigações. A Lili não foi relicenciada nesta entrega. A política do repositório também separa direitos do código e da marca Concat. Foram preservadas a marca Lili e as licenças existentes. Consultar C11/C12 ao decidir a distribuição, além das licenças próprias de modelos, fontes e mídias.

## Referências fixadas para revisitar

- C01: [Apresentação e capacidades declaradas](https://github.com/jub0t/Concat/blob/f0c0169628c61de7311f7fc15ee5be82dd611d2e/README.md).
- C02: [MCP, ferramentas, protocolo e limites do modo headless](https://github.com/jub0t/Concat/blob/f0c0169628c61de7311f7fc15ee5be82dd611d2e/docs/MCP.md).
- C03: [Comandos de edição, áudio, trilhas, timelines e propriedades](https://github.com/jub0t/Concat/tree/f0c0169628c61de7311f7fc15ee5be82dd611d2e/src/crates/concat-project/src/commands).
- C04: [Catálogo, pacotes e efeitos](https://github.com/jub0t/Concat/tree/f0c0169628c61de7311f7fc15ee5be82dd611d2e/src/crates/concat-effects/src).
- C05: [Compositor e transições](https://github.com/jub0t/Concat/tree/f0c0169628c61de7311f7fc15ee5be82dd611d2e/src/crates/concat-render/src).
- C06: [Renderização de texto](https://github.com/jub0t/Concat/tree/f0c0169628c61de7311f7fc15ee5be82dd611d2e/src/crates/concat-text/src).
- C07: [Whisper, TTS e voz](https://github.com/jub0t/Concat/tree/f0c0169628c61de7311f7fc15ee5be82dd611d2e/src/crates/concat-speech/src).
- C08: [Máscaras, segmentação e modelos visuais](https://github.com/jub0t/Concat/tree/f0c0169628c61de7311f7fc15ee5be82dd611d2e/src/crates/concat-vision/src).
- C09: [Exportação e requisitos nativos](https://github.com/jub0t/Concat/blob/f0c0169628c61de7311f7fc15ee5be82dd611d2e/src/README.md).
- C10: [Mensagens tipadas da API](https://github.com/jub0t/Concat/blob/f0c0169628c61de7311f7fc15ee5be82dd611d2e/src/crates/concat-api/src/message.rs).
- C11: [Marca e redistribuição](https://github.com/jub0t/Concat/blob/f0c0169628c61de7311f7fc15ee5be82dd611d2e/TRADEMARK.md).
- C12: [Licença](https://github.com/jub0t/Concat/blob/f0c0169628c61de7311f7fc15ee5be82dd611d2e/LICENSE).
- C13: [Declaração da versão, Rust e licença do workspace](https://github.com/jub0t/Concat/blob/f0c0169628c61de7311f7fc15ee5be82dd611d2e/src/Cargo.toml).

## Verificação e limites

Testes automatizados do bridge usam processo simulado, sem executar o Concat. Cobrem ausência, inicialização, ambiente/pasta isolados, allowlist de consultas, paginação, erros, respostas excessivas e encerramento; teste HTTP confirma que comandos enviados no corpo não são encaminhados. Isso não comprova compatibilidade com um binário Concat real nem ativa catálogo/renderização na Lili. Revisão visual desktop/Safari real permanece pendente; não houve envio de mídia pessoal nem testes em projetos reais.
