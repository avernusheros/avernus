import os

current_dir = os.path.dirname(__file__)
ignores = ['__init__.py']

files = [f for f in os.listdir(current_dir) if f.endswith(".py") and f not in ignores]
modules = [f.replace(".py", "") for f in files]

sources = {}

for m in modules:
    exec("import " + m)
    exec("ds = "+m+".DataSource()")
    sources[ds.name] = ds


print sources
