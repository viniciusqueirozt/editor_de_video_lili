# Rodada 4 — noite de 01 para 02/11/2026: entrega e recuperação da exportação

## Recursos preparados

**Nome útil ao baixar.** Novas exportações sugerem arquivo com nome do projeto no momento da geração, revisão, perfil, resolução e identificador curto do trabalho. Exemplo sintético: Ensaio-Ágata-v12-final-1080x1920-aaaaaaaaaaaa.mp4. Renomear o projeto depois não muda a identificação do vídeo já gerado. O armazenamento interno continua usando o caminho técnico video.mp4 dentro do job; não move nem renomeia mídia real.

**Disponibilidade real do arquivo.** Ao consultar a fila/histórico, o servidor verifica existência, tamanho não nulo e, quando registrado, igualdade ao tamanho da exportação finalizada. Arquivo ausente, vazio, alterado ou temporariamente inacessível deixa de ser apresentado como pronto para baixar. O estado é calculado na consulta, sem regravar ou apagar o histórico. Isso é verificação de presença/tamanho, não checksum completo ou nova validação dos frames.

**Preparar nova exportação.** O cartão indisponível oferece atalho para selecionar o perfil anterior, rever os avisos e gerar a montagem atual. Não dispara render automaticamente, não sobrescreve a saída anterior e não promete restaurar o estado antigo do projeto. São preservados revisão, qualidade e dados históricos disponíveis. Prévia recebe rótulo específico para distinguir de entrega final.

**Prévia sem cache quebrado.** Ao reutilizar resultado renderizado em memória, o app confirma seu estado no servidor. Se o arquivo saiu do disco, a prévia da revisão atual pode ser gerada novamente. O histórico ignora resultados marcados indisponíveis; erro ao abrir o vídeo apresenta orientação e remove o item do cache para nova tentativa, em vez de manter reprodução vazia.

## Compatibilidade, nomes e permissões

- Cabeçalho HTTP com filename ASCII e filename* UTF-8, seguindo RFC 6266; acentos são preservados onde suportados. Nomes têm limite de bytes, extensão MP4 fixa e remoção de separadores/caminhos, controles e caracteres de nome perigosos. Reservados do Windows recebem prefixo seguro. O nome nunca escolhe o caminho lido pelo servidor.
- HEAD e requisições Range continuam funcionando. Importações/trabalhos que não são exports ou prévias não viram downloads pela rota de exportação. Permissão download_exports continua exigida, independentemente de ter permissão de visualização.
- Jobs legados sem nome/snapshot recebem identificação genérica, sem fingir conhecer o nome antigo. Mesmo sem metadados de resultado, um job legado finalizado pode disponibilizar arquivo não vazio existente; a interface não mostra dimensões/revisão undefined. Não se usa o nome atual do projeto para inventar histórico.
- A primeira verificação focada encontrou uma incompatibilidade com um teste existente de autorização que usava job legado sem result. A implementação foi corrigida para conservar esse caso, sem enfraquecer a permissão nem alterar a fixture para esconder o problema.
- Links continuam construídos com IDs validados e rota local; nome/metadados são escapados na interface. Botão de recuperação de um projeto antigo não muda outro projeto que foi aberto depois.

## Verificação

Passou a **suíte completa de 176 testes Python**, justificada por mudanças compartilhadas em leitura de jobs e entrega de arquivos. Cinco testes novos: quatro casos unitários de nomes/cabeçalhos/disponibilidade e um integrado HTTP com MP4 sintético. Foram verificados Unicode, tamanho, nomes adversos, ausência de injeção de cabeçalho/caminhos, snapshot após renomear projeto, HEAD, Range com bytes corretos, arquivo apagado/vazio/truncado, HTTP 410 para saída indisponível, job de importação recusado e legado. Arquivos de origem preservados e consultas sem mutação do histórico. Testes existentes de contas/permissões e gateway permaneceram aprovados.

Passaram **24 arquivos JavaScript**, com casos ampliados de cartões, nomes escapados, estado indisponível, recuperação sem gerar automaticamente, projeto alterado, metadados legados, recomposição da prévia ausente e erro do player. A contagem não soma repetições da rodada. Nenhuma mídia pessoal, credencial ou chamada real de IA usada; nenhum pacote externo instalado. Diff e sintaxe revisados.

Não houve validação visual desktop nem Safari real. Interpretação do nome no menu de salvar/compartilhar do iPhone e aparência dos novos estados precisam de revisão humana; testes HTTP/DOM não comprovam o fluxo no aparelho.

## Ativação

Código/testes preparados. A versão do servidor em execução ainda não anuncia export_delivery: nomes e disponibilidade enriquecidos aguardam ativação segura no fechamento, junto de library_sounds e spatial_transitions. O frontend tem compatibilidade com respostas antigas; tratamento do erro do player está servido. Editor e login remoto consultados saudáveis, sem reinício, alteração de sessões, túnel ou projetos reais. Checkpoint local, GitHub acumulado para o fechamento após segurança/extra.

## Referência e continuação

Fonte técnica primária consultada: [RFC 6266, nome de arquivo e internacionalização](https://www.rfc-editor.org/rfc/rfc6266). Não houve pesquisa repetida de concorrentes, cópia Concat, inclusão de nuvem/backup ou inferência de licença por separação de processos.

Próxima rodada às 03h55: revisão de segurança/acesso/contas, com identidades/portal simulados; não ativar isolamento individual nem atribuir proprietários de projetos reais sem o fluxo seguro e a decisão correspondentes. Depois, extra de visual/pesquisa se limites e horário permitirem, e publicação/ativação verificadas até antes das 5h. Não repetir uma rodada de edição no lugar da auditoria.
