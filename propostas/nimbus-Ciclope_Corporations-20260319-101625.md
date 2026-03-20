Backup de On-Premises
======================================================================

Cliente: Ciclope Corporations
Data: 19/03/2026

## 1. Formulário de Proposta Técnica

- A Ciclope Corporations é uma empresa que atua no setor de tecnologia, especializada em soluções de armazenamento e gerenciamento de dados. Com sede em Recife, a empresa possui uma grande quantidade de dados, principalmente arquivos de vídeo, que precisam ser gerenciados de forma eficiente.
- O projeto visa garantir a migração de 5TB de dados de Recife para a nuvem AWS, assegurando cópias em duas regiões: São Paulo e Norte da Virgínia.
- Esta proposta refere-se a um projeto de backup de dados on-premises, que inclui a transferência e armazenamento seguro na AWS.
- O projeto será executado em uma conta AWS que será criada como parte do projeto, utilizando as regiões sa-east-1 (São Paulo) e us-east-1 (Norte da Virgínia).
- A Darede será responsável por configurar a transferência de dados utilizando AWS DataSync, armazenar os dados no AWS S3 e gerenciar os backups com AWS Backup, enquanto a Ciclope Corporations será responsável por fornecer os acessos necessários e validar a integridade dos dados após a migração.

## 2. Resumo

- A Ciclope Corporations é uma empresa que atua no setor de tecnologia, especializada em soluções de armazenamento e gerenciamento de dados. Com sede em Recife, a empresa possui uma grande quantidade de dados, principalmente arquivos de vídeo, que precisam ser gerenciados de forma eficiente.
- O projeto tem como objetivo garantir a migração de 5TB de dados de Recife para a nuvem AWS, assegurando cópias em duas regiões: São Paulo e Norte da Virgínia.
- A proposta envolve a transferência dos dados utilizando AWS DataSync, armazenamento no AWS S3 e gerenciamento de backups com AWS Backup.
- O projeto será executado em uma conta AWS que será criada como parte do projeto, utilizando as regiões sa-east-1 (São Paulo) e us-east-1 (Norte da Virgínia).
- A Darede será responsável por configurar a transferência de dados e gerenciar os backups, enquanto a Ciclope Corporations será responsável por fornecer os acessos necessários e validar a integridade dos dados após a migração.

## 3. Desafio

- Garantir a transferência de 5TB de dados de Recife para a nuvem AWS utilizando AWS DataSync.
- Armazenar os dados migrados no AWS S3, com cópias em duas regiões: São Paulo e Norte da Virgínia.
- Configurar políticas de backup no AWS Backup para assegurar a retenção e recuperação dos dados armazenados.
- Documentar todo o processo de migração, incluindo as etapas de transferência e configuração de backups.
- Decomissionar os dados locais após a validação da integridade e disponibilidade dos dados na nuvem.

## 4. Cenário apresentado

- Atualmente, a Ciclope Corporations possui 5TB de dados armazenados localmente em Recife, principalmente arquivos de vídeo.
- A infraestrutura atual não possui redundância geográfica, o que limita a segurança e a recuperação de desastres.
- A equipe de infraestrutura do cliente é composta por 10 profissionais, especializados em gerenciamento de dados e suporte técnico.
- Não há uma estratégia de backup implementada para os dados locais, o que representa um risco significativo para a integridade das informações.
- A empresa enfrenta limitações de largura de banda durante a transferência de dados, o que pode impactar o tempo necessário para a migração para a nuvem.
- A conformidade com regulamentações de dados, como a LGPD, é uma preocupação importante que deve ser considerada durante o processo de migração.

## 5. Arquitetura de solução

- A solução será hospedada na AWS, utilizando uma conta que será criada como parte do projeto.
- A transferência de dados de Recife para a AWS será realizada utilizando o AWS DataSync.
    - Serão configurados agentes DataSync on-premises para a transferência inicial dos 5TB de dados.
    - Os dados serão transferidos inicialmente para a região sa-east-1 (São Paulo).
- Após a transferência, os dados serão armazenados no AWS S3.
    - Utilizará S3 Standard para dados frequentemente acessados e S3 Glacier para arquivamento.
    - A replicação entre regiões garantirá cópias dos dados na região us-east-1 (Norte da Virgínia).
- O gerenciamento de backups será realizado com o AWS Backup.
    - Serão configuradas políticas de backup para garantir a retenção e recuperação dos dados armazenados no S3.
- A segurança dos dados será garantida através de criptografia em repouso e em trânsito.
    - Utilizará AWS KMS para criptografia de dados em S3 e TLS para dados em trânsito.
- O controle de acesso será gerenciado por meio de políticas de IAM, restringindo o acesso apenas a usuários autorizados.

## 6. Escopo de atividades

<!-- Criado pelo Nimbus -→
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
- Transferir dados de Recife para a AWS utilizando AWS DataSync
    - Configurar agentes DataSync on-premises para a transferência inicial dos 5TB de dados.
    - Realizar a transferência dos dados para a região sa-east-1 (São Paulo).
