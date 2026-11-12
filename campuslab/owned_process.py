"""Windows job lifetime for our fixed collector, including its descendants."""
import ctypes
from ctypes import wintypes as w
import subprocess


class BasicLimits(ctypes.Structure):
    _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
                ('flags', w.DWORD), ('working_min', ctypes.c_size_t), ('working_max', ctypes.c_size_t),
                ('active_limit', w.DWORD), ('affinity', ctypes.c_size_t), ('priority', w.DWORD), ('scheduling', w.DWORD)]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [('basic', BasicLimits), ('io', ctypes.c_ulonglong * 6),
                ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
                ('peak_process_memory', ctypes.c_size_t), ('peak_job_memory', ctypes.c_size_t)]


class OwnedProcess:
    """The child must wait for one stdin byte before spawning any descendants."""
    def __init__(self, command, cwd=None):
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        for name, args, returns in [
            ('CreateJobObjectW', [ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            ('SetInformationJobObject', [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            ('AssignProcessToJobObject', [w.HANDLE, w.HANDLE], w.BOOL),
            ('CloseHandle', [w.HANDLE], w.BOOL)]:
            fn = getattr(self.api, name); fn.argtypes = args; fn.restype = returns
        self.job = self.api.CreateJobObjectW(None, None)
        self.process = None
        if not self.job:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            limits = ExtendedLimits(); limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not self.api.SetInformationJobObject(self.job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
                raise ctypes.WinError(ctypes.get_last_error())
            self.process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE,
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                            creationflags=subprocess.CREATE_NO_WINDOW)
            if not self.api.AssignProcessToJobObject(self.job, int(self.process._handle)):
                raise ctypes.WinError(ctypes.get_last_error())
            # The reviewed wrapper cannot launch the target until assignment succeeds.
            self.process.stdin.write(b'1'); self.process.stdin.close()
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.job:
            self.api.CloseHandle(self.job); self.job = None
        if self.process:
            if self.process.poll() is None:
                self.process.kill()
            self.process.wait(timeout=5)
            if self.process.stdin and not self.process.stdin.closed:
                self.process.stdin.close()
