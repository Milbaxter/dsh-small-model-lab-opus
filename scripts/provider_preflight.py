#!/usr/bin/env python3
"""Test native function calling for every currently listed Qwen3-8B endpoint.

Credentials remain in the environment. No substitute models or provider fallback.
This is plumbing, not an evaluation task or grader.
"""
import datetime
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

ROOT = 'https://openrouter.ai/api/v1'
MODEL = 'qwen/qwen3-8b'

def request(path, body=None):
    headers = {'Authorization': 'Bearer ' + os.environ['OPENROUTER_API_KEY'],
               'Content-Type': 'application/json'}
    req = urllib.request.Request(ROOT + path, headers=headers,
                                 data=None if body is None else json.dumps(body).encode())
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def main():
    out = Path(os.environ.get('PREFLIGHT_OUTPUT', '.local/preflight.json'))
    out.parent.mkdir(parents=True, exist_ok=True)
    status, catalog = request('/models/qwen/qwen3-8b/endpoints')
    if status != 200:
        raise SystemExit('Cannot enumerate providers; refusing inference.')
    report = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'model': MODEL, 'endpoint_catalog': catalog, 'attempts': [], 'passed': False,
              'reported_cost_usd': 0}
    for endpoint in catalog['data']['endpoints']:
        provider = endpoint['tag']
        body = {'model': MODEL, 'provider': {'only': [provider], 'allow_fallbacks': False},
                'temperature': 0, 'top_p': 1, 'max_tokens': 256,
                'reasoning': {'enabled': False},
                'messages': [{'role': 'user', 'content': 'Call the echo tool with text set to probe-ok. Do not answer with text. /no_think'}],
                'tools': [{'type': 'function', 'function': {'name': 'echo',
                    'description': 'Echo a string.', 'parameters': {'type': 'object',
                    'properties': {'text': {'type': 'string'}}, 'required': ['text'],
                    'additionalProperties': False}}}], 'tool_choice': 'auto'}
        code, result = request('/chat/completions', body)
        calls = ((result.get('choices') or [{}])[0].get('message') or {}).get('tool_calls', [])
        passed = False
        try:
            passed = any(c['function']['name'] == 'echo' and
                         json.loads(c['function']['arguments']) == {'text': 'probe-ok'} for c in calls)
        except (KeyError, ValueError, TypeError):
            pass
        cost = (result.get('usage') or {}).get('cost')
        report['reported_cost_usd'] += cost or 0
        report['attempts'].append({'provider': provider, 'http_status': code,
                                   'request': body, 'response': result, 'passed': passed,
                                   'cost_reported': cost})
        report['passed'] = passed
        out.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'provider': provider, 'status': code, 'passed': passed,
                          'cost': cost, 'error': result.get('error')}), flush=True)
        if passed:
            report['selected_provider'] = provider
            break
    report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    out.write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if report['passed'] else 2)

if __name__ == '__main__':
    main()
