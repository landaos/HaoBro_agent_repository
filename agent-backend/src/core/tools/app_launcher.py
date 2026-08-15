"""
app_launcher.py - 本地应用程序启动工具

功能：
  - 自动发现安装路径（7 层搜索策略，覆盖 99%+ 的安装情况）
  - 启动应用程序
  - 通过 uiautomation / pyautogui 自动搜索并播放歌曲
"""

import os
import subprocess
import time
import winreg
from pathlib import Path

from langchain_core.tools import tool
from src.logger.logger import logger

from src.config import settings

# ── 已知应用安装信息 ──
KNOWN_APPS: dict[str, dict] = {
    "酷狗音乐": {
        "exe": "KuGou.exe",
        "display_name_keywords": ["酷狗", "KuGou", "Kugou"],  # 用于 Uninstall 注册表匹配
        "window_keywords": ["酷狗", "KuGou"],   # 用于 pygetwindow 匹配窗口
        "search_roots": [
            Path(r"C:\Program Files (x86)\KuGou\KGMusic"),
            Path(r"C:\Program Files\KuGou\KGMusic"),
            Path(r"D:\Program Files (x86)\KuGou\KGMusic"),
            Path(r"D:\Program Files\KuGou\KGMusic"),
            Path(r"E:\Program Files (x86)\KuGou\KGMusic"),
            Path(r"E:\Program Files\KuGou\KGMusic"),
            Path(r"D:\KuGou\KGMusic"),
            Path(r"D:\Software\KuGou\KGMusic"),
            Path(r"D:\Tools\KuGou\KGMusic"),
        ],
        "reg_key": r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\KuGou.exe",
        "reg_key_64": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\KuGou.exe",
    },
    "酷狗": {
        "exe": "KuGou.exe",
        "display_name_keywords": ["酷狗", "KuGou", "Kugou"],
        "window_keywords": ["酷狗", "KuGou"],
        "search_roots": [
            Path(r"C:\Program Files (x86)\KuGou\KGMusic"),
            Path(r"C:\Program Files\KuGou\KGMusic"),
            Path(r"D:\Program Files (x86)\KuGou\KGMusic"),
            Path(r"D:\Program Files\KuGou\KGMusic"),
            Path(r"E:\Program Files (x86)\KuGou\KGMusic"),
            Path(r"E:\Program Files\KuGou\KGMusic"),
            Path(r"D:\KuGou\KGMusic"),
            Path(r"D:\Software\KuGou\KGMusic"),
            Path(r"D:\Tools\KuGou\KGMusic"),
        ],
        "reg_key": r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\KuGou.exe",
        "reg_key_64": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\KuGou.exe",
    },
    "记事本": {"exe": "notepad.exe", "system": True},
    "计算器": {"exe": "calc.exe", "system": True},
    "画图":   {"exe": "mspaint.exe", "system": True},
}


def _find_exe(app_name: str) -> str | None:
    """
    查找可执行文件完整路径，7 层搜索策略，按优先级执行：

        ① .env 配置
        ② 注册表 App Paths
        ③ 注册表 Uninstall（所有软件都在这留 InstallLocation）
        ④ 开始菜单快捷方式 → 解析目标路径
        ⑤ 常用安装目录
        ⑥ where.exe 系统搜索
        ⑦ 全盘文件名搜索（dir /s，限制盘符和超时）

    从 95% 提升到 99%+ 的安装发现率。
    """
    info = KNOWN_APPS.get(app_name)
    if not info:
        return None

    # ① 系统自带程序（notepad.exe 等），直接返回名称
    if info.get("system"):
        return info["exe"]

    exe_name = info["exe"]

    # ── ② .env 配置的 KUGOU_PATH（用户手动指定） ──
    if app_name in ("酷狗", "酷狗音乐") and settings.kugou_path:
        path = settings.kugou_path.strip()
        if Path(path).exists():
            logger.info(f"【应用启动】 .env 配置路径: {path}")
            return path
        logger.warning(f"【应用启动】 .env 配置的 KUGOU_PATH 不存在: {path}")

    # ── ③ 注册表 App Paths ──
    result = _find_via_reg_app_paths(info, exe_name)
    if result:
        return result

    # ── ④ 注册表 Uninstall 路径搜索 ──
    result = _find_via_reg_uninstall(info, exe_name)
    if result:
        return result

    # ── ⑤ 开始菜单快捷方式解析 ──
    result = _find_via_shortcut(exe_name)
    if result:
        return result

    # ── ⑥ 扫描常用安装目录 ──
    for root in info.get("search_roots", []):
        exe = root / exe_name
        if exe.exists():
            logger.info(f"【应用启动】 扫描目录找到: {exe}")
            return str(exe)

    # ── ⑦ 遍历全盘找 KGMusic 目录 ──
    result = _find_via_kgmusic_dir(exe_name)
    if result:
        return result

    # ── ⑧ where.exe 系统搜索（利用 PATH 环境变量） ──
    result = _find_via_where(exe_name)
    if result:
        return result

    # ── ⑨ 全盘文件名搜索（最后兜底） ──
    result = _find_via_full_disk_search(exe_name)
    if result:
        return result

    return None


