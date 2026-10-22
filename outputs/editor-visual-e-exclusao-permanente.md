# Editor, exclusão permanente e esteira de nuvem — 22/10/2026

## Entregas

- A identidade clara da inicial foi aplicada à biblioteca, roteiro, pedidos, ajustes de cena/narração, trilhas, menus e janelas de IA/exportação. A prévia de vídeo continua escura. Novo arquivo web/studio.css preserva os controles e a linha do tempo existentes.
- No celular, o cabeçalho reúne projeto, menu de ações e exportação. O menu dá acesso à inicial, novo projeto, ajuda de conexão e exclusão recuperável. Painéis mantêm rolagem própria e campos adequados ao toque; zoom não foi bloqueado.
- Na Lixeira da inicial, cada projeto tem Restaurar e Excluir permanentemente. A segunda opção explica o impacto e exige digitar EXCLUIR antes de habilitar o envio. Cancelar não remove nada.
- A exclusão permanente remove apenas a pasta local do projeto selecionado, incluindo originais importados, prévias, histórico, espelho de recuperação e exports guardados nessa pasta. Downloads e originais fora dela permanecem. Não existe Desfazer para essa ação.
- POST /api/projects/ID/purge exige projeto na Lixeira, revisão atual e confirmação exata. Bloqueia uploads pendentes e jobs em execução. Valida o destino dentro do diretório de dados e rejeita links simbólicos, junctions e reparse points antes de remover arquivos. Enfileirar jobs passou a conferir se o projeto continua ativo, evitando tarefas atrasadas após exclusão.

## Limites da remoção

O total removed_bytes representa o tamanho lógico contado antes de remover os arquivos, não uma medição garantida de espaço físico recuperado no sistema de arquivos. Permissões, arquivos abertos, antivírus ou alterações externas simultâneas podem impedir concluir a remoção. Uma falha durante a remoção pode ser parcial e é informada assim ao usuário; não prometer restauração após iniciar a exclusão permanente. A validação de links não é uma proteção universal contra um processo local malicioso alterando diretórios simultaneamente.

Arquivos na Lixeira dentro de um projeto ativo continuam recuperáveis; a exclusão permanente desta entrega refere-se ao projeto inteiro na Lixeira da inicial.

## Nuvem na esteira

Ver [esteira-do-projeto.md](esteira-do-projeto.md). Recurso planejado, também identificado como tal em Preferências. Nenhum provedor foi conectado e não houve envio de arquivos.

Planejamento: autenticação oficial; projeto, originais/áudios e vídeo final; fila persistente e retomada; manifesto/hash; histórico por revisão; restauração testada; liberação local somente depois de cópia remota verificada. Não tratar sincronização simples como backup com retenção. Destino e limites serão definidos antes de implementar.

## Verificação

- 67 testes Python passaram na suíte completa. Novos casos cobrem confirmação, estado na Lixeira, revisão, destino fora do projeto, reparse point, remoção efetiva só do projeto sintético, preservação de outro projeto/arquivo externo e bloqueio de jobs pelo HTTP.
- Conferência no navegador: editor desktop; simulação 390 × 780 com biblioteca, menu móvel e exportação; abertura da confirmação permanente, botão inicialmente bloqueado e habilitação após digitar EXCLUIR. A confirmação de teste foi cancelada pela interface. Exclusões efetivas ocorreram somente nas suítes automatizadas com dados temporários.
- A simulação usa um servidor de fixture com dados sintéticos e permissão de iframe da mesma origem apenas para testar largura pequena. Não é teste de hardware/Safari. O servidor real mantém frame-ancestors none e o gateway mantém X-Frame-Options DENY.
- Provas locais, fora do Git: outputs/lili-studio-mobile.png, outputs/lili-studio-biblioteca.png, outputs/lili-studio-exportar.png e outputs/lili-exclusao-permanente.png.
- Ativação: servidor local reiniciado após ausência de jobs e uploads recentes. Os hashes de project.json e revisões dos projetos reais, ativos e na Lixeira, foram comparados antes/depois e permaneceram idênticos. Nenhum projeto real foi excluído. Gateway, sessões, conector e túnel preservados; API remota sem login segue 401.

## Próxima verificação humana

Conferir o novo visual, teclado e gestos no iPhone. A validação anterior da inicial no celular foi confirmada pelo usuário; esta atualização do editor ainda precisa desse reteste.
