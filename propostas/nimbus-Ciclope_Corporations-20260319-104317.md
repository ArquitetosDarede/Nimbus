Backup de On-Premises
======================================================================

Cliente: Ciclope Corporations
Data: 19/03/2026

## 1. Formulário de Proposta Técnica

- A Ciclope Corporations é uma empresa que atua na produção e distribuição de conteúdo audiovisual, com um acervo significativo de arquivos de vídeo. 
- Com a necessidade de garantir a segurança e a disponibilidade dos seus dados, a Ciclope Corporations deseja migrar 5TB de dados de vídeo do seu ambiente on-premises em Recife para a nuvem AWS antes de decomissionar os dados locais. 
- Esta proposta refere-se a um projeto de backup que envolve a transferência de dados para a AWS e a configuração de backups em múltiplas regiões. 
- O projeto será executado em uma conta AWS fornecida pelo cliente, utilizando as regiões de São Paulo e Norte Virginia. 
- A Darede será responsável por configurar o AWS DataSync para a transferência dos dados, criar buckets no Amazon S3 para armazenamento e implementar o AWS Backup para gerenciar cópias de segurança, enquanto a Ciclope Corporations será responsável por fornecer os acessos necessários e validar o funcionamento das soluções implementadas.

## 2. Resumo

- A Ciclope Corporations é uma empresa que atua na produção e distribuição de conteúdo audiovisual, com um acervo significativo de arquivos de vídeo. 
- O projeto de Backup de On-Premises visa garantir a segurança e a disponibilidade dos dados, migrando 5TB de arquivos de vídeo do ambiente on-premises em Recife para a nuvem AWS. 
- A solução proposta envolve a utilização de AWS DataSync para a transferência dos dados, Amazon S3 para armazenamento e AWS Backup para gerenciar cópias de segurança em múltiplas regiões. 
- O projeto será executado em uma conta AWS fornecida pelo cliente, utilizando as regiões de São Paulo e Norte Virginia para garantir redundância geográfica. 
- A Darede será responsável pela implementação da solução, enquanto a Ciclope Corporations deverá fornecer os acessos necessários e validar o funcionamento das soluções implementadas.

## 3. Desafio

- Garantir a transferência de 5TB de dados de vídeo do ambiente on-premises em Recife para a AWS utilizando AWS DataSync.
- Configurar um bucket no Amazon S3 na região de São Paulo para armazenar os dados transferidos e habilitar a replicação cruzada para a região de Norte Virginia.
- Implementar o AWS Backup para gerenciar cópias de segurança dos dados armazenados no S3, assegurando a disponibilidade em caso de falhas regionais.
- Estabelecer políticas de segurança, incluindo criptografia em trânsito e em repouso, para proteger os dados durante a transferência e armazenamento.
- Validar a execução do projeto dentro das limitações de largura de banda e regulamentações de proteção de dados, garantindo que todos os dados estejam na nuvem antes do decomissionamento dos dados locais.

## 4. Cenário apresentado

- Atualmente, a Ciclope Corporations possui um ambiente on-premises em Recife, onde armazena aproximadamente 5TB de dados de vídeo.
- Os dados são armazenados em servidores locais, que precisam ser migrados para a nuvem para garantir segurança e disponibilidade.
- A equipe de infraestrutura da Ciclope Corporations é composta por profissionais especializados em tecnologia da informação, mas a quantidade exata de membros da equipe não foi especificada.
- O projeto de Backup de On-Premises requer a configuração de backups na AWS e a implementação de redundância geográfica para garantir a integridade dos dados.
- A Ciclope Corporations enfrenta limitações de largura de banda para a transferência de dados e deve atender a regulamentações de proteção de dados durante o processo de migração.
- A solução proposta envolve a utilização de AWS DataSync para a transferência dos dados, Amazon S3 para armazenamento e AWS Backup para gerenciar cópias de segurança em múltiplas regiões.

## 5. Arquitetura de solução

<!-- Criado pelo Nimbus -→
- A proposta de arquitetura para Ciclope Corporations envolve a transferência de 5TB de dados de vídeo de um ambiente on-premises em Recife para a AWS, com armazenamento em múltiplas regiões para garantir redundância geográfica.
- Utilizaremos AWS DataSync para a transferência inicial dos dados, configurando um agente DataSync no ambiente on-premises para transferir dados para um bucket S3 na região US East (Norte Virginia).
- Os dados transferidos serão armazenados em buckets do Amazon S3, que serão criados nas regiões de São Paulo e Norte Virginia, com replicação cruzada habilitada para garantir redundância geográfica.
- O AWS Backup será implementado para gerenciar cópias de segurança dos dados armazenados no S3, configurando planos de backup para realizar cópias regulares entre as regiões de São Paulo e Norte Virginia.
- A segurança dos dados será garantida através de controles de criptografia, utilizando TLS para criptografar dados durante a transferência e habilitando criptografia do lado do servidor com AWS KMS para todos os objetos no S3.
- O fluxo de dados será monitorado e gerenciado para assegurar que os dados sejam transferidos e armazenados de forma segura e eficiente, atendendo às regulamentações de proteção de dados.