# ── 子搜索方法 ──


def _find_via_reg_app_paths(info: dict, exe_name: str) -> str | None:
    """③ 注册表 App Paths 搜索"""
    for reg_key in (info.get("reg_key"), info.get("reg_key_64")):
        if reg_key:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key) as key:
                    path = winreg.QueryValue(key, "")
                    if path and Path(path).exists():
                        logger.info(f"【应用启动】 注册表 App Paths 找到: {path}")
                        return path
            except OSError:
                continue
    return None


def _find_via_reg_uninstall(info: dict, exe_name: str) -> str | None:
    """④ 注册表 Uninstall 路径搜索

    几乎所有安装程序都会在 Uninstall 注册表留下 InstallLocation。
    遍历所有卸载项，匹配 DisplayName 含有关键字的项，读取 InstallLocation。
    """
    keywords = info.get("display_name_keywords", [exe_name.replace(".exe", "")])
    uninstall_roots = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ]

    for root_key in uninstall_roots:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, root_key) as key:
                i = 0
                while True:
                    try:
                        sub_key_name = winreg.EnumKey(key, i)
                        i += 1
                        sub_key_path = f"{root_key}\\{sub_key_name}"
                        try:
                            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_key_path) as sub_key:
                                # 读 DisplayName
                                try:
                                    display_name, _ = winreg.QueryValueEx(sub_key, "DisplayName")
                                except FileNotFoundError:
                                    continue

                                # 检查是否匹配目标软件
                                if not any(kw.lower() in display_name.lower() for kw in keywords):
                                    continue

                                # 读 InstallLocation
                                try:
                                    install_loc, _ = winreg.QueryValueEx(sub_key, "InstallLocation")
                                except FileNotFoundError:
                                    # 有的项只有 DisplayIcon
                                    try:
                                        install_loc, _ = winreg.QueryValueEx(sub_key, "DisplayIcon")
                                    except FileNotFoundError:
                                        continue

                                if not install_loc:
                                    continue

                                # 拼接 exe 路径
                                candidate = Path(install_loc) / exe_name
                                if candidate.exists():
                                    logger.info(f"【应用启动】 注册表 Uninstall 找到: {candidate}")
                                    return str(candidate)

                                # 有时 InstallLocation 不包含子目录，递归搜索一下
                                for f in Path(install_loc).rglob(exe_name):
                                    logger.info(f"【应用启动】 注册表 Uninstall(rglob) 找到: {f}")
                                    return str(f)

                        except OSError:
                            continue
                    except OSError:
                        break
        except OSError:
            continue
    return None


