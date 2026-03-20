Backup de On-Premises
======================================================================

Cliente: Ciclope Corporations
Data: 18/03/2026

## 1. Formulário de Proposta Técnica

- A Ciclope Corporations é uma empresa que atua na produção e distribuição de conteúdo audiovisual. Com sede em Recife, a empresa possui um grande volume de dados, principalmente arquivos de vídeo, que precisam ser gerenciados de forma eficiente.
- Com o objetivo de garantir a segurança e a integridade dos dados, a Ciclope Corporations deseja transferir aproximadamente 5TB de dados para a nuvem AWS, assegurando cópias na região de São Paulo e na região Norte da Virgínia.
- Esta proposta refere-se a um projeto de backup de dados on-premises, que envolve a transferência de dados de Recife para a AWS.
- O projeto será executado utilizando uma conta AWS que será criada como parte do projeto, nas regiões de São Paulo (sa-east-1) e Norte da Virgínia (us-east-1).
- A Darede será responsável por configurar a arquitetura de backup na nuvem, utilizando AWS DataSync para a transferência dos dados, enquanto a Ciclope Corporations será responsável por garantir que todos os dados estejam disponíveis para a transferência antes do decomissionamento dos dados locais.

## 2. Resumo

- A Ciclope Corporations é uma empresa que atua na produção e distribuição de conteúdo audiovisual, com sede em Recife. A empresa possui um grande volume de dados, principalmente arquivos de vídeo, que precisam ser gerenciados de forma eficiente.
- O projeto visa garantir cópias dos dados na nuvem AWS, especificamente nas regiões de São Paulo e Norte da Virgínia, antes do decomissionamento dos dados locais.
- A proposta envolve a transferência de aproximadamente 5TB de dados utilizando AWS DataSync para mover os dados para o Amazon S3, onde serão armazenados de forma segura e durável.
- O projeto será executado em uma conta AWS que será criada como parte do projeto, nas regiões de São Paulo (sa-east-1) e Norte da Virgínia (us-east-1).
- A Darede será responsável por configurar a arquitetura de backup na nuvem e realizar a transferência dos dados, enquanto a Ciclope Corporations será responsável por garantir que todos os dados estejam disponíveis para a transferência.

## 3. Desafio

- Transferir aproximadamente 5TB de dados de vídeo de Recife para a nuvem AWS.
- Configurar agentes AWS DataSync on-premises para garantir a transferência contínua dos dados.
- Armazenar os dados transferidos no Amazon S3, utilizando S3 Standard para dados ativos e S3 Glacier para arquivamento.
- Garantir que as cópias dos dados estejam disponíveis nas regiões de São Paulo e Norte da Virgínia antes do decomissionamento dos dados locais.
- Implementar controles de segurança, incluindo criptografia em repouso e em trânsito, para proteger os dados durante a transferência e armazenamento.
- Validar a integridade dos dados após a transferência para assegurar que todas as informações foram copiadas corretamente.

## 4. Cenário apresentado

- Atualmente, a Ciclope Corporations possui aproximadamente 5TB de dados armazenados localmente em Recife, sendo a maioria composta por arquivos de vídeo.
- A infraestrutura atual não conta com soluções de backup na nuvem, o que representa um risco para a integridade e segurança dos dados.
- A equipe de TI da Ciclope Corporations é composta por 5 profissionais, especializados em gerenciamento de dados e infraestrutura, mas não possuem experiência prévia com soluções de nuvem.
- A empresa enfrenta limitações de largura de banda que podem impactar a transferência dos dados para a nuvem, além de estar sujeita a regulamentações de proteção de dados que precisam ser consideradas durante o processo de migração.
- Não há um plano de conformidade com a LGPD atualmente implementado, o que pode resultar em riscos legais e de reputação.
- A Ciclope Corporations está buscando uma solução que permita a transferência segura e eficiente dos dados para a nuvem AWS, garantindo cópias nas regiões de São Paulo e Norte da Virgínia antes do decomissionamento dos dados locais.

## 5. Arquitetura de solução