- Armazenar os dados no AWS S3
    - Utilizar S3 Standard para dados frequentemente acessados e S3 Glacier para arquivamento.
    - Configurar a replicação dos dados para a região us-east-1 (Norte da Virgínia).
- Configurar políticas de backup no AWS Backup
    - Estabelecer políticas de retenção e recuperação de dados armazenados no S3.
- Validar a integridade dos dados após a migração
    - Realizar testes para garantir que todos os dados foram transferidos corretamente e estão acessíveis.
- Decomissionar dados locais após a validação
    - Garantir que todos os dados estejam na nuvem AWS antes de remover os dados locais.

| Título do Escopo | Horas Mínimas | Horas Médias | BU Autoridade |
|------------------|---------------|--------------|----|
| Planejamento do Projeto | 21 | 31 | PDM |
| Transferir dados para AWS | 40 | 60 | Data Migration |
| Armazenar dados no AWS S3 | 30 | 50 | Data Storage |
| Configurar políticas de backup | 20 | 30 | Backup Management |
| Validar integridade dos dados | 15 | 25 | Data Validation |
| Decomissionar dados locais | 10 | 15 | Data Management |
| Total | 136 | 211 |  |
</exemplo>

## 7. Informações da Proposta Técnica

- Versão da Proposta Técnica: V1.
- A Proposta Técnica tem a validade de 60 dias, a partir da data da Proposta Comercial. Após essa data, o conteúdo técnico (Desafio, Arquitetura, Escopo, Critérios de Sucesso e/ou Resultados Esperados não terão mais validade), sendo necessário atualizar a Proposta com a Equipe de Arquitetura/Pré-vendas da DAREDE.
- Código Verificador Interno: ARCHPSALES20250617V1.

## 8. Premissas

- A proposta foi desenvolvida baseando-se nas informações fornecidas pela Ciclope Corporations através de: reuniões, trocas de e-mails compartilhados durante a fase de pré-vendas;
- A Ciclope Corporations é responsável por todos seus dados, backups, softwares, plugins, códigos fonte, branchs e administração de seus repositórios. Todos os procedimentos necessários no caso de qualquer eventualidade que possa ocorrer e por se recuperar de qualquer falha durante a execução das atividades deste projeto, que não tenha relação direta com as mesmas;
- A Ciclope Corporations será responsável por fornecer os acessos necessários e informações sobre o ambiente para que a contratada possa seguir com o atendimento do ticket/projeto;
- A Ciclope Corporations fornecerá e se responsabilizará pela aquisição de todo o licenciamento de sistemas operacionais, software e plugins, além dos certificados digitais necessários, que não estiverem cobertos pelos modelos de licenciamento do Provedor de Nuvem ou disponibilizados de maneira simples para contratação em Marketplace, salvo quando expressamente definido como parte da proposta;
- A Ciclope Corporations deverá designar uma pessoa para disponibilizar toda a informação necessária e contar com conhecimento técnico suficiente, para a boa condução das atividades ou solicitando internamente o que for preciso e atuar junto à equipe técnica da contratada se necessário, com agendamento à combinar entre as partes;
- Em fase de Projeto, a Ciclope Corporations e a contratada realizarão reuniões estratégicas e de planejamento, utilizando as horas de Setup descritas nessa proposta; caso as atividades planejadas ultrapassem as horas contratadas como "Setup do Projeto", poderão ser contratadas horas adicionais de acordo com a necessidade, com o alinhamento prévio e aprovação da Ciclope Corporations e da contratada;
- Horas de projeto serão utilizadas para planejamento, reuniões, alinhamentos e definição de configurações;
- Todas as atividades seguirão cronograma estabelecido entre as partes após a ativação do contrato;
- A Ciclope Corporations e seus colaboradores conhecem e estão de acordo com o modelo de responsabilidade compartilhada da AWS;
- Os custos de infraestrutura apresentados devem ser considerados como uma estimativa e podem variar conforme o uso real dos serviços;
- Em caso de adoção de Savings Plans, fica definido que os custos determinados pela política de Savings só serão válidos após a ativação do comprometimento através da console da AWS;

## 9. Pontos não contemplados por esta proposta

