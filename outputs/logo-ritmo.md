# Lili · Ritmo

Conceito 1 escolhido pelo usuário em 22/10/2026. Quatro hastes arredondadas alternadas com pontos representam o nome lili e o ritmo da montagem. Marca adaptada em geometria vetorial, com wordmark próprio desenhado em curvas; não depende de baixar uma fonte.

## Aplicação

- Inicial: símbolo e nome em versão clara no menu escuro.
- Editor: assinatura escura no notebook; símbolo compacto no cabeçalho do celular.
- Login do editor remoto: assinatura vetorial e ícone da aba, sem exigir sessão para carregar os três arquivos de marca permitidos.
- Favicon SVG: fundo verde-floresta e marca clara, com URL versionada para renovar o cache.
- Atalho/PWA: PNGs 192 e 512 pixels, fundo sólido e símbolo dentro da área segura central. Manifesto preserva id/start_url e atualiza cores e URLs dos ícones.
- O portal hospedado em chatgpt.site é uma aplicação separada e ainda mantém sua identidade anterior. Esta entrega altera o editor e seu login.

## Arquivos

- web/logo-ritmo.svg: marca para fundo claro.
- web/logo-ritmo-inverse.svg: marca para fundo escuro.
- web/favicon.svg: ícone de aba.
- web/icon-192.png e web/icon-512.png: ícones do aplicativo.
- scripts/build-brand.py: reconstrói os vetores e rasteriza a geometria dos ícones com Pillow. Nenhuma mídia de usuário é usada.

Cores: verde-floresta #283c30, sálvia #789460, lima #d6e8ae e fundo #f5f5f0.

## Verificação

Sete testes focados do gateway passaram, incluindo ícones públicos sem liberar APIs, projetos ou sessões. SVGs XML válidos; dimensões e fundo dos PNGs conferidos. Inicial real inspecionada no navegador. Endereço remoto retorna login com a marca, ícones 200 e API sem sessão 401. Prova local em outputs/lili-logo-ritmo-aplicada.png, fora do Git.

Reiniciado apenas o gateway, após conferir ausência de upload recente. Isso encerra sessões em memória e pode exigir entrar novamente. Editor, arquivos, credenciais e túnel/endereço preservados. Mudanças de autorização preparadas na esteira não foram ativadas por esta entrega.

O novo ícone de um atalho já instalado no iPhone pode permanecer em cache e precisar de atualização/recriação do atalho. Aparência em Safari/iPhone real ainda precisa de conferência.
