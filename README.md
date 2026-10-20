# Lili — seu estúdio de vídeo

Editor local para a Elisa revisar uma primeira montagem, ajustar cenas e acrescentar a narração. A interface e o Codex compartilham o mesmo projeto, com proteção de cenas, revisões e histórico de alterações.

## Primeira versão funcional

- Importação de vídeos e áudios, com miniaturas e prévias compatíveis com o navegador.
- No celular, importação em destaque, andamento do envio na área principal e barra inferior de ferramentas.
- Roteiro dividido em blocos e etiquetas por arquivo.
- Sequência editável: trocar tomada, ajustar entrada e saída, reordenar, editar título e controlar volume.
- Linha do tempo com régua, cursor, zoom, miniaturas proporcionais, divisão no cursor e aparo por arrasto.
- Faixa de narração com forma de onda obtida do áudio.
- Proteção de cenas e desfazer, com salvamento no computador.
- Narração adicionada depois da montagem, com volume e posição inicial.
- Exportação real em MP4/H.264, em 1080 × 1920 ou prévia leve em 540 × 960.
- CLI e servidor MCP para o Codex inspecionar mídia e editar a mesma montagem da interface.
- Pedidos de ajuste salvos em uma fila local para o Codex.
- Botão **Editar com IA**: analisa o roteiro e folhas de contato dos vídeos usando o Codex instalado, e aplica uma montagem editável na linha do tempo.

O botão **Editar com IA** executa uma análise visual pelo Codex CLI conectado à conta ChatGPT do notebook; consome os limites dessa conta. Não exige uma chave de API. O notebook precisa estar ligado, conectado e com `codex login` concluído. A análise recebe o roteiro e uma folha com 12 quadros por vídeo, seleciona trechos e aplica a montagem na mesma linha do tempo, com opção de Desfazer. São aceitos até 40 vídeos por análise. É uma primeira montagem: amostragem visual não identifica com precisão todos os gestos nem mede sincronismo por frase. A narração selecionada é preservada, e não há geração de voz ou música.

Importe os arquivos, preencha o roteiro em **Arquivos → Roteiro**, abra **Editar com IA**, informe uma direção opcional e toque em **Montar na linha do tempo**. O roteiro digitado é salvo ao abrir esse fluxo. Acompanhe o andamento nessa janela, mesmo se acessando pelo iPhone. Cenas protegidas precisam ser mantidas. Mudanças na revisão durante a análise impedem a aplicação do resultado para preservar a edição manual. A montagem é validada pelo servidor antes de ser salva; o processo Codex roda em modo somente leitura, sem shell nem ferramentas conectadas do projeto.

O botão **Rascunho por etiquetas** continua como alternativa local sem IA. Os **pedidos de ajuste** escritos na aba Codex ainda formam uma fila para uma sessão do agente; eles são independentes do botão de montagem automática.

## Iniciar no Windows

Na raiz deste checkout:

```powershell
.\iniciar.ps1
```

Abrir **http://127.0.0.1:8765**. O terminal precisa permanecer aberto. Para iniciar sem janela de terminal, usar `iniciar.ps1 -Background`; o PID e os logs ficam em `work/`.

O inicializador usa primeiro `.venv`, depois o Python fornecido pelo Codex se disponível, ou o Python do sistema. Nesta máquina, as dependências já estão disponíveis localmente em `work/python-packages` e no runtime do Codex.

Para preparar outra máquina com Python 3.12 ou superior:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\iniciar.ps1
```

Um FFmpeg instalado no sistema pode ser usado; alternativamente, `imageio-ffmpeg` fornece o executável. A variável `LILI_FFMPEG` seleciona outro caminho. Títulos usam Arial no Windows ou DejaVu Sans no Linux; `LILI_FONT` permite escolher outro arquivo de fonte.

## Edição pelo Codex

Ver [CLI, MCP e operações](docs/codex.md). A CLI já permite trabalhar com o servidor em execução:

```powershell
python -m lili.cli list
python -m lili.cli context ID_DO_PROJETO
```

O MCP oferece leitura de contexto, folhas de imagens, edição, exportação e consulta de progresso. Uma configuração local por projeto pode ser usada em `.codex/config.toml`; caminhos específicos da máquina são ignorados pelo Git. O cliente precisa carregar esse cadastro para apresentar as ferramentas.

## Material já usado no piloto

Foram analisados dois vídeos finalizados da Elisa e recebidos os nove arquivos do passeio na Catedral, além do roteiro. Uma primeira montagem visual foi preparada pelo Codex com esses nove arquivos e salva como projeto editável. Os originais permanecem preservados.

- [Roteiro e plano de montagem](outputs/roteiro-cora-catedral.md).
- [Análise inicial do estilo](outputs/analise-referencias-elisa.md).
- [Direção de produto](outputs/direcao-produto.md).
- [Estado e verificação da versão 0.1](outputs/versao-0.1.md).
- [Linha do tempo, PWA e acesso remoto](outputs/linha-do-tempo-e-celular.md).

## Dados locais

Os projetos, mídias importadas, prévias, exportações e históricos ficam em `work/lili-data/`, fora do versionamento. O editor escuta apenas em `127.0.0.1`. Importação, edição manual e exportação usam processamento local. Ao iniciar **Editar com IA**, o roteiro, metadados e folhas de contato são enviados ao Codex para análise.

O acesso pelo iPhone foi preparado como PWA, com um gateway de login separado. Executar `acesso-remoto.ps1 -Modo Preparar` e criar o login no notebook em `http://127.0.0.1:8767/auth/setup`. Depois, `acesso-remoto.ps1 -Modo Ativar` abre um endereço HTTPS temporário da Cloudflare para o gateway autenticado. Essa ativação dá acesso pela internet aos usuários que tiverem a senha; vídeos e comandos transitam pelo túnel até o celular. Ainda falta testar a ativação externa e o uso em iPhone real. `-Modo Desativar` encerra o acesso externo. O túnel nunca deve apontar diretamente para a porta 8765 do editor.

A interface tem layout responsivo e cuidados de toque. O notebook deve permanecer ligado e conectado. O CapCut continua como alternativa de finalização; a transferência de timeline editável entre os programas não foi implementada.

## Motor de processamento

Esta versão usa FFmpeg local. O [Concat](https://github.com/jub0t/Concat) continua como motor candidato para uma etapa posterior; seu código não foi incorporado ao projeto. O código da versão publicada v0.2.7 consultada não tinha o comando MCP disponível na branch principal. Nenhuma integração operacional com o Concat é alegada nesta versão.

## Verificação

```powershell
python -m unittest discover -s tests -v
node --check web/app.js
node --check web/timeline.js
node --check web/sw.js
```

Os testes cobrem persistência, revisões concorrentes, cenas protegidas, divisão de clipes, desfazer, importação, envio em blocos, montagem de vídeo sem áudio, narração adicional, forma de onda, títulos, orientação por metadados, exportação, leitura parcial de mídia, protocolo MCP e autenticação do gateway remoto. O Node é necessário apenas para a verificação de sintaxe do JavaScript, não para executar o editor.
