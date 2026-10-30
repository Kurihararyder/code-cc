"""Windows：用系統的 IShellLinkW 建立 .lnk 捷徑，整個過程都是 Unicode（路徑有中文也行）。

為什麼不用 PowerShell 的 WScript.Shell：它內部用系統的 ANSI 字碼頁處理路徑，英文版 Windows 上檔名或路徑有中文就會
「Unable to save shortcut」（GitHub 的 Windows 機器上實際發生過）。

這是一支獨立的小程式，由安裝精靈用另一個行程執行（python -I winlnk.py）：萬一 COM 呼叫出事，只有這個行程會掛，
安裝精靈本身不受影響；安裝精靈看不到成功的項目就改用 .cmd 捷徑。
輸入：環境變數 CPE_LNKS，內容是 {"items": [{"lnk", "target", "args", "wd", "icon", "desc"}, ...]}（JSON）。
輸出（UTF-8）：每一項一行，"OK 序號" 或 "FAIL 序號 : 原因"。結束碼 0 表示全部成功。
"""
import json
import os
import sys

# IShellLinkW、IPersistFile 的虛擬函式表位置（含 IUnknown 的 0、1、2）
QUERY_INTERFACE, RELEASE = 0, 2
SET_DESCRIPTION, SET_WORKING_DIRECTORY, SET_ARGUMENTS, SET_ICON_LOCATION, SET_PATH = 7, 9, 11, 17, 20
PERSIST_FILE_SAVE = 6
COINIT_APARTMENTTHREADED, CLSCTX_INPROC_SERVER = 0x2, 0x1


def make_all(items):
    import ctypes
    from ctypes import wintypes as wt

    ole32 = ctypes.OleDLL("ole32")
    ole32.CoUninitialize.restype = None             # 沒有回傳值：不能當成 HRESULT 檢查

    class GUID(ctypes.Structure):
        _fields_ = [("Data1", wt.DWORD), ("Data2", wt.WORD), ("Data3", wt.WORD), ("Data4", ctypes.c_ubyte * 8)]

    def guid(text):
        g = GUID()
        ole32.CLSIDFromString(ctypes.c_wchar_p(text), ctypes.byref(g))
        return g

    clsid_shell_link = guid("{00021401-0000-0000-C000-000000000046}")
    iid_shell_link = guid("{000214F9-0000-0000-C000-000000000046}")
    iid_persist_file = guid("{0000010B-0000-0000-C000-000000000046}")

    def call(obj, index, argtypes, *args, restype=ctypes.HRESULT):
        """呼叫 COM 物件的第 index 個虛擬函式（obj 是介面指標）。HRESULT 失敗會丟 OSError。"""
        vtable = ctypes.cast(ctypes.cast(obj, ctypes.POINTER(ctypes.c_void_p))[0], ctypes.POINTER(ctypes.c_void_p))
        return ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(vtable[index])(obj, *args)

    def release(obj):
        call(obj, RELEASE, (), restype=ctypes.c_ulong)

    def make(item):
        link = ctypes.c_void_p()
        ole32.CoCreateInstance(ctypes.byref(clsid_shell_link), None, CLSCTX_INPROC_SERVER, ctypes.byref(iid_shell_link), ctypes.byref(link))
        try:
            call(link, SET_PATH, (wt.LPCWSTR,), item["target"])
            call(link, SET_ARGUMENTS, (wt.LPCWSTR,), item.get("args") or "")
            call(link, SET_WORKING_DIRECTORY, (wt.LPCWSTR,), item.get("wd") or "")
            call(link, SET_DESCRIPTION, (wt.LPCWSTR,), item.get("desc") or "")
            if item.get("icon"):
                call(link, SET_ICON_LOCATION, (wt.LPCWSTR, ctypes.c_int), item["icon"], 0)
            persist = ctypes.c_void_p()
            call(link, QUERY_INTERFACE, (ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)), ctypes.byref(iid_persist_file), ctypes.byref(persist))
            try:
                call(persist, PERSIST_FILE_SAVE, (wt.LPCWSTR, wt.BOOL), item["lnk"], True)
            finally:
                release(persist)
        finally:
            release(link)

    initialised = False
    try:
        ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
        initialised = True
    except OSError:
        pass                                    # 這個執行緒已經用別的模式初始化過（RPC_E_CHANGED_MODE），照樣可以用
    results = []
    try:
        for i, item in enumerate(items):
            try:
                make(item)
                results.append((i, None))
            except Exception as e:                  # 一項失敗不影響其他項；原因寫出來
                results.append((i, f"{type(e).__name__}: {e}"))
    finally:
        if initialised:
            ole32.CoUninitialize()
    return results


def main():
    out = sys.stdout.buffer
    if sys.platform != "win32":
        out.write("FAIL 0 : 只有 Windows 才能建立 .lnk\n".encode("utf-8"))
        return 2
    try:
        items = json.loads(os.environ["CPE_LNKS"])["items"]
    except (KeyError, ValueError) as e:
        out.write(f"FAIL 0 : 讀不到要建立的捷徑清單（{type(e).__name__}）\n".encode("utf-8"))
        return 2
    bad = 0
    for i, err in make_all(items):
        if err:
            bad += 1
            out.write(f"FAIL {i} : {err}\n".encode("utf-8"))
        else:
            out.write(f"OK {i}\n".encode("utf-8"))
    out.flush()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