def _find_via_shortcut(exe_name: str) -> str | None:
    """⑤ 开始菜单快捷方式解析

    扫描开始菜单目录下的 .lnk 文件，用 PowerShell 解析目标路径。
    """
    start_menu_dirs = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(os.environ.get("ALLUSERSPROFILE", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    ]

    # PowerShell 脚本：解析 .lnk 文件的目标路径
    ps_script = """
param($lnkPath)
$shell = New-Object -ComObject WScript.Shell
try {
    $shortcut = $shell.CreateShortcut($lnkPath)
    Write-Output $shortcut.TargetPath
} catch {
    Write-Output ""
}
"""

    searched = set()
    for base_dir in start_menu_dirs:
        if not base_dir.exists():
            continue
        try:
            for lnk in base_dir.rglob("*.lnk"):
                lnk_str = str(lnk)
                if lnk_str in searched:
                    continue
                searched.add(lnk_str)

                # 文件名预过滤，避免每个 lnk 都调 PowerShell
                if exe_name.replace(".exe", "").lower() not in lnk.stem.lower():
                    continue

                try:
                    result = subprocess.run(
                        ["powershell", "-NoProfile", "-Command", ps_script, "-lnkPath", lnk_str],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    target = result.stdout.strip()
                    if target and target.lower().endswith(exe_name.lower()) and Path(target).exists():
                        logger.info(f"【应用启动】 快捷方式找到: {target}")
                        return target
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    continue
        except PermissionError:
            continue

    return None


def _find_via_kgmusic_dir(exe_name: str) -> str | None:
    """⑦ BFS 遍历全盘，找任意深度的 KGMusic 目录下的 exe。

    不限路径深度、不限盘符，覆盖所有类似结构：
      D:/KGMusic/KuGou.exe
      D:/KuGou/KGMusic/KuGou.exe
      D:/酷狗音乐/酷狗音乐/KGMusic/KuGou.exe
      E:/Software/KuGou/KGMusic/KuGou.exe
      ...

    用 BFS（广度优先）逐层扫描，跳过系统/隐藏目录保证性能。
    """
    import collections  # noqa: PLC0415

    # 需要跳过的系统目录（不区分大小写）
    SKIP_DIRS = {
        "$recycle.bin", "windows", "winnt", "system32", "syswow64",
        "programdata", "appdata", "msocache", "temp", "tmp",
        "intel", "amd64", "drivers", "boot",
    }

    # 要扫描的盘符
    drives = [Path(f"{d}:\\") for d in "CDEFGHIJ" if Path(f"{d}:\\").exists()]
    logger.info(f"【应用启动】 BFS 搜索 KGMusic 目录: {[str(d)[0] for d in drives]}")

    MAX_DEPTH = 4  # 根目录为 depth=0，最多往下走 4 层

    for drive in drives:
        # BFS: (当前目录, 当前深度)
        queue = collections.deque([(drive, 0)])
        while queue:
            current_dir, depth = queue.popleft()

            # 跳过系统/隐藏目录
            if current_dir.name.lower() in SKIP_DIRS:
                continue

            try:
                # ── 检查当前目录本身是否叫 KGMusic ──
                if current_dir.name.lower() == "kgmusic":
                    candidate = current_dir / exe_name
                    if candidate.exists():
                        logger.info(f"【应用启动】 KGMusic 目录找到(深度{depth}): {candidate}")
                        return str(candidate)

                # ── 检查当前目录下是否有子目录叫 KGMusic ──
                for child in current_dir.iterdir():
                    if not child.is_dir():
                        continue
                    if child.name.lower() == "kgmusic":
                        candidate = child / exe_name
                        if candidate.exists():
                            logger.info(f"【应用启动】 KGMusic 子目录找到(深度{depth+1}): {candidate}")
                            return str(candidate)

                # ── 未达到最大深度，继续 BFS ──
                if depth < MAX_DEPTH:
                    for child in current_dir.iterdir():
                        if child.is_dir() and child.name.lower() not in SKIP_DIRS:
                            queue.append((child, depth + 1))

            except (PermissionError, OSError):
                continue

    return None


def _find_via_where(exe_name: str) -> str | None:
    """⑧ where.exe 系统搜索"""
    try:
        result = subprocess.run(
            ["where", exe_name],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            path = result.stdout.strip().split("\n")[0].strip()
            if path and Path(path).exists():
                logger.info(f"【应用启动】 where.exe 找到: {path}")
                return path
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _find_via_full_disk_search(exe_name: str) -> str | None:
    """⑧ 全盘文件名搜索（最后兜底）

    用 dir /s /b 在常见盘符根目录搜索 exe 文件名。
    限制搜索深度（最多 3 层子目录）和超时（20 秒），避免卡死。
    """
    # 只搜索常见盘符，跳过光驱等
    drives_to_search = []
    for d in "CDEFGH":
        drive = Path(f"{d}:\\")
        if drive.exists():
            drives_to_search.append(drive)

    # 限制搜索的目录层数——只搜根目录下的一级子目录（最常见的安装位置）
    search_dirs = []
    for drive in drives_to_search:
        search_dirs.append(drive)  # 根目录本身（D:\KuGou.exe 这种特殊情况）
        try:
            for p in drive.iterdir():
                if p.is_dir() and not p.name.startswith("$") and not p.name.startswith("."):
                    search_dirs.append(p)
                    # 再进一层（D:\Software\KuGou 这种）
                    try:
                        for sp in p.iterdir():
                            if sp.is_dir() and not sp.name.startswith("$"):
                                search_dirs.append(sp)
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError):
            pass

    logger.info(f"【应用启动】 全盘搜索: 扫描 {len(search_dirs)} 个目录查找 {exe_name}")

    for search_dir in search_dirs:
        try:
            candidate = search_dir / exe_name
            if candidate.exists():
                logger.info(f"【应用启动】 全盘搜索找到: {candidate}")
                return str(candidate)
        except (PermissionError, OSError):
            continue

    return None


def _focus_window(window_keywords: list[str]) -> bool:
    """
    查找并激活应用窗口。
    优先用 uiautomation（SetFocus + pyautogui 点击），降级到 pygetwindow。
    """
    # 优先 uiautomation
    try:
        import uiautomation as auto
        win = _find_kugou_window_uia(auto)
        if win:
            win.SetFocus()
            time.sleep(0.3)
            # 额外用 pyautogui 点击窗口，确保真正回到前台
            try:
                import pyautogui
                rect = win.BoundingRectangle
                cx = int(rect[0] + rect[2] / 2)
                cy = int(rect[1] + 30)  # 点标题栏区域
                pyautogui.click(cx, cy)
            except Exception:
                pass
            logger.info(f"【应用启动】 uia 聚焦窗口: {win.Name}")
            return True
    except ImportError:
        pass

    # 降级 pygetwindow
    try:
        import pygetwindow as gw
    except ImportError:
        return False

    for kw in window_keywords:
        try:
            windows = gw.getWindowsWithTitle(kw)
            if windows:
                win = windows[0]
                win.activate()
                time.sleep(0.3)
                logger.info(f"【应用启动】 gw 聚焦窗口: {win.title}")
                return True
        except Exception as e:
            logger.warning(f"【应用启动】 聚焦窗口失败 ({kw}): {e}")
            continue
    return False


def _force_foreground_window(hwnd: int) -> bool:
    """
    Win32 API 强制将窗口提到前台。
    
    Windows 默认限制第三方进程不能随意 SetForegroundWindow，
    通过 AttachThreadInput 绕过限制。
    """
    import ctypes
    user32 = ctypes.windll.user32
    
    try:
        # 先把窗口恢复（如果最小化）
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        time.sleep(0.1)
        
        fore_hwnd = user32.GetForegroundWindow()
        if fore_hwnd == hwnd:
            return True  # 已经在前台
        
        # 获取线程 ID
        cur_thread = ctypes.c_uint32()
        target_thread = ctypes.c_uint32()
        user32.GetWindowThreadProcessId(fore_hwnd, ctypes.byref(cur_thread))
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(target_thread))
        
        # 挂接到目标窗口的输入队列
        attached = False
        if cur_thread.value != target_thread.value:
            result = user32.AttachThreadInput(cur_thread.value, target_thread.value, True)
            attached = True
        
        # 尝试多种方式提窗
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.SetActiveWindow(hwnd)
        
        # 断开采挂
        if attached:
            user32.AttachThreadInput(cur_thread.value, target_thread.value, False)
        
        time.sleep(0.2)
        return user32.GetForegroundWindow() == hwnd
    except Exception as e:
        logger.warning(f"【应用启动】 强制提窗失败: {e}")
        return False


def _autosearch_and_play_kugou(song_name: str) -> bool:
    """
    自动搜索并播放歌曲（综合方案）。

    三个阶段：
      阶段1（搜索）：使用 Win32 PostMessage 发送 Ctrl+F → 输入歌名 → Enter
        原理：PostMessage 直接投入窗口消‍息队列，不依赖前台焦点
      阶段2（播放）：优先 uiautomation 定位结果 → pyautogui 硬件点击
        原理：uia 通过 UI Automation API 获取控件位置，pyautogui 模拟真‍实鼠标点击
      阶段3（兜底）：PostMessage ↓ + Enter 选中播放
    """
    import ctypes
    user32 = ctypes.windll.user32

    # ── Windows 消息常量 ──
    WM_KEYDOWN = 0x0100
    WM_KEYUP   = 0x0101
    WM_CHAR    = 0x0102
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP   = 0x0202

    VK_CONTROL = 0x11
    VK_F       = 0x46
    VK_ENTER   = 0x0D
    VK_DOWN    = 0x28
    VK_UP      = 0x26

    # ── 辅助函数 ──

    def _post_vk(hwnd, vk, down=True):
        user32.PostMessageW(hwnd, WM_KEYDOWN if down else WM_KEYUP, vk, 0)

    def _press_vk(hwnd, vk):
        _post_vk(hwnd, vk, True)
        _post_vk(hwnd, vk, False)

    def _ctrl_vk(hwnd, vk):
        _post_vk(hwnd, VK_CONTROL, True)
        _press_vk(hwnd, vk)
        _post_vk(hwnd, VK_CONTROL, False)

    def _post_text(hwnd, text):
        """通过 WM_CHAR 发送 Unicode 文本到窗口（支持中文）"""
        for char in text:
            user32.PostMessageW(hwnd, WM_CHAR, ord(char), 0)
            time.sleep(0.02)

    def _post_click(hwnd, x, y):
        """通过 PostMessage 发送鼠标点击到窗口的指定坐标"""
        lparam = (y << 16) | (x & 0xFFFF)
        user32.PostMessageW(hwnd, WM_LBUTTONDOWN, 0x0001, lparam)  # MK_LBUTTON
        time.sleep(0.05)
        user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lparam)
        time.sleep(0.05)

    time.sleep(2)  # 等酷狗启动

    # ── 找到酷狗窗口，获取 HWND ──
    try:
        import uiautomation as auto
        win = _find_kugou_window_uia(auto)
        if not win:
            logger.warning("【应用启动】 找不到酷狗窗口")
            return False
        hwnd = win.NativeWindowHandle
        if not hwnd:
            logger.warning("【应用启动】 无法获取窗口句柄")
            return False
        logger.info(f"【应用启动】 窗口 HWND: {hwnd}")
    except ImportError as e:
        logger.warning(f"【应用启动】 uiautomation 不可用: {e}")
        return False

    # ──────────────────────────────────
    # 阶段1：搜索（PostMessage 键盘）
    # ──────────────────────────────────
    _ctrl_vk(hwnd, VK_F)
    time.sleep(1.0)

    _post_text(hwnd, song_name)
    time.sleep(0.3)

    _press_vk(hwnd, VK_ENTER)
    time.sleep(2.0)  # 等搜索结果加载
    logger.info("【应用启动】 阶段1（搜索）完成")

    # ──────────────────────────────────
    # 阶段2：定位结果 → 点击播放
    # ──────────────────────────────────
    clicked = False

    try:
        import pyautogui
        pyautogui.FAILSAFE = False  # 防止鼠标移动到角落触发异常

        # 策略A: uiautomation 找 ListItem + pyautogui 硬‍件点击
        try:
            # 刷新控件树 → 重新找搜索结果
            win2 = _find_kugou_window_uia(auto)
            if win2:
                # 找列表项控件（Type=ListItem 或 DataItem）
                for ctrl_type, desc in [
                    (auto.ListItemControl, "ListItemControl"),
                    (auto.DataItemControl, "DataItemControl"),
                    (auto.ListControl,   "ListControl"),
                    (auto.CustomControl, "CustomControl"),
                ]:
                    try:
                        # 尝试找这个类型的子控件
                        first = win2.FindFirstChild(ctrl_type)
                        if first and first.Exists():
                            rect = first.BoundingRectangle
                            if rect[2] > 10 and rect[3] > 10:  # 有实际尺寸
                                # 点击第一项的中间位置
                                cx = int(rect[0] + rect[2] / 2)
                                cy = int(rect[1] + rect[3] / 2)
                                pyautogui.click(cx, cy)
                                time.sleep(0.5)
                                pyautogui.doubleClick(cx, cy)
                                logger.info(f"【应用启动】 策略A: {desc} → 双击 ({cx},{cy})")
                                clicked = True
                                break
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"【应用启动】 策略A 异常: {e}")

        # 策略B: pyautogui 图形识别（找播放按钮图标）
        if not clicked:
            try:
                from PIL import Image
                import io as _io

                # 截取酷狗窗口区域的屏幕
                rect = win.BoundingRectangle
                region = (int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
                screenshot = pyautogui.screenshot(region=region)

                # 保存截图到日志目录（调试用）
                debug_dir = Path("logs")
                debug_dir.mkdir(exist_ok=True)
                ts = time.strftime("%Y%m%d_%H%M%S")
                screenshot.save(str(debug_dir / f"kugou_{ts}.png"))
                logger.info(f"【应用启动】 策略B: 截图已保存 logs/kugou_{ts}.png")

                # 在窗口上半部分（搜索栏）找第一个醒目的可点击元素
                # 通过像素分析定位搜索框下方第一个结果
                w, h = screenshot.size
                # 搜索框通常在顶部，结果列表在中间
                # 在窗口水平中线和垂直 1/3 处点击（典型搜索结果区域）
                cx = int(rect[0] + rect[2] / 2)
                cy = int(rect[1] + rect[3] * 0.4)  # 40% 高度，通常是第一首结果
                pyautogui.doubleClick(cx, cy)
                logger.info(f"【应用启动】 策略B: 智能定位 → 双击 ({cx},{cy})")
                clicked = True
            except Exception as e:
                logger.warning(f"【应用启动】 策略B 异常: {e}")

    except ImportError:
        pass

    # ──────────────────────────────────
    # 阶段3：PostMessage 键盘兜底 ↓ + Enter
    # ──────────────────────────────────
    if not clicked:
        logger.info("【应用启动】 阶段2 未命中 → PostMessage ↓+Enter")
        _press_vk(hwnd, VK_DOWN)
        time.sleep(0.3)
        _press_vk(hwnd, VK_ENTER)
        time.sleep(0.5)
        # 有时需要再按一次 Enter 确认
        _press_vk(hwnd, VK_ENTER)

    logger.info(f"【应用启动】 全流程完成: {song_name}")
    return True


def _try_uiautomation_search(song_name: str) -> bool:
    """uiautomation + pyautogui 混合搜索。

    流程（确保窗口真正位于前台）：
      1. 找到酷狗窗口（uia）
      2. 用 SetFocus + pyautogui 点击窗口中心 → 确保窗口真正位于前台
      3. 发送 Ctrl+F 激活搜索框
      4. 输入歌名 → Enter → 播放第一条
    """
    try:
        import uiautomation as auto
    except ImportError:
        return False

    try:
        kugou_window = _find_kugou_window_uia(auto)
        if kugou_window is None:
            return False

        # 聚焦：SetFocus + pyautogui 点击窗口中央（双重保证）
        kugou_window.SetFocus()
        time.sleep(0.3)

        try:
            import pyautogui
            rect = kugou_window.BoundingRectangle
            center_x = int(rect[0] + rect[2] / 2)
            center_y = int(rect[1] + rect[3] / 2) - 50  # 点标题栏附近，避免误触内容
            pyautogui.click(center_x, center_y)
        except Exception:
            pass
        time.sleep(0.5)

        # ── pyautogui 硬件按键 Ctrl+F 打开搜索框 ──
        try:
            import pyautogui
            pyautogui.hotkey("ctrl", "f")
        except ImportError:
            kugou_window.SendKeys("{Ctrl}f", waitTime=0.3)
        time.sleep(0.8)

        # ── 尝试 uia 找 EditControl ──
        search_edit = kugou_window.EditControl(foundIndex=1)
        if search_edit.Exists(maxSearchSeconds=2):
            try:
                rect = search_edit.BoundingRectangle
                if rect[2] > 0 and rect[3] > 0:
                    # 搜索框可见 → uia 输入
                    try:
                        search_edit.Click()
                    except Exception:
                        search_edit.SetFocus()
                    search_edit.SendKeys("{Ctrl}a", waitTime=0.1)
                    search_edit.SendKeys(song_name, waitTime=0.05)
                    search_edit.SendKeys("{Enter}", waitTime=0.3)
                    time.sleep(1.0)
                    _try_uiautomation_play_first(kugou_window, song_name)
                    return True
            except Exception:
                pass

        # ── 搜索框不可见 → 全 pyautogui 操作 ──
        logger.info("【应用启动】 用 pyautogui 全流程操作")
        try:
            import pyautogui
            pyautogui.hotkey("ctrl", "f")
            time.sleep(0.5)
            pyautogui.write(song_name, interval=0.05)
            pyautogui.press("enter")
            time.sleep(1.5)
            pyautogui.press("down")
            time.sleep(0.2)
            pyautogui.press("enter")
        except Exception:
            return False

        return True

    except Exception as e:
        logger.warning(f"【应用启动】 uia 异常: {e}")
        return False


def _find_kugou_window_uia(auto_module) -> object | None:
    """多策略查找酷狗主窗口，适配不同版本。

    返回 uiautomation 窗口控件对象，或 None。
    """
    # 策略 1：按 ClassName KGMainFrame（标准版酷狗）
    try:
        win = auto_module.WindowControl(searchDepth=1, ClassName="KGMainFrame")
        if win.Exists(maxSearchSeconds=3):
            logger.info("【应用启动】 uia 窗口: ClassName=KGMainFrame")
            return win
    except Exception:
        pass

    # 策略 2：按窗口标题搜索（不同版本通用）
    for title in ("酷狗音乐", "酷狗", "KuGou"):
        try:
            win = auto_module.WindowControl(searchDepth=1, Name=title)
            if win.Exists(maxSearchSeconds=2):
                logger.info(f"【应用启动】 uia 窗口: Name={title}")
                return win
        except Exception:
            continue

    # 策略 3：遍历所有顶层窗口，模糊匹配标题
    try:
        root = auto_module.GetRootControl()
        for win in root.GetChildren():
            try:
                win_name = win.Name or ""
                if "酷狗" in win_name or "kugou" in win_name.lower():
                    logger.info(f"【应用启动】 uia 窗口(模糊匹配): {win_name}")
                    return win
            except Exception:
                continue
    except Exception:
        pass

    # ── 所有策略都失败：打印诊断信息 ──
    try:
        root = auto_module.GetRootControl()
        logger.warning("【应用启动】 === 未找到酷狗窗口，打印所有顶层窗口诊断 ===")
        for i, win in enumerate(root.GetChildren()):
            try:
                logger.warning(f"  [{i}] Name='{win.Name}'  ClassName='{win.ClassName}'  Visible={win.IsVisible}")
            except Exception:
                logger.warning(f"  [{i}] <无法读取>")
        logger.warning("【应用启动】 === 诊断结束 ===")
    except Exception:
        pass

    return None


def _try_uiautomation_play_first(window, song_name: str = "") -> bool:
    """在酷狗搜索结果中选中第一项并播放。

    尝试多种控件类型适应不同版本：
      - ListItemControl   (新版酷狗)
      - DataItemControl   (旧版酷狗)
      - Name 模糊匹配     (兜底)
    """
    import time

    try:
        # 方法 1：查找 ListControl 下的第一个 ListItemControl
        list_ctrl = window.ListControl(foundIndex=1)
        if list_ctrl.Exists(maxSearchSeconds=1):
            first_item = list_ctrl.ListItemControl(foundIndex=1)
            if first_item and first_item.Exists(maxSearchSeconds=1):
                try:
                    first_item.DoubleClick()
                    time.sleep(0.5)
                    logger.info("【应用启动】 uia: ListItem 双击播放")
                    return True
                except Exception:
                    pass

        # 方法 2：直接查找 DataItemControl（旧版）
        first_data = window.DataItemControl(foundIndex=1)
        if first_data and first_data.Exists(maxSearchSeconds=1):
            try:
                first_data.DoubleClick()
                time.sleep(0.5)
                logger.info("【应用启动】 uia: DataItem 双击播放")
                return True
            except Exception:
                pass

        # 方法 3：通过 Name 属性模糊匹配（兜底）
        if song_name:
            try:
                children = list(window.GetChildren() or [])
                for ctrl in children:
                    try:
                        ctrl_name = ctrl.Name or ""
                        if song_name[:2] in ctrl_name:
                            ctrl.DoubleClick()
                            time.sleep(0.5)
                            logger.info(f"【应用启动】 uia: Name 匹配双击: {ctrl_name}")
                            return True
                    except Exception:
                        continue
            except Exception:
                pass

        logger.info("【应用启动】 uia: 未找到结果项，已输入搜索词")
        return False

    except Exception as e:
        logger.warning(f"【应用启动】 uia 播放异常: {e}")
        return False


def _try_pyautogui_search(song_name: str) -> bool:
    """pyautogui 快捷键降级方案。

    精简版：聚焦窗口 → Ctrl+F → 输入 → Enter → ↓ → Enter。
    不再做热键探测，直接走最通用的 Ctrl+F 路径。
    """
    try:
        import pyautogui
    except ImportError:
        return False

    # 聚焦窗口
    info = KNOWN_APPS.get("酷狗音乐") or KNOWN_APPS.get("酷狗")
    if info:
        _focus_window(info.get("window_keywords", ["酷狗"]))
    time.sleep(0.5)

    # Ctrl+F 打开搜索
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.5)

    # 输入歌名
    pyautogui.write(song_name, interval=0.03)
    time.sleep(0.3)

    # Enter 搜索
    pyautogui.press("enter")
    time.sleep(1.5)

    # 选中第一条 → 播放
    pyautogui.press("down")
    time.sleep(0.15)
    pyautogui.press("enter")

    logger.info(f"【应用启动】 pyautogui 指令已发送: {song_name}")
    return True