| Título do Escopo | Horas Mínimas | Horas Médias | BU Autoridade |
|------------------|---------------|--------------|---------------|
| Planejamento do Projeto | 21 | 31 | PDM |
| Configurar AWS DataSync para transferência de dados | 40 | 60 | Data Transfer |
| Provisionar armazenamento no Amazon S3 | 20 | 30 | Storage |
| Implementar AWS Backup | 15 | 25 | Backup |
| Garantir segurança dos dados | 10 | 15 | Security |
| Realizar testes de validação | 30 | 50 | QA |
| Total | 136 | 211 |  |
</exemplo>

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
- Configurar AWS DataSync para transferência de dados
    - Instalar e configurar um agente DataSync no ambiente on-premises em Recife.
    - Criar uma tarefa de transferência para mover os dados para um bucket S3 na região US East (Norte Virginia).
- Provisionar armazenamento no Amazon S3
    - Criar buckets S3 nas regiões de São Paulo e Norte Virginia.
    - Habilitar replicação cruzada entre os buckets S3 para garantir redundância geográfica.
- Implementar AWS Backup
    - Configurar planos de backup para realizar cópias regulares dos dados entre as regiões de São Paulo e Norte Virginia.
- Garantir segurança dos dados
    - Implementar criptografia em trânsito utilizando TLS durante a transferência com AWS DataSync.
    - Habilitar criptografia em repouso com AWS KMS para todos os objetos no S3.
- Realizar testes de validação
    - Testar a integridade dos dados transferidos e a funcionalidade dos backups configurados.
    - Validar a conectividade e o acesso aos dados armazenados no S3.

| Título do Escopo | Horas Mínimas | Horas Médias | BU Autoridade |
|------------------|---------------|--------------|---------------|
| Planejamento do Projeto | 21 | 31 | PDM |
| Configurar AWS DataSync para transferência de dados | 40 | 60 | Data Transfer |
| Provisionar armazenamento no Amazon S3 | 20 | 30 | Storage |
| Implementar AWS Backup | 15 | 25 | Backup |
| Garantir segurança dos dados | 10 | 15 | Security |
| Realizar testes de validação | 30 | 50 | QA |
| Total | 136 | 211 |  |
</exemplo>

## 7. Informações da Proposta Técnica

- Versão da Proposta Técnica: V1.
- A Proposta Técnica tem a validade de 60 dias, a partir da data da Proposta Comercial. Após essa data, o conteúdo técnico (Desafio, Arquitetura, Escopo, Critérios de Sucesso e/ou Resultados Esperados) não terá mais validade, sendo necessário atualizar a Proposta com a Equipe de Arquitetura/Pré-vendas da DAREDE.
- Código Verificador Interno: ARCHPSALES20250617V1.

## 8. Premissas

- A proposta foi desenvolvida baseando-se nas informações fornecidas pela Ciclope Corporations através de: reuniões e trocas de e-mails compartilhados durante a fase de pré-vendas;
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

- Estruturação e análise de queries, regras de negócio, plano de execução, indexação, saneamento ou interações diretas com os conteúdos de bancos de dados;
- Migração e/ou implantação de servidores, aplicações e bancos de dados;

- Virtualização ou serviços de infraestrutura on-premise ou em outros provedores de nuvem não abordados no escopo desta proposta;
- Operação de equipamentos de rede de data center, borda, WAN, LAN ou WLAN;
- Criação e recuperação de backups que não estejam relacionados apenas a boas práticas de execução técnica das atividades contempladas neste projeto;
- A implementação de novos serviços em cloud ou ambiente diferente dos citados nessa proposta, exceto se documentados e aprovados pela Ciclope Corporations e DAREDE;
- A definição exata da quantidade de IOPS e throughput a serem utilizados nos discos rígidos dos servidores;

- Refinamento de regras ou políticas em appliances ou softwares de segurança;
- A implementação de um SOC 24x7 junto ao time de segurança da contratante;
- Administração e manutenção das regras de firewall personalizadas de acesso, bloqueio, whitelist e blacklist;

- A implementação de um NOC para monitoramento ativo 24x7 dos recursos de nuvem com ferramenta interna da contratada;

- Intermediação ou venda de licenças de software que sejam necessárias para a migração e implementação do ambiente e/ou recursos da solução no provedor de computação em nuvem de destino;

