Backup de On-Premises
======================================================================

Cliente: Ciclope Corporations
Data: 20/03/2026

## 1. Formulário de Proposta Técnica

- A Ciclope Corporations é uma empresa que atua no setor de produção e distribuição de conteúdo audiovisual. Com sede em Recife, a empresa possui um grande volume de dados, principalmente arquivos de vídeo, que precisam ser gerenciados de forma eficiente.
- O projeto visa garantir a migração de 5TB de dados de vídeo do ambiente on-premises para a nuvem AWS, assegurando cópias na região de São Paulo e Norte Virginia.
- Esta proposta refere-se à implementação de uma solução de backup utilizando serviços da AWS, incluindo AWS DataSync para a transferência de dados, Amazon S3 para armazenamento e AWS Backup para gerenciamento dos backups.
- O projeto será executado em uma conta AWS que será criada como parte do projeto, utilizando as regiões South America (São Paulo) e US East (Norte Virginia).
- A Darede será responsável por planejar e implementar a arquitetura de backup, enquanto a Ciclope Corporations será responsável por fornecer os acessos necessários e validar a integridade dos dados após a migração.

## 2. Resumo

- A Ciclope Corporations é uma empresa que atua no setor de produção e distribuição de conteúdo audiovisual, com sede em Recife. A empresa possui um grande volume de dados, principalmente arquivos de vídeo, que precisam ser gerenciados de forma eficiente.
- O projeto visa garantir a migração de 5TB de dados de vídeo do ambiente on-premises para a nuvem AWS, assegurando cópias na região de São Paulo e Norte Virginia.
- Esta proposta refere-se à implementação de uma solução de backup utilizando serviços da AWS, incluindo AWS DataSync para a transferência de dados, Amazon S3 para armazenamento e AWS Backup para gerenciamento dos backups.
- O projeto será executado em uma conta AWS que será criada como parte do projeto, utilizando as regiões South America (São Paulo) e US East (Norte Virginia).
- A Darede será responsável por planejar e implementar a arquitetura de backup, enquanto a Ciclope Corporations será responsável por fornecer os acessos necessários e validar a integridade dos dados após a migração.

## 3. Desafio

- Garantir a migração de 5TB de dados de vídeo do ambiente on-premises em Recife para a nuvem AWS.
- Implementar a solução de backup utilizando AWS DataSync para transferência eficiente dos dados.
- Armazenar os dados migrados no Amazon S3, garantindo alta durabilidade e disponibilidade.
- Configurar a replicação dos dados entre as regiões de São Paulo e Norte Virginia utilizando Amazon S3 Cross-Region Replication.
- Gerenciar e automatizar o processo de backup dos dados armazenados no S3 com AWS Backup.
- Decomissionar os dados locais após a validação da integridade e disponibilidade dos dados na nuvem.

## 4. Cenário apresentado

- Atualmente, a Ciclope Corporations possui um ambiente on-premises em Recife, onde armazena aproximadamente 5TB de dados, principalmente arquivos de vídeo.
- A empresa não possui uma infraestrutura de backup na nuvem, o que a impede de garantir a segurança e a disponibilidade dos dados.
- A equipe de infraestrutura é composta por profissionais com experiência em gerenciamento de dados, mas não possui expertise específica em soluções de nuvem.
- A Ciclope Corporations enfrenta limitações de largura de banda que podem impactar a transferência de grandes volumes de dados para a nuvem.
- A empresa está ciente das regulamentações de armazenamento de dados e busca uma solução que esteja em conformidade com essas normas.
- O projeto de migração para a nuvem visa não apenas a transferência dos dados, mas também a decomissão dos dados locais após a validação da integridade e disponibilidade na AWS.

## 5. Arquitetura de solução

