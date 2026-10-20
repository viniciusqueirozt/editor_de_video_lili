# Editor de Vídeo Lili

Projeto de edição de vídeo assistida por IA para reduzir o trabalho manual da Elisa e preservar seu estilo, com gravação e revisão pelo iPhone e processamento no computador.

## Estado atual

O projeto está na fase de planejamento e validação técnica. Ainda não há aplicativo próprio, integração operacional com o Codex ou edição automática testada com os vídeos da Elisa.

O [plano do piloto](outputs/piloto-elisa.md) registra os requisitos, as verificações realizadas, as limitações conhecidas e o primeiro teste proposto.

## Fluxo proposto

1. Receber os vídeos originais e o briefing do trabalho.
2. Analisar o material e aplicar referências de edição aprovadas pela Elisa.
3. Usar o Codex e o Concat para montar uma primeira versão.
4. Entregar uma prévia para revisão no iPhone.
5. Aplicar ajustes solicitados e exportar a versão aprovada.

Serão avaliadas duas formas de revisão: pedidos por mensagem e finalização manual no CapCut. A transferência de projetos com todas as faixas editáveis para o CapCut ainda não foi confirmada.

## Conteúdo atendido pelo piloto

- Vlogs, rotinas, bastidores e conteúdo lowfi.
- Reviews, promocionais e depoimentos.
- Campanhas, ensaios publicitários e trends, em testes posteriores.

Publicação principalmente no Instagram e depois no TikTok. Durações informadas: 15 a 30 segundos, 1 minuto e 30 segundos a 3 minutos e, ocasionalmente, 4 a 5 minutos.

## Base técnica em avaliação

O [Concat](https://github.com/jub0t/Concat) é o motor de edição candidato. Seu código atual inclui MCP; o código da versão publicada v0.2.7 consultada não contém o comando `--mcp`. A escolha entre a API da versão publicada e uma compilação com MCP depende de um teste de integração.

Referência consultada do Concat: `79116bd0f9a103c633d888603ad27890e929dbdc`. O código do Concat não foi incorporado a este repositório. Sua licença e os termos das futuras integrações devem ser considerados antes da comercialização.

## Próximo passo

Selecionar um review ou depoimento já entregue, com o vídeo final, os arquivos originais, o briefing e uma estimativa do tempo de edição. Comparar qualidade e tempo de revisão nos dois fluxos antes de ampliar o sistema.

## Arquivos locais

Guardar material de trabalho em `media/`, `videos/`, `exports/` ou `work/`, que são ignoradas pelo Git. Credenciais devem permanecer em arquivos locais ignorados, como `.env`; compartilhar somente exemplos sem segredos.
