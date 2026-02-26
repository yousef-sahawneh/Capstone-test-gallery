import os
import contextlib

@contextlib.contextmanager
def redirect_native_output(stdout_path: str = "vendor_native.log", stderr_path: str = "vendor_native.log"):
    """
    Redirect OS-level stdout/stderr (C/C++ printf) to files.
    This avoids console spam without interfering with Python logging as much as NUL redirection.
    """
    stdout_fd = os.dup(1)
    stderr_fd = os.dup(2)

    out_f = open(stdout_path, "a", buffering=1)
    err_f = open(stderr_path, "a", buffering=1)

    try:
        os.dup2(out_f.fileno(), 1)
        os.dup2(err_f.fileno(), 2)
        yield
        
    finally:
        os.dup2(stdout_fd, 1)
        os.dup2(stderr_fd, 2)
        os.close(stdout_fd)
        os.close(stderr_fd)
        out_f.close()
        err_f.close()
