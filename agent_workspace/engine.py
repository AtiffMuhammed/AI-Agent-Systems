"""Retrieve, synthesize, validate references, and record an observable run."""
import re
import time

from . import providers
from .store import clean_text, terms


def evidence_claims(question, sources):
    tokens = set(terms(question))
    claims = []
    for source in sources[:4]:
        lines = [(index,line) for index,line in enumerate(source['body'].splitlines()) if line.strip()]
        lines.sort(key=lambda pair: -len(tokens.intersection(terms(pair[1]))))
        if not lines:
            continue
        index,line = lines[0]
        excerpt = line.strip()
        if len(excerpt) > 900:
            excerpt = excerpt[:900] + ' … [excerpt truncated]'
        claims.append({'text':f'Line {source["start_line"] + index}: {excerpt}', 'sources':[source['source_id']]})
    return claims


def validate_output(data, sources):
    if not isinstance(data,dict) or type(data.get('insufficient_evidence')) is not bool:
        raise providers.ProviderError('Model response failed the evidence format check.')
    claims, steps = data.get('claims'), data.get('next_steps')
    if not isinstance(claims,list) or not isinstance(steps,list) or len(claims)>8 or len(steps)>5:
        raise providers.ProviderError('Model response failed the evidence format check.')
    allowed = {s['source_id'] for s in sources}
    verified = []
    for claim in claims:
        if not isinstance(claim,dict):
            raise providers.ProviderError('Model claim failed validation.')
        text = clean_text(claim.get('text'),'Claim',2400)
        refs = claim.get('sources')
        if not isinstance(refs,list) or not refs or any(not isinstance(ref,str) or ref not in allowed for ref in refs) or re.search(r'\[S\d+\]',text):
            raise providers.ProviderError('Model cited a missing or invalid source.')
        verified.append({'text':text,'sources':list(dict.fromkeys(refs))})
    cleaned = [clean_text(s,'Suggested step',300) for s in steps]
    if data['insufficient_evidence']:
        return [], [], True
    if not verified:
        raise providers.ProviderError('Model returned no supported claims.')
    return verified,cleaned,False


def evidence_steps(sources):
    """Offer explicit TODOs from retrieved notes; never mark them executed."""
    steps = []
    for source in sources:
        for line in source['body'].splitlines():
            match = re.match(r'^\s*(?:[-*]\s+)?(?:TODO\s*:\s*|\[ \]\s+)(.+)',line,re.I)
            if match:
                title = match.group(1).strip()
                if 0 < len(title) <= 300 and title not in steps:
                    steps.append(title)
    return steps[:5]


def answer(store, project, question, provider='evidence', generator=None):
    question = clean_text(question,'Question',2000)
    if provider not in ('evidence','ollama','openrouter'):
        raise ValueError('Unknown answer mode.')
    started = time.monotonic()
    trace, warnings = [], []
    def event(stage, detail):
        trace.append({'stage':stage,'detail':detail,'elapsed_ms':round((time.monotonic()-started)*1000)})
    event('retrieve','Search project-local document chunks with SQLite FTS5/BM25.')
    sources = store.search(project,question)
    event('retrieve',f'Selected {len(sources)} source passages.')
    claims, steps, mode = [], [], 'evidence'
    status = 'no_evidence' if not sources else 'answered'
    if sources:
        claims = evidence_claims(question,sources)
        steps = evidence_steps(sources)
        if provider != 'evidence':
            event('synthesize',f'Request structured claims from {provider}.')
            try:
                data = (generator or providers.generate)(provider,question,sources)
                claims, steps, insufficient = validate_output(data,sources)
                mode = provider
                status = 'insufficient_evidence' if insufficient else 'answered'
                event('validate','All claim references point to retrieved sources; factual accuracy still needs review.')
            except (providers.ProviderError,ValueError) as error:
                claims = evidence_claims(question,sources)
                steps = evidence_steps(sources)
                warnings.append(str(error))
                status = 'fallback'
                event('fallback','Model output was unavailable or invalid. Returned actual source excerpts.')
        else:
            event('extract','Returned matching source lines without an LLM call.')
    else:
        event('stop','No matching evidence. No model request was made.')
    event('save','Save the result and evidence snapshots for export and later review.')
    result = {'question':question,'requested_provider':provider,'mode':mode,'status':status,'claims':claims,
              'next_steps':steps,'sources':sources,'trace':trace,'warnings':warnings,
              'elapsed_ms':round((time.monotonic()-started)*1000)}
    return store.save_run(project,result)


def markdown_report(run):
    data = run['result']
    lines = ['# Project evidence report', '',f'Question: {data["question"]}', '',
             f'Created (UTC): {run["created"]}', f'Mode: {data["mode"]} | Status: {data["status"]}', '']
    if data['mode'] == 'evidence':
        lines.extend(['These are retrieved excerpts, not an AI-generated answer.', ''])
    if not data['claims']:
        lines.extend(['The imported evidence does not answer this question. Try specific project terms or import another source.', ''])
    for claim in data['claims']:
        refs = ' '.join('[' + ref + ']' for ref in claim['sources'])
        # Export as a plain fenced quote so embedded Markdown remains visibly data.
        fence = '`' * max(3, max((len(m[0]) for m in re.finditer(r'`+',claim['text'])),default=0)+1)
        lines.extend([f'{refs}', fence+'text', claim['text'], fence, ''])
    if data['next_steps']:
        lines.extend(['## Suggested next steps (not executed)', ''])
        lines.extend('- ' + step.replace('\n',' ') for step in data['next_steps'])
        lines.append('')
    lines.extend(['## Evidence snapshots', ''])
    for source in data['sources']:
        body = source['body']
        fence = '`' * max(3,max((len(m[0]) for m in re.finditer(r'`+',body)),default=0)+1)
        lines.extend([f'### [{source["source_id"]}] {source["name"]} — lines {source["start_line"]}–{source["end_line"]}',
                      f'SHA-256: {source["digest"]}', '',fence+'text',body,fence,''])
    if data['warnings']:
        lines.extend(['## Warnings', '', *data['warnings'], ''])
    lines.extend(['## Limits', '', 'Search is lexical. Valid source references do not prove that an AI claim is factually supported. Review the excerpts. Suggestions are never executed automatically.', ''])
    return '\n'.join(lines)
