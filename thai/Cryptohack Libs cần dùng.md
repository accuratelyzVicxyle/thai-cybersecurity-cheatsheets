ต้องใช้ # Cryptohack Libs

## บทนำเกี่ยวกับ Crypto

- base64: ไลบรารี `base64`
- `from Crypto.Util.number import *`
- `^` ใช้งานได้กับตัวเลขเท่านั้น ผลลัพธ์คือตัวเลข
-  ด้วยตัวแปรที่เป็นไบต์ เมื่อเรียกดัชนี จะส่งกลับจำนวนเต็ม 0 ถึง 255
- pwntools: การเชื่อมต่อ netcat

## สมมาตร

```python
import requests, json, string
from pwn import *
from Crypto.Cipher import AES
```

## คีย์สาธารณะ / ECC

```python
import fastecdsa
from fastecdsa.point import Point
from fastecdsa.curve import P256
from ecdsa.ecdsa import Public_key, Private_key, Signature, generator_192
```

## เครื่องมือ

เครื่องมือ - RsaCtf: <https://github.com/RsaCtfTool/RsaCtfTool>
- padding-oracle-attack: <https://github.com/KishanBagaria/padding-oracle-attacker>
- SageMath: <https://doc.sagemath.org/html/en/installation/index.html>
- yafu: <https://github.com/bbuhrow/yafu>

## การติดตั้ง Sage ใน WSL (Kali)

```bash
wsl --install -d kali-linux
# ติดตั้งคอนดา:
cd ~
wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-Linux-x86_64.sh
# จากนั้นสร้าง env sage:
conda create -n sage sage python=3.12 -c conda-forge
```

หลังจากเปิดใช้งาน sage (`conda activate sage`) ให้ติดตั้ง libs เพิ่มเติมสำหรับ python ใน env:

```bash
pip install z3-solver libnum factordb-py pyOpenSSL hlextend
pip install py_ecc fastecdsa coincurve gmssl gmpy2
```

```bash
python -m pip install -U \
  pycryptodome cryptography \
  sympy gmpy2 \
  z3-solver \
  fpylll \
  galois \
  py_ecc ecdsa \
  numpy scipy mpmath \
  pwntools requests
python -m pip install -U \
  networkx ortools \
  randcrack mnemonic owiener libnum primefac \
  coincurve pynacl \
  argon2-cffi bcrypt \
  python-flint \
  scapy pillow \
  phe pqcrypto
python -m pip install cypari2
```
