# Documentação do projeto

## Contexto e desenvolvimento

- [Contexto](PROJECT_CONTEXT.md): objetivo, escopo e evidências disponíveis.
- [Plano](PLAN.md): fases, critérios de passagem e pendências.
- [Próximos passos](PROXIMOS_PASSOS.md): pendências, responsáveis e perguntas para avançar à primeira análise.
- [Arquitetura](ARCHITECTURE.md): estrutura técnica e responsabilidades.
- [Catálogo de análises](ANALYSIS_CATALOG.md): definições, contratos, comparação e decisões humanas.
- [Decisões](DECISIONS.md): decisões adotadas e questões abertas.
- [Estado da entrega](STATUS.md): mudanças, verificações e limites efetivos.

## Uso e operação

- [Análises sintéticas R01–R06](guides/ANALISES_SINTETICAS.md): calcular os roteiros, escolher filtros e baixar tabelas, gráficos e pacote completo.
- [Prévia da aplicação](guides/PREVIEW.md): roteiro de conferência da demonstração sintética.
- [Configurar KAPPA/PUC_OLAP](operations/CONFIGURAR_KAPPA.md): modelo preparado e passo a passo para Matheus.
- [PostgreSQL sintético](operations/SYNTHETIC_POSTGRES.md): gerar e executar a base local de desenvolvimento sem extrair dados reais.
- [Diagnóstico e descoberta do banco](operations/DATABASE_DISCOVERY.md): execução manual autorizada.
- [Dicionário sanitizado](operations/SANITIZED_DATA_DICTIONARY.md): material para a próxima fase.
- [Solicitações para a DSI](operations/DSI_REQUESTS.md): infraestrutura, acessos e operação.

## Branding e referências

- [Materiais de branding da PUC-Rio](../assets/branding/README.md): onde adicionar marcas,
  ícones, fontes, paleta, manuais e templates; identidade obrigatória para o sistema.
- [Guia original de desenvolvimento](references/Guia_Desenvolvimento_VRAC_Codex.md):
  conteúdo original preservado, incluindo os prompts por fase.
- [Instruções permanentes](../AGENTS.md): regras para manutenção e desenvolvimento.

A documentação semântica fornecida por Matheus e seu mapeamento detalhado são referências
internas locais, excluídas do Git e do contexto Docker. A síntese, as variantes e suas
limitações estão no [catálogo](ANALYSIS_CATALOG.md); não há dependência desses arquivos
locais para instalar, testar ou carregar o catálogo.

## Roteiros internos das análises

A especificação detalhada de 28/10/2026 está disponível localmente em
[Roteiros de análise de docentes e alunos](ROTEIROS_ANALISES_VRAC.local.md), com
[inventário das páginas e visuais](EVIDENCIAS_PAINEIS_VRAC.local.json). Cobre seis
roteiros, filtros, regras, resultados, decisões e casos de aceite futuros. Ambos
contêm metadados internos e estão excluídos do Git e do contexto Docker; os links
só funcionam no ambiente em que esses arquivos foram gerados. O aplicativo e seus
testes não dependem desses arquivos. Compartilhamento externo exige liberação específica.