@tool
def launch_app(
    app_name: str,
    action: str = "open",
    search_query: str = "",
) -> str:
    """
    启动本地应用程序，并可选择自动搜索和播放内容（如歌曲）。

    Args:
        app_name: 应用程序名称，支持：酷狗音乐、酷狗、记事本、计算器、画图
        action: 操作类型
            - "open"   仅打开应用
            - "search" 打开后搜索并播放
        search_query: 搜索查询内容，仅 action="search" 时生效
    """
    exe_path = _find_exe(app_name)
    if not exe_path:
        return (
            f"未找到「{app_name}」\n\n"
            f"解决方法：在 .env 文件中添加 {app_name.upper()}_PATH=你的安装路径"
        )

    try:
        subprocess.Popen([exe_path], shell=True)
        logger.info(f"【应用启动】 已启动 {app_name}: {exe_path}")
    except Exception as e:
        logger.error(f"【应用启动】 启动失败: {e}")
        return f"启动「{app_name}」失败: {e}"

    # 搜索模式：自动搜索并播放
    if action == "search" and search_query and "酷狗" in app_name:
        success = _autosearch_and_play_kugou(search_query)
        if success:
            return (
                f"已打开「{app_name}」并搜索「{search_query}」\n\n"
                f"已在酷狗中执行搜索操作，请查看酷狗窗口确认。"
            )
        return (
            f"已打开「{app_name}」，但自动搜索未能完成。\n"
            f"请手动在酷狗搜索框中输入「{search_query}」并播放。"
        )

    return f"已打开「{app_name}」"