### Pontos não contemplados por esta proposta

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
- Estruturação e análise de queries, regras de negócio, plano de execução, indexação, saneamento ou interações diretas com os conteúdos de bancos de dados;
- Migração e/ou implantação de servidores, aplicações e bancos de dados;
<!-- Infraestrutura e Redes -->
- Virtualização ou serviços de infraestrutura on-premise ou em outros provedores de nuvem não abordados no escopo desta proposta;
- Operação de equipamentos de rede de data center, borda, WAN, LAN ou WLAN;
- Criação e recuperação de backups que não estejam relacionados apenas a boas práticas de execução técnica das atividades contempladas neste projeto;
- A implementação de novos serviços em cloud ou ambiente diferente dos citados nessa proposta, exceto se documentados e aprovados pela Ciclope Corporations e DAREDE;
- A definição exata da quantidade de IOPS e throughput a serem utilizados nos discos rígidos dos servidores;
<!-- Segurança -->
- Refinamento de regras ou políticas em appliances ou softwares de segurança;
- A implementação de um SOC 24x7 junto ao time de segurança da contratante;
- Administração e manutenção das regras de firewall personalizadas de acesso, bloqueio, whitelist e blacklist;
<!-- Service Desk -->
- A implementação de um NOC para monitoramento ativo 24x7 dos recursos de nuvem com ferramenta interna da contratada;
<!-- Licenciamento -->
- Intermediação ou venda de licenças de software que sejam necessárias para a migração e implementação do ambiente e/ou recursos da solução no provedor de computação em nuvem de destino;
<!-- Sustentação -->
- A atualização automatizada ou manual da aplicação da Ciclope Corporations, que poderá ser acompanhada como atividade de sustentação para garantir o funcionamento da infraestrutura, dentro das atribuições técnicas da DAREDE, mas que é de responsabilidade da Ciclope Corporations;

## 10. Fatores influenciadores

### Fatores que influenciam cenários de custos
- A escolha da região impacta diretamente nos custos de transferência e armazenamento dos dados.
- A possibilidade de reservas e savings plans para os serviços AWS contemplados na proposta pode reduzir os custos.
  - O tempo de compromisso de reservas e savings plans pode ser de 1 ou 3 anos.
  - O valor de entrada para reservas e savings plans pode ser nenhum, parcial ou total.
- A utilização de serviços em Multi-AZ ou Single-AZ pode afetar a disponibilidade e os custos.
- O uso de instâncias, serviços gerenciados ou serverless também influencia os custos totais do projeto.

### Premissas para cenários de custos
- Os backups diários terão uma alteração estimada de 2% para volumes EBS associados a instâncias EC2.
- Os backups diários terão uma alteração estimada de 5% para bancos de dados não gerenciados.
- Serão realizados 2 backups completos para bancos do RDS, sendo um embutido no serviço e outro com armazenamento adicional.
- A transferência de dados para fora do ambiente implementado será considerada conforme o padrão.

### Fatores de custos estimados que podem ser refinados
- O volume de tráfego de saída para a internet a partir da VPC pode variar e impactar os custos.
- O volume de dados distribuídos pelo CloudFront e sua distribuição regional influenciam os custos operacionais.
- O volume de tráfego de saída para outras regiões da AWS pode afetar o custo total do projeto.
- O volume de dados alterado entre snapshots pode impactar os custos de armazenamento.
- O volume de logs gerados com monitoramento de recursos, atividades e configurações pode influenciar os custos.

### Fatores de custos não contemplados que envolvem análises à parte ou informações adicionais
- O volume de tráfego intrarregional (entre zonas de disponibilidade) pode não estar incluído nas estimativas.
- A quantidade de chamadas de API do S3 para diversas operações pode impactar os custos, mas não está detalhada nas estimativas.

### Custos Equipamentos, Licenças ou AWS
Todas as calculadoras representam uma estimativa de custos.
- [Titulo da calculadora] - [On-Demand / Savings Plans de 1 ano / 3 anos]
  - Região: [Região AWS]
  - Link calculadora: [URL da calculadora AWS]
  - Upfront cost: X,XXX.XX USD
  - Monthly cost: X,XXX.XX USD
  - Yearly cost: XX,XXX.XX USD

## 11. Resultados esperados

### Resultados esperados

- Todos os 5TB de dados migrados de Recife para a nuvem AWS utilizando AWS DataSync.
- Os dados estarão armazenados no AWS S3, com cópias em duas regiões: São Paulo e Norte da Virgínia.
- As políticas de backup configuradas no AWS Backup garantirão a retenção e recuperação dos dados armazenados.
- A integridade dos dados será validada após a migração, assegurando que todos os dados estejam acessíveis e corretos.
- Os dados locais serão decommissionados somente após a confirmação de que todos os dados estão na nuvem AWS e funcionando corretamente.

### Critérios de sucesso:
- Redução de custos operacionais em até 20% após a migração para a nuvem.
- Aumento da disponibilidade dos dados, com tempo de inatividade não superior a 1% ao longo do ano.
- Validação da integridade dos dados com uma taxa de sucesso de 100% após a migração.
- Conformidade com a LGPD garantida, evitando penalidades legais.

## 12. Estimativa de horas

- Horas setup 8x5 (mínimas): 136 horas
- Horas setup 8x5 (médias): 211 horas

## 13. Próximos passos

- Apresentação da proposta para a Ciclope Corporations, detalhando a arquitetura e o plano de migração.
- Ajustes em cenários de custos de acordo com informações adicionais trazidas pelo cliente, como orçamento e prazos.
- Avaliação por parte da Ciclope Corporations de qual seria a forma de implementação mais alinhada com suas expectativas e necessidades.
- Escolha do cenário de implantação e eventual ajuste no volume de horas de trabalho de acordo com as atividades selecionadas.
- Definição de um cronograma para a execução das atividades, incluindo datas para a migração e validação dos dados.

