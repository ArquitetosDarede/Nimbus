Backup de On-Premises
======================================================================

Cliente: Ciclope Corporations
Data: 2026-03-18T10:03:57.414298

## Formulário de Proposta Técnica

Cliente: Ciclope Corporations.
Data desta proposta: 27/10/2023.

## Resumo

A Ciclope Corporations é uma empresa que opera com um grande volume de dados, incluindo arquivos de vídeo, e busca garantir a segurança e a integridade de suas informações.
O projeto visa migrar 5TB de dados de backup de um ambiente on-premise para a AWS, garantindo cópias na região de São Paulo e na região de Norte Virginia.
A proposta inclui a configuração de uma arquitetura de backup que permita o decommissionamento seguro dos dados locais após a migração.
O projeto será executado utilizando serviços da AWS, como AWS S3, AWS Backup e AWS DataSync.
A equipe da Ciclope Corporations será responsável por fornecer os acessos necessários e validar o funcionamento das soluções implementadas após a migração.

## Desafio

Garantir a migração de 5TB de dados de backup do ambiente on-premise para a nuvem AWS.
Configurar cópias dos dados nas regiões de São Paulo e Norte Virginia para garantir redundância e disponibilidade.
Implementar uma arquitetura de backup adequada para arquivos de vídeo, assegurando que os dados sejam acessíveis e seguros.
Decomissionar os dados locais após a confirmação de que todas as cópias foram migradas com sucesso e estão operacionais na nuvem.
Estabelecer um cronograma para a migração, garantindo que os dados sejam copiados antes do decommissionamento dos dados locais.

## Cenário apresentado

Atualmente, a Ciclope Corporations possui um ambiente on-premise em Recife, contendo aproximadamente 5TB de dados, principalmente arquivos de vídeo.
A empresa busca garantir cópias desses dados na nuvem AWS, com a necessidade de realizar a migração para duas regiões: São Paulo e Norte Virginia.
A equipe técnica da Ciclope Corporations é responsável pela gestão dos dados, mas pode necessitar de suporte adicional para a migração e configuração da nova arquitetura de backup.
O projeto inclui a configuração de backups em duas regiões, assegurando a redundância e a disponibilidade dos dados.
A Ciclope Corporations planeja decomissionar os dados locais após a confirmação de que todas as cópias foram migradas com sucesso e estão operacionais na nuvem.

## Arquitetura de solução

A solução será hospedada na AWS, utilizando uma conta fornecida pela Ciclope Corporations na região South America (São Paulo) e na região US East (Norte Virginia).
A infraestrutura será organizada em uma AWS VPC dedicada para o projeto.
    - A VPC será segmentada em sub-redes públicas e privadas, distribuídas entre múltiplas zonas de disponibilidade.
    - As sub-redes públicas hospedarão recursos de acesso externo, como o Amazon S3 para armazenamento de dados.
    - As sub-redes privadas hospedarão os serviços de backup e migração.
Os dados de 5TB serão migrados para o Amazon S3 utilizando o AWS DataSync, que facilitará a transferência eficiente e segura dos dados.
O AWS Backup será configurado para gerenciar backups automáticos dos dados armazenados no S3, garantindo a integridade e a disponibilidade das informações.
A arquitetura de backup incluirá cópias dos dados em ambas as regiões (São Paulo e Norte Virginia) para garantir redundância e recuperação em caso de falhas.
O decommissionamento dos dados locais será realizado após a validação de que todas as cópias foram migradas com sucesso e estão operacionais na nuvem.

## Escopo de atividades

- Planejamento do Projeto
    - Validar requisitos definidos em proposta
        - Validar requisitos técnicos 
        - Validar requisitos de negócio 
        - Validar escopos do projeto e entregáveis
    - Definir responsáveis pelas entregas do projeto 
    - Levantar parâmetros de configuração
        - Estruturas de nomes
        - Políticas de tags
        - Configurações de conectividade
        - Requisitos de segurança e acessos
        - Políticas de continuidade do negócio
    - Documentar o planejamento definido
- Migrar dados de 5TB para AWS
    - Utilizar AWS DataSync para transferir os dados do ambiente on-premise para o Amazon S3.
    - Garantir que a migração ocorra em duas regiões: São Paulo e Norte Virginia.
    - Validar a integridade dos dados após a migração.
- Configurar backups em duas regiões
    - Implementar AWS Backup para gerenciar backups automáticos dos dados armazenados no S3.
    - Configurar políticas de backup que garantam a recuperação dos dados em caso de falhas.
- Decomissionar dados locais
    - Realizar o decommissionamento dos dados locais após a validação de que todas as cópias foram migradas com sucesso.
- Gerenciamento do Projeto 
    - Inicialização
        - Handover Interno para equipe de Projetos (Reunião + Ata)
        - Kickoff com equipe da Ciclope Corporations (Apresentação + Reunião + Ata)

## Informações da Proposta Técnica

Versão da Proposta Técnica: V1.
A Proposta Técnica tem a validade de 60 dias, a partir da data da Proposta Comercial. Após essa data, o conteúdo técnico (Desafio, Arquitetura, Escopo, Critérios de Sucesso e/ou Resultados Esperados) não terá mais validade, sendo necessário atualizar a Proposta com a Equipe de Arquitetura/Pré-vendas da DAREDE.
Código Verificador Interno: ARCHPSALES20250617V1.

