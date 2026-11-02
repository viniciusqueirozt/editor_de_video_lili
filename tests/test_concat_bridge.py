import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from lili.concat_bridge import ConcatBridge,find_concat,MAX_LINE
from lili.core import EditorError

class ConcatBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir="work/tests");self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.binary=self.root/"concat.exe";self.binary.write_bytes(b"synthetic test only")
    def process(self,replies):
        process=Mock();process.stdout=io.BytesIO(b"".join(json.dumps(r).encode()+b"\n" for r in replies));process.stdin=io.BytesIO();process.poll.return_value=None;return process
    def test_missing_binary_is_reported_without_starting_a_process(self):
        runner=Mock();bridge=ConcatBridge(self.root/'missing.exe',scope=self.root,popen=runner)
        self.assertFalse(bridge.inspect()['installed']);self.assertFalse(bridge.availability()['editing_ready']);runner.assert_not_called()
        self.assertIsNone(find_concat({'LILI_CONCAT':'relative.exe'}))
    def test_discovery_only_calls_version_and_catalogue_under_a_local_root(self):
        replies=[{'id':1,'result':{'serverInfo':{'name':'Concat'}}},{'id':2,'result':{'tools':[{'name':'concat_version'},{'name':'effects_list'},{'name':'edit_apply'}]}},{'id':3,'result':{'content':[{'type':'text','text':'{"version":"synthetic"}'}]}},{'id':4,'result':{'structuredContent':{'effects':[{'id':'example'}]}}}]
        process=self.process(replies);writes=[]
        class Input(io.BytesIO):
            def write(self,data):writes.append(json.loads(data));return len(data)
        process.stdin=Input();runner=Mock(return_value=process);bridge=ConcatBridge(self.binary,scope=self.root/'isolated',popen=runner)
        result=bridge.inspect();self.assertTrue(result['discovery_ok']);self.assertFalse(result['editing_ready']);self.assertEqual(result['engine']['version'],'synthetic')
        called=[r['params']['name'] for r in writes if r.get('method')=='tools/call'];self.assertEqual(called,['concat_version','effects_list']);self.assertNotIn('edit_apply',called)
        args,kwargs=runner.call_args;self.assertEqual(args[0],[str(self.binary),'--mcp','headless']);self.assertEqual(kwargs['env']['CONCAT_MCP_ROOTS'],str(self.root/'isolated'));self.assertNotIn('CONCAT_API_TOKEN',kwargs['env']);process.terminate.assert_called_once()
    def test_protocol_errors_are_sanitized_and_process_is_stopped(self):
        process=self.process([{'id':1,'error':{'message':'private/path/secret'}}]);bridge=ConcatBridge(self.binary,scope=self.root,popen=Mock(return_value=process))
        with self.assertRaises(EditorError) as caught:bridge.inspect()
        self.assertNotIn('secret',str(caught.exception));process.terminate.assert_called_once()
    def test_duplicate_pagination_is_refused(self):
        process=self.process([{'id':1,'result':{}},{'id':2,'result':{'tools':[],'nextCursor':'repeat'}},{'id':3,'result':{'tools':[],'nextCursor':'repeat'}}])
        with self.assertRaises(EditorError):ConcatBridge(self.binary,scope=self.root,popen=Mock(return_value=process)).inspect()
    def test_oversized_responses_do_not_escape_the_limit(self):
        process=self.process([]);process.stdout=io.BytesIO(b'x'*(MAX_LINE+1)+b'\n')
        with self.assertRaises(EditorError):ConcatBridge(self.binary,scope=self.root,popen=Mock(return_value=process)).inspect()

    def test_process_start_failure_is_sanitized(self):
        with self.assertRaises(EditorError) as caught:
            ConcatBridge(self.binary,scope=self.root,popen=Mock(side_effect=PermissionError('private/path/secret'))).inspect()
        self.assertEqual(caught.exception.status,503);self.assertNotIn('secret',str(caught.exception))
