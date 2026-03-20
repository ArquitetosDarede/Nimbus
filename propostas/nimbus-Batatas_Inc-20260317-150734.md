PROPOSTA TECNICA - MIGRACAO PARA AWS
======================================================================

Cliente: Batatas Inc.
Data: 2026-03-17T15:07:04.071392

## Formulário de Proposta Técnica

A proposta visa a migração de um servidor Windows Server 2019, atualmente em ambiente on-premises em São Paulo, para a AWS EC2 utilizando o AWS Application Migration Service (AWS MGN). O objetivo é garantir a continuidade dos negócios com um plano de rollback em caso de falhas.

**Cliente**: Batatas Inc.  
**Contato**: Joao Moreira  
**Email**: jmoreira@batatasinc.com  
**Telefone**: +55 11 97433-3333  

**Requisitos de Negócio**:
- Migrar servidor Windows Server 2019 para AWS EC2.
- Garantir continuidade de negócios com rollback em caso de falhas.

**Requisitos Técnicos**:
- Instância equivalente ao servidor atual com 32GB RAM e 16 vCPUs.
- Integração com Active Directory on-premises.

**Tecnologias Utilizadas**:
- AWS EC2
- AWS MGN
- AWS Application Migration Service

**Cronograma**: 17 dias  
**Orçamento**: R$ 5.000,00  

**Restrições**:
- Janela de manutenção aos finais de semana.
- Plano de contingência com rollback para o servidor atual.

## Resumo

A proposta visa a migração de um servidor Windows Server 2019, atualmente em ambiente on-premises em São Paulo, para a AWS EC2 utilizando o AWS Application Migration Service (AWS MGN). O objetivo é garantir a continuidade dos negócios com um plano de rollback em caso de falhas.

**Cliente**: Batatas Inc.  
**Contato**: Joao Moreira  
**Email**: jmoreira@batatasinc.com  
**Telefone**: +55 11 97433-3333  

**Requisitos de Negócio**:
- Migrar servidor Windows Server 2019 para AWS EC2.
- Garantir continuidade de negócios com rollback em caso de falhas.

**Requisitos Técnicos**:
- Instância equivalente ao servidor atual com 32GB RAM e 16 vCPUs.
- Integração com Active Directory on-premises.

**Tecnologias Utilizadas**:
- AWS EC2
- AWS MGN
- AWS Application Migration Service

**Cronograma**: 17 dias  
**Orçamento**: R$ 5.000,00  

**Restrições**:
- Janela de manutenção aos finais de semana.
- Plano de contingência com rollback para o servidor atual.

## Desafio

A arquitetura proposta para a migração do servidor Windows Server 2019 da Batatas Inc. para a AWS EC2 é composta por uma série de componentes e serviços que garantem a continuidade dos negócios e a integração com o Active Directory on-premises.

**Topologia de Serviços:**
1. **AWS EC2**: A instância EC2 será configurada com 32GB de RAM e 16 vCPUs, equivalente ao servidor atual. A configuração incluirá:
   - **Grupos de Segurança**: Para controlar o tráfego de entrada e saída da instância, permitindo apenas o tráfego necessário.
   - **Subnets**: A instância será alocada em uma subnet apropriada para garantir a segurança e a conectividade.
   - **Elastic IP**: Para garantir um endereço IP fixo durante a migração.

2. **AWS MGN (Application Migration Service)**: Este serviço será utilizado para configurar o replication server, permitindo a replicação contínua de 2TB de dados para uma área de staging na AWS. O AWS MGN facilitará a migração com um rollback automático para o servidor on-premises em caso de falhas.

3. **Active Directory**: A integração com o Active Directory on-premises será realizada para garantir que a autenticação e o acesso dos usuários permaneçam inalterados após a migração. Isso incluirá:
   - Testes de autenticação de usuários na nova instância EC2.
   - Acesso a recursos compartilhados e aplicação de políticas de grupo.

## Cenário apresentado

O principal desafio da migração do servidor Windows Server 2019 da Batatas Inc. para a AWS EC2 é garantir a continuidade dos negócios durante todo o processo, minimizando o tempo de inatividade e assegurando que todos os serviços e integrações funcionem corretamente após a migração.

