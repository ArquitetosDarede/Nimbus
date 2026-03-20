import sys, os
sys.path.insert(0, 'src')
print('START', flush=True)

from agents.analysis_agent import AnalysisAgent

print('Creating AnalysisAgent...', flush=True)
agent = AnalysisAgent()

print('Running analyze...', flush=True)
try:
    result = agent.analyze('Proposta backup 5TB Ciclope Corporations', input_type='text', notion_cache='')
    print(f"Success: {result.get('status', 'ok')}", flush=True)
    if result.get('error'):
        print(f"Error: {result.get('error')}", flush=True)
    else:
        analysis = result.get('analysis', {})
        if isinstance(analysis, dict):
            print(f"Company: {analysis.get('clientInfo', {}).get('companyName', '?')}", flush=True)
        else:
            print(f"Analysis text: {str(analysis)[:100]}", flush=True)
except Exception as e:
    print(f'Exception: {type(e).__name__}: {e}', flush=True)
    import traceback
    traceback.print_exc()

print('DONE', flush=True)
