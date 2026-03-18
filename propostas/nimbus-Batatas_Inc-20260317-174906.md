Migração para AWS
======================================================================

Cliente: Batatas Inc.
Data: 2026-03-17T17:48:49.427435

## Formulário de Proposta Técnica



## Resumo

- A Batatas Inc. opera um e-commerce de batatas artesanais, com uma base de usuários de aproximadamente 50.000 usuários ativos mensais e picos de 5.000 acessos simultâneos durante promoções sazonais.
- A empresa deseja migrar sua infraestrutura legada, atualmente em servidores on-premise (Windows Server 2016, SQL Server 2014, aplicação .NET Framework 4.5), para a AWS, visando aumentar a escalabilidade e a segurança.
- Esta proposta refere-se a um projeto de migração para a AWS, que incluirá a configuração de um ambiente que atenda aos requisitos de compliance com a LGPD e a implementação de DR com RPO de 1h e RTO de 4h.
- O projeto será executado em uma nova conta AWS, na região South America (São Paulo).
- A Darede será responsável por criar os recursos em nuvem e executar a migração, enquanto a Batatas Inc. será responsável por fornecer os acessos necessários e validar o funcionamento das aplicações após a migração.

## Desafio

- Migrar servidores on-premise para a AWS, garantindo a continuidade das operações do e-commerce de batatas artesanais.
- Configurar a infraestrutura na AWS para suportar até 50.000 usuários ativos mensais e picos de 5.000 acessos simultâneos durante promoções sazonais.
- Implementar um banco de dados de aproximadamente 200GB no Amazon RDS, assegurando alta disponibilidade e performance.
- Estabelecer um plano de Disaster Recovery (DR) com RPO de 1h e RTO de 4h, utilizando serviços adequados da AWS.
- Implementar práticas de CI/CD para a automação do deploy da aplicação, utilizando AWS CodePipeline e AWS CodeDeploy.
- Configurar um sistema de monitoramento centralizado com Amazon CloudWatch para garantir a visibilidade e a saúde da infraestrutura.

## Cenário apresentado

- Atualmente, a Batatas Inc. opera um e-commerce de batatas artesanais, utilizando uma infraestrutura legada em servidores on-premise, que inclui:
    - 1x Servidor Windows Server 2016.
    - 1x Servidor SQL Server 2014 com um banco de dados de aproximadamente 200GB.
- A empresa possui cerca de 50.000 usuários ativos mensais, com picos de 5.000 acessos simultâneos durante promoções sazonais.
- A equipe técnica da Batatas Inc. é composta por profissionais com experiência em .NET e administração de servidores, mas a equipe é limitada em termos de recursos para gerenciar a migração e a nova infraestrutura na nuvem.
- O orçamento mensal estimado para a infraestrutura em nuvem é de R$15.000.
- A empresa precisa garantir compliance com a LGPD e implementar um plano de Disaster Recovery (DR) com RPO de 1h e RTO de 4h.
- A Batatas Inc. deseja também implementar práticas de CI/CD e um sistema de monitoramento centralizado para garantir a eficiência e a segurança da operação.

## Arquitetura de solução

- A solução será hospedada na AWS, utilizando uma conta fornecida pela Batatas Inc. na região South America (São Paulo).
- A infraestrutura será organizada em uma AWS VPC dedicada para o projeto.
    - A VPC será segmentada em sub-redes públicas e privadas distribuídas entre múltiplas zonas de disponibilidade.
    - As sub-redes públicas hospedarão recursos de acesso externo, como o Amazon API Gateway e Load Balancers.
    - As sub-redes privadas hospedarão os servidores de aplicação e banco de dados.
- Os servidores de aplicação serão migrados para instâncias do Amazon EC2, utilizando o AWS Application Migration Service para facilitar a replicação.
    - As instâncias EC2 serão configuradas com grupos de segurança apropriados para controlar o tráfego de entrada e saída.
- O banco de dados SQL Server será migrado para o Amazon RDS, garantindo alta disponibilidade e backup automático.
    - O RDS será configurado para suportar o volume de dados de aproximadamente 200GB e atender aos requisitos de performance.
- A implementação de Disaster Recovery (DR) será realizada utilizando o AWS Backup, com políticas de backup que garantam RPO de 1h e RTO de 4h.
- A automação do processo de deploy da aplicação será feita utilizando AWS CodePipeline e AWS CodeDeploy, implementando práticas de CI/CD.
- O monitoramento da infraestrutura será realizado utilizando Amazon CloudWatch, com alertas configurados para eventos críticos e métricas de performance.

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
- Provisionar estrutura de redes com AWS VPC (1x VPCs)
    - Definir propriedades de redes e conectividade
        - Planejar configurações de conectividade de contas, VPNs e Transit Gateway
        - Determinar CIDR Blocks e subnets
        - Definir regras de roteamento
    - Provisionar estrutura de redes
        - Criar VPC, subnets públicas e privadas
            - Configurar Internet Gateway e NAT Gateway
            - Configurar tabelas de rotas
        - Criar Network ACLs e configurar regras de Inbound e Outbound
        - Implementar VPC Endpoints
        - Estabelecer peering entre VPCs