- A solução será implementada na AWS, utilizando uma conta que será criada como parte do projeto, nas regiões de São Paulo (sa-east-1) e Norte da Virgínia (us-east-1).
- A transferência dos dados de vídeo de Recife para a AWS será realizada utilizando o serviço AWS DataSync.
    - Serão configurados agentes DataSync on-premises para garantir a transferência contínua dos dados.
    - Os dados serão movidos para buckets do Amazon S3 nas regiões de São Paulo e Norte da Virgínia.
- Os dados transferidos serão armazenados no Amazon S3, utilizando S3 Standard para dados ativos e S3 Glacier para arquivamento.
    - Isso garantirá a durabilidade e a redundância dos dados antes do decomissionamento dos dados locais.
- A segurança dos dados será garantida através de controles de criptografia.
    - A criptografia em repouso será habilitada no S3 utilizando AES-256.
    - A criptografia em trânsito será implementada utilizando TLS 1.2+ durante a transferência dos dados.
- O gerenciamento de permissões de acesso aos dados será realizado através de políticas de IAM, garantindo acesso restrito e seguro.
- O fluxo de dados será monitorado para assegurar que a transferência ocorra de forma eficiente e dentro dos prazos estabelecidos.

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
- Configurar agentes AWS DataSync
    - Instalar e configurar agentes DataSync on-premises para transferência contínua dos dados.
    - Testar a conectividade e a configuração dos agentes.
- Transferir dados de Recife para a AWS
    - Utilizar AWS DataSync para mover 5TB de dados de vídeo para o Amazon S3.
    - Monitorar o progresso da transferência e resolver quaisquer problemas que possam surgir.
- Armazenar dados no Amazon S3
    - Configurar buckets do Amazon S3 nas regiões de São Paulo e Norte da Virgínia.
    - Armazenar dados ativos no S3 Standard e arquivar dados no S3 Glacier conforme necessário.
- Implementar controles de segurança
    - Habilitar criptografia em repouso no S3 utilizando AES-256.
    - Implementar criptografia em trânsito utilizando TLS 1.2+ durante a transferência dos dados.
    - Configurar políticas de IAM para gerenciar permissões de acesso aos dados.
- Validar a integridade dos dados
    - Realizar testes para garantir que todos os dados foram transferidos corretamente e estão acessíveis nas regiões designadas.
- Encerrar o projeto
    - Documentar o processo de transferência e os resultados.
    - Realizar uma reunião de encerramento com a equipe da Ciclope Corporations para discutir os resultados e lições aprendidas.

| Título do Escopo | Horas Mínimas | Horas Médias | BU Autoridade |
|------------------|---------------|--------------|---------------|
| Planejamento do Projeto | 21 | 31 | PDM |
| Configurar agentes AWS DataSync | 10 | 15 | Data Transfer |
| Transferir dados de Recife para a AWS | 80 | 120 | Data Transfer |
| Armazenar dados no Amazon S3 | 15 | 25 | Data Storage |
| Implementar controles de segurança | 10 | 15 | Security |
| Validar a integridade dos dados | 5 | 10 | Data Quality |
| Encerrar o projeto | 5 | 10 | Project Management |
| Total | 146 | 226 |  |

## 7. Informações da Proposta Técnica

- Versão da Proposta Técnica: V1
- A Proposta Técnica tem a validade de 60 dias, a partir da data da Proposta Comercial. Após essa data, o conteúdo técnico (Desafio, Arquitetura, Escopo, Critérios de Sucesso e/ou Resultados Esperados) não terá mais validade, sendo necessário atualizar a Proposta com a Equipe de Arquitetura/Pré-vendas da DAREDE.
- Código Verificador Interno: ARCHPSALES20250617V1

## 8. Premissas