- A proposta de arquitetura para Ciclope Corporations envolve a utilização de serviços AWS para realizar o backup de 5TB de dados de vídeo de um ambiente on-premises em Recife, garantindo cópias na região de São Paulo e Norte Virginia.
- A solução utiliza AWS DataSync para transferência eficiente dos dados, implantando agentes DataSync em VMware no local para minimizar a latência de rede.
- Os dados serão armazenados no Amazon S3, utilizando a classe de armazenamento S3 Standard para garantir alta durabilidade e disponibilidade.
- A replicação dos dados entre as regiões de São Paulo e Norte Virginia será configurada utilizando Amazon S3 Cross-Region Replication, com regras de replicação habilitadas.
- O gerenciamento e a automação do processo de backup dos dados armazenados no S3 serão realizados com AWS Backup, criando planos de backup com regras de frequência diária e retenção de 30 dias.
- A segurança dos dados será garantida através de criptografia em repouso utilizando AWS KMS para gerenciar chaves de criptografia.
- O controle de acesso aos serviços AWS será implementado através de políticas de IAM, restringindo o acesso a usuários autorizados.
- O monitoramento do processo de replicação de dados será realizado habilitando métricas de replicação no S3 e monitorando via Amazon CloudWatch.

## 6. Escopo de atividades

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
- Implementar a solução de backup com AWS DataSync
    - Implantar agentes DataSync em VMware no local para transferência de dados.
    - Configurar a transferência de 5TB de dados de vídeo do ambiente on-premises para o Amazon S3.
- Armazenar dados no Amazon S3
    - Criar buckets no Amazon S3 na região South America (São Paulo).
    - Configurar a classe de armazenamento S3 Standard para os dados.
- Configurar replicação de dados
    - Implementar Amazon S3 Cross-Region Replication para replicar dados para a região US East (Norte Virginia).
    - Configurar regras de replicação com métricas habilitadas.
- Gerenciar backups com AWS Backup
    - Criar planos de backup com regras de frequência diária e retenção de 30 dias.
    - Automatizar o processo de backup dos dados armazenados no S3.
- Validar a integridade dos dados
    - Realizar testes para garantir que todos os dados foram migrados e estão acessíveis.
    - Decomissionar dados locais após a validação da migração.

| Título do Escopo | Horas Mínimas | Horas Médias | BU Autoridade |
|------------------|---------------|--------------|----|
| Planejamento do Projeto | 21 | 31 | PDM |
| Implementar a solução de backup com AWS DataSync | 40 | 60 | Data Management |
| Armazenar dados no Amazon S3 | 15 | 25 | Data Management |
| Configurar replicação de dados | 20 | 30 | Data Management |
| Gerenciar backups com AWS Backup | 25 | 35 | Data Management |
| Validar a integridade dos dados | 30 | 50 | Data Management |
| Total | 151 | 231 |  |

## 7. Informações da Proposta Técnica

- Versão da Proposta Técnica: V1
- A Proposta Técnica tem a validade de 60 dias, a partir da data da Proposta Comercial. Após essa data, o conteúdo técnico (Desafio, Arquitetura, Escopo, Critérios de Sucesso e/ou Resultados Esperados não terão mais validade), sendo necessário atualizar a Proposta com a Equipe de Arquitetura/Pré-vendas da DAREDE.
- Código Verificador Interno: ARCHPSALES20250617V1

## 8. Premissas

- A proposta foi desenvolvida baseando-se nas informações fornecidas pela Ciclope Corporations através de: reuniões, trocas de e-mails compartilhados durante a fase de pré-vendas;
- A Ciclope Corporations é responsável por todos seus dados, backups, softwares, plugins, códigos fonte, branchs e administração de seus repositórios. Todos os procedimentos necessários no caso de qualquer eventualidade que possa ocorrer e por se recuperar de qualquer falha durante a execução das atividades deste projeto, que não tenha relação direta com as mesmas;
- A Ciclope Corporations será responsável por fornecer os acessos necessários e informações sobre o ambiente para que a contratada possa seguir com o atendimento do ticket/projeto;
- A Ciclope Corporations fornecerá e se responsabilizará pela aquisição de todo o licenciamento de sistemas operacionais, software e plugins, além dos certificados digitais necessários, que não estiverem cobertos pelos modelos de licenciamento do Provedor de Nuvem ou disponibilizados de maneira simples para contratação em Marketplace, salvo quando expressamente definido como parte da proposta;
- A Ciclope Corporations deverá designar uma pessoa para disponibilizar toda a informação necessária e contar com conhecimento técnico suficiente, para a boa condução das atividades ou solicitando internamente o que for preciso e atuar junto à equipe técnica da contratada se necessário, com agendamento à combinar entre as partes;
- Em fase de Projeto, a Ciclope Corporations e a contratada realizarão reuniões estratégicas e de planejamento, utilizando as horas de Setup descritas nessa proposta. Caso as atividades planejadas ultrapassem as horas contratadas como "Setup do Projeto", poderão ser contratadas horas adicionais de acordo com a necessidade, com o alinhamento prévio e aprovação da Ciclope Corporations e da contratada;
- Horas de projeto serão utilizadas para planejamento, reuniões, alinhamentos e definição de configurações;
- Todas as atividades seguirão cronograma estabelecido entre as partes após a ativação do contrato;
- A Ciclope Corporations e seus colaboradores conhecem e estão de acordo com o modelo de responsabilidade compartilhada da AWS;
- Os custos de infraestrutura apresentados devem ser considerados como uma estimativa e podem variar conforme o uso real dos serviços;
- Em caso de adoção de Savings Plans, fica definido que os custos determinados pela política de Savings só serão válidos após a ativação do comprometimento através da console da AWS;

