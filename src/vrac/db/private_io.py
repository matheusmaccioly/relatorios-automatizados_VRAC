"""Saídas manuais fora do workspace, em diretório novo com acesso restrito."""

import ctypes
import json
import os
from pathlib import Path
from uuid import UUID


class PrivateOutputError(RuntimeError):
    """Falha segura: não carregar caminhos ou metadados na mensagem pública."""


_FORBIDDEN_PARTS = {".git", ".aws", ".agents", ".codex", ".ssh"}


def _external_directory(path: Path, workspace: Path) -> Path:
    if not path.is_absolute() or path.is_symlink():
        raise PrivateOutputError("Escolha um diretório local absoluto fora do workspace.")
    resolved = path.resolve()
    if (
        resolved.is_relative_to(workspace.resolve())
        or any(part.casefold() in _FORBIDDEN_PARTS for part in resolved.parts)
        or str(resolved).startswith(("\\\\", "//"))
        or resolved == Path(resolved.anchor)
    ):
        raise PrivateOutputError("Escolha um diretório local absoluto fora do workspace.")
    if os.name == "nt":
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
        kernel.GetDriveTypeW.restype = wintypes.UINT
        if kernel.GetDriveTypeW(resolved.anchor) == 4:  # DRIVE_REMOTE
            raise PrivateOutputError("A saída deve ficar em armazenamento local privado.")
    return resolved


def _restrict_windows_directory(path: Path) -> None:
    """DACL protegida com uma única ACE para o usuário do processo (sem herança)."""
    from ctypes import wintypes

    class SidAndAttributes(ctypes.Structure):
        _fields_ = [("sid", wintypes.LPVOID), ("attributes", wintypes.DWORD)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    security = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [wintypes.LPVOID]
    kernel.LocalFree.restype = wintypes.LPVOID
    security.OpenProcessToken.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    security.OpenProcessToken.restype = wintypes.BOOL
    security.GetTokenInformation.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    security.GetTokenInformation.restype = wintypes.BOOL
    security.ConvertSidToStringSidW.argtypes = [wintypes.LPVOID, ctypes.POINTER(wintypes.LPWSTR)]
    security.ConvertSidToStringSidW.restype = wintypes.BOOL
    security.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.DWORD),
    ]
    security.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL
    security.SetFileSecurityW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID]
    security.SetFileSecurityW.restype = wintypes.BOOL

    token = wintypes.HANDLE()
    sid_text = wintypes.LPWSTR()
    descriptor = wintypes.LPVOID()
    try:
        if not security.OpenProcessToken(kernel.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
            raise OSError("Não foi possível proteger a saída.")
        length = wintypes.DWORD()
        security.GetTokenInformation(token, 1, None, 0, ctypes.byref(length))
        if not length.value:
            raise OSError("Não foi possível proteger a saída.")
        buffer = ctypes.create_string_buffer(length.value)
        if not security.GetTokenInformation(token, 1, buffer, length, ctypes.byref(length)):
            raise OSError("Não foi possível proteger a saída.")
        user = ctypes.cast(buffer, ctypes.POINTER(SidAndAttributes)).contents
        if not security.ConvertSidToStringSidW(user.sid, ctypes.byref(sid_text)):
            raise OSError("Não foi possível proteger a saída.")
        sddl = f"D:P(A;OICI;FA;;;{sid_text.value})"
        if not security.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, 1, ctypes.byref(descriptor), None
        ):
            raise OSError("Não foi possível proteger a saída.")
        # DACL_SECURITY_INFORMATION | PROTECTED_DACL_SECURITY_INFORMATION
        if not security.SetFileSecurityW(str(path), 0x80000004, descriptor):
            raise OSError("Não foi possível proteger a saída.")
    finally:
        if descriptor:
            kernel.LocalFree(descriptor)
        if sid_text:
            kernel.LocalFree(ctypes.cast(sid_text, wintypes.LPVOID))
        if token:
            kernel.CloseHandle(token)


def _restrict_directory(path: Path) -> None:
    if os.name == "nt":
        _restrict_windows_directory(path)
    else:
        path.chmod(0o700)


def create_private_run_directory(base: Path, execution_id: str, *, workspace: Path) -> Path:
    """Não modificar ACL de pastas existentes; proteger apenas a nova pasta da execução."""
    try:
        if str(UUID(execution_id)) != execution_id:
            raise ValueError
        directory = _external_directory(base, workspace)
        directory.mkdir(mode=0o700, exist_ok=True)  # pai já deve existir
        run_directory = directory / execution_id
        run_directory.mkdir(mode=0o700, exist_ok=False)
        _restrict_directory(run_directory)  # nenhum dado escrito antes desta proteção
        return run_directory
    except (OSError, ValueError, RuntimeError):
        raise PrivateOutputError(
            "Não foi possível preparar a saída privada. Confira diretório e permissões locais."
        ) from None


def write_private_report(run_directory: Path, command: str, report: dict[str, object]) -> None:
    if command not in {"diagnose", "inventory"}:
        raise PrivateOutputError("Tipo de saída não permitido.")
    try:
        if run_directory.is_symlink():
            raise ValueError
        data = json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2).encode("utf-8")
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
        descriptor = os.open(run_directory / f"{command}.json", flags, 0o600)
        with os.fdopen(descriptor, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
    except (OSError, ValueError, TypeError):
        raise PrivateOutputError("Não foi possível gravar o arquivo privado da execução.") from None
