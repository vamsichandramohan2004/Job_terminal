from . import storage

def ensure_db():
    storage.init_db()

def set_config(key:str, value:str):
    storage.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (key, str(value)))
    print(f"config set {key} = {value}")

def get_config(key:str):
    r = storage.fetch_one("SELECT value FROM meta WHERE key=?", (key,))
    return r['value'] if r else None
