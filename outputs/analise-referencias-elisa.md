# Análise inicial das referências da Elisa

Versão 0.1 — baseada em dois vídeos finalizados fornecidos pelo usuário. Estas observações descrevem as amostras; ainda precisam da validação da Elisa e não representam todos os formatos do seu trabalho.

## Arquivos analisados

| Referência | Duração | Imagem | Conteúdo observado |
| --- | --- | --- | --- |
| IMG_7019_vlog cora 2.MOV | 35,734 s | 1080 × 1920, aproximadamente 30 fps | Passeio, piquenique e apresentação de uma atividade/produto |
| IMG_6447_vlog cora.MOV | 34,833 s | 1080 × 1920, aproximadamente 30 fps | Apresentação do perfil, rotina e convite a parcerias |

Os dois arquivos são verticais, proporção 9:16, com vídeo HEVC de 8 bits e indicação BT.709/SDR, além de áudio AAC estéreo a 44,1 kHz. Isso descreve as exportações recebidas; não comprova as configurações de captura dos originais.

## O que as amostras mostram

### A narração organiza a história

Os dois vídeos têm fala contínua em português, identificada por transcrição automática local. As cenas ilustram as ideias narradas, com mudanças de assunto acompanhadas por mudanças de imagem.

No 7019, a menção à catedral, aproximadamente aos 6 segundos, coincide com a imagem do local. Por volta dos 25 segundos, a narrativa passa para o livro/atividade e as imagens passam a mostrar esse material.

No 6447, a apresentação da Elisa é acompanhada por sua imagem com a gata, aproximadamente aos 6 segundos. O trecho sobre a comunidade, aproximadamente de 13 a 18 segundos, acompanha uma gravação de tela do perfil. A menção a produtos, perto dos 24 segundos, acompanha uma demonstração.

O usuário confirmou posteriormente o processo da Elisa: roteiro, gravação, montagem visual, gravação da narração e união do vídeo com a voz. Portanto, a primeira montagem deve partir do roteiro e dos brutos; a narração posterior orienta o ajuste final. O [roteiro recebido do passeio na Catedral](roteiro-cora-catedral.md) documenta essa aplicação.

### O ritmo combina durações diferentes

Há planos sustentados por alguns segundos e sequências curtas com várias mudanças rápidas de tomada. No 7019, a região próxima de 25 a 26 segundos contém várias imagens diferentes em menos de um segundo. No 6447, há uma sequência dinâmica entre aproximadamente 4 e 6 segundos.

Implicação para o piloto: usar durações variáveis e reservar sequências rápidas para momentos selecionados. Uma regra fixa de duração por clipe perderia parte do ritmo observado. As posições exatas e a relação com batidas da música ainda não foram validadas.

### A seleção de cenas faz parte da identidade

As amostras alternam detalhes da gata, pessoas, ações, planos do ambiente e, quando relevante, produto ou gravação de tela. No passeio, isso cria uma progressão visual de chegada, experiência no local, atividade e encerramento. Na apresentação, organiza personagem, criadora, rotina, comunidade e proposta de parceria.

Implicação para o piloto: manter essas funções narrativas no catálogo de material. A escolha da tomada e do momento dentro dela merece revisão da Elisa.

### Texto e encerramento têm funções específicas

No 7019, foi observado um título branco curto, em duas linhas, na região central da abertura. As amostras visuais restantes dão destaque às cenas. No 6447, parte do texto visível pertence à própria gravação de tela do Instagram.

As falas finais contêm uma pergunta/convite no passeio e um convite a colaboração no vídeo de apresentação, segundo a transcrição automática.

Implicação para o piloto: tratar título, legendas de fala, texto capturado em tela e chamada final como decisões separadas. O perfil inicial não deve acrescentar legendas ou efeitos recorrentes sem validação da Elisa.

## Primeiro perfil proposto para aprovação

| Elemento | Regra inicial proposta |
| --- | --- |
| Estrutura | Abertura com personagem ou situação; desenvolvimento com cenas relacionadas à fala; fechamento coerente com o objetivo |
| Montagem | Narração como referência de sentido, com cenas escolhidas por assunto e ação |
| Ritmo | Planos de duração variável e pequenas sequências rápidas em pontos selecionados |
| Enquadramento | Alternar detalhes, ações e contexto; preservar o assunto importante ao ajustar o quadro |
| Texto | Título breve quando fizer sentido; estilo e uso de legendas dependem da aprovação da Elisa |
| Efeitos | Reproduzir somente os efeitos identificados e aprovados; parâmetros ainda não determinados |
| Som | Preservar a narração fornecida; volumes, música e tratamento precisam de avaliação específica |
| Revisão | Troca de tomada, duração, texto e encerramento devem permanecer ajustáveis no projeto |

Não foi feita clonagem de voz, treinamento de modelo ou edição dos arquivos recebidos.

## Como comparar os dois caminhos de revisão

**Pedidos por mensagem:** gerar uma prévia com posições de tempo claras; testar pedidos como trocar a tomada de um trecho, prolongar uma cena ou simplificar o título. O motor deve refazer a prévia a partir do projeto preservado.

**Finalização no CapCut:** testar uma montagem base, com a possibilidade de manter trilha e textos separados na entrega auxiliar. A transferência de uma timeline integralmente editável para o CapCut continua sem validação; um MP4 sozinho não preserva os elementos independentes.

A comparação precisa usar o mesmo conjunto de brutos e registrar tempo ativo da Elisa, quantidade de ajustes e satisfação com o resultado.

## Método e limites

- Metadados e decodificação de imagem extraídos localmente com FFmpeg/PyAV.
- Inspeção de amostras visuais a cada dois segundos e amostras adicionais em trechos de cortes rápidos, texto e produto.
- Transcrição automática com Whisper base, executada localmente. Nomes, palavras e tempos podem conter erros; a transcrição não é uma legenda final aprovada.
- Detecção automática de mudanças de cena usada para localizar trechos. Sua contagem não foi tratada como número exato de cortes, pois movimento de câmera também produz detecções.
- Não houve avaliação auditiva humana ou aferição de sincronismo musical. Timbre, volume ideal, identidade da trilha e equilíbrio entre voz e música continuam pendentes.
- As imagens finais permitem observar o resultado, mas não revelar com segurança a fonte exata, o preset de cor, a velocidade original, os efeitos usados ou a intenção de cada escolha.
- Os vídeos e as amostras de imagem permanecem locais. Não foram enviados a serviços externos nem incluídos no Git.

## Próximo teste necessário

O roteiro do passeio na Catedral foi recebido e a ordem do processo foi confirmada pelo usuário. Posteriormente, os nove brutos correspondentes também foram fornecidos e uma primeira montagem visual foi feita pelo Codex no editor local; ver [estado da versão 0.1](versao-0.1.md). O próximo teste é a revisão dessa montagem pela Elisa, seguida do ajuste com sua narração separada. Comparar pedidos por mensagem com os controles manuais necessários, mantendo o CapCut como alternativa de finalização.

Os vídeos finalizados já recebidos servem como referência e como resultado de comparação; o ganho real de tempo depende de testar a edição a partir dos brutos.
