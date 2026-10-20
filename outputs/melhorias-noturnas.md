# Lili — melhorias noturnas de 20/10/2026

## Escopo autorizado

Trabalhar em funções e segurança enquanto o usuário dorme, poupar tokens e usar funções locais gratuitas. Sem depender do iPhone. Não prometer paridade completa com CapCut em uma noite. A montagem automática usa limites da conta Codex e não é IA ilimitada gratuita. Não alterar a montagem aprovada da Cora, originais ou credenciais. Não abrir novas portas nem trocar o túnel.

## Pesquisa inicial (fontes oficiais)

- [Shotcut — recursos](https://www.shotcut.org/features/): referência para filtros de áudio/vídeo e edição local. Priorizar controles simples que também funcionem na exportação.
- [Kdenlive](https://kdenlive.org/): referência para edição não linear, áudio e títulos/legendas.
- [Kdenlive — proxies](https://docs.kdenlive.org/en/project_and_asset_management/project_settings/proxy_settings.html): versões leves para editar e originais para exportar; a Lili já segue essa arquitetura.
- [OpenShot — recursos](https://www.openshot.org/features/): referência de ferramentas de edição em software livre.

As referências orientam prioridades de produto; seu código e suas marcas não foram incorporados. Não repetir pesquisa geral a cada rodada.

## Primeira rodada

- Duplicação de cenas: operação `clip_duplicate` e botão Duplicar. Insere cópia após a seleção; preserva o original protegido e cria cópia destravada para ajustes. Desfazer usa o histórico existente.
- Segurança HTTP: validação comum ao editor e gateway antes de ler/encaminhar requisições. Rejeita Content-Length duplicado, tamanho inválido, Transfer-Encoding e Host duplicado. Limita o corpo a 2 GB; os limites menores por endpoint continuam valendo.
- Conexões têm prazo de inatividade de 120 segundos, para não manter leituras abandonadas indefinidamente.
- Verificação: 33 testes passaram, incluindo pedidos HTTP ambíguos rejeitados por ambos os servidores antes da leitura do corpo, além da duplicação com preservação de cena protegida e Desfazer. Sintaxe JavaScript verificada.
- Ativação: editor e gateway reiniciados após confirmar ausência de jobs em andamento. Credenciais e túnel preservados; sessões do gateway em memória foram encerradas, exigindo novo login. Evitar novos reinícios do gateway sem necessidade nas próximas rodadas.

## Agenda e economia

Solicitadas cinco rodadas por hora neste mesmo chat. Uma melhoria completa por rodada, cerca de 10 minutos de esforço. Parar após as cinco execuções; não prolongar agenda. Não fazer novas chamadas de IA reais se testes simulados verificarem a mudança. Testar apenas o que mudou e a suíte completa quando necessário.

## Próximas prioridades

1. Recuperação/backup de projeto e histórico; permitir restaurar sem perda de importações posteriores. Avaliar antes de modificar o formato.
2. Melhorias úteis de áudio: fades e nível, sempre com prévia e exportação consistentes.
3. Velocidade e ajustes visuais; não adicionar controle que só altere a prévia.
4. Legendas locais: verificar dependências existentes antes de prometer automação ou baixar modelos.
5. Auditar uploads abandonados, limitação de concorrência/recursos, validação de entradas e proteção do processamento de IA.

Não é auditoria completa de segurança. iPhone/Safari real continua pendente. Registrar cada entrega concreta abaixo e remover itens já resolvidos da lista.
