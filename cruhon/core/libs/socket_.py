"""
cruhon/core/libs/socket_.py
===========================
TCP/IP sockets for Cruhon — @socket.*

Resolve names, open TCP connections, send/receive bytes and probe ports —
all without @raw.

━━━ NAMES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @socket.hostname[]              → this machine's host name
  @socket.fqdn[]                  → fully-qualified domain name
  @socket.host_to_ip[host]        → resolve a host name to an IP
  @socket.ip_to_host[ip]          → reverse-resolve an IP to a host name
  @socket.resolve[host; port]     → getaddrinfo records

━━━ CONNECTION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @socket.connect[host; port]     → connected TCP socket
  @socket.connect[host; port; t]  → with a timeout (seconds)
  @socket.send[sock; data]        → send all bytes
  @socket.recv[sock; n]           → receive up to n bytes
  @socket.close[sock]             → close the socket

━━━ PROBE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @socket.is_open[host; port]     → bool: can we connect to host:port
  @socket.is_open[host; port; t]  → with a timeout
  @socket.free_port[]             → an unused local TCP port number

━━━ SERVER (TCP) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @socket.tcp[]                   → a fresh unconnected TCP socket
  @socket.server[port]            → listening socket bound to all interfaces
  @socket.server[host; port]      → listening socket on a specific host
  @socket.bind[sock; host; port]  → bind a socket to an address
  @socket.listen[sock]            → start listening (default backlog)
  @socket.listen[sock; backlog]   → listen with a backlog size
  @socket.accept[sock]            → (connection, address) for next client

━━━ UDP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @socket.udp[]                   → a UDP (datagram) socket
  @socket.send_to[sock; data; host; port] → send a datagram
  @socket.recv_from[sock; n]      → (data, sender_address)

━━━ OPTIONS / INFO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @socket.set_timeout[sock; secs] → set a socket timeout (None = blocking)
  @socket.reuse[sock]             → enable SO_REUSEADDR
  @socket.local[sock]             → this socket's own (host, port)
  @socket.peer[sock]              → the connected peer's (host, port)
  @socket.shutdown[sock]          → disable further sends and receives
  @socket.file[sock]              → a file-like wrapper over the socket
"""
from ..registry import register_lib, register_lib_call

_SK = "__import__('socket')"


def register():
    register_lib("socket", None)

    # ── Names ─────────────────────────────────────────────────
    register_lib_call("socket", "hostname",
        lambda a: f"{_SK}.gethostname()")
    register_lib_call("socket", "fqdn",
        lambda a: f"{_SK}.getfqdn({a[0]})" if a else f"{_SK}.getfqdn()")
    register_lib_call("socket", "host_to_ip",
        lambda a: f"{_SK}.gethostbyname({a[0]})")
    register_lib_call("socket", "ip_to_host",
        lambda a: f"{_SK}.gethostbyaddr({a[0]})[0]")
    register_lib_call("socket", "resolve",
        lambda a: f"{_SK}.getaddrinfo({a[0]}, {a[1]})")

    # ── Connection ────────────────────────────────────────────
    register_lib_call("socket", "connect",
        lambda a: (
            f"{_SK}.create_connection(({a[0]}, {a[1]}), {a[2]})" if len(a) > 2 else
            f"{_SK}.create_connection(({a[0]}, {a[1]}))"
        ))
    register_lib_call("socket", "send",
        lambda a: f"{a[0]}.sendall({a[1]})")
    register_lib_call("socket", "recv",
        lambda a: f"{a[0]}.recv({a[1]})")
    register_lib_call("socket", "close",
        lambda a: f"{a[0]}.close()")

    # ── Probe ─────────────────────────────────────────────────
    register_lib_call("socket", "is_open",
        lambda a: (
            f"(lambda _h, _p, _t: (lambda _s: (_s.settimeout(_t), _s.connect_ex((_h, _p)) == 0, _s.close())[1])"
            f"({_SK}.socket()))({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _h, _p: (lambda _s: (_s.settimeout(5), _s.connect_ex((_h, _p)) == 0, _s.close())[1])"
            f"({_SK}.socket()))({a[0]}, {a[1]})"
        ))
    register_lib_call("socket", "free_port",
        lambda a: (
            f"(lambda _s: (_s.bind(('', 0)), _s.getsockname()[1], _s.close())[1])"
            f"({_SK}.socket({_SK}.AF_INET, {_SK}.SOCK_STREAM))"
        ))

    # ── Server (TCP) ──────────────────────────────────────────
    register_lib_call("socket", "tcp",
        lambda a: f"{_SK}.socket({_SK}.AF_INET, {_SK}.SOCK_STREAM)")
    register_lib_call("socket", "server",
        lambda a: (
            f"(lambda _h, _p: (lambda _s: (_s.setsockopt({_SK}.SOL_SOCKET, {_SK}.SO_REUSEADDR, 1), "
            f"_s.bind((_h, _p)), _s.listen(), _s)[3])({_SK}.socket()))({a[0]}, {a[1]})"
            if len(a) > 1 else
            f"(lambda _p: (lambda _s: (_s.setsockopt({_SK}.SOL_SOCKET, {_SK}.SO_REUSEADDR, 1), "
            f"_s.bind(('', _p)), _s.listen(), _s)[3])({_SK}.socket()))({a[0]})"
        ))
    register_lib_call("socket", "bind",
        lambda a: f"{a[0]}.bind(({a[1]}, {a[2]}))")
    register_lib_call("socket", "listen",
        lambda a: f"{a[0]}.listen({a[1]})" if len(a) > 1 else f"{a[0]}.listen()")
    register_lib_call("socket", "accept",
        lambda a: f"{a[0]}.accept()")

    # ── UDP ───────────────────────────────────────────────────
    register_lib_call("socket", "udp",
        lambda a: f"{_SK}.socket({_SK}.AF_INET, {_SK}.SOCK_DGRAM)")
    register_lib_call("socket", "send_to",
        lambda a: f"{a[0]}.sendto({a[1]}, ({a[2]}, {a[3]}))")
    register_lib_call("socket", "recv_from",
        lambda a: f"{a[0]}.recvfrom({a[1]})")

    # ── Options / Info ────────────────────────────────────────
    register_lib_call("socket", "set_timeout",
        lambda a: f"{a[0]}.settimeout({a[1]})")
    register_lib_call("socket", "reuse",
        lambda a: f"{a[0]}.setsockopt({_SK}.SOL_SOCKET, {_SK}.SO_REUSEADDR, 1)")
    register_lib_call("socket", "local",
        lambda a: f"{a[0]}.getsockname()")
    register_lib_call("socket", "peer",
        lambda a: f"{a[0]}.getpeername()")
    register_lib_call("socket", "shutdown",
        lambda a: f"{a[0]}.shutdown({_SK}.SHUT_RDWR)")
    register_lib_call("socket", "file",
        lambda a: f"{a[0]}.makefile({a[1]})" if len(a) > 1 else f"{a[0]}.makefile('rwb')")