A complexidade da integração com o Active Directory on-premises é um fator crítico, pois a autenticação e o acesso dos usuários dependem desse sistema. A migração deve ser realizada em uma janela de manutenção aos finais de semana, o que requer um planejamento rigoroso para evitar interrupções nas operações.

Além disso, a replicação contínua de 2TB de dados para a área de staging na AWS pode impactar a performance da rede e o tempo total de migração, dependendo da largura de banda disponível e da eficiência do processo de replicação.

Os testes de inicialização e de integração com o Active Directory são essenciais para garantir que todos os serviços estejam operacionais antes do cutover final. A documentação técnica detalhada do processo de migração também é necessária para facilitar futuras manutenções e auditorias.

## Arquitetura de solução

A Batatas Inc. atualmente opera um servidor Windows Server 2019 em um ambiente on-premises localizado em São Paulo. Este servidor é crítico para as operações da empresa, pois suporta diversas aplicações e serviços essenciais. A migração para a AWS EC2 visa não apenas a modernização da infraestrutura, mas também a melhoria da escalabilidade, segurança e continuidade dos negócios.

O projeto de migração envolve a utilização do AWS Application Migration Service (AWS MGN) para facilitar a transição do servidor, garantindo que a instância EC2 resultante seja equivalente ao servidor atual, com 32GB de RAM e 16 vCPUs. Além disso, a integração com o Active Directory on-premises é uma necessidade fundamental para manter a autenticação e o acesso dos usuários.

O escopo da migração inclui a configuração da instância EC2, a instalação do AWS Application Migration Service Agent, e a replicação contínua de 2TB de dados para uma área de staging na AWS. O plano de migração será executado em uma janela de manutenção aos finais de semana, com um plano de contingência que permite o rollback para o servidor atual em caso de falhas.

O cronograma total para a migração está estimado em 17 dias, com um orçamento de R$ 5.000,00. As atividades de backup, treinamento de usuários e monitoramento continuado após a migração estão excluídas do escopo do projeto.

## Escopo de atividades

O escopo da migração do servidor Windows Server 2019 da Batatas Inc. para a AWS EC2 via AWS MGN inclui as seguintes atividades:

**Atividades Incluídas:**
1. **Configuração da Instância EC2**: Definição do tipo e tamanho da instância, configuração de armazenamento e criptografia.
2. **Setup do AWS MGN Replication Server**: Preparação do ambiente para a replicação contínua.
3. **Instalação do AWS Application Migration Service Agent**: Implementação do agente no Windows Server 2019.
4. **Replicação Contínua de 2TB de Dados**: Transferência dos dados para a área de staging na AWS.
5. **Criação e Ajuste de Launch Templates**: Configuração dos templates para a instância EC2.
6. **Testes de Inicialização**: Verificação do funcionamento da instância após a migração.
7. **Testes de Integração com Active Directory**: Garantir que a autenticação e o acesso estejam funcionando corretamente.
8. **Cutover Controlado**: Realização do cutover durante a janela de manutenção aos finais de semana.
9. **Validação Pós-Migração**: Testes para confirmar a integridade dos dados e a funcionalidade dos serviços.
10. **Documentação Técnica**: Registro detalhado do processo de migração, incluindo topologia, regras de segurança e fluxos de dados.

**Atividades Excluídas:**
- Backup dos dados.
- Treinamento de usuários.
- Monitoramento continuado após o projeto.

## Informações da Proposta Técnica

A proposta visa a migração de um servidor Windows Server 2019, atualmente em ambiente on-premises em São Paulo, para a AWS EC2 utilizando o AWS Application Migration Service (AWS MGN). O objetivo é garantir a continuidade dos negócios com um plano de rollback em caso de falhas.

**Cliente**: Batatas Inc.  
**Contato**: Joao Moreira  
**Email**: jmoreira@batatasinc.com  
**Telefone**: +55 11 97433-3333  

**Requisitos de Negócio**:
- Migrar servidor Windows Server 2019 para AWS EC2.
- Garantir continuidade de negócios com rollback em caso de falhas.

**Requisitos Técnicos**:
- Instância equivalente ao servidor atual com 32GB RAM e 16 vCPUs.
- Integração com Active Directory on-premises.

**Tecnologias Utilizadas**:
- AWS EC2
- AWS MGN
- AWS Application Migration Service

**Cronograma**: 17 dias  
**Orçamento**: R$ 5.000,00  

