# Esteira da Lili

## Entregue nesta versão

- Identidade visual da inicial nas telas do editor, painéis, linha do tempo e janelas.
- Menu de projeto compacto no celular.
- Exclusão permanente de projeto já na Lixeira, com confirmação digitada e bloqueio de processamentos. Remove apenas dados na pasta do projeto; arquivos fora dela permanecem.

## Próxima frente: nuvem, backup e liberação local

Solicitação registrada em 22/10/2026. Ainda não implementada. Não há envio de dados nem backup remoto ativo.

### 1. Escolher o destino e conectar a conta

Avaliar o provedor com o usuário antes de integrar: espaço disponível, custo, tamanho dos vídeos, upload pelo notebook e permissão por projeto. Usar autenticação oficial com permissões mínimas; não pedir senhas no chat nem guardar tokens no Git. Nenhum plano pago deve ser contratado automaticamente.

### 2. Cópia verificável do projeto

Enviar gravações originais importadas, áudios, roteiro, metadados da montagem e vídeo final escolhido. Prévias e caches podem ser recriados e não precisam ocupar a nuvem por padrão. Manifesto de arquivos com tamanho e hash, cópias por revisão e histórico separado da sincronização. Excluir localmente não deve apagar o último backup remoto automaticamente.

### 3. Envio em segundo plano

Fila persistente, progresso, retomada de transferências interrompidas, novas tentativas com espera e tratamento de cota/espaço insuficiente. Mudanças durante o upload geram nova revisão; uma cópia só recebe o estado Verificada depois de conferir os arquivos e o manifesto no destino. Não mostrar Backup ativo enquanto houver falha ou pendência.

### 4. Arquivar na nuvem e liberar o notebook

Ação explícita disponível apenas após cópia íntegra verificada. Guardar no notebook uma referência pequena ao projeto arquivado, miniatura e localização remota. Liberar arquivos grandes, proxies e exports locais com confirmação. Não usar uma pasta de sincronização como garantia de backup: a exclusão pode se propagar.

### 5. Restaurar para editar

Baixar os arquivos necessários para o notebook, validar os hashes e abrir a mesma montagem. Mostrar estado Arquivado / Baixando / Pronto para editar. O processamento continua no notebook; a hospedagem do portal não passa a armazenar nem editar os vídeos.

### Critérios para considerar o backup pronto

- Restaurar um projeto sintético completo e comparar montagem e arquivos.
- Simular conexão interrompida, cota esgotada, reinício do notebook e revisão concorrente.
- Confirmar que nenhuma remoção local ocorre com backup pendente ou divergente.
- Documentar retenção, recuperação e exclusão definitiva remota separadamente.

## Outras pendências

- Cancelamento/expiração de uploads abandonados.
- Legendas locais, perfis de estilo e formatos adicionais de projeto.
- Inicialização do conector após reinício do Windows.
- Validação da interface no Safari real, além dos testes no notebook.
