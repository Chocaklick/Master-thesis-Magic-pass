"""Read local credentials without persisting, printing or passing them to CLI."""
import os


def load_credential(config):
    names = [config["credential_environment_variable"],
             config["alternative_credential_environment_variable"]]
    if os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as registry:
                for name in names:
                    try:
                        value, _ = winreg.QueryValueEx(registry, name)
                        if isinstance(value, str) and value.strip():
                            return value.strip(), "Windows current-user environment"
                    except FileNotFoundError:
                        pass
        except FileNotFoundError:
            pass
    for name in names:
        if os.environ.get(name, "").strip():
            return os.environ[name].strip(), "process environment"
    return None, "absent"