## 9. Pontos não contemplados por esta proposta

Exceto quando expressamente indicados nesta proposta, não estão inclusos no projeto quaisquer serviços de desenho, desenvolvimento, criação, teste, ajuste, configuração, troubleshooting ou quaisquer outros procedimentos ou serviços que tenham a ver com:

- A implantação dos serviços propostos de forma assistida, compartilhada e presencial;
- A execução de tarefas fora do planejamento, havendo a necessidade, deverá ser previamente acordado novas ações, cronogramas e prazos;
- Esta proposta não contempla escopos de Disaster Recovery;

- A implementação de quaisquer monitoramentos customizados com ferramenta ou serviço nativo;

- Desenvolvimento e/ou refatoração de código (Backend/Frontend, APIs, ETL, Infraestrutura, esteira de CI/CD);
- Instalação de quaisquer bibliotecas de dependência de código, runtimes ou pacotes de SDK para funcionamento da aplicação;

- Estruturação e análise de queries, regras de negócio, plano de execução, indexação, saneamento ou interações diretas com os conteúdos de Bancos de dados;
- Migração e/ou implantação de servidores, aplicações e bancos de dados;

- Virtualização ou serviços de infraestrutura on-premise ou em outros provedores de nuvem não abordados no escopo desta proposta;
- Operação de equipamentos de Rede de data center, borda, WAN, LAN ou WLAN;
- Criação e recuperação de Backups que não estejam relacionados apenas a boas práticas de execução técnica das atividades contempladas neste projeto;
- A implementação de novos serviços em cloud ou ambiente diferente dos citados nessa proposta, exceto se documentados e aprovados pela Ciclope Corporations e DAREDE;
- A definição exata da quantidade de IOPS e throughput a serem utilizados nos discos rígidos dos servidores;

- Refinamento de regras ou políticas em appliances ou softwares de segurança;
- A implementação de um SOC 24x7 junto ao time de segurança da contratante;
- Administração e manutenção das regras de Firewall personalizadas de acesso, bloqueio, whitelist e backlist;

- A implementação de um NOC para monitoramento ativo 24x7 dos recursos de nuvem com ferramenta interna da contratada;

- Intermediação ou venda de licenças de Software que sejam necessárias para a migração e implementação do ambiente e/ou recursos da solução no provedor de computação em nuvem de destino;

- A atualização automatizada ou manual da aplicação da Ciclope Corporations, que poderá ser acompanhada como atividade de sustentação para garantir o funcionamento da infraestrutura, dentro das atribuições técnicas da DAREDE, mas que é de responsabilidade da Ciclope Corporations;

## 10. Fatores influenciadores

### Fatores que influenciam cenários de custos
- A escolha da região impacta diretamente nos custos de transferência e armazenamento dos dados;
- A possibilidade de reservas e savings plans para os serviços AWS contemplados na proposta pode reduzir os custos operacionais;
  - O tempo de compromisso de reservas e savings plans pode ser de 1 ou 3 anos;
  - O valor de entrada para reservas e savings plans (upfront) pode ser nenhum, parcial ou total;