- Migrar servidores com AWS Application Migration Service (1x Servidor Windows Server)
    - Identificar configurações do servidor de origem
        - Avaliar compatibilidade do servidor para a execução da replicação
        - Mapear tam

## Informações da Proposta Técnica

- Versão da Proposta Técnica: V1.
- A Proposta Técnica tem a validade de 60 dias, a partir da data da Proposta Comercial. Após essa data, o conteúdo técnico (Desafio, Arquitetura, Escopo, Critérios de Sucesso e/ou Resultados Esperados) não terá mais validade, sendo necessário atualizar a Proposta com a Equipe de Arquitetura/Pré-vendas da DAREDE.
- Código Verificador Interno: ARCHPSALES20250617V1.

## Premissas

- A proposta foi desenvolvida baseando-se nas informações fornecidas pela CONTRATANTE através de: reuniões, trocas de e-mails compartilhados durante a fase de pré-vendas;
- A CONTRATANTE é responsável por todos seus dados, backups, softwares, plugins, códigos fonte, branchs e administração de seus repositórios. Todos os procedimentos necessários no caso de qualquer eventualidade que possa ocorrer e por se recuperar de qualquer falha durante a execução das atividades deste projeto, que não tenha relação direta com as mesmas;
- A CONTRATANTE será responsável por fornecer os acessos necessários e informações sobre o ambiente para que a contratada possa seguir com o atendimento do ticket/projeto;
- A CONTRATANTE fornecerá e se responsabilizará pela aquisição de todo o licenciamento de sistemas operacionais, software e plugins, além dos certificados digitais necessários, que não estiverem cobertos pelos modelos de licenciamento do Provedor de Nuvem ou disponibilizados de maneira simples para contratação em Marketplace, salvo quando expressamente definido como parte da proposta;
- A CONTRATANTE deverá designar uma pessoa para disponibilizar toda a informação necessária e contar com conhecimento técnico suficiente, para a boa condução das atividades ou solicitando internamente o que for preciso e atuar junto à equipe técnica da CONTRATADA se necessário, com agendamento à combinar.

## Pontos não contemplados por esta proposta

Exceto quando expressamente indicados nesta proposta, não estão inclusos no projeto quaisquer serviços de desenho, desenvolvimento, criação, teste, ajuste, configuração, troubleshooting ou quaisquer outros procedimentos ou serviços que tenham a ver com:
- A implantação dos serviços propostos de forma assistida, compartilhada e presencial;
- A execução de tarefas fora do planejamento, havendo a necessidade, deverá ser previamente acordado novas ações, cronogramas e prazos;
- Esta proposta não contempla escopos de Disaster Recovery
- A implementação de quaisquer monitoramentos customizados com ferramenta ou serviço nativo;
- Desenvolvimento e/ou refatoração de código (Backend/Frontend, APIs, ETL, Infraestrutura, esteira de CI/CD);
- Instalação de quaisquer bibliotecas de dependência de código, runtimes ou pacotes de SDK para funcionamento da aplicação.
- Estruturação e análise de queries, regras de negócio, plano de execução, indexação, saneamento ou interações direta com os conteúdos de Bancos de dados;
- Migração e/ou implantação de servidores, aplicações e bancos de dados;
- Virtualização ou serviços de infraestrutura on-premise ou em outros provedores de nuvem não abordados no escopo desta proposta;
- Operação de equipamentos de Rede de data center, borda.

## Fatores influenciadores

### Fatores que influenciam cenários de custos
- A escolha da região AWS pode impactar significativamente os custos, com variações de preços entre as diferentes regiões.
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
- O volume de tráfego de saída para outras regiões.

## Resultados esperados

- A infraestrutura migrada para a AWS estará totalmente operacional, suportando até 50.000 usuários ativos mensais e picos de 5.000 acessos simultâneos durante promoções sazonais.
- O banco de dados de aproximadamente 200GB será configurado no Amazon RDS, garantindo alta disponibilidade e performance.
- Um plano de Disaster Recovery (DR) será implementado, com RPO de 1h e RTO de 4h, assegurando a continuidade das operações em caso de falhas.
- As práticas de CI/CD serão implementadas, permitindo automação no processo de deploy da aplicação, utilizando AWS CodePipeline e AWS CodeDeploy.
- O monitoramento centralizado da infraestrutura será realizado através do Amazon CloudWatch, com alertas configurados para eventos críticos e métricas de performance.
- A conformidade com a LGPD será garantida através da implementação de controles de segurança adequados e práticas de hardening nos servidores.

## Estimativa de horas

- Horas setup 8x5 (mínimas): 98 horas
- Horas setup 8x5 (médias): 151 horas

## Próximos passos

- Apresentação de proposta;
- Ajustes em cenários de custos de acordo com informações adicionais trazidas pelo cliente;
- Avaliação por parte do cliente de qual seria a forma de implementação mais alinhada com expectativas e necessidades;
- Escolha de cenário de implantação e eventual ajuste no volume de horas de trabalho de acordo com as atividades selecionadas.