**Restrições**:
- Janela de manutenção aos finais de semana.
- Plano de contingência com rollback para o servidor atual.

## Premissas

- **Janela de Manutenção**: A migração do servidor Windows Server 2019 para a AWS EC2 será realizada em uma janela de manutenção aos finais de semana, minimizando o impacto nas operações da Batatas Inc.

- **Rollback**: Um plano de contingência está em vigor, permitindo o rollback para o servidor atual em caso de falhas durante a migração.

- **Recursos Técnicos**: A instância EC2 será configurada para ser equivalente ao servidor atual, com 32GB de RAM e 16 vCPUs, garantindo que o desempenho seja mantido.

- **Integração com Active Directory**: A integração com o Active Directory on-premises é uma premissa fundamental, assegurando que a autenticação e o acesso dos usuários permaneçam inalterados após a migração.

- **Documentação Completa**: A documentação técnica do processo de migração será elaborada, incluindo detalhes sobre a configuração da instância, topologia de rede e regras de segurança.

Essas premissas são essenciais para garantir que a migração ocorra de forma eficiente e que a continuidade dos negócios da Batatas Inc. seja assegurada.

## Pontos não contemplados por esta proposta

- **Backup dos Dados**: A proposta não inclui a realização de backups dos dados antes da migração, o que é uma prática recomendada para garantir a integridade dos dados durante o processo de migração.

- **Treinamento de Usuários**: Não está previsto um plano de treinamento para os usuários da Batatas Inc. sobre o novo ambiente, o que pode ser necessário para garantir que todos estejam familiarizados com as mudanças.

- **Monitoramento Continuado**: A proposta não contempla a implementação de soluções de monitoramento contínuo após a migração, que são essenciais para garantir a performance e a segurança do ambiente.

- **Custos de Licenciamento**: Não foram considerados os custos de licenciamento do Windows Server na AWS, que podem variar dependendo do modelo de licenciamento escolhido.

- **Suporte Técnico Adicional**: Não foram incluídos custos para suporte técnico adicional que pode ser necessário durante ou após a migração, especialmente se surgirem problemas imprevistos.

Esses pontos devem ser considerados para garantir uma migração completa e bem-sucedida, minimizando riscos e assegurando a continuidade das operações da Batatas Inc.

## Fatores influenciadores

- **Complexidade da Integração com Active Directory**: A migração requer uma integração eficaz com o Active Directory on-premises, o que pode impactar o tempo e os recursos necessários para a configuração e testes.

- **Janela de Manutenção**: A necessidade de realizar a migração em uma janela de manutenção específica aos finais de semana pode limitar a flexibilidade no cronograma e aumentar a pressão para que todas as etapas sejam concluídas dentro do prazo.

- **Volume de Dados**: A replicação contínua de 2TB de dados pode afetar a performance da rede e o tempo total de migração, dependendo da largura de banda disponível e da eficiência do processo de replicação.

- **Testes de Validação**: A realização de testes de inicialização e de integração com o Active Directory é crucial para garantir que todos os serviços estejam operacionais após a migração, o que pode demandar tempo adicional.

- **Documentação Técnica**: A necessidade de elaborar documentação técnica detalhada pode impactar o cronograma, especialmente se houver mudanças ou ajustes durante o processo de migração.

Esses fatores devem ser considerados para garantir uma migração bem-sucedida e a continuidade das operações da Batatas Inc. durante e após o processo.

## Fatores que influenciam cenários de custos

- **Tipo e Tamanho da Instância EC2**: O custo da instância EC2 será influenciado pelo tipo e tamanho escolhidos, que devem ser equivalentes ao servidor atual (32GB RAM e 16 vCPUs). A escolha de instâncias com recursos adicionais pode aumentar os custos.

- **Transferência de Dados**: A replicação contínua de 2TB de dados para a área de staging na AWS pode resultar em custos variáveis de transferência de dados, dependendo da largura de banda disponível e da eficiência do processo de replicação.

- **Uso do AWS MGN**: O uso do AWS Application Migration Service pode incorrer em custos adicionais, dependendo da quantidade de dados e do tempo de uso do serviço durante a migração.

- **Janela de Manutenção**: A migração será realizada durante uma janela de manutenção específica, o que pode impactar os custos associados à mão de obra e à disponibilidade de recursos.

