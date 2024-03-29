# -*- coding: utf-8 -*-
"""
Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1FPsXH07BTTRUj-PbZHGHusUhVlW7TbOs

# **LIBRARY IMPORT**
"""

import Crypto 
import binascii
import pandas as pd
import hashlib
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from google.colab import files

"""# **DATASET IMPORT**

*   Dataset yang diambil adalah sebuah dataset tentang sensor untuk mengecek kualitas air pantai di Chicago, USA 
*   Kolom yang diambil dalam dataset ini adalah "Measurement Timestamp", "Water Temperature", "Turbidity", "Transducer Depth", "Wave Height", "Wave Period", "Battery Life"
"""

## Read csv dataset
source_df = pd.read_csv('https://firebasestorage.googleapis.com/v0/b/dataset-476f2.appspot.com/o/beach-water-quality-automated-sensors-1.csv?alt=media&token=ef3a2566-9f96-4236-8008-7e6a1d2dc470')

## Mengambil kolom yg digunakan
source_df = source_df[["Measurement Timestamp", "Beach Name",  "Water Temperature", "Turbidity", "Transducer Depth", "Wave Height", "Wave Period", "Battery Life"]]
source_df = source_df.rename({'Measurement Timestamp': 'timestamp', 'Beach Name' : 'beach_name', 'Water Temperature' : 'water_temperature', 'Turbidity': 'turbidity','Transducer Depth' : 'transducer_depth', 'Wave Height' : 'wave_height', 'Wave Period' : 'wave_period', 'Battery Life' : 'battery_life'}, axis='columns')

## Konfirgurasi jumlah data yang diambil
source_df = source_df.head(10000)

"""# **DATA PREPARATION**

*   Melakukan proses insert nilai yang kosong dikarenakan pada kolom 'transducer_depth' terdapat baris yang tidak ada nilainya
*   Melakukan convert type data ke DateTime untuk kolom timestamp, agar data timestamp bisa diproses dan diurutkan dengan benar
*   Melakukan convert type data dari float ke string untuk setiap data sensor, dikarenakan setiap kolom nilainnya akan di convert menjadi hexa
"""

normalized_df = source_df.copy(deep=True)

## Drop baris dengan timestamp tidak valid
normalized_df = normalized_df.dropna(subset=['timestamp'])

## Insert nilai placeholder untuk transducer depth kosong
normalized_df['transducer_depth'] = normalized_df['transducer_depth'].fillna(-1)

## Convert float to string
normalized_df['water_temperature'] = normalized_df['water_temperature'].apply(str)
normalized_df['turbidity'] = normalized_df['turbidity'].apply(str)
normalized_df['transducer_depth'] = normalized_df['transducer_depth'].apply(str)
normalized_df['wave_height'] = normalized_df['wave_height'].apply(str)
normalized_df['wave_period'] = normalized_df['wave_period'].apply(str)
normalized_df['battery_life'] = normalized_df['battery_life'].apply(str) 

## Convert string ke datetime untuk sorting
normalized_df['timestamp'] = pd.to_datetime(normalized_df['timestamp'])
normalized_df = normalized_df.sort_values(by=['timestamp'])
normalized_df = normalized_df.reset_index(drop=True)

## Kembalikan timestamp ke string untuk memudahkan pemrosesan
normalized_df['timestamp'] = normalized_df['timestamp'].apply(str)

"""# **DATA GROUPABLES**"""

# Lists to help group data by beach-sensor (for public key selection)
beach_list = normalized_df['beach_name'].unique()
sensor_list = normalized_df.columns[2:].tolist()

print(beach_list)
print(sensor_list)

# List and map to group data into block (each block is representing 1 timestamp)
timestamp_list = normalized_df['timestamp'].unique()
timestamp_map = { timestamp_list[i] : int(i) for i in range(0, len(timestamp_list) ) }

print(timestamp_list)
print(timestamp_map)

"""# **PUBLIC KEY & PRIVATE KEY**"""

public_key = {}
encryptor = {}

keys_df = pd.DataFrame(data = {
    'beach_name': [],
    'sensor_no': [],
    'sensor_name': [],
    'public_key': [],
})

