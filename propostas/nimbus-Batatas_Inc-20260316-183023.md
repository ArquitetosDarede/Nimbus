PROPOSTA TECNICA - MIGRACAO PARA AWS
======================================================================

Cliente: Batatas Inc.
Data: 2026-03-16T18:30:01.398523

## 1. Formulário de Proposta Técnica

### Formulário de Proposta Técnica

**Cliente:** Batatas Inc.  
**Projeto:** Migração de 1 servidor Windows 2019 on-premises em São Paulo para EC2 via AWS MGN  
**Contato:** João Moreira (jmoreira@batatasinc.com, +55 11 97433-3333)  

**Requisitos de Negócio:**
- Migrar servidor Windows 2019 para AWS EC2.
- Manter integração com Active Directory (AD) on-premises.

**Requisitos Técnicos:**
- Servidor alvo com 32GB de RAM e 16 vCPUs.
- Utilizar AWS MGN para migração.

**Escopo:**
- **Inclusões:** A definir.
- **Exclusões:** Backup (fora do escopo).

**Tecnologias:**
- AWS EC2
- AWS MGN

**Restrições:**
- Janela de manutenção aos finais de semana.
- Plano de contingência para reversão em caso de falha.

**Cronograma:** 30 dias  
**Orçamento:** R$ 5.000,00  

**Resultados Esperados:**
- Migração bem-sucedida do servidor para a AWS EC2.
- Integração contínua com o AD on-premises.
- Estabelecimento de um ambiente seguro e escalável na nuvem.

**Estimativa de Horas:** A confirmar.  

**Próximos Passos:**
- Confirmação dos requisitos e escopo detalhado.
- Planejamento da execução da migração.
- Definição de um cronograma de reuniões para acompanhamento do progresso.

## 2. Resumo

### Resumo

A proposta visa a migração de um servidor Windows 2019, atualmente em ambiente on-premises em São Paulo, para a infraestrutura da AWS utilizando o AWS MGN. Este projeto é fundamental para a Batatas Inc. devido à necessidade de modernização de sua infraestrutura de TI e à manutenção da integração com o Active Directory (AD) existente.

**Objetivos Principais:**
- Migrar o servidor Windows 2019 para AWS EC2, garantindo que a operação continue integrada com o AD on-premises.
- Utilizar AWS MGN para facilitar a migração, assegurando uma transição suave e eficiente.

**Requisitos Técnicos:**
- O servidor migrado deve ter 32GB de RAM e 16 vCPUs, com a configuração de um EC2 equivalente na AWS.
- A migração deve ser realizada em uma janela de manutenção programada para os finais de semana, minimizando o impacto nas operações da empresa.

**Orçamento e Prazo:**
- O projeto está orçado em R$ 5.000,00 e deve ser concluído em um prazo de 30 dias.

**Limitações:**
- O escopo da proposta não inclui a realização de backups, que será considerada fora do escopo do projeto.

**Resultados Esperados:**
- A migração bem-sucedida do servidor para a AWS, com a continuidade da operação e integração com o AD, resultando em um ambiente mais escalável e seguro.

## 3. Desafio

### Desafio

A migração do servidor Windows 2019 da Batatas Inc. representa um desafio significativo, pois envolve a transição de um ambiente on-premises para a nuvem, utilizando a AWS. Este processo deve ser realizado de forma a garantir a continuidade das operações e a integração com o Active Directory (AD) existente.

**Principais Desafios:**
- **Complexidade da Migração:** A migração de 2TB de dados requer um planejamento cuidadoso para evitar perda de informações e garantir a integridade dos dados durante o processo.
- **Manutenção da Integração com AD:** A necessidade de manter a integração com o AD on-premises é crucial para a operação contínua dos serviços da empresa, exigindo uma configuração adequada na nova infraestrutura.
- **Janela de Manutenção:** A migração deve ser realizada em uma janela de manutenção restrita aos finais de semana, o que limita o tempo disponível para a execução das atividades.
- **Plano de Contingência:** É essencial ter um plano de contingência robusto para reverter a migração em caso de falhas, garantindo a continuidade dos serviços.

