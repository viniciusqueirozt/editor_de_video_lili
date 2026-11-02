# Primeira integração Edvid na Lili — 02/11/2026

Entrega solicitada diretamente pelo usuário, independente das rodadas automáticas.

## Disponível
Em Legendas, abra uma legenda existente e toque em **Dividir, juntar ou sincronizar**:
- Dividir: instante na montagem, atalho para meio/cursor escolhido e dois textos revisáveis.
- Juntar com a próxima: mantém entrada da primeira, saída da próxima e estilo da primeira. O intervalo entre elas passa a ter legenda; isso é informado antes de aplicar.
- Sincronizar todas: antecipar/atrasar por segundos ou mm:ss.mmm, preservando durações e espaços.

O painel mostra os blocos propostos antes de gravar. Cancelar não altera o projeto. Aplicar usa um único captions_replace com revisão esperada, histórico, Desfazer e Refazer. Vídeo, música, narração e sons independentes não são movidos.

Validação: mínimo de 0,1 s por bloco, texto não vazio de até 160 caracteres, IDs exclusivos, sem sobreposição e dentro do vídeo. Preserva estilos e trata texto como conteúdo literal. Propostas antigas/troca de projeto, clique duplo e falha de gravação são tratados. Ajustes ainda não aplicados no painel anterior precisam ser aplicados ou cancelados antes de organizar.

## Reutilização e licença
Adaptadas as regras de divisão/junção/deslocamento de helpers/caption_edit.py do repositório geovanejunior92-debug/edvid, revisão 230316f2a860f2b67e02440fc6e0bd77afdaaf61. Implementação JavaScript adaptada a segundos, IDs, estilos e API da Lili. Aviso MIT/copyright Creator Factory preservado em third_party/edvid/LICENSE e no módulo.

Não houve incorporação de Concat, Remotion, RVM, pesos, fontes, LUTs, mídia do autor ou autenticação externa. Nenhum modelo/dependência foi instalado e nenhuma chamada real de IA foi feita.

## Correção descoberta no navegador
A primeira abertura do projeto podia terminar antes de timeline.js carregar e mostrar renderTimeline is not defined. A inicialização agora espera DOMContentLoaded, após os módulos deferidos, preservando projeto e painel pedidos na URL. Há teste para os estados loading, interactive e complete.

## Verificações
- 28 arquivos JavaScript verificados: regressões anteriores e três novos grupos de organização/modelo, interface e inicialização.
- Nove testes Python focados passaram: API atômica/histórico, invalidez/revisão, assets HTTP, SRT, wrapping e exportação sintética com tempos/estilos, incluindo checagem de pixels.
- Projeto sintético isolado no navegador desktop: divisão aplicada, junção aplicada e sincronização aplicada, com resultado visível. A captura foi guardada fora do Git.
- Falhas iniciais dos novos harnesses eram comparação entre contextos VM e espera de microtarefas; corrigidas no teste, sem enfraquecer as verificações.
- Safari/iPhone real continua pendente. Não foi executada novamente a suíte Python inteira: mudanças de modelo/exportação foram verificadas pelos testes focados existentes.

## Ativação
Ativação conferida: arquivos JS/CSS, /editor e /api/health retornaram 200. Somente o editor foi reiniciado após confirmar zero jobs ativos, uploads parciais e mídias em processamento. Gateway preservado; túnel remoto permaneceu saudável e com o mesmo endereço. Projetos reais, originais e sessões não foram alterados por testes.

Esta entrega não gera legendas automaticamente nem mede o tempo das palavras. A divisão inicial do texto é sugestão revisável. A prévia do novo painel é dos blocos e seus tempos; o resultado pode ser conferido no player existente.

## Continuação autorizada
Próximas integrações, ainda planejadas: proposta de tomadas por roteiro; perfil mensurável das referências da Elisa; transcrição local em worker cancelável com cache correto e benchmark. O lote upstream não deve ser portado sem corrigir a invalidação de cache identificada na análise.
