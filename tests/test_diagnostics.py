import asyncio
import json
import pathlib
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from diagnostics import SessionRecorder, redact, MAX_BYTES, record_ui_event


class RecorderTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.temp.name) / '.config' / 'ClawMetrics'
        self.recorder = SessionRecorder(self.base, 'test', lambda: {'enabled': True}, lambda: '123')

    async def asyncTearDown(self):
        await self.recorder.stop()
        self.temp.cleanup()

    async def test_start_stop_and_durable_first_sample(self):
        status = await self.recorder.start()
        self.assertTrue(status['recording'])
        await self.recorder.start()  # idempotent
        self.assertEqual(len(self.recorder.status()['sessions']), 1)
        meta = json.loads((self.recorder.current / 'session.json').read_text())
        self.assertEqual(meta['samples'], 1)
        self.assertIn('game_id', (self.recorder.current / 'telemetry.csv').read_text())
        await self.recorder.stop()
        self.assertEqual(self.recorder.status()['sessions'][0]['state'], 'stopped')
        recovered = SessionRecorder(self.base, 'test', lambda: {}, lambda: None)
        self.assertEqual(recovered.status()['sessions'][0]['state'], 'stopped')

    async def test_recovery_only_marks_unclean_end(self):
        await self.recorder.start()
        await self.recorder.stop()
        path = self.recorder.current / 'session.json'
        meta = json.loads(path.read_text())
        meta['state'] = 'recording'  # persisted state left by a killed process
        path.write_text(json.dumps(meta))
        recovered = SessionRecorder(self.base, 'test', lambda: {}, lambda: None)
        self.assertEqual(recovered.status()['sessions'][0]['state'], 'interrupted')
        self.assertIn('Cause unknown', json.loads(path.read_text())['recovery_note'])

    async def test_report_uses_session_boot_and_time_window(self):
        await self.recorder.start()
        await self.recorder.stop()
        with patch('diagnostics.command_result', return_value={'ok': True, 'returncode': 0, 'text': 'amdgpu timeout\ndecky error\n'}) as cmd:
            result = self.recorder.export(self.recorder.current.name)
        args = cmd.call_args.args[0]
        self.assertIn(self.recorder.boot_id.replace('-', ''), args)
        self.assertNotIn(self.recorder.boot_id, args)
        self.assertIn('--since', args)
        self.assertIn('--until', args)
        with zipfile.ZipFile(result['path']) as report:
            self.assertIsNone(report.testzip())
            self.assertEqual(len(report.namelist()), 9)
            self.assertIn('editor-ui.jsonl',report.namelist())
            self.assertIn(b'amdgpu timeout', report.read('gpu-errors.log'))
            self.assertIn(b'decky error', report.read('decky.log'))
        self.assertEqual(pathlib.Path(result['path']).stat().st_mode & 0o777, 0o600)
        with self.assertRaises(ValueError):
            self.recorder.export('../../settings.json')

    async def test_filtered_logs_survive_general_log_flood(self):
        await self.recorder.start()
        await self.recorder.stop()
        def query(args):
            text = 'RGB config\n' * 2500
            if '--grep' in args:
                text = 'amdgpu ring timeout\n' if 'amdgpu' in args[-1] else 'PluginLoader failure\n'
            if '--priority' in args:
                text = 'kernel warning\n'
            return {'ok': True, 'returncode': 0, 'text': text}
        with patch('diagnostics.command_result', side_effect=query) as commands:
            result = self.recorder.export(self.recorder.current.name)
        self.assertEqual(commands.call_count, 4)
        for call in commands.call_args_list:
            self.assertIn(self.recorder.boot_id.replace('-', ''), call.args[0])
        with zipfile.ZipFile(result['path']) as report:
            self.assertIn(b'ring timeout', report.read('gpu-errors.log'))
            self.assertIn(b'PluginLoader failure', report.read('decky.log'))
            self.assertIn(b'kernel warning', report.read('system-warnings.log'))
            self.assertIn('compatibility.json', report.namelist())

    async def test_journal_failure_is_not_reported_as_no_errors(self):
        await self.recorder.start()
        await self.recorder.stop()
        with patch('diagnostics.command_result', return_value={
                'ok': False, 'returncode': 1, 'text': 'Failed to add match: Invalid argument'}):
            result = self.recorder.export(self.recorder.current.name)
        with zipfile.ZipFile(result['path']) as report:
            details = json.loads(report.read('diagnostics.json'))
            self.assertFalse(details['journal_ok'])
            self.assertEqual(details['journal_returncode'], 1)
            self.assertIn(b'collection failed', report.read('gpu-errors.log'))
            self.assertIn(b'collection failed', report.read('decky.log'))

    async def test_ui_export_uses_only_the_recorded_boot_and_time_window(self):
        await self.recorder.start();await self.recorder.stop()
        meta=self.recorder.meta
        entries=[{'at':meta['started_at'],'boot_id':self.recorder.boot_id,'event':'settings_save_start'},
                 {'at':meta['started_at']-100,'boot_id':self.recorder.boot_id,'event':'editor_open'},
                 {'at':meta['started_at'],'boot_id':'other-boot','event':'ui_error'}]
        (self.recorder.root/'editor-ui.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in entries))
        with patch('diagnostics.command_result',return_value={'ok':True,'returncode':0,'text':'','byte_truncated':True,'queried_output_bytes':700000,'captured_bytes':524288}):
            result=self.recorder.export(self.recorder.current.name)
        with zipfile.ZipFile(result['path']) as report:
            rows=[json.loads(line) for line in report.read('editor-ui.jsonl').splitlines()]
            self.assertEqual(rows,[entries[0]])
            details=json.loads(report.read('diagnostics.json'))
            self.assertEqual(details['ui_event_count'],1)
            self.assertTrue(details['log_queries']['system-journal.log']['byte_truncated'])
            self.assertIsNone(details['log_queries']['system-journal.log']['line_limit_reached'])

    async def test_invalid_boot_does_not_query_unrelated_current_boot(self):
        await self.recorder.start()
        await self.recorder.stop()
        path = self.recorder.current / 'session.json'
        meta = json.loads(path.read_text())
        meta['boot_id'] = 'invalid'
        path.write_text(json.dumps(meta))
        with patch('diagnostics.command_result') as command:
            result = self.recorder.export(self.recorder.current.name)
        command.assert_not_called()
        with zipfile.ZipFile(result['path']) as report:
            self.assertFalse(json.loads(report.read('diagnostics.json'))['journal_ok'])
            self.assertIn(b'invalid session boot ID', report.read('system-journal.log'))

    async def test_limit_preserves_evidence_and_retention(self):
        # Exported ZIPs share the session prefix but must not count as directories.
        (self.recorder.root / 'session-20000101T000000Z-aaaaaaaa-CrashReport.zip').write_bytes(b'zip')
        for _ in range(6):
            await self.recorder.start()
            await self.recorder.stop()
        self.assertEqual(len(self.recorder.status()['sessions']), 5)
        with (self.recorder.current / 'telemetry.csv').open('ab') as stream:
            stream.truncate(MAX_BYTES)
        self.assertFalse(self.recorder._sample())
        self.assertEqual(self.recorder.meta['state'], 'size_limit')

    def test_redaction(self):
        value = redact('/home/ivo/game token=abc password:xyz 192.168.1.1')
        self.assertNotIn('ivo', value)
        self.assertNotIn('abc', value)
        self.assertNotIn('xyz', value)
        self.assertNotIn('192.168.1.1', value)


class OverlayDetectionTests(unittest.TestCase):
    def test_exact_library_only_and_deleted_mapping(self):
        from diagnostics import overlay_loaded
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            process = root / '123'
            process.mkdir()
            maps = process / 'maps'
            maps.write_text('100-200 r-xp 0 00:00 0 /plugin/native64/libMangoHud.so.other\n')
            self.assertFalse(overlay_loaded('/plugin/native64/libMangoHud.so', root))
            maps.write_text('100-200 r-xp 0 00:00 0 /plugin/native64/libMangoHud.so (deleted)\n')
            self.assertTrue(overlay_loaded('/plugin/native64/libMangoHud.so', root))
            maps.write_text('100-200 r-xp 0 00:00 0 /plugin/native64/libMangoHud_opengl.so\n')
            self.assertTrue(overlay_loaded(('/plugin/native64/libMangoHud.so',
                                            '/plugin/native64/libMangoHud_opengl.so'), root))


class AutomaticLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_detection_debounce_manual_pause_and_reload(self):
        from diagnostics import OverlayRecording
        from unittest.mock import AsyncMock, Mock
        recorder = Mock()
        recorder.status.return_value = {'recording': False}
        recorder.start = AsyncMock()
        recorder.stop = AsyncMock()
        control = OverlayRecording(recorder)
        await control.update(False)
        recorder.start.assert_not_awaited()
        await control.update(True)
        recorder.start.assert_awaited_once()
        await control.update(True)  # no repeated starts even after limit/error
        recorder.start.assert_awaited_once()
        await control.update(False)
        await control.update(False)
        await control.update(None)  # inaccessible /proc must not close a session
        recorder.stop.assert_not_awaited()
        for _ in range(3):
            await control.update(False)
        recorder.stop.assert_awaited_once_with('overlay_unloaded')
        await control.update(True)
        self.assertEqual(recorder.start.await_count, 2)
        await control.manual(False)
        await control.update(True)
        self.assertEqual(recorder.start.await_count, 2)
        for _ in range(3):
            await control.update(False)
        await control.update(True)
        self.assertEqual(recorder.start.await_count, 3)


class CompatibilityTests(unittest.TestCase):
    def test_discovery_missing_nodes_and_named_sensors(self):
        from diagnostics import compatibility_snapshot
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            empty = compatibility_snapshot(root, root / 'os-release')
            self.assertEqual(empty['hwmon'], [])
            self.assertIsNone(empty['device']['product_name'])
            hw = root / 'class/hwmon/hwmon7'
            hw.mkdir(parents=True)
            (hw / 'name').write_text('k10temp')
            (hw / 'temp1_input').write_text('42000')
            (hw / 'temp1_label').write_text('Tctl')
            (root / 'os-release').write_text('ID=bazzite\nVERSION_ID=44')
            found = compatibility_snapshot(root, root / 'os-release')
            self.assertIn('bazzite', found['os_release'])
            self.assertEqual(found['hwmon'][0]['channels'][0]['label'], 'Tctl')
            self.assertTrue(found['hwmon'][0]['channels'][0]['readable'])
            self.assertIn('Unverified', found['support_status'])

class UiEventTests(unittest.TestCase):
    def test_command_output_keeps_last_error_after_rgb_flood(self):
        import sys
        from diagnostics import command_result
        result=command_result([sys.executable,'-c',"import sys;sys.stdout.write('RGB config spam\\n'*40000+'CRITICAL_STEAM_UI_ERROR\\n')"])
        self.assertTrue(result['ok'])
        self.assertTrue(result['byte_truncated'])
        self.assertEqual(result['captured_bytes'],512*1024)
        self.assertIn('CRITICAL_STEAM_UI_ERROR',result['text'])

    def test_ui_trace_survives_reopen_is_bounded_and_redacted(self):
        with tempfile.TemporaryDirectory() as directory:
            record_ui_event(directory,'editor_open')
            record_ui_event(directory,'ui_error','/home/alice/file token=secret 192.168.1.1')
            path=pathlib.Path(directory)/'diagnostics/editor-ui.jsonl'
            text=path.read_text();self.assertIn('editor_open',text)
            self.assertNotIn('alice',text);self.assertNotIn('192.168.1.1',text);self.assertNotIn('token=secret',text)
            self.assertEqual(path.stat().st_mode&0o777,0o600)
            with patch('diagnostics.os.fsync'):
                for _ in range(220):record_ui_event(directory,'editor_exit_request','x'*400)
            self.assertLess(path.stat().st_size,61000)
            self.assertEqual(json.loads(path.read_text().splitlines()[-1])['event'],'editor_exit_request')
            with self.assertRaises(ValueError):record_ui_event(directory,'unknown')