- A utilização de serviços em Multi-AZ ou Single-AZ pode influenciar a disponibilidade e os custos associados;
- O uso de instâncias, serviços gerenciados ou serverless pode afetar a estrutura de custos do projeto.

### Premissas para cenários de custos
- Considera-se que os backups diários terão uma alteração de 2% para volumes EBS associados a instâncias EC2;
- Considera-se que os backups diários terão uma alteração de 5% para bancos de dados não gerenciados;
- Para bancos do RDS, serão considerados 2 backups completos (um embutido no serviço e outro com armazenamento adicional);
- A transferência de dados para fora do ambiente implementado será considerada conforme o padrão.

### Fatores de custos estimados que podem ser refinados
- O volume de tráfego de saída para a internet a partir da VPC pode impactar os custos finais;
- O volume de dados distribuídos pelo CloudFront e sua distribuição regional pode influenciar os custos de transferência;
- O volume de tráfego de saída para outras regiões da AWS deve ser monitorado para evitar surpresas financeiras;
- O volume de dados alterado entre snapshots pode afetar os custos de armazenamento.

### Fatores de custos não contemplados que envolvem análises à parte ou informações adicionais
- O volume de tráfego intrarregional (entre zonas de disponibilidade) pode não estar totalmente considerado nos custos estimados;
- A quantidade de chamadas de API do S3 para diversas operações pode impactar os custos operacionais.

### Custos Equipamentos, Licenças ou AWS
Todas as calculadoras representam uma estimativa de custos.
- [Titulo da calculadora] - [On-Demand / Savings Plans de 1 ano / 3 anos]
  - Região: [Região AWS]
  - Link calculadora: [URL da calculadora AWS]
  - Upfront cost: X,XXX.XX USD
  - Monthly cost: X,XXX.XX USD
  - Yearly cost: XX,XXX.XX USD

## 11. Resultados esperados

- A proposta de arquitetura para Ciclope Corporations envolve a utilização de serviços AWS para realizar o backup de 5TB de dados de vídeo de um ambiente on-premises em Recife, garantindo cópias na região de São Paulo e Norte Virginia.
- A solução utiliza AWS DataSync para transferência eficiente dos dados, implantando agentes DataSync em VMware no local para minimizar a latência de rede.
- Os dados serão armazenados no Amazon S3, utilizando a classe de armazenamento S3 Standard para garantir alta durabilidade e disponibilidade.
- A replicação dos dados entre as regiões de São Paulo e Norte Virginia será configurada utilizando Amazon S3 Cross-Region Replication, com regras de replicação habilitadas.
- O gerenciamento e a automação do processo de backup dos dados armazenados no S3 serão realizados com AWS Backup, criando planos de backup com regras de frequência diária e retenção de 30 dias.
- A segurança dos dados será garantida através de criptografia em repouso utilizando AWS KMS para gerenciar chaves de criptografia.
- O controle de acesso aos serviços AWS será implementado através de políticas de IAM, restringindo o acesso a usuários autorizados.
- O monitoramento do processo de replicação de dados será realizado habilitando métricas de replicação no S3 e monitorando via Amazon CloudWatch.
- A criptografia em trânsito será habilitada durante a transferência de dados com AWS DataSync, garantindo a segurança dos dados sensíveis.
- A conformidade com as regulamentações de armazenamento de dados e a LGPD será assegurada, evitando penalidades legais e danos à reputação.

## 12. Estimativa de horas

- Horas setup 8x5 (mínimas): 151 horas
- Horas setup 8x5 (médias): 231 horas

## 13. Próximos passos

- Apresentação de proposta para a Ciclope Corporations, detalhando a arquitetura e o plano de migração.
- Ajustes em cenários de custos de acordo com informações adicionais trazidas pelo cliente.
- Avaliação por parte da Ciclope Corporations sobre a forma de implementação mais alinhada com suas expectativas e necessidades.
- Escolha de cenário de implantação e eventual ajuste no volume de horas de trabalho de acordo com as atividades selecionadas.
- Definição do prazo para a conclusão do projeto e alinhamento do orçamento disponível para garantir a viabilidade da proposta.