- A proposta foi desenvolvida baseando-se nas informações fornecidas pela Ciclope Corporations através de: reuniões e trocas de e-mails compartilhados durante a fase de pré-vendas;
- A Ciclope Corporations é responsável por todos seus dados, backups, softwares, plugins, códigos fonte, branchs e administração de seus repositórios; todos os procedimentos necessários no caso de qualquer eventualidade que possa ocorrer e por se recuperar de qualquer falha durante a execução das atividades deste projeto, que não tenha relação direta com as mesmas;
- A Ciclope Corporations será responsável por fornecer os acessos necessários e informações sobre o ambiente para que a contratada possa seguir com o atendimento do projeto;
- A Ciclope Corporations fornecerá e se responsabilizará pela aquisição de todo o licenciamento de sistemas operacionais, software e plugins, além dos certificados digitais necessários, que não estiverem cobertos pelos modelos de licenciamento do Provedor de Nuvem ou disponibilizados de maneira simples para contratação em Marketplace, salvo quando expressamente definido como parte da proposta;
- A Ciclope Corporations deverá designar uma pessoa para disponibilizar toda a informação necessária e contar com conhecimento técnico suficiente para a boa condução das atividades ou solicitando internamente o que for preciso e atuar junto à equipe técnica da contratada se necessário, com agendamento a combinar entre as partes;
- Todas as atividades seguirão cronograma estabelecido entre as partes após a ativação do contrato;
- A Ciclope Corporations e seus colaboradores conhecem e estão de acordo com o modelo de responsabilidade compartilhada da AWS;
- Os custos de infraestrutura apresentados devem ser considerados como uma estimativa e podem variar conforme o uso real dos serviços.

## 9. Pontos não contemplados por esta proposta

### 9. Pontos não contemplados por esta proposta

Exceto quando expressamente indicados nesta proposta, não estão inclusos no projeto quaisquer serviços de desenho, desenvolvimento, criação, teste, ajuste, configuração, troubleshooting ou quaisquer outros procedimentos ou serviços que tenham a ver com:
<!-- Geral -->
- A implantação dos serviços propostos de forma assistida, compartilhada e presencial;
- A execução de tarefas fora do planejamento, havendo a necessidade, deverá ser previamente acordado novas ações, cronogramas e prazos;
- Esta proposta não contempla escopos de Disaster Recovery, embora o padrão de recuperação de desastres 'Active-Passive DR' esteja incluído na arquitetura proposta;
<!-- Monitoramento -->
- A implementação de quaisquer monitoramentos customizados com ferramenta ou serviço nativo;
<!-- Desenvolvimento -->
- Desenvolvimento e/ou refatoração de código (Backend/Frontend, APIs, ETL, Infraestrutura, esteira de CI/CD);
- Instalação de quaisquer bibliotecas de dependência de código, runtimes ou pacotes de SDK para funcionamento da aplicação;
<!-- Banco de Dados -->
- Estruturação e análise de queries, regras de negócio, plano de execução, indexação, saneamento ou interações diretas com os conteúdos de Bancos de dados;
- Migração e/ou implantação de servidores, aplicações e bancos de dados;
<!-- Infraestrutura e Redes -->
- Virtualização ou serviços de infraestrutura on-premise ou em outros provedores de nuvem não abordados no escopo desta proposta;
- Operação de equipamentos de Rede de data center, borda, WAN, LAN ou WLAN;
- Criação e recuperação de Backups que não estejam relacionados apenas a boas práticas de execução técnica das atividades contempladas neste projeto;
- A implementação de novos serviços em cloud ou ambiente diferente dos citados nessa proposta, exceto se documentados e aprovados pela Ciclope Corporations e DAREDE;
- A definição exata da quantidade de IOPS e throughput a serem utilizados nos discos rígidos dos servidores;
<!-- Segurança -->
- Refinamento de regras ou políticas em appliances ou softwares de segurança;
- A implementação de um SOC 24x7 junto ao time de segurança da contratante;
- Administração e manutenção das regras de Firewall personalizadas de acesso, bloqueio, whitelist e backlist;
<!-- Service Desk -->
- A implementação de um NOC para monitoramento ativo 24x7 dos recursos de nuvem com ferramenta interna da contratada;
<!-- Licenciamento -->
- Intermediação ou venda de licenças de Software que sejam necessárias para a migração e implementação do ambiente e/ou recursos da solução no provedor de computação em nuvem de destino;
<!-- Sustentação -->
- A atualização automatizada ou manual da aplicação da Ciclope Corporations, que poderá ser acompanhada como atividade de sustentação para garantir o funcionamento da infraestrutura, dentro das atribuições técnicas da DAREDE, mas que é de responsabilidade da Ciclope Corporations;

