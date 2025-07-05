# jupyter_notebook_config.py
c = get_config()
c.NotebookApp.password = 'argon2:$argon2id$v=19$m=10240,t=10,p=8$BZw6BBxzOwqGAz5UCNjrzg$hFeFt7AgW3x8p+m1p3X/81FZ31cVmZWnLl08DxyeBOk'
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False
c.NotebookApp.allow_root = True