## Premissas

- A proposta foi desenvolvida baseando-se nas informações fornecidas pela CONTRATANTE através de: reuniões, trocas de e-mails compartilhados durante a fase de pré-vendas;
- A CONTRATANTE é responsável por todos seus dados, backups, softwares, plugins, códigos fonte, branchs e administração de seus repositórios. Todos os procedimentos necessários no caso de qualquer eventualidade que possa ocorrer e por se recuperar de qualquer falha durante a execução das atividades deste projeto, que não tenha relação direta com as mesmas;
- A CONTRATANTE será responsável por fornecer os acessos necessários e informações sobre o ambiente para que a contratada possa seguir com o atendimento do ticket/projeto;
- A CONTRATANTE fornecerá e se responsabilizará pela aquisição de todo o licenciamento de sistemas operacionais, software e plugins, além dos certificados digitais necessários, que não estiverem cobertos pelos modelos de licenciamento do Provedor de Nuvem ou disponibilizados de maneira simples para contratação em Marketplace, salvo quando expressamente definido como parte da proposta;
- A CONTRATANTE deverá designar uma pessoa para disponibilizar toda a informação necessária e contar com conhecimento técnico suficiente, para a boa condução das atividades ou solicitando internamente o que for preciso e atuar junto à equipe técnica da CONTRATADA se necessário, com agendamento à combinar.

## Pontos não contemplados por esta proposta

Exceto quando expressamente indicados nesta proposta, não estão inclusos no projeto quaisquer serviços de desenho, desenvolvimento, criação, teste, ajuste, configuração, troubleshooting ou quaisquer outros procedimentos ou serviços que tenham a ver com:
<!-- Geral -->
- A implantação dos serviços propostos de forma assistida, compartilhada e presencial;
- A execução de tarefas fora do planejamento, havendo a necessidade, deverá ser previamente acordado novas ações, cronogramas e prazos;
- Esta proposta não contempla escopos de Disaster Recovery;
<!-- Monitoramento -->
- A implementação de quaisquer monitoramentos customizados com ferramenta ou serviço nativo;
<!-- Desenvolvimento -->
- Desenvolvimento e/ou refatoração de código (Backend/Frontend, APIs, ETL, Infraestrutura, esteira de CI/CD);
- Instalação de quaisquer bibliotecas de dependência de código, runtimes ou pacotes de SDK para funcionamento da aplicação;
<!-- Banco de Dados -->
- Estruturação e análise de queries, regras de negócio, plano de execução, indexação, saneamento ou interações direta com os conteúdos de Bancos de dados;
- Migração e/ou implantação de servidores, aplicações e bancos de dados;
<!-- Infraestrutura e Redes -->
- Virtualização ou serviços de infraestrutura on-premise ou em outros provedores de nuvem não abordados no escopo desta proposta;
- Operação de equipamentos de Rede de data center, borda.

## Fatores influenciadores

### Fatores que influenciam cenários de custos
- A escolha da região AWS impacta significativamente os custos, com variações de preços entre as regiões de São Paulo e Norte Virginia.
- A possibilidade de reservas e savings plans para os serviços AWS contemplados na proposta pode reduzir os custos:
  - O tempo de compromisso de reservas e savings plans pode ser de 1 ou 3 anos.
  - O valor de entrada para reservas e savings plans (upfront) pode ser nenhum, parcial ou total.
- A decisão de utilizar serviços em Multi-AZ ou Single-AZ afetará a resiliência e os custos da infraestrutura.
- O uso de instâncias, serviços gerenciados ou soluções serverless influenciará a estrutura de custos e a escalabilidade.

### Premissas para cenários de custos
- Backups diários com 2% de alteração para volumes EBS associados a instâncias EC2.
- Backups diários com 5% de alteração para bancos de dados não gerenciados.
- Dois backups completos para bancos do RDS (um embutido no serviço, outro com armazenamento adicional).
- O custo de transferência de dados para fora do ambiente implementado será considerado no cálculo.

### Fatores de custos estimados que podem ser refinados
- O volume de tráfego de saída para a internet a partir da VPC pode variar conforme a demanda.
- O volume de dados distribuídos pelo CloudFront e sua distribuição regional afetará os custos.

## Resultados esperados

Garantir a migração de 5TB de dados de backup do ambiente on-premise para a nuvem AWS.
Configurar cópias dos dados nas regiões de São Paulo e Norte Virginia para garantir redundância e disponibilidade.
Implementar uma arquitetura de backup adequada para arquivos de vídeo, assegurando que os dados sejam acessíveis e seguros.
Decomissionar os dados locais após a confirmação de que todas as cópias foram migradas com sucesso e estão operacionais na nuvem.
Estabelecer um cronograma para a migração, garantindo que os dados sejam copiados antes do decommissionamento dos dados locais.

## Estimativa de horas

Horas setup 8x5 (mínimas): 120 horas
Horas setup 8x5 (médias): 180 horas

## Próximos passos

- Apresentação de proposta;
- Ajustes em cenários de custos de acordo com informações adicionais trazidas pelo cliente;
- Avaliação por parte do cliente de qual seria a forma de implementação mais alinhada com expectativas e necessidades;
- Escolha de cenário de implantação e eventual ajuste no volume de horas de trabalho de acordo com as atividades selecionadas.

