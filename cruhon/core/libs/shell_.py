"""
Shell / system wrappers for Cruhon — @shell.*

Covers subprocess / os / sys / shutil so a non-coder can run system
commands, check exit codes, read output and manage the process environment
without knowing Popen, PIPE, or communicate().

━━━ RUN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shell.run[cmd]                  → CompletedProcess (stdout + returncode)
  @shell.run[cmd; cwd=; env=; timeout=]
  @shell.output[cmd]               → stdout string (raises on error)
  @shell.output[cmd; cwd=]
  @shell.lines[cmd]                → stdout as list of lines
  @shell.code[cmd]                 → exit code int
  @shell.ok[cmd]                   → bool (exit code == 0)
  @shell.bg[cmd]                   → Popen handle (non-blocking)
  @shell.bg_stdin[cmd]             → Popen with stdin/stdout PIPE (text mode)
  @shell.pipe[cmd1; cmd2]          → stdout of cmd1 piped into cmd2

━━━ SAFE RUN (argv list, no shell=True) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Everything above passes a STRING through the shell (shell=True) — exactly
  like os.system()/subprocess.run(cmd, shell=True) in plain Python, it
  interprets metacharacters (;, |, &&, $(...), backticks, ...). Use the
  argv-list form below whenever part of the command comes from data you
  don't fully trust — a filename from @input, a value from an HTTP
  response, etc. — since it never invokes a shell at all.
  @shell.exec[argv]                → CompletedProcess, e.g. @shell.exec[["ls"; "-la"]]
  @shell.exec[argv; cwd=; env=; timeout=]
  @shell.exec_output[argv]         → stdout string (raises on error)
  @shell.exec_code[argv]           → exit code int
  @shell.exec_ok[argv]             → bool (exit code == 0)
  @shell.exec_bg[argv]             → Popen handle (non-blocking)

━━━ PROCESS CONTROL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shell.kill[proc]                — proc.kill()
  @shell.terminate[proc]           — proc.terminate()
  @shell.wait[proc]                → proc.wait()
  @shell.wait[proc; timeout]       → proc.wait(timeout=n)
  @shell.communicate[proc]         → (stdout, stderr) tuple
  @shell.communicate[proc; input]  → with stdin data
  @shell.poll[proc]                → returncode or None
  @shell.returncode[proc]          → proc.returncode

━━━ LOOKUP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shell.which[cmd]                → full path or None
  @shell.exists[cmd]               → bool (command found in PATH)

━━━ ENVIRONMENT / PROCESS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shell.env[key]                  → os.environ.get(key)
  @shell.env[key; default]
  @shell.env_set[key; value]       — set env var for current process
  @shell.env_del[key]              — unset env var
  @shell.env_all[]                 → full dict copy of os.environ
  @shell.cwd[]                     → current working directory
  @shell.cd[path]                  — change working directory
  @shell.args[]                    → sys.argv list
  @shell.exit[code]                — sys.exit(code)  (default 0)
  @shell.platform[]                → sys.platform string
  @shell.python_version[]          → Python version string
  @shell.pid[]                     → current process PID
  @shell.cpu_count[]               → os.cpu_count()
  @shell.hostname[]                → socket.gethostname()
  @shell.username[]                → getpass.getuser()
  @shell.home[]                    → user home directory
"""
from ..registry import register_lib, register_lib_call

_SP  = "__import__('subprocess')"
_OS  = "__import__('os')"
_SYS = "__import__('sys')"
_SHU = "__import__('shutil')"
_MOD = "cruhon.core.libs.shell_"


def _pipe_cmd(cmd1: str, cmd2: str) -> str:
    return (
        f"(lambda _c1, _c2: "
        f"{_SP}.run(_c2, input={_SP}.run(_c1, shell=True, capture_output=True, text=True).stdout, "
        f"shell=True, capture_output=True, text=True).stdout.strip()"
        f")({cmd1}, {cmd2})"
    )


