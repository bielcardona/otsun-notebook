from bielcardona/python-freecad:1.0.1-1

## Hack per fer que les llibreries carreguin el libstdc modern
#RUN rm /usr/lib/x86_64-linux-gnu/libstdc++.so.6
#RUN ln -s /freecad_root/usr/lib/libstdc++.so.6.0.34 /usr/lib/x86_64-linux-gnu/libstdc++.so.6

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

# arxius que s'han de distribuir dins de la imatge
COPY dist /dist

WORKDIR /