**Expectativas:**
- A migração deve ser concluída em 30 dias, dentro do orçamento de R$ 5.000,00, assegurando que todos os requisitos técnicos e de negócio sejam atendidos.

## 4. Cenário apresentado

### Cenário apresentado

A Batatas Inc. está buscando modernizar sua infraestrutura de TI através da migração de um servidor Windows 2019, atualmente em um ambiente on-premises em São Paulo, para a nuvem da AWS, utilizando o AWS MGN. Este movimento é parte de uma estratégia mais ampla para melhorar a eficiência operacional e a escalabilidade dos serviços.

**Contexto do Projeto:**
- **Ambiente Atual:** O servidor Windows 2019 armazena e processa dados críticos para a operação da empresa, totalizando aproximadamente 2TB de dados locais.
- **Objetivo da Migração:** Garantir que a operação continue integrada com o Active Directory (AD) on-premises, permitindo que os usuários mantenham acesso aos recursos necessários sem interrupções.

**Requisitos e Restrições:**
- **Requisitos de Negócio:** 
  - Migrar o servidor para AWS EC2.
  - Manter a integração com o AD existente.
- **Requisitos Técnicos:**
  - O servidor alvo deve ter 32GB de RAM e 16 vCPUs, com configuração equivalente na AWS.
  - A migração deve ser realizada utilizando o AWS MGN.
- **Restrições:**
  - A migração deve ocorrer em uma janela de manutenção aos finais de semana.
  - Um plano de contingência deve estar em vigor para reverter a migração em caso de falha.
  - O escopo não inclui a realização de backups.

**Orçamento e Prazo:**
- **Orçamento:** R$ 5.000,00.
- **Prazo:** 30 dias para a conclusão do projeto.

Este cenário apresenta uma oportunidade significativa para a Batatas Inc. melhorar sua infraestrutura de TI, mas também envolve desafios que devem ser cuidadosamente gerenciados para garantir uma transição suave e bem-sucedida.

## 5. Arquitetura de solução

### Arquitetura de solução

A arquitetura proposta para a migração do servidor Windows 2019 da Batatas Inc. para a AWS utiliza os serviços AWS EC2 e AWS MGN, garantindo uma transição eficiente e segura. A seguir, detalhamos a topologia, controles de segurança e preocupações operacionais.

#### Topologia da Solução

1. **Instância EC2**: 
   - Tipo: A instância EC2 será provisionada com 32GB de RAM e 16 vCPUs, conforme os requisitos técnicos.
   - Armazenamento: Será configurado um volume EBS para armazenar os dados do servidor, com criptografia em repouso habilitada.
   - Elastic IP: Um Elastic IP será associado à instância para garantir um endereço IP fixo.

2. **AWS MGN**:
   - O AWS MGN será utilizado para realizar a migração do servidor Windows 2019. Este serviço permite a replicação contínua dos dados, minimizando o tempo de inatividade.

3. **Rede**:
   - A instância EC2 será colocada em uma VPC (Virtual Private Cloud) com subnets apropriadas, garantindo isolamento e segurança.
   - Grupos de segurança serão configurados para permitir apenas o tráfego necessário, restringindo acessos não autorizados.

#### Controles de Segurança

- **IAM Roles**: Serão configuradas políticas de IAM para garantir que apenas usuários e serviços autorizados tenham acesso à instância EC2 e aos recursos associados.
- **Criptografia**: A criptografia de dados em repouso será aplicada ao volume EBS e a comunicação será protegida com TLS para dados em trânsito.
- **Monitoramento**: O AWS CloudTrail e o Amazon CloudWatch serão utilizados para monitorar atividades e gerar logs de auditoria, permitindo a detecção de atividades suspeitas.

#### Preocupações Operacionais

- **Janela de Manutenção**: A migração será realizada durante a janela de manutenção aos finais de semana, minimizando o impacto nas operações da Batatas Inc.
- **Plano de Contingência**: Um plano de contingência será estabelecido para reverter a migração em caso de falha, garantindo que o servidor on-premises permaneça disponível até que a migração seja validada.
- **Documentação**: Toda a arquitetura e configuração serão documentadas, incluindo a topologia da rede, regras de segurança e fluxos de dados, para facilitar a manutenção e futuras auditorias.

