import subprocess
import tempfile
import os
from typing import Optional

class SandboxResult:
    def __init__(self, ok: bool, timed_out: bool, stdout: str, stderr: str):
        self.ok = ok
        self.timed_out = timed_out
        self.stdout = stdout
        self.stderr = stderr
        
    def __str__(self):
        return f"SandboxResult(ok={self.ok}, timed_out={self.timed_out}, stdout={self.stdout!r}, stderr={self.stderr!r})"

class LocalSandbox:
    """A minimal local sandbox to execute Python code with a timeout."""
    
    def run_python(self, code: str, timeout: int = 3) -> SandboxResult:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "script.py")
            with open(file_path, "w", encoding='utf-8') as f:
                f.write(code)
                
            try:
                import sys
                result = subprocess.run(
                    [sys.executable, "script.py"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                return SandboxResult(
                    ok=(result.returncode == 0),
                    timed_out=False,
                    stdout=result.stdout.strip(),
                    stderr=result.stderr.strip()
                )
            except subprocess.TimeoutExpired as e:
                return SandboxResult(
                    ok=False,
                    timed_out=True,
                    stdout=(e.stdout.decode().strip() if e.stdout else ""),
                    stderr=f"TimeoutExpired: Execution exceeded {timeout} seconds."
                )
            except Exception as e:
                return SandboxResult(ok=False, timed_out=False, stdout="", stderr=str(e))
