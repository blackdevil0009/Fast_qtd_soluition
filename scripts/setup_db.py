# Initializes SQLite DB schema for fastqtd
from fastqtd.db import init_db
if __name__ == '__main__':
    init_db()
    print('Initialized SQLite DB at data/fastqtd.db')