Esta arquitetura visa não apenas atender aos requisitos técnicos e de negócios, mas também garantir a segurança e a continuidade das operações durante e após a migração.

## 6. Escopo de atividades

### Escopo de atividades

O escopo das atividades para a migração do servidor Windows 2019 da Batatas Inc. para a AWS é delineado da seguinte forma:

#### Atividades Incluídas
- **Planejamento da Migração**: Definição da estratégia de migração utilizando o AWS MGN, incluindo a configuração inicial do serviço.
- **Provisionamento da Instância EC2**: Criação da instância EC2 com 32GB de RAM e 16 vCPUs, conforme os requisitos técnicos.
- **Configuração de Rede**: Estabelecimento da VPC, subnets e grupos de segurança necessários para a instância EC2.
- **Integração com Active Directory**: Manutenção da integração com o Active Directory on-premises.
- **Execução da Migração**: Realização da migração dos dados e aplicações do servidor Windows 2019 utilizando o AWS MGN.
- **Validação Pós-Migração**: Testes para garantir que a migração foi bem-sucedida e que todas as funcionalidades estão operando conforme esperado.
- **Documentação**: Criação de documentação técnica detalhando a arquitetura, configurações e processos realizados durante a migração.

#### Atividades Excluídas
- **Backup**: A criação de backups do servidor on-premises antes da migração está explicitamente fora do escopo deste projeto.

#### Considerações Adicionais
- **Janela de Manutenção**: Todas as atividades de migração serão realizadas durante a janela de manutenção aos finais de semana para minimizar o impacto nas operações.
- **Plano de Contingência**: Um plano de contingência será implementado para reverter a migração em caso de falha, garantindo que o servidor atual permaneça disponível até que a migração seja validada.

Este escopo foi elaborado para atender às necessidades da Batatas Inc. dentro do prazo de 30 dias e orçamento de R$ 5.000,00.

## 7. Informações da Proposta Técnica

### Informações da Proposta Técnica

**Cliente:** Batatas Inc.  
**Projeto:** Migração de 1 servidor Windows 2019 on-premises em São Paulo para EC2 via AWS MGN  
**Contato:** João Moreira (jmoreira@batatasinc.com, +55 11 97433-3333)  

**Requisitos de Negócio:**
- Migrar servidor Windows 2019 para AWS EC2.
- Manter integração com Active Directory (AD) on-premises.

**Requisitos Técnicos:**
- Servidor alvo com 32GB de RAM e 16 vCPUs.
- Utilizar AWS MGN para migração.

**Escopo:**
- **Inclusões:** A definir.
- **Exclusões:** Backup (fora do escopo).

**Tecnologias Utilizadas:**
- AWS EC2
- AWS MGN

**Restrições:**
- Janela de manutenção aos finais de semana.
- Plano de contingência para reversão em caso de falha.

**Cronograma:** 30 dias  
**Orçamento:** R$ 5.000,00  

**Confiança no Projeto:** 80%  

**Dados Faltantes:** Nenhum dado faltante identificado até o momento.

## 8. Premissas

### Premissas

- **Integração com AD:** Assume-se que a integração com o Active Directory (AD) on-premises será mantida sem interrupções durante e após a migração.
- **Capacidade do Servidor:** O servidor alvo na AWS terá 32GB de RAM e 16 vCPUs, conforme especificado nos requisitos técnicos.
- **Uso do AWS MGN:** A migração será realizada utilizando o AWS MGN, garantindo uma transição eficiente e minimizando o tempo de inatividade.
- **Janela de Manutenção:** A migração ocorrerá exclusivamente durante a janela de manutenção definida para os finais de semana, evitando impactos nas operações diárias da empresa.
- **Plano de Contingência:** Um plano de contingência estará em vigor para reverter a migração em caso de falhas, assegurando a continuidade dos serviços.
- **Exclusão de Backup:** A proposta não inclui a realização de backups, que é explicitamente considerada fora do escopo do projeto.

Essas premissas são fundamentais para o planejamento e execução bem-sucedida da migração, garantindo que todas as partes envolvidas estejam alinhadas e cientes das expectativas.