## 10. Fatores influenciadores

### 10. Fatores influenciadores

#### Fatores que influenciam cenários de custos
- Escolha de região;
- Possibilidade de reservas e savings plans para os serviços AWS contemplados na proposta;
  - Tempo de compromisso de reservas e savings plans (1 ou 3 anos);
  - Valor de entrada para reservas e savings plans (upfront): nenhum, parcial, total;
- Serviços em Multi-AZ ou Single-AZ;
- Uso de instâncias, serviços gerenciados ou serverless;

#### Premissas para cenários de custos
- Backups diários com 2% de alteração para volumes associados a instâncias EC2;
- Backups diários com 5% de alteração para dados armazenados no Amazon S3;
- Data transfer out do ambiente implementado (padrão);

#### Fatores de custos estimados que podem ser refinados
- Volume de tráfego de saída para a internet a partir da VPC;
- Volume de dados distribuídos pelo CloudFront e sua distribuição regional;
- Volume de tráfego de saída para outras regiões da AWS;
- Volume de dados alterado entre snapshots;
- Volume de logs gerados com monitoramento de recursos, atividades e configurações;

#### Fatores de custos não contemplados que envolvem análises à parte ou informações adicionais
- Volume de tráfego intrarregional (entre zonas de disponibilidade);
- Quantidade de chamadas de API do S3 para diversas operações;

#### Custos Equipamentos, Licenças ou AWS
Todas as calculadoras representam uma estimativa de custos.
- [Titulo da calculadora] - [On-Demand / Savings Plans de 1 ano / 3 anos]
  - Região: [Região AWS]
  - Link calculadora: [URL da calculadora AWS]
  - Upfront cost: X,XXX.XX USD
  - Monthly cost: X,XXX.XX USD
  - Yearly cost: XX,XXX.XX USD

## 11. Resultados esperados

### Resultados esperados

- Todos os 5TB de dados de vídeo serão transferidos de Recife para a nuvem AWS utilizando AWS DataSync, garantindo a eficiência na movimentação dos dados.
- Os dados transferidos serão armazenados de forma segura e durável no Amazon S3, utilizando S3 Standard para dados ativos e S3 Glacier para arquivamento.
- As cópias dos dados estarão disponíveis nas regiões de São Paulo e Norte da Virgínia, assegurando redundância e conformidade local.
- A segurança dos dados será garantida através da implementação de criptografia em repouso e em trânsito, protegendo as informações durante o armazenamento e a transferência.
- A integridade dos dados será validada após a transferência, assegurando que todos os dados foram copiados corretamente e estão acessíveis nas regiões designadas.

**Critérios de sucesso:**
- Completar a transferência de 5TB de dados dentro do prazo estabelecido de 3 meses.
- Garantir que a latência de acesso aos dados armazenados no S3 esteja abaixo de 100 ms.
- Validar que todos os dados transferidos estão acessíveis e íntegros nas regiões de São Paulo e Norte da Virgínia.

## 12. Estimativa de horas

- Horas setup 8x5 (mínimas): 146 horas
- Horas setup 8x5 (médias): 226 horas

## 13. Próximos passos

- Apresentação de proposta para a Ciclope Corporations, detalhando a arquitetura de backup e a estratégia de transferência de dados.
- Ajustes em cenários de custos de acordo com informações adicionais trazidas pelo cliente, garantindo que a proposta esteja alinhada com as expectativas financeiras.
- Avaliação por parte da Ciclope Corporations de qual seria a forma de implementação mais alinhada com suas expectativas e necessidades.
- Escolha de cenário de implantação e eventual ajuste no volume de horas de trabalho de acordo com as atividades selecionadas.