- A atualização automatizada ou manual da aplicação da Ciclope Corporations, que poderá ser acompanhada como atividade de sustentação para garantir o funcionamento da infraestrutura, dentro das atribuições técnicas da DAREDE, mas que é de responsabilidade da Ciclope Corporations;

## 10. Fatores influenciadores

### Fatores que influenciam cenários de custos
- A escolha da região impacta diretamente nos custos de transferência e armazenamento dos dados;
- A possibilidade de reservas e savings plans para os serviços AWS contemplados na proposta pode reduzir os custos operacionais;
  - O tempo de compromisso de reservas e savings plans pode ser de 1 ou 3 anos;
  - O valor de entrada para reservas e savings plans (upfront) pode ser nenhum, parcial ou total;
- A utilização de serviços em Multi-AZ ou Single-AZ afetará a disponibilidade e os custos associados;
- O uso de instâncias, serviços gerenciados ou serverless influenciará a estrutura de custos do projeto.

### Premissas para cenários de custos
- Considerar backups diários com 2% de alteração para volumes EBS associados a instâncias EC2;
- Considerar backups diários com 5% de alteração para bancos de dados não gerenciados;
- Incluir 2 backups completos para bancos do RDS (um embutido no serviço, outro com armazenamento adicional);
- Avaliar a data transfer out do ambiente implementado como padrão.

### Fatores de custos estimados que podem ser refinados
- O volume de tráfego de saída para a internet a partir da VPC pode variar e impactar os custos;
- O volume de dados distribuídos pelo CloudFront e sua distribuição regional afetará os custos de transferência;
- O volume de tráfego de saída para outras regiões da AWS deve ser considerado na estimativa de custos;
- O volume de dados alterado entre snapshots pode influenciar os custos de armazenamento;
- O volume de logs gerados com monitoramento de recursos, atividades e configurações também deve ser considerado.

### Fatores de custos não contemplados que envolvem análises à parte ou informações adicionais
- O volume de tráfego intrarregional (entre zonas de disponibilidade) pode impactar os custos de transferência;
- A quantidade de chamadas de API do S3 para diversas operações deve ser monitorada e considerada nos custos. 

### Custos Equipamentos, Licenças ou AWS
Todas as calculadoras representam uma estimativa de custos.
- [Titulo da calculadora] - [On-Demand / Savings Plans de 1 ano / 3 anos]
  - Região: [Região AWS]
  - Link calculadora: [URL da calculadora AWS]
  - Upfront cost: X,XXX.XX USD
  - Monthly cost: X,XXX.XX USD
  - Yearly cost: XX,XXX.XX USD

## 11. Resultados esperados

- A proposta de arquitetura para Ciclope Corporations envolve a transferência de 5TB de dados de vídeo de um ambiente on-premises em Recife para a AWS, com armazenamento em múltiplas regiões para garantir redundância geográfica.
- Utilizaremos AWS DataSync para a transferência inicial dos dados, configurando um agente DataSync no ambiente on-premises para transferir dados para um bucket S3 na região US East (Norte Virginia).
- Os dados transferidos serão armazenados em buckets do Amazon S3, que serão criados nas regiões de São Paulo e Norte Virginia, com replicação cruzada habilitada para garantir redundância geográfica.
- O AWS Backup será implementado para gerenciar cópias de segurança dos dados armazenados no S3, configurando planos de backup para realizar cópias regulares entre as regiões de São Paulo e Norte Virginia.
- A segurança dos dados será garantida através de controles de criptografia, utilizando TLS para criptografar dados durante a transferência e habilitando criptografia do lado do servidor com AWS KMS para todos os objetos no S3.
- O fluxo de dados será monitorado e gerenciado para assegurar que os dados sejam transferidos e armazenados de forma segura e eficiente, atendendo às regulamentações de proteção de dados.

## 12. Estimativa de horas

- Horas setup 8x5 (mínimas): 136 horas
- Horas setup 8x5 (médias): 211 horas

## 13. Próximos passos

- Apresentação de proposta para a Ciclope Corporations, detalhando a arquitetura e o plano de migração.
- Ajustes em cenários de custos de acordo com informações adicionais trazidas pelo cliente, incluindo a definição de orçamento e prazos.
- Avaliação por parte do cliente de qual seria a forma de implementação mais alinhada com suas expectativas e necessidades.
- Escolha de cenário de implantação e eventual ajuste no volume de horas de trabalho de acordo com as atividades selecionadas.
- Definição da data limite para a migração dos dados, garantindo que todos os dados sejam migrados antes do decomissionamento.
- Estabelecimento de reuniões regulares para acompanhamento do progresso do projeto e resolução de quaisquer questões que possam surgir durante a execução.