## 9. Pontos não contemplados por esta proposta

### Pontos não contemplados por esta proposta

- **Backup de Dados:** A proposta explicitamente não inclui a realização de backups dos dados do servidor Windows 2019 antes da migração. A responsabilidade pela proteção dos dados durante a migração recai sobre a Batatas Inc.
  
- **Treinamento e Suporte Pós-Migração:** Não está previsto um treinamento formal para a equipe da Batatas Inc. sobre a nova infraestrutura ou suporte contínuo após a migração, além do acompanhamento imediato pós-migração.

- **Atualizações de Software:** A proposta não contempla a atualização de software ou sistemas operacionais que possam ser necessários após a migração para garantir compatibilidade ou segurança.

- **Customizações Específicas:** Qualquer customização adicional ou configuração específica que não esteja detalhada nos requisitos técnicos será considerada fora do escopo.

- **Monitoramento Contínuo:** A implementação de soluções de monitoramento contínuo da infraestrutura na AWS não está incluída na proposta e deve ser considerada separadamente.

Esses pontos devem ser considerados pela Batatas Inc. para garantir que todas as necessidades e expectativas sejam atendidas durante e após o processo de migração.

## 10. Fatores influenciadores

### Fatores influenciadores

- **Tecnologia Utilizada:** A escolha de tecnologias como AWS EC2 e AWS MGN impacta diretamente na eficiência e na segurança da migração, influenciando a complexidade do processo e a necessidade de expertise técnica.

- **Janela de Manutenção:** A restrição para realizar a migração apenas durante os finais de semana pode limitar a flexibilidade no planejamento e execução das atividades, exigindo um cronograma rigoroso.

- **Integração com AD:** A necessidade de manter a integração com o Active Directory on-premises é um fator crítico que pode influenciar a abordagem técnica e a configuração do ambiente na nuvem.

- **Orçamento:** O limite orçamentário de R$ 5.000,00 pode restringir a escolha de soluções e serviços adicionais que poderiam facilitar a migração ou melhorar a segurança e a performance do ambiente.

- **Plano de Contingência:** A existência de um plano de contingência para reversão em caso de falha é fundamental, pois pode impactar a confiança na migração e a disposição da equipe em adotar a nova infraestrutura.

- **Expectativas de Performance:** A expectativa de que o servidor na AWS funcione com desempenho equivalente ao ambiente on-premises pode influenciar a configuração e a escolha do tipo de instância EC2.

Esses fatores devem ser considerados ao longo do processo de migração para garantir que as expectativas da Batatas Inc. sejam atendidas e que a transição para a nuvem seja bem-sucedida.

## 11. Fatores que influenciam cenários de custos

### Fatores que influenciam cenários de custos

Os custos associados à migração do servidor Windows 2019 da Batatas Inc. para a AWS são influenciados por diversos fatores, que incluem:

1. **Tipo e Tamanho da Instância EC2**:
   - A escolha da instância EC2 com 32GB de RAM e 16 vCPUs impacta diretamente o custo mensal, uma vez que instâncias maiores e mais potentes têm tarifas mais elevadas.

2. **Uso do AWS MGN**:
   - O AWS MGN (AWS Application Migration Service) tem custos associados à replicação e ao uso de recursos durante o processo de migração. O tempo de uso e a quantidade de dados transferidos também afetam o custo total.

3. **Armazenamento**:
   - O volume EBS (Elastic Block Store) utilizado para armazenar dados da instância EC2 terá custos baseados no tipo de armazenamento (SSD, HDD) e na capacidade provisionada.

4. **Transferência de Dados**:
   - Custos de transferência de dados podem ser incorridos ao mover dados do ambiente on-premises para a AWS, especialmente se a quantidade de dados for significativa (2TB, conforme mencionado).

5. **Licenciamento de Software**:
   - Se houver necessidade de licenciamento adicional para o Windows Server ou outros softwares utilizados no servidor, isso também impactará o custo total do projeto.

6. **Suporte e Manutenção**:
   - A necessidade de suporte técnico adicional ou serviços gerenciados pode gerar custos extras, dependendo do nível de suporte requerido pela Batatas Inc.

7. **Janela de Manutenção**:
   - A realização da migração durante a janela de manutenção aos finais de semana pode influenciar os custos operacionais, especialmente se houver necessidade de horas extras para a equipe técnica.

8. **Plano de Contingência**:
   - A implementação de um plano de contingência para reverter a migração em caso de falha pode envolver custos adicionais, como a manutenção do servidor on-premises até que a migração seja validada.

Esses fatores devem ser considerados cuidadosamente para garantir que o orçamento de R$ 5.000,00 seja suficiente para cobrir todos os aspectos da migração e operação do novo ambiente na AWS.

## 12. Premissas para cenários de custos

### Premissas para cenários de custos

As seguintes premissas foram consideradas para a estimativa de custos da migração do servidor Windows 2019 da Batatas Inc. para a AWS:

1. **Capacidade do Servidor**:
   - Assume-se que a instância EC2 provisionada terá 32GB de RAM e 16 vCPUs, conforme os requisitos técnicos definidos.

2. **Uso do AWS MGN**:
   - A migração será realizada utilizando o AWS MGN, e os custos associados a este serviço foram considerados na estimativa.

3. **Armazenamento**:
   - O custo do armazenamento EBS será baseado na capacidade provisionada e no tipo de armazenamento escolhido (SSD ou HDD).

4. **Transferência de Dados**:
   - A estimativa inclui custos de transferência de dados ao mover 2TB de dados do ambiente on-premises para a AWS.

5. **Licenciamento de Software**:
   - Assume-se que todos os custos de licenciamento necessários para o Windows Server e outros softwares utilizados estão incluídos no orçamento.

6. **Suporte Técnico**:
   - O custo de suporte técnico adicional ou serviços gerenciados não foi incluído, a menos que explicitamente mencionado.

7. **Janela de Manutenção**:
   - A migração será realizada durante a janela de manutenção aos finais de semana, o que pode impactar os custos operacionais, especialmente se horas extras forem necessárias.

8. **Plano de Contingência**:
   - O custo para manter o servidor on-premises disponível até a validação da migração está considerado, caso haja necessidade de reverter a migração.

Essas premissas são fundamentais para garantir que o orçamento de R$ 5.000,00 seja suficiente para cobrir todos os aspectos da migração e operação do novo ambiente na AWS.

## 13. Fatores de custos estimados que podem ser refinados

### Fatores de custos estimados que podem ser refinados

Os seguintes fatores de custos estimados para a migração do servidor Windows 2019 da Batatas Inc. para a AWS podem ser refinados à medida que mais informações se tornam disponíveis:

1. **Tipo e Tamanho da Instância EC2**:
   - A escolha final do tipo de instância EC2 pode ser ajustada com base em testes de desempenho e requisitos específicos de carga de trabalho, o que pode impactar o custo mensal.

2. **Armazenamento EBS**:
   - O tipo de armazenamento (SSD vs. HDD) e a capacidade exata necessária podem ser refinados após uma análise mais detalhada dos dados a serem migrados e do desempenho desejado.

3. **Transferência de Dados**:
   - O custo de transferência de dados pode ser ajustado com base na quantidade real de dados que será transferida durante a migração, especialmente se houver compressão ou otimização de dados.

4. **Licenciamento de Software**:
   - Custos de licenciamento podem variar dependendo de acordos específicos com fornecedores de software e a necessidade de licenças adicionais para o Windows Server ou outros aplicativos.

5. **Suporte Técnico**:
   - A necessidade de suporte técnico adicional pode ser refinada com base na complexidade da migração e na experiência da equipe interna da Batatas Inc.

6. **Janela de Manutenção**:
   - O custo associado à janela de manutenção pode ser ajustado se a migração exigir mais ou menos tempo do que o inicialmente previsto, impactando as horas de trabalho da equipe.

7. **Plano de Contingência**:
   - O custo para manter o servidor on-premises disponível até a validação da migração pode ser refinado com base na duração real da migração e na necessidade de reversão.

Esses fatores devem ser monitorados e ajustados conforme necessário para garantir que o orçamento de R$ 5.000,00 permaneça adequado para cobrir todos os aspectos da migração e operação do novo ambiente na AWS.

