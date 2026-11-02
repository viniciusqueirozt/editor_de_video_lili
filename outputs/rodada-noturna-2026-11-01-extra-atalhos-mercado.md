# Extra — noite de 01 para 02/11/2026: atalhos de trabalho e mercado

## Pesquisa pública e decisões

Consultadas páginas oficiais em 02/11/2026. É uma amostra pública de posicionamento/monetização, sem entrevistas, testes com clientes ou prova de receita/lucro.

| Produto/fonte | Oferta observável | Aprendizado para a Lili |
| --- | --- | --- |
| [Microsoft Clipchamp](https://clipchamp.com/en/pricing/) | Edição gratuita com export até 1080p; recursos premium associados ao Microsoft 365 Personal/Family, incluindo 4K, acervo e brand kit | Entrada simples e ferramentas identificáveis antes de recursos avançados; não esconder o caminho básico de edição/entrega |
| [CapCut: comparação oficial](https://www.capcut.com/resource/capcut-standard-vs-pro) | Diferencia funções gratuitas e assinaturas com recursos/acervo/IA/nuvem; preços variam por região, plataforma e promoção | Tornar claro o que já funciona, o que consome IA externa e o que ainda é planejado; reduzir procura pelo recurso |
| [DaVinci Resolve/Studio](https://www.blackmagicdesign.com/products/davinciresolve) | Versão gratuita e Studio à venda com recursos adicionais; página consultada também vende hardware e apresenta oferta promocional | Núcleo útil pode coexistir com produto comercial; qualidade do fluxo e confiança na entrega importam além da quantidade de efeitos |

A comparação trata cobrança anunciada, não receita comprovada. Valores regionais/promocionais não foram convertidos em preço da Lili nem usados para estimar ganhos. O desenho implementado abaixo é próprio; não copia interface, marca, assets ou código dos concorrentes.

## Melhoria visual/funcional entregue

A inicial ganhou **Qual é o próximo passo?**, com escolha explícita de projeto e quatro cartões: Importar arquivos, Ajustar transições, Revisar legendas e Preparar entrega. Cada um abre diretamente o painel correspondente do editor existente. Não dispara edição, envio ao Codex, geração ou exportação por URL. A interface mantém as funções atuais acessíveis e não apresenta transcrição/recorte locais ainda inexistentes como prontos.

O projeto selecionado acompanha os links; se for excluído, a lista usa um ativo disponível. Sem projetos, o bloco fica oculto e os links antigos são removidos. Nomes são escapados e o contexto indica que abrir um atalho não altera montagem. A entrada por panel=ai já existente continua válida; intenções desconhecidas não executam ações. Projetos sem cenas suficientes recebem orientação para a biblioteca.

Layout com cartões em duas colunas no espaço móvel e quatro em telas largas, seletor com fonte de 16 px, alvos maiores que 44 px, foco visível, quebra de textos longos e hover limitado a mouse. Nenhuma alteração da logo ou migração para app nativo/Rust.

## Hipótese comercial futura, sem implementação de cobrança

Manter o núcleo local gratuito útil e o código próprio fechado, conforme a direção do usuário. Avaliar comercialização de automações de fluxo, configurações de marca/estilo, instalação/suporte ou serviços de equipe/nuvem opcionais, apenas após provar utilidade com Elisa e validar demanda. São hipóteses, não decisão de planos/preços, promessa de renda nem autorização para contratar infraestrutura. Armazenamento remoto, colaboração e serviços exigem decisões próprias; nada foi ativado nesta extra.

## Verificação e limites

Passaram **25 arquivos JavaScript**, um novo de navegação: projeto escolhido, ausência/exclusão de projetos, nomes escapados, quatro links, abertura dos painéis existentes, intenção desconhecida, cenas insuficientes e troca de projeto enquanto aguarda fila. Três testes HTTP existentes focados também passaram: rotas inicial/editor, entrega de exportação e JSON truncado. A suíte Python de segurança permaneceu como última completa (182 casos); não foi repetida por mudanças apenas de frontend/documentação.

Tentada revisão desktop pela skill computer-use usando o runtime oficial; a inicialização falhou novamente com failed to write kernel assets/path not found, antes de controlar qualquer janela. Não se usou outro mecanismo de navegador para contornar a restrição. Assim, revisão visual desktop e Safari real permanecem pendentes. CSS/DOM não comprovam comportamento no aparelho.

## Publicação

Frontend compatível servido após atualizar; sem serviços reiniciados durante a extra. Fechamento a seguir: revisão final, sincronizar código/testes/documentação, confirmar ausência de trabalhos/envios antes de reiniciar só o editor, preservar gateway/conector/túnel/sessões e conferir capacidades de áudio/transições/entrega. Encerrar antes das 5h; nenhum novo agendamento ou trabalho diurno automático.


## Estado final após publicação

Entrega publicada e código ativo no editor no fechamento de 02/11/2026, acumulado até cef630b. Reinício somente do editor após ausência de jobs/uploads/processamento; gateway, conector, túnel e sessões preservados. Verificadas saúde e capacidades HTTP, bloqueio sem login e endereço remoto saudável. A indicação anterior de ativação pendente é histórica. Revisão visual desktop e Safari real continuam pendentes. Ver [relatório consolidado](relatorio-noite-01-02-11-2026.md) para verificações, limitações e próximo passo.
