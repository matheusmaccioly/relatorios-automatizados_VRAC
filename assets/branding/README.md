# Branding institucional da PUC-Rio

Coloque nesta pasta os materiais oficiais de identidade visual que orientarão o sistema VRAC.
**Estado atual: aguardando materiais oficiais e validação da aplicação visual.**

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

Adicionar arquivos ou preencher `tokens.toml` **não altera a interface automaticamente**.
O consumo desses materiais será integrado à aplicação a partir das regras aprovadas.
O exemplo é documental e ainda não é carregado pelo aplicativo.

## Regra para o desenvolvimento

Todo elemento visual do sistema deve seguir o branding da PUC-Rio: telas, navegação,
cores, tipografia, marcas, ícones, gráficos, tabelas e futuras exportações. As regras
também se aplicam a estados de carregamento, vazio, aviso e erro.

Usar somente as marcas e variantes autorizadas nos materiais fornecidos. Não criar
logotipos, paletas, fontes ou assinaturas PUC-Rio/VRAC por aproximação. Centralizar o
consumo dos recursos e tokens para manter a identidade consistente entre interface
e arquivos produzidos pelo sistema.

O tema atual da demonstração é provisório; não representa conformidade institucional.
A ausência de materiais mantém a aplicação visual pendente, sem impedir os testes
sintéticos e o desenvolvimento de regras sem apresentação visual.

Esta pasta recebe recursos de marca autorizados para o projeto. Credenciais, dados
acadêmicos e documentos privados operacionais continuam fora do workspace e do Git.