for beach in beach_list:
  public_key[beach] = [{} for _ in range(len(sensor_list))]
  encryptor[beach] = [{} for _ in range(len(sensor_list))]

  for i in range(len(sensor_list)):
    keyPair = RSA.generate(1024)
    pubkey = keyPair.publickey()

    public_key_hex = str(hex(int.from_bytes(pubkey.exportKey(format='DER'),'big')))[2:]
    private_key_hex = str(hex(int.from_bytes(keyPair.exportKey(format='DER'),'big')))[2:]

    public_key[beach][i] = public_key_hex
    encryptor[beach][i] = PKCS1_OAEP.new(keyPair.publickey())

    keys_df = keys_df.append({
        'beach_name': beach,
        'sensor_no': i,
        'sensor_name': sensor_list[i],
        'public_key': public_key_hex,
        'public_key': private_key_hex,
    }, ignore_index=True)

# set sensor_no sebagai integer
keys_df['sensor_no'] = keys_df['sensor_no'].apply(int)

"""# **DATA STREAM HEAD HASH**

*   Melakukan proses hashing untuk setiap nama kolom dataset kedalam SHA1
*   Melakukan proses dari hasil hash di convert menjadi hexa
"""

## Proses hash dengan SHA1

head_hash = [hashlib.sha1(x.encode('UTF-8')).hexdigest() for x in sensor_list]

"""# **DATA STREAM CIPHER HASH**

Penjelasan:
*   Melakukan proses hashing nilai pada setiap kolom kedalam SHA1
*   Melakukan proses encryp dari hasil hash
*   Melakukan proses dari hasil encryp di convert menjadi hexa
"""

cipher_hash_df = normalized_df.copy(deep=True)

## Proses encryption
for row in cipher_hash_df.index:
  for i in range(len(sensor_list)):
    cipher_hash_df.loc[row, sensor_list[i]] = encryptor[cipher_hash_df.loc[row, 'beach_name']][i].encrypt(cipher_hash_df.loc[row, sensor_list[i]].encode('UTF-8'))

## Proses hash to SHA1
cipher_hash_df['water_temperature'] = [hashlib.sha1(val).hexdigest() for val in cipher_hash_df['water_temperature']]
cipher_hash_df['turbidity'] = [hashlib.sha1(val).hexdigest() for val in cipher_hash_df['turbidity']]
cipher_hash_df['transducer_depth'] = [hashlib.sha1(val).hexdigest() for val in cipher_hash_df['transducer_depth']]
cipher_hash_df['wave_height'] = [hashlib.sha1(val).hexdigest() for val in cipher_hash_df['wave_height']]
cipher_hash_df['wave_period'] = [hashlib.sha1(val).hexdigest() for val in cipher_hash_df['wave_period']]
cipher_hash_df['battery_life'] = [hashlib.sha1(val).hexdigest() for val in cipher_hash_df['battery_life']]

"""# **BLOCK TABLE**

Membuat tabel yang berisi block_id dan timestamp
"""

block_df = pd.DataFrame(data = {
    'timestamp': normalized_df['timestamp'].unique(),
})

block_df = block_df.reset_index()
block_df = block_df.rename(columns={'index':'block_id'})

"""# **INDEX TABLE**

Melakukan penggabungan nilai data stream head hash, data stream hash dan public key
"""

index_df = pd.DataFrame(data = {
    'block_id': [],
    'index': [],
})

print(len(head_hash[i]), '-', len(cipher_hash_df.loc[row, sensor_list[0]]), '-', len(public_key[cipher_hash_df.loc[row, 'beach_name']][0]) )
for row in cipher_hash_df.index:
  for i in range(len(sensor_list)):
    index_df = index_df.append({
        'block_id': timestamp_map[cipher_hash_df.loc[row, 'timestamp']],
        'index': head_hash[i] + cipher_hash_df.loc[row, sensor_list[i]] + public_key[cipher_hash_df.loc[row, 'beach_name']][i]
    }, ignore_index=True)


# set block_id sebagai integer
index_df['block_id'] = index_df['block_id'].apply(int)

"""# **CONVERT TO CSV**"""

## Block Table
block_df.to_csv('block.csv', index=False)
files.download('block.csv')

## Index Table
index_df.to_csv('index.csv', index=False)
files.download('index.csv')

## Key Export
keys_df.to_csv('keys.csv', index=False)
files.download('keys.csv')