## 14. Fatores de custos não contemplados que envolvem análises à parte ou informações adicionais

### Fatores de custos não contemplados que envolvem análises à parte ou informações adicionais

Os seguintes fatores de custos não estão contemplados na proposta e podem exigir análises adicionais ou informações complementares para uma estimativa mais precisa:

1. **Backup de Dados**:
   - A proposta não inclui a realização de backups dos dados do servidor Windows 2019 antes da migração. A responsabilidade pela proteção dos dados durante a migração deve ser considerada, e a implementação de uma estratégia de backup pode gerar custos adicionais.

2. **Licenciamento de Software**:
   - Custos relacionados ao licenciamento de software adicional que possa ser necessário para a operação do servidor na AWS não foram incluídos. Isso pode incluir licenças para o Windows Server ou outros aplicativos que a Batatas Inc. utiliza.

3. **Suporte Técnico Adicional**:
   - A necessidade de suporte técnico adicional ou serviços gerenciados não foi considerada. Dependendo da complexidade da migração e da experiência da equipe interna, pode ser necessário contratar suporte externo, o que impactaria o custo total.

4. **Treinamento e Capacitação**:
   - Custos associados ao treinamento da equipe da Batatas Inc. para operar e gerenciar o novo ambiente na AWS não foram incluídos. Isso pode ser essencial para garantir uma transição suave e eficiente.

5. **Monitoramento e Auditoria**:
   - A implementação de soluções de monitoramento e auditoria para garantir a conformidade e a segurança do ambiente na AWS pode gerar custos adicionais que não foram considerados na proposta inicial.

6. **Ajustes de Infraestrutura**:
   - Qualquer necessidade de ajustes na infraestrutura existente da Batatas Inc. para suportar a nova configuração na AWS, como upgrades de rede ou hardware, não foi contemplada e pode impactar o custo total.

Esses fatores devem ser avaliados e discutidos com a Batatas Inc. para garantir que todos os aspectos da migração sejam considerados e que o orçamento de R$ 5.000,00 seja adequado para cobrir todas as necessidades do projeto.

## 15. Custos Equipamentos, Licenças ou AWS

### Custos Equipamentos, Licenças ou AWS

Os custos associados à migração do servidor Windows 2019 da Batatas Inc. para a AWS incluem os seguintes itens:

1. **Instância EC2**:
   - Custo mensal da instância EC2 com 32GB de RAM e 16 vCPUs, que será a base para a operação do servidor migrado.

2. **Armazenamento EBS**:
   - Custos relacionados ao armazenamento EBS (Elastic Block Store) para a instância EC2, que dependerão do tipo de armazenamento (SSD ou HDD) e da capacidade provisionada.

3. **Transferência de Dados**:
   - Custos de transferência de dados ao mover 2TB de dados do ambiente on-premises para a AWS. Isso pode incluir taxas de entrada e saída de dados.

4. **Licenciamento de Software**:
   - Custos de licenciamento para o Windows Server e outros softwares que possam ser necessários para a operação do servidor na AWS.

5. **AWS MGN**:
   - Custos associados ao uso do AWS Application Migration Service (MGN) para a replicação e migração do servidor, que podem incluir taxas baseadas no volume de dados replicados.

6. **Suporte Técnico**:
   - Possíveis custos adicionais para suporte técnico ou serviços gerenciados, caso a Batatas Inc. opte por contratar assistência externa durante ou após a migração.

7. **Monitoramento e Segurança**:
   - Custos para implementar soluções de monitoramento e segurança, como AWS CloudWatch e AWS CloudTrail, para garantir a conformidade e a segurança do ambiente.

Esses custos devem ser considerados na estimativa total do projeto, que está orçada em R$ 5.000,00, e podem ser ajustados conforme necessário durante o planejamento e a execução da migração.

## 16. Resultados esperados

### Resultados esperados

- **Migração Bem-Sucedida:** A migração do servidor Windows 2019 para a AWS EC2 deve ser realizada com sucesso, garantindo que todos os dados e aplicações sejam transferidos sem perda de informações.

- **Integração com AD:** A continuidade da integração com o Active Directory on-premises será mantida, permitindo que os usuários acessem os recursos necessários sem interrupções.

