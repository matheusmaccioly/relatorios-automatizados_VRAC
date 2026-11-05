# Branding institucional da PUC-Rio

Coloque nesta pasta os materiais oficiais de identidade visual que orientarão o sistema VRAC.
**Estado atual: materiais recebidos em 28/10/2026 e aplicados à demonstração;
revisão por Matheus e pelo responsável institucional ainda pendente.**

Foram fornecidas assinaturas RGB (PNG, JPG e AI), uma prancha de referência EMoD
de 23-10-18 e as famílias Literata e Rethink Sans. Os originais foram preservados.
O inventário e as limitações estão em [guidelines/README.md](guidelines/README.md).
O aplicativo utiliza a assinatura horizontal abreviada monocromática, sem recorte, e
aplica Rethink Sans no corpo e nos títulos, com Literata em rótulos e identificação
editorial. Matheus indicou o site público e o portal como o que há de mais próximo do
design system (D-032): seus valores passaram a orientar paleta e componentes, sem
constituir um manual completo. [Referências e divergências](guidelines/README.md).

| Material | Onde colocar |
|---|---|
| Logotipos, brasões e assinaturas oficiais, com suas variantes | [logos/](logos/README.md) |
| Favicon e ícones institucionais | [icons/](icons/README.md) |
| Fontes e condições de uso fornecidas pela instituição | [fonts/](fonts/README.md) |
| Manual de marca, orientações, exemplos aprovados e referências | [guidelines/](guidelines/README.md) |
| Templates institucionais para orientar gráficos, tabelas e materiais | [templates/](templates/README.md) |
| Paleta, tipografia e referências dos arquivos aprovados | [tokens.example.toml](tokens.example.toml) |

## Como adicionar os materiais

1. Adicionar os arquivos oficiais nas pastas correspondentes, preservando os originais.
2. Informar a origem e a versão dos materiais junto ao manual em `guidelines/`.
3. Identificar as variantes permitidas para aplicação web, fundo claro/escuro,
   tamanhos mínimos e área de proteção, conforme o manual fornecido.
4. Quando os valores forem confirmados, copiar `tokens.example.toml` para `tokens.toml`
   e preencher as referências e os valores oficiais. Caminhos de arquivos são relativos
   a esta pasta; campos vazios significam pendência, nunca um valor oficial presumido.
5. Registrar a revisão da aplicação com Matheus e o responsável institucional pela
   identidade visual antes de declarar conformidade.

Os valores em `tokens.toml` agora são consumidos por `src/vrac/branding.py`.
O exemplo permanece apenas documental. Após alterar tokens ou arquivos selecionados,
sincronizar os arquivos web e reiniciar a demonstração:

```powershell
.\.venv\Scripts\python.exe scripts/sync-branding.py
.\scripts\run-demo.cmd
```

O script gera `.streamlit/config.toml` e copia seis pesos de fontes e a marca em uso,
sem alterações, para `static/branding/`. Essa pasta pública deve conter somente esses recursos web,
nunca fontes de dados, documentos internos ou configurações privadas. Nenhum CDN,
Google Fonts ou download de fontes é usado pela interface.

## Regra para o desenvolvimento

Todo elemento visual do sistema deve seguir o branding da PUC-Rio: telas, navegação,
cores, tipografia, marcas, ícones, gráficos, tabelas e futuras exportações. As regras
também se aplicam a estados de carregamento, vazio, aviso e erro.

Usar somente as marcas e variantes autorizadas nos materiais fornecidos. Não criar
logotipos, paletas, fontes ou assinaturas PUC-Rio/VRAC por aproximação. Centralizar o
consumo dos recursos e tokens para manter a identidade consistente entre interface
e arquivos produzidos pelo sistema.

O tema foi aplicado aos materiais disponíveis; não representa homologação visual.
Regras não documentadas (como tamanho mínimo, hierarquia tipográfica institucional,
favicon e cores semânticas) continuam pendentes. A interface foi conferida em Chrome
headless (D-032); falta a revisão humana de Matheus e do responsável institucional.

Esta pasta recebe recursos de marca autorizados para o projeto. Credenciais, dados
acadêmicos e documentos privados operacionais continuam fora do workspace e do Git.
