import os
import subprocess
import sys
import tempfile
import signal

MAX_OUTPUT_CHARS = 10_000


def _limits(timeout: int):
    """Resource limits applied to the child process (Linux/macOS only)."""
    def apply():
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (timeout + 1, timeout + 1))
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)   # 512 MB memory
        resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024,) * 2)      # 1 MB per written file
    return apply


def _read(path: str) -> tuple[str, bool]:
    with open(path, "r", errors="replace") as f:
        text = f.read(MAX_OUTPUT_CHARS + 1)
    return text[:MAX_OUTPUT_CHARS], len(text) > MAX_OUTPUT_CHARS


def run_code(code: str, timeout: int = 5) -> dict:
    """Run Python code in an isolated subprocess and capture the result.

    The script is saved as main.py, so tracebacks look like: File "main.py", line N
    """
    with tempfile.TemporaryDirectory() as workdir:
        script = os.path.join(workdir, "main.py")
        out_path = os.path.join(workdir, "_stdout.txt")
        err_path = os.path.join(workdir, "_stderr.txt")
        with open(script, "w", encoding="utf-8") as f:
            f.write(code)

        # Minimal environment: no API keys or secrets from the parent process
        env = {"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"}
        posix = os.name == "posix"

        timed_out = False
        with open(out_path, "w") as out, open(err_path, "w") as err:
            proc = subprocess.Popen(
                [sys.executable, "-I", "main.py"],   # -I = isolated mode
                cwd=workdir,
                stdout=out,
                stderr=err,
                stdin=subprocess.DEVNULL,
                env=env,
                preexec_fn=_limits(timeout) if posix else None,
                start_new_session=posix,
            )
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    if posix:
                        os.killpg(proc.pid, signal.SIGKILL)   # kill the whole process group
                    else:
                        proc.kill()
                finally:
                    proc.wait()

        stdout, out_cut = _read(out_path)
        stderr, err_cut = _read(err_path)

    return {
        "ok": proc.returncode == 0 and not timed_out,
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": timed_out,
        "truncated": out_cut or err_cut,
    }