import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent_workspace.engine import answer, markdown_report
from agent_workspace.providers import ProviderError, generate
from agent_workspace.store import Store


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name)/'store.db')
        self.project = self.store.create_project('Monitor')['id']
        self.store.import_document(self.project,'design.md','# Monitor\nThe ESP32 samples temperature every 30 seconds.\nBattery voltage is not measured yet.')

    def test_evidence_mode_is_offline_and_preserves_source_references(self):
        with patch('agent_workspace.providers.generate',side_effect=AssertionError('No model call expected')):
            run = answer(self.store,self.project,'How often does ESP32 sample temperature?')
        result = run['result']
        self.assertEqual(result['mode'],'evidence')
        self.assertIn('30 seconds',result['claims'][0]['text'])
        self.assertEqual(result['claims'][0]['sources'],['S1'])
        self.assertEqual(self.store.run(self.project,run['id']),run)
        self.assertIn('design.md — lines 1–3',markdown_report(run))

    def test_unknown_question_does_not_call_provider(self):
        def must_not_run(*args):
            self.fail('No evidence must mean no model call')
        run = answer(self.store,self.project,'quasars zebras','ollama',must_not_run)
        self.assertEqual(run['result']['status'],'no_evidence')
        self.assertEqual(run['result']['sources'],[])

    def test_model_synthesis_and_suggestions_are_saved_but_no_tasks_are_created(self):
        model = lambda *args: {'claims':[{'text':'The sample interval is 30 seconds.','sources':['S1']}],
                              'next_steps':['Measure battery voltage.'],'insufficient_evidence':False}
        result = answer(self.store,self.project,'temperature','ollama',model)['result']
        self.assertEqual(result['mode'],'ollama')
        self.assertEqual(result['next_steps'],['Measure battery voltage.'])
        self.assertEqual(self.store.tasks(self.project),[])

    def test_bad_citations_and_invalid_shapes_fall_back_without_fake_model_answer(self):
        bad_outputs = [None, {}, {'insufficient_evidence':False,'claims':[{'text':'Invented fact','sources':['S99']}],'next_steps':[]},
                       {'insufficient_evidence':False,'claims':[{'text':'Fact [S2]','sources':['S1']}],'next_steps':[]},
                       {'insufficient_evidence':False,'claims':[{'text':'Fact','sources':['S1']}],'next_steps':[None]}]
        for value in bad_outputs:
            with self.subTest(value=value):
                result = answer(self.store,self.project,'temperature','ollama',lambda *a:value)['result']
                self.assertEqual(result['status'],'fallback')
                self.assertEqual(result['mode'],'evidence')
                self.assertIn('30 seconds',result['claims'][0]['text'])

    def test_provider_error_is_visible_and_falls_back(self):
        def fail(*args):
            raise ProviderError('Provider unavailable.')
        result = answer(self.store,self.project,'temperature','openrouter',fail)['result']
        self.assertEqual(result['warnings'],['Provider unavailable.'])
        self.assertEqual(result['requested_provider'],'openrouter')
        self.assertEqual(result['mode'],'evidence')

    def test_model_can_decline_insufficient_evidence(self):
        result = answer(self.store,self.project,'temperature','ollama',lambda *a:{'claims':[],'next_steps':[],'insufficient_evidence':True})['result']
        self.assertEqual(result['status'],'insufficient_evidence')
        self.assertEqual(result['claims'],[])

    def test_offline_mode_extracts_explicit_todos_but_does_not_execute_them(self):
        self.store.import_document(self.project,'tests.md','TODO: Calibrate the sensor.\n- [ ] Measure battery voltage.')
        result = answer(self.store,self.project,'calibrate sensor')['result']
        self.assertIn('Calibrate the sensor.',result['next_steps'])
        self.assertEqual(self.store.tasks(self.project),[])

    def test_model_prompt_uses_only_selected_project_evidence(self):
        other = self.store.create_project('Other')['id']
        self.store.import_document(other,'notes.md','SENSITIVE-UNRELATED temperature project')
        sources = self.store.search(self.project,'temperature')
        response = {'message':{'content':json.dumps({'insufficient_evidence':False,'claims':[{'text':'30 seconds','sources':['S1']}],'next_steps':[]})}}
        with patch.dict(os.environ,{'OLLAMA_MODEL':'installed-model'}), patch('agent_workspace.providers.post_json',return_value=response) as post:
            generate('ollama','temperature',sources)
        url,payload,headers = post.call_args.args
        self.assertEqual(url,'http://127.0.0.1:11434/api/chat')
        self.assertFalse(payload['stream'])
        self.assertNotIn('SENSITIVE-UNRELATED',json.dumps(payload))
        self.assertIn('untrusted',payload['messages'][0]['content'])

    def test_openrouter_key_is_only_in_server_request_header(self):
        response = {'choices':[{'message':{'content':'{}'}}]}
        with patch.dict(os.environ,{'OPENROUTER_MODEL':'chosen-model','OPENROUTER_API_KEY':'test-only-secret'}), patch('agent_workspace.providers.post_json',return_value=response) as post:
            generate('openrouter','temperature',self.store.search(self.project,'temperature'))
        url,payload,headers = post.call_args.args
        self.assertEqual(url,'https://openrouter.ai/api/v1/chat/completions')
        self.assertEqual(headers['Authorization'],'Bearer test-only-secret')
        self.assertNotIn('test-only-secret',json.dumps(payload))

    def test_export_fences_source_markdown_including_nested_backticks(self):
        self.store.import_document(self.project,'code.md','```\nbattery\n```')
        report = markdown_report(answer(self.store,self.project,'battery'))
        self.assertIn('````text',report)

    def test_export_escapes_links_and_html_in_untrusted_suggestions(self):
        model = lambda *a:{'insufficient_evidence':False,'claims':[{'text':'30 seconds','sources':['S1']}],
                          'next_steps':['![image](https://example.com/track) <script>bad</script>']}
        report = markdown_report(answer(self.store,self.project,'temperature','ollama',model))
        self.assertIn(r'\!\[image\]\(https://example.com/track\)',report)
        self.assertIn(r'\<script\>',report)