- **Testes e Validação**: Os testes de inicialização e integração com o Active Directory podem exigir tempo e recursos adicionais, impactando o custo total do projeto.

- **Documentação e Suporte**: A elaboração de documentação técnica e o suporte pós-migração também podem influenciar os custos, dependendo da complexidade do ambiente e das necessidades de manutenção.

Esses fatores devem ser monitorados e ajustados conforme necessário para garantir que o orçamento de R$ 5.000,00 seja mantido dentro dos limites estabelecidos.

## Premissas para cenários de custos

- **Custo da Instância EC2**: O custo será baseado no tipo e tamanho da instância EC2 escolhida, que deve ser equivalente ao servidor atual (32GB RAM e 16 vCPUs). A escolha de instâncias com recursos adicionais ou diferentes tipos de instâncias pode impactar o custo total.

- **Transferência de Dados**: A replicação contínua de 2TB de dados para a área de staging na AWS pode gerar custos de transferência de dados, que devem ser estimados com base na largura de banda disponível e na eficiência do processo de replicação.

- **Uso do AWS MGN**: O uso do AWS Application Migration Service pode incorrer em custos adicionais, dependendo da quantidade de dados a serem migrados e do tempo de uso do serviço.

- **Janela de Manutenção**: A migração será realizada durante uma janela de manutenção específica, o que pode impactar os custos associados à mão de obra e à disponibilidade de recursos.

- **Testes e Validação**: A realização de testes de inicialização e de integração com o Active Directory pode exigir tempo e recursos adicionais, impactando o custo total do projeto.

- **Documentação e Suporte**: A elaboração de documentação técnica e o suporte pós-migração também podem influenciar os custos, dependendo da complexidade do ambiente e das necessidades de manutenção.

Essas premissas devem ser monitoradas e ajustadas conforme necessário para garantir que o orçamento de R$ 5.000,00 seja mantido dentro dos limites estabelecidos.

## Fatores de custos estimados que podem ser refinados

- **Custo de Transferência de Dados**: O volume de dados a ser replicado (2TB) pode resultar em custos variáveis de transferência de dados, dependendo da largura de banda disponível e da eficiência do processo de replicação.

- **Tipo e Tamanho da Instância EC2**: O custo da instância EC2 será influenciado pelo tipo e tamanho escolhidos, que devem ser equivalentes ao servidor atual (32GB RAM e 16 vCPUs). A escolha de instâncias com recursos adicionais pode aumentar os custos.

- **Uso do AWS MGN**: O uso do AWS Application Migration Service pode incorrer em custos adicionais, dependendo da quantidade de dados a serem migrados e do tempo de uso do serviço.

- **Testes e Validação**: A realização de testes de inicialização e de integração com o Active Directory pode exigir tempo e recursos adicionais, impactando o custo total do projeto.

- **Documentação e Suporte**: A elaboração de documentação técnica e o suporte pós-migração também podem influenciar os custos, dependendo da complexidade do ambiente e das necessidades de manutenção.

Esses fatores devem ser monitorados e ajustados conforme necessário para garantir que o orçamento de R$ 5.000,00 seja mantido dentro dos limites estabelecidos.

## Fatores de custos não contemplados que envolvem análises à parte ou informações adicionais

- **Custos de Licenciamento**: A proposta não inclui uma análise detalhada dos custos de licenciamento do Windows Server na AWS, que podem variar dependendo do modelo de licenciamento escolhido (por exemplo, licenciamento sob demanda ou reservado).

- **Backup de Dados**: A proposta não contempla a realização de backups dos dados antes da migração, o que é uma prática recomendada para garantir a integridade dos dados durante o processo de migração.

- **Treinamento de Usuários**: Não está previsto um plano de treinamento para os usuários da Batatas Inc. sobre o novo ambiente, o que pode ser necessário para garantir que todos estejam familiarizados com as mudanças.

- **Monitoramento Continuado**: A proposta não inclui a implementação de soluções de monitoramento contínuo após a migração, que são essenciais para garantir a performance e a segurança do ambiente.

- **Suporte Técnico Adicional**: Não foram incluídos custos para suporte técnico adicional que pode ser necessário durante ou após a migração, especialmente se surgirem problemas imprevistos.

