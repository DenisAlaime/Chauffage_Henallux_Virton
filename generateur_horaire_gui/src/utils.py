import os
import ftplib
import configparser

def validate_file_path(file_path: str) -> bool:
    return os.path.isfile(file_path)

def validate_positive_integer(value: str) -> bool:
    return value.isdigit() and int(value) > 0

def read_ini_file(file_path: str) -> list:
    salles = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                if "=" in s:
                    _, val = s.split("=", 1)
                    val = val.strip()
                    if val:
                        salles.append(val)
    except Exception as e:
        print(f"Error reading INI file: {e}")
    return salles

def write_output_file(file_path: str, content: str) -> None:
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing output file: {e}")

def upload_xml_via_ftp(xml_path, config_path="config.ini"):
    """
    Lit les paramètres FTP dans config.ini et téléverse xml_path sur le serveur.
    config.ini attendu (section [ftp]) :
      host = ftp.example.com
      port = 21
      user = username
      password = secret
      remote_dir = /path/on/server
      use_tls = false
      passive = true
    Retourne (True, message) ou (False, erreur).
    """
    if not os.path.exists(xml_path):
        return False, f"Fichier local introuvable: {xml_path}"
    if not os.path.exists(config_path):
        return False, f"Fichier de config introuvable: {config_path}"

    cfg = configparser.ConfigParser()
    cfg.read(config_path, encoding="utf-8")
    if "ftp" not in cfg:
        return False, "Section [ftp] manquante dans config.ini"

    ftp_cfg = cfg["ftp"]
    host = ftp_cfg.get("host")
    if not host:
        return False, "host manquant dans config.ini"
    port = ftp_cfg.getint("port", fallback=21)
    user = ftp_cfg.get("user", fallback="")
    password = ftp_cfg.get("password", fallback="")
    remote_dir = ftp_cfg.get("remote_dir", fallback="")
    use_tls = ftp_cfg.getboolean("use_tls", fallback=False)
    passive = ftp_cfg.getboolean("passive", fallback=True)

    try:
        if use_tls:
            ftp = ftplib.FTP_TLS()
        else:
            ftp = ftplib.FTP()
        ftp.connect(host, port, timeout=30)
        if user:
            ftp.login(user, password)
        else:
            ftp.login()  # anonymous

        if use_tls:
            # secure data connection after login
            ftp.prot_p()

        ftp.set_pasv(passive)

        # changer / créer le répertoire distant (essayer récursif simple)
        if remote_dir:
            parts = [p for p in remote_dir.replace("\\", "/").split("/") if p]
            for p in parts:
                try:
                    ftp.cwd(p)
                except ftplib.error_perm:
                    try:
                        ftp.mkd(p)
                        ftp.cwd(p)
                    except Exception as e:
                        ftp.quit()
                        return False, f"Impossible de créer ou accéder à {p} : {e}"

        remote_name = os.path.basename(xml_path)
        with open(xml_path, "rb") as f:
            ftp.storbinary(f"STOR {remote_name}", f)

        ftp.quit()
        return True, f"Téléversement réussi: {remote_name}"
    except Exception as e:
        try:
            ftp.quit()
        except Exception:
            pass
        return False, str(e)