def register():
    register_lib("shell", None)

    # ── RUN ──────────────────────────────────────────────────
    register_lib_call("shell", "run",
        lambda a: f"{_SP}.run({a[0]}, shell=True, capture_output=True, text=True{', ' + ', '.join(a[1:]) if len(a)>1 else ''})")

    register_lib_call("shell", "output",
        lambda a: (
            f"{_SP}.check_output({a[0]}, shell=True, text=True{', ' + ', '.join(a[1:]) if len(a)>1 else ''}).strip()"
        ))

    register_lib_call("shell", "lines",
        lambda a: f"{_SP}.check_output({a[0]}, shell=True, text=True).splitlines()")

    register_lib_call("shell", "code",
        lambda a: f"{_SP}.run({a[0]}, shell=True, capture_output=True).returncode")

    register_lib_call("shell", "ok",
        lambda a: f"({_SP}.run({a[0]}, shell=True, capture_output=True).returncode == 0)")

    register_lib_call("shell", "bg",
        lambda a: f"{_SP}.Popen({a[0]}, shell=True)")

    register_lib_call("shell", "bg_stdin",
        lambda a: f"{_SP}.Popen({a[0]}, shell=True, stdin={_SP}.PIPE, stdout={_SP}.PIPE, text=True)")

    # ── SAFE (no shell=True) — takes an argv list, never interprets shell
    # metacharacters. Use these instead of @shell.run/output/bg whenever any
    # part of the command is built from data you don't fully trust (a
    # filename from user @input, a value from an HTTP response, etc.) —
    # shell=True string commands are vulnerable to injection the same way
    # os.system()/subprocess.run(cmd, shell=True) are in plain Python.
    register_lib_call("shell", "exec",
        lambda a: f"{_SP}.run({a[0]}, capture_output=True, text=True{', ' + ', '.join(a[1:]) if len(a)>1 else ''})")

    register_lib_call("shell", "exec_output",
        lambda a: f"{_SP}.check_output({a[0]}, text=True{', ' + ', '.join(a[1:]) if len(a)>1 else ''}).strip()")

    register_lib_call("shell", "exec_code",
        lambda a: f"{_SP}.run({a[0]}, capture_output=True).returncode")

    register_lib_call("shell", "exec_ok",
        lambda a: f"({_SP}.run({a[0]}, capture_output=True).returncode == 0)")

    register_lib_call("shell", "exec_bg",
        lambda a: f"{_SP}.Popen({a[0]})")

    register_lib_call("shell", "pipe",
        lambda a: _pipe_cmd(a[0], a[1]))

    # ── PROCESS CONTROL ───────────────────────────────────────
    register_lib_call("shell", "kill",
        lambda a: f"{a[0]}.kill()")

    register_lib_call("shell", "terminate",
        lambda a: f"{a[0]}.terminate()")

    register_lib_call("shell", "wait",
        lambda a: (
            f"{a[0]}.wait(timeout={a[1]})" if len(a) > 1 else
            f"{a[0]}.wait()"
        ))

    register_lib_call("shell", "communicate",
        lambda a: (
            f"{a[0]}.communicate(input={a[1]})" if len(a) > 1 else
            f"{a[0]}.communicate()"
        ))

    register_lib_call("shell", "poll",
        lambda a: f"{a[0]}.poll()")

    register_lib_call("shell", "returncode",
        lambda a: f"{a[0]}.returncode")

    # ── LOOKUP ───────────────────────────────────────────────
    register_lib_call("shell", "which",
        lambda a: f"{_SHU}.which({a[0]})")

    register_lib_call("shell", "exists",
        lambda a: f"({_SHU}.which({a[0]}) is not None)")

    # ── ENVIRONMENT / PROCESS ────────────────────────────────
    register_lib_call("shell", "env",
        lambda a: (
            f"{_OS}.environ.get({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_OS}.environ.get({a[0]})"
        ))

    register_lib_call("shell", "env_set",
        lambda a: f"{_OS}.environ.__setitem__({a[0]}, str({a[1]}))")

    register_lib_call("shell", "env_del",
        lambda a: f"{_OS}.environ.pop({a[0]}, None)")

    register_lib_call("shell", "cwd",
        lambda a: f"{_OS}.getcwd()")

    register_lib_call("shell", "cd",
        lambda a: f"{_OS}.chdir({a[0]})")

    register_lib_call("shell", "args",
        lambda a: f"{_SYS}.argv")

    register_lib_call("shell", "exit",
        lambda a: f"{_SYS}.exit({a[0] if a else 0})")

    register_lib_call("shell", "platform",
        lambda a: f"{_SYS}.platform")

    register_lib_call("shell", "python_version",
        lambda a: f"{_SYS}.version")

    register_lib_call("shell", "pid",
        lambda a: f"{_OS}.getpid()")

    register_lib_call("shell", "env_all",
        lambda a: f"dict({_OS}.environ)")

    register_lib_call("shell", "cpu_count",
        lambda a: f"{_OS}.cpu_count()")

    register_lib_call("shell", "hostname",
        lambda a: "__import__('socket').gethostname()")

    register_lib_call("shell", "username",
        lambda a: "__import__('getpass').getuser()")

    register_lib_call("shell", "home",
        lambda a: f"{_OS}.path.expanduser('~')")