Esses fatores devem ser considerados para garantir uma migração completa e bem-sucedida, minimizando riscos e assegurando a continuidade das operações da Batatas Inc.

## Custos Equipamentos, Licenças ou AWS

- **Instância EC2**: O custo da instância EC2 será baseado no tipo e tamanho escolhidos, que devem ser equivalentes ao servidor atual (32GB RAM e 16 vCPUs). O preço pode variar dependendo da região e do modelo de pagamento (sob demanda ou reservado).

- **Licenciamento do Windows Server**: A proposta não inclui uma análise detalhada dos custos de licenciamento do Windows Server na AWS, que pode ser afetada pelo modelo de licenciamento escolhido (por exemplo, licenciamento sob demanda ou reservado).

- **Transferência de Dados**: A replicação contínua de 2TB de dados para a área de staging na AWS pode resultar em custos variáveis de transferência de dados, dependendo da largura de banda disponível e da eficiência do processo de replicação.

- **Uso do AWS MGN**: O uso do AWS Application Migration Service pode incorrer em custos adicionais, dependendo da quantidade de dados a serem migrados e do tempo de uso do serviço.

- **Suporte Técnico**: Custos adicionais podem ser necessários para suporte técnico durante e após a migração, especialmente se surgirem problemas imprevistos.

Esses custos devem ser monitorados e ajustados conforme necessário para garantir que o orçamento de R$ 5.000,00 seja mantido dentro dos limites estabelecidos.

## Resultados esperados

Os resultados esperados da migração do servidor Windows Server 2019 da Batatas Inc. para a AWS EC2 incluem:

- **Migração Bem-Sucedida**: A migração será realizada com sucesso, garantindo que todos os dados e aplicações sejam transferidos corretamente para a nova instância EC2.

- **Continuidade dos Negócios**: A operação do servidor migrado deverá ser ininterrupta, com a funcionalidade total dos serviços e aplicações, assegurando que os usuários possam acessar os recursos sem interrupções.

- **Integração com Active Directory**: A autenticação e o acesso dos usuários ao Active Directory on-premises devem funcionar perfeitamente, permitindo que os usuários continuem a acessar suas contas e recursos como antes da migração.

- **Documentação Técnica Completa**: A documentação técnica do ambiente migrado será elaborada, incluindo topologia, regras de segurança e fluxos de dados, facilitando futuras manutenções e auditorias.

- **Rollback Eficiente**: Em caso de falhas durante a migração, o plano de rollback permitirá a restauração rápida do servidor on-premises, minimizando o impacto nas operações da empresa.

- **Validação de Dados**: Todos os dados migrados serão validados para garantir a integridade e a precisão, assegurando que não haja perda de informações durante o processo.

Esses resultados são fundamentais para garantir que a Batatas Inc. possa operar de forma eficiente e segura após a migração.

## Estimativa de horas

A estimativa de horas para a migração do servidor Windows Server 2019 da Batatas Inc. para a AWS EC2 via AWS MGN é a seguinte:

- **Preparação do AWS MGN Replication Server**: 2 dias
- **Instalação do AWS Application Migration Service Agent**: 1 dia
- **Replicação Contínua de 2TB de Dados**: 7 dias
- **Testes de Inicialização**: 2 dias
- **Testes de Integração com Active Directory**: 3 dias
- **Cutover Controlado**: 1 dia
- **Validação Pós-Migração**: 1 dia
- **Documentação Técnica**: 1 dia

**Total Estimado**: 17 dias

Essa estimativa considera todas as etapas necessárias para garantir uma migração bem-sucedida e a continuidade das operações da Batatas Inc. durante e após o processo de migração.

## Próximos passos

1. **Reunião de Kick-off**: Agendar uma reunião inicial com a equipe da Batatas Inc. para discutir o plano de migração, esclarecer dúvidas e alinhar expectativas.

2. **Preparação do Ambiente**: Iniciar a preparação do AWS MGN replication server e realizar o levantamento do ambiente atual para identificar todos os componentes que precisam ser migrados.

3. **Instalação do AWS Application Migration Service Agent**: Implementar o agente no Windows Server 2019 para iniciar a replicação dos dados.

4. **Configuração da Instância EC2**: Definir o tipo e tamanho da instância EC2, configurar armazenamento e criptografia, e associar os recursos necessários.

