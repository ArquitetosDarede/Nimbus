#!/usr/bin/env python3
"""Direct test of proposal generation pipeline."""
import asyncio
import json
from datetime import datetime
from src.agents.orchestrator import OrchestratorAgent

async def test_batatas_generation():
    """Test Batatas Inc proposal generation directly."""
    orchestrator = OrchestratorAgent()
    
    # Build full context with all known information
    client_info = {
        "client": "Batatas Inc.",
        "project": "Migração de servidor Windows 2019 para AWS EC2",
        "contact": "João Moreira (jmoreira@batatasinc.com, +55 11 97433-3333)",
        "business_requirements": [
            "Migrar servidor Windows 2019 para AWS EC2",
            "Manter integração com Active Directory (AD) on-premises"
        ],
        "technical_requirements": [
            "Servidor alvo com 32GB de RAM e 16 vCPUs",
            "Utilizar AWS MGN para migração",
            "Dados: 2TB"
        ],
        "scope_inclusions": [
            "Configuração de instância EC2",
            "Setup de AWS MGN",
            "Teste de integração com AD",
            "Replicação contínua de dados",
            "Testes de inicialização",
            "Cutover controlado",
            "Validação pós-migração"
        ],
        "scope_exclusions": [
            "Backup",
            "Treinamento do usuário"
        ],
        "technologies": ["AWS EC2", "AWS MGN", "Windows 2019", "Active Directory"],
        "constraints": [
            "Janela de manutenção aos finais de semana",
            "Plano de contingência para reversão"
        ],
        "timeline_days": 17,
        "timeline_detail": "Preparação 2d, instalação agent 1d, replicação contínua 7d, testes e templates 5d, cutover 1d, validação 1d",
        "budget": 5000,
        "budget_currency": "BRL",
        "migration_steps": [
            "Preparação do AWS MGN Replication Server",
            "Instalação do AWS Application Migration Service Agent",
            "Replicação contínua dos dados",
            "Criação de launch templates",
            "Testes de inicialização",
            "Cutover com corte de tráfego",
            "Validação pós-migração",
            "Rollback automático se necessário"
        ],
        "ad_tests": [
            "Autenticação de usuários AD",
            "Acesso a network shares",
            "Aplicação de Group Policies",
            "Sincronização NTP",
            "Conectividade RDP",
            "Teste de rollback"
        ]
    }
    
    input_text = f"""
Cliente: {client_info['client']}
Projeto: {client_info['project']}
Contato: {client_info['contact']}

Requisitos de Negócio:
{chr(10).join(f"- {req}" for req in client_info['business_requirements'])}

Requisitos Técnicos:
{chr(10).join(f"- {req}" for req in client_info['technical_requirements'])}

Escopo - Inclusões:
{chr(10).join(f"- {inc}" for inc in client_info['scope_inclusions'])}

Escopo - Exclusões:
{chr(10).join(f"- {exc}" for exc in client_info['scope_exclusions'])}

Tecnologias: {', '.join(client_info['technologies'])}

Restrições:
{chr(10).join(f"- {rest}" for rest in client_info['constraints'])}

Cronograma: {client_info['timeline_days']} dias
Detalhe: {client_info['timeline_detail']}

Orçamento: R$ {client_info['budget']:,.2f}

Passos da Migração:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(client_info['migration_steps']))}

Testes de Integração com AD:
{chr(10).join(f"- {test}" for test in client_info['ad_tests'])}
"""

    print("[DEBUG] Iniciando análise de requisitos...")
    
    # Step 1: Analyze requirements
    analysis_result = orchestrator.analyze_requirements(input_text, input_type="text")
    if isinstance(analysis_result, dict) and "errors" in analysis_result:
        print(f"[ANALYSIS ERROR] {analysis_result}")
        return
    
    analysis = analysis_result.get("analysis", {})
    print(f"[ANALYSIS OK] {len(analysis.get('data_gaps', []))} gaps identified")
    
    # Step 2: If no critical gaps, generate proposal
    if analysis.get("confidence_score", 0) > 0.6:
        print("[DEBUG] Confiança suficiente. Iniciando geração de proposta...")
        
        generation_context = {
            "user_input": input_text,
            "analysis": analysis,
            "client_info": client_info,
            "chat_history": [],
            "known_user": {},
            "ingestion_evidence": {}
        }
        
        proposal_result = orchestrator.generate_proposal(
            client_key="Batatas Inc",
            generation_context=generation_context
        )
        
        if isinstance(proposal_result, dict) and proposal_result.get("status") == "success":
            proposal = proposal_result.get("proposal", {})
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"propostas/nimbus-Batatas_Inc-{timestamp}-TEST.md"
            
            # Save proposal
            with open(filename, "w", encoding="utf-8") as f:
                f.write(proposal.get("markdown", ""))
            
            print(f"\n✅ [SUCCESS] Proposta gerada: {filename}")
            
            # Print metrics
            sections = proposal.get("sections", [])
            print(f"📊 Métricas: {len(sections)} seções")
            print(f"📋 Review Score: {proposal_result.get('review_score', 'N/A')}")
            return filename
        else:
            print(f"[GENERATION ERROR] {proposal_result}")
            return None
    else:
        print(f"[ANALYSIS] Confiança baixa ({analysis.get('confidence_score', 0):.1%}). Questões adicionais necessárias.")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_batatas_generation())
    print(f"\nResultado final: {result}")
