"""Constructed VM evidence exercises contracts, not a real Linux guest."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from campuslab.vm_course import analyze, collect, compare_identity, make_task, validate_spec


VM_ID = '12345678-1234-4234-8234-123456789abc'


def vm_evidence(provider='virtualbox'):
    spec = make_task()
    now = datetime.now(timezone.utc)
    target = r'C:\VirtualBox\VBoxManage.exe' if provider == 'virtualbox' else r'C:\VMware\vmrun.exe'
    selected = VM_ID if provider == 'virtualbox' else r'C:\VMs\Linux\Linux.vmx'
    return dict(schema=1, task_id=spec['id'], collected_at=now.isoformat(),
                target=dict(requested=target, actual=target, exists=True),
                facts=dict(os='Windows', host=dict(id='a'*64,
                    virtualization=dict(firmware_enabled=True, vm_monitor=True, slat=True, hypervisor_present=False),
                    source='constructed CIM', error=''),
                    software=dict(provider=provider, version='7.2.0' if provider == 'virtualbox' else '1.17.0', returncode=0, error=''),
                    inventory=dict(kind='registered' if provider == 'virtualbox' else 'running',
                        returncode=0, items=[dict(id=selected, name='Linux')], error=''),
                    instance=dict(requested=selected, uuid=VM_ID, name='Linux', os_type='Ubuntu_64',
                        state='running', exists=True, listed=True, error=''),
                    guest=dict(schema=1, task_id=spec['id'], vm_id=selected, hardware_uuid=VM_ID,
                        machine_id_sha256='b'*64, collected_at=(now-timedelta(seconds=1)).isoformat(),
                        os='Linux', kernel='6.8.0', verification=dict(returncode=0, stdout='Linux:6', error=''),
                        source='manual-linux-guest-probe')))


class VmTest(unittest.TestCase):
    def test_complete_each_provider(self):
        for provider in ('virtualbox', 'vmware'):
            with self.subTest(provider=provider):
                self.assertTrue(analyze(make_task(), vm_evidence(provider))['passed'])

    def test_software_not_guest_or_instance(self):
        r=vm_evidence(); r['facts']['guest']=None
        self.assertFalse(analyze(make_task(), r)['passed'])
        statuses={c['id']:c['status'] for c in analyze(make_task(),r)['checks']}
        self.assertEqual(statuses['vm:software'],'pass')
        self.assertEqual(statuses['guest:linux'],'unknown')
        r['facts']['instance'].update(requested=None,uuid=None,name=None,os_type=None,state=None,exists=None,listed=None)
        self.assertEqual(next(c['status'] for c in analyze(make_task(),r)['checks'] if c['id']=='vm:instance'),'unknown')

    def test_host_unknown_and_false(self):
        r=vm_evidence()
        for key in r['facts']['host']['virtualization']:
            r['facts']['host']['virtualization'][key]=None
        self.assertEqual(analyze(make_task(),r)['checks'][1]['status'],'unknown')
        r['facts']['host']['virtualization']['firmware_enabled']=False
        self.assertEqual(analyze(make_task(),r)['checks'][1]['status'],'mismatch')
        r['facts']['host']['virtualization']['hypervisor_present']=True
        self.assertEqual(analyze(make_task(),r)['checks'][1]['status'],'unknown')

    def test_incomplete_and_wrong_types_rejected(self):
        mutations=[lambda r:r['facts'].pop('guest'), lambda r:r['target'].update(actual=r'C:\Other\VBoxManage.exe'),
            lambda r:r['facts']['software'].update(returncode=False),lambda r:r['facts']['instance'].update(exists=1),
            lambda r:r['facts']['host']['virtualization'].update(slat='yes'),
            lambda r:r['facts']['guest']['verification'].update(returncode=False),
            lambda r:r['facts']['guest'].update(vm_id='ffffffff-ffff-4fff-8fff-ffffffffffff'),
            lambda r:r['facts']['guest'].update(hardware_uuid='ffffffff-ffff-4fff-8fff-ffffffffffff'),
            lambda r:r['facts']['guest'].update(task_id='wrong'),
            lambda r:r['facts']['inventory'].update(items=[]),
            lambda r:r['facts']['instance'].update(uuid=None),
            lambda r:r['target'].update(actual=None)]
        for mutate in mutations:
            r=vm_evidence(); mutate(r)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                analyze(make_task(),r)

    def test_stale_or_future_guest_does_not_pass(self):
        for delta in (-1801,1):
            r=vm_evidence(); r['facts']['guest']['collected_at']=(datetime.fromisoformat(r['collected_at'])+timedelta(seconds=delta)).isoformat()
            self.assertFalse(analyze(make_task(),r)['passed'])

    def test_missing_guest_identity_linux_and_running_are_not_pass(self):
        mutations=[lambda r:r['facts']['guest'].update(machine_id_sha256=None),
            lambda r:r['facts']['guest'].update(hardware_uuid=None),lambda r:r['facts']['guest'].update(os='Windows'),
            lambda r:r['facts']['guest']['verification'].update(stdout='OK'),
            lambda r:r['facts']['instance'].update(state='poweroff'),
            lambda r:r['facts']['software'].update(version='6.1.0'),
            lambda r:r['facts']['software'].update(error='failed')]
        for mutate in mutations:
            r=vm_evidence(); mutate(r)
            with self.subTest(mutate=mutate):
                self.assertFalse(analyze(make_task(),r)['passed'])

    def test_retest_identities_and_guest_time(self):
        a=vm_evidence(); b=deepcopy(a)
        b['collected_at']=(datetime.fromisoformat(a['collected_at'])+timedelta(seconds=2)).isoformat()
        b['facts']['guest']['collected_at']=a['collected_at']
        compare_identity(a,b)
        for mutate in [lambda r:r['facts']['host'].update(id='c'*64),
            lambda r:r['facts']['instance'].update(requested='ffffffff-ffff-4fff-8fff-ffffffffffff'),
            lambda r:r['facts']['guest'].update(machine_id_sha256='c'*64),
            lambda r:r['facts']['guest'].update(collected_at=a['facts']['guest']['collected_at'])]:
            r=deepcopy(b);mutate(r)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):compare_identity(a,r)

    def test_task_is_fixed_even_when_resealed(self):
        from campuslab.rules import seal
        spec=make_task();spec['verify']='arbitrary-script'
        with self.assertRaises(ValueError):validate_spec(seal(spec))

    def test_collect_missing_tool_still_complete(self):
        with tempfile.TemporaryDirectory() as folder, patch('campuslab.vm_course.host_evidence') as host:
            host.return_value=vm_evidence()['facts']['host']
            r=collect(make_task(),str(Path(folder)/'VBoxManage.exe'))
        result=analyze(make_task(),r)
        self.assertFalse(result['passed'])
        self.assertEqual(next(c['status'] for c in result['checks'] if c['id']=='vm:software'),'missing')

    def test_guest_probe_runs_no_install_or_vm_launch(self):
        from campuslab.guest_probe import probe
        with patch('campuslab.guest_probe.platform.system',return_value='Linux'), \
             patch('campuslab.guest_probe.read_value',side_effect=lambda p: VM_ID if p.endswith('product_uuid') else 'machine'), \
             patch('campuslab.guest_probe.subprocess.run') as run:
            run.return_value.returncode=0; run.return_value.stdout='Linux\n';run.return_value.stderr=''
            r=probe(make_task()['id'],VM_ID)
        self.assertEqual(r['verification']['stdout'],'Linux:6')
        self.assertEqual(run.call_args.args[0],['/bin/uname','-s'])

    def test_collect_vbox_only_fixed_read_commands(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'VBoxManage.exe';target.touch()
            replies=[(0,'7.2.0r123',''),(0,'"Linux" {'+VM_ID+'}\n',''),
                (0,'UUID="'+VM_ID+'"\nname="Linux"\nostype="Ubuntu_64"\nVMState="running"\n','')]
            with patch('campuslab.vm_course.host_evidence',return_value=vm_evidence()['facts']['host']), \
                 patch('campuslab.vm_course._command',side_effect=replies) as run:
                r=collect(make_task(),str(target),VM_ID)
            self.assertTrue(r['facts']['instance']['exists'])
            self.assertEqual([c.args[0][1:] for c in run.call_args_list],[['--version'],['list','vms'],['showvminfo',VM_ID,'--machinereadable']])
            self.assertFalse(analyze(make_task(),r)['passed'])

    def test_collect_vmware_reads_selected_config_only(self):
        import uuid
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'vmrun.exe';target.touch()
            vm=Path(folder)/'Linux.vmx'
            vm.write_text('uuid.bios = "'+uuid.UUID(VM_ID).bytes_le.hex(' ')+'"\nguestOS = "ubuntu-64"\ndisplayName = "Linux"\n',encoding='utf-8')
            replies=[(4294967295,'vmrun version 1.17.0 build-1\nUsage: vmrun',''),(0,'Total running VMs: 0\n','')]
            with patch('campuslab.vm_course.host_evidence',return_value=vm_evidence()['facts']['host']), \
                 patch('campuslab.vm_course._command',side_effect=replies) as run:
                r=collect(make_task(),str(target),str(vm))
            self.assertEqual(r['facts']['instance']['uuid'],VM_ID)
            self.assertTrue(r['facts']['instance']['exists'])
            self.assertFalse(r['facts']['instance']['listed'])
            self.assertEqual([c.args[0][1:] for c in run.call_args_list],[[],['-T','ws','list']])
            self.assertEqual(next(c['status'] for c in analyze(make_task(),r)['checks'] if c['id']=='vm:software'),'pass')
            self.assertFalse(analyze(make_task(),r)['passed'])


if __name__=='__main__':unittest.main()