- **Desempenho Equivalente:** O servidor na AWS deve operar com desempenho equivalente ao ambiente on-premises, utilizando uma instância EC2 com 32GB de RAM e 16 vCPUs, conforme os requisitos técnicos.

- **Redução de Custos Operacionais:** A migração para a nuvem deve resultar em uma redução nos custos operacionais a longo prazo, aproveitando a escalabilidade e flexibilidade da infraestrutura da AWS.

- **Documentação Completa:** Será gerada documentação técnica detalhada do ambiente migrado, incluindo topologia, regras e fluxos aplicados, para facilitar a gestão e manutenção futura.

- **Acompanhamento Pós-Migração:** Um acompanhamento pós-migração será realizado para garantir que todas as funcionalidades estejam operando conforme esperado e para resolver quaisquer problemas que possam surgir.

Esses resultados são fundamentais para que a Batatas Inc. alcance seus objetivos de modernização da infraestrutura de TI e melhore sua eficiência operacional.

## 17. Estimativa de horas

### Estimativa de horas

A estimativa de horas para a migração do servidor Windows 2019 da Batatas Inc. para a AWS é baseada nas seguintes atividades e suas respectivas durações:

1. **Planejamento da Migração**: 8 horas
   - Definição da estratégia de migração e configuração inicial do AWS MGN.

2. **Provisionamento da Instância EC2**: 6 horas
   - Definição do tipo e tamanho da instância, configuração de armazenamento e criptografia, e associação de recursos de rede.

3. **Configuração de Rede**: 4 horas
   - Estabelecimento da VPC, subnets e grupos de segurança necessários.

4. **Integração com Active Directory**: 4 horas
   - Configuração da integração com o AD on-premises.

5. **Execução da Migração**: 12 horas
   - Realização da migração dos dados e aplicações utilizando o AWS MGN.

6. **Validação Pós-Migração**: 6 horas
   - Testes para garantir que a migração foi bem-sucedida e que todas as funcionalidades estão operando conforme esperado.

7. **Documentação**: 4 horas
   - Criação de documentação técnica detalhando a arquitetura, configurações e processos realizados durante a migração.

8. **Acompanhamento e Suporte**: 4 horas
   - Monitoramento do ambiente após a migração e suporte para resolver quaisquer problemas que possam surgir.

#### Total Estimado: 48 horas

Essa estimativa pode ser ajustada conforme necessário, dependendo da complexidade da migração e da experiência da equipe envolvida. É importante considerar que a janela de manutenção aos finais de semana pode impactar a execução das atividades, e um plano de contingência deve estar em vigor para garantir a reversão em caso de falha.

## 18. Próximos passos

### Próximos passos

1. **Confirmação do Escopo:** Validar e confirmar o escopo da migração com a equipe da Batatas Inc., assegurando que todas as partes interessadas estejam alinhadas.

2. **Planejamento Detalhado:** Desenvolver um plano detalhado de migração, incluindo cronograma, recursos necessários e designação de responsabilidades.

3. **Configuração do Ambiente AWS:**
   - Provisionar a instância EC2 com as especificações de 32GB de RAM e 16 vCPUs.
   - Configurar as permissões de acesso com IAM Roles e aplicar práticas de segurança.

4. **Execução da Migração:**
   - Realizar a migração dos dados e aplicações utilizando o AWS MGN durante a janela de manutenção programada.
   - Monitorar o processo de migração para garantir a integridade dos dados.

5. **Integração com AD:** Garantir que a integração com o Active Directory on-premises esteja funcionando corretamente após a migração.

6. **Testes e Validação:** Realizar testes de funcionalidade e desempenho no novo ambiente para assegurar que tudo esteja operando conforme esperado.

7. **Documentação:** Criar documentação técnica detalhada do novo ambiente, incluindo topologia, regras e fluxos aplicados.

8. **Acompanhamento Pós-Migração:** Estabelecer um período de acompanhamento para resolver quaisquer problemas que possam surgir e garantir a continuidade das operações.

Esses passos são essenciais para garantir uma migração bem-sucedida e a satisfação das necessidades da Batatas Inc. durante todo o processo.

