'''
lydia barnes
lydia.barnes@tuta.io

created november 2022

example parameters for fibre photometry project

'''

def getParameters():
    
    p = {
        "projectName": "behapy",
        "projectDir": "/Users/lydiabarnes/Documents/0_lydia/projects/behapy",
        "dataDir": "/Users/lydiabarnes/Documents/0_lydia/data/behapy",
        "normMethod": 'fit', #see normalise() in fp.py
        "normDetrend": True,
    }

    sinfo = [
        'Rats18-21-210330-104533',
        'Rats22-24-210330-121724',
        'Rats25-28-210330-141217',
        'Rats29-31-210330-151439',
    ]
    return p,sinfo

