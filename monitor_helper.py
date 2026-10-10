import winreg
import mss

def get_hardware_monitor_names():
    names = []
    base_key_path = r'SYSTEM\CurrentControlSet\Enum\DISPLAY'
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key_path) as base_key:
            for i in range(winreg.QueryInfoKey(base_key)[0]):
                dev_id = winreg.EnumKey(base_key, i)
                dev_path = f'{base_key_path}\\{dev_id}'
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, dev_path) as dev_key:
                    for j in range(winreg.QueryInfoKey(dev_key)[0]):
                        inst_id = winreg.EnumKey(dev_key, j)
                        inst_path = f'{dev_path}\\{inst_id}\\Device Parameters'
                        try:
                            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, inst_path) as param_key:
                                edid, _ = winreg.QueryValueEx(param_key, 'EDID')
                                for k in range(54, 109, 18):
                                    if edid[k:k+4] == b'\x00\x00\x00\xfc':
                                        name = edid[k+4:k+18].decode('ascii', errors='ignore').strip('\x00\n\r\t ')
                                        if name and name not in names:
                                            names.append(name)
                        except Exception:
                            pass
    except Exception:
        pass
    return names

def get_monitor_choices():
    """
    絵文字を排除し、EDIDから取得した実機の製品型番（例: Pixio PX248 WAVE等）を含めた
    綺麗なモニター一覧辞書を返す
    """
    hw_names = get_hardware_monitor_names()
    choices = {"自動追従 (ゲーム画面があるモニター)": "auto"}

    try:
        with mss.mss() as sct:
            for idx, m in enumerate(sct.monitors[1:], start=1):
                res_str = f"{m['width']}x{m['height']}"
                # 実機の型番名があれば付与
                if idx - 1 < len(hw_names):
                    model = hw_names[idx - 1]
                    label = f"ディスプレイ {idx}: {model} ({res_str})"
                else:
                    label = f"ディスプレイ {idx} ({res_str})"
                choices[label] = idx
    except Exception:
        pass

    return choices

if __name__ == "__main__":
    print(get_monitor_choices())
