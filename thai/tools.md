# tools - กล่องเครื่องมือ Crypto

คู่มือการติดตั้ง + คำสั่งสำหรับชุดเครื่องมือถอดรหัสลับ: สภาพแวดล้อม Python/Sage, แฟคตอริ่ง, RSA all-in-one, OpenSSL, แฮช, stego, นิติวิทยาศาสตร์ กฎทั่วไป: **จัดลำดับความสำคัญของเครื่องมือออฟไลน์** — ห้ามอัปโหลดข้อมูลที่ละเอียดอ่อน (การทดสอบ ข้อมูลลับ ดัมพ์) ไปยังบริการเว็บสาธารณะ เมื่อถูกบังคับให้ใช้เว็บ (การค้นหาแบบสาธารณะเช่น factordb.com) ให้ส่งเฉพาะค่าที่ "ไม่เป็นอันตราย" เท่านั้น (หมายเลขสาธารณะ n)

## Sage บน WSL

วิธีชั่วคราว (เซสชันปัจจุบันเท่านั้น):
```bash
source ~/miniforge3/etc/profile.d/conda.sh
conda activate sage
```
วิธีถาวร (แนะนำ):
```bash
~/miniforge3/bin/conda init bash
exec bash          # หรือออกจาก SSH แล้วเข้าสู่ระบบอีกครั้ง
conda activate sage
```

## Python 3 สภาพแวดล้อม (WSL/Linux)

```bash
python3 -m venv v && source v/bin/activate
pip install pycryptodome gmpy2 sympy pwntools
# หรือด้วยยูวี:
uv venv && uv pip install pycryptodome gmpy2 && uv run solve.py
```
เครื่องมี `python2` ของตัวเองเพื่อใช้สำหรับสคริปต์เก่า (สคริปต์รุ่นเก่าที่พิมพ์โดยไม่มีวงเล็บ)

## factordb-หลาม

เช็คอิน N เข้าสู่ FactorDB โดยไม่ต้องเปิดเว็บ
```python
from factordb.factordb import FactorDB
f = FactorDB(n); f.connect()
print(f.get_status(), f.get_factor_list())
```
หมายเหตุ: สถานะ `C` คอมโพสิต = ยังไม่ได้แยกตัวประกอบ รายการอาจมีปัจจัยผสม → ตรวจสอบด้วยตนเอง `p*q == n` และ `isprime` สำหรับแต่ละปัจจัย

## Fermat (p ≈ q) — เขียนเอง ลองทุกครั้งก่อนที่จะคิดถึง ECM

ยอดคงเหลือ N ถึง (≥2048บิต) ซึ่ง FactorDB ไม่มี → p สามารถใกล้เคียงกับ √N. **PARI `factor()` ไม่มีขั้นตอนนี้** (สายโซ่: การแบ่งการทดลอง → Rho/SQUFOF → ECM → MPQS) → การแฮงแบบไม่มีที่สิ้นสุด: ECM ไม่สามารถเก็บแฟคเตอร์ 4096 บิตได้ (บันทึก ~275 บิต), MPQS ตายที่ ~130 ตัวเลข Python 5 บรรทัดทันที:
```python
from gmpy2 import isqrt
def fermat(n, max_iter=10**6):
    a = isqrt(n)
    if a*a < n: a += 1
    for _ in range(max_iter):
        b2 = a*a - n
        b = isqrt(b2)
        if b*b == b2: return int(a-b), int(a+b)   # ไม่มี = ไม่ใช่ p≈q
        a += 1
```
ตัวอย่างจริง: RSA-8192 สมดุลกับ p−q = 2886 → แฟร์มาต์ชนะในรอบที่ 1 (0.000 วินาที) PARI ค้างตลอดไป

## SymPy

เลขคณิตสำหรับตัวเลขขนาดเล็ก (เดรัจฉาน, ค้นหาจำนวนเฉพาะ, ตัวประกอบ ≤ ~40 บิต, ความสอดคล้อง, ไดโอแฟนไทน์/เพลล์) N ขนาดใหญ่ (2048 บิต) ไม่ใช่ — ตาม chain factordb → Fermat → PARI/Sage ทดสอบบน sympy 1.14 — **3 ฟังก์ชั่นไม่ใช่ระดับบนสุด** (ดูการนำเข้าด้านล่าง)
```python
from sympy import (primerange, isprime, nextprime, prevprime, prime, primepi,
                   randprime, factorint, divisors, mod_inverse, gcd, lcm,
                   sqrt_mod, legendre_symbol, is_quad_residue,
                   n_order, primitive_root, discrete_log, diophantine)
# 3 ฟังก์ชั่นเหล่านี้ไม่ใช่ระดับบนสุด (sympy 1.13/1.14):
from sympy.core.intfunc import igcdex                 # (x, y, g): a*x + b*y = ก
from sympy.ntheory.modular import crt                 # -> (x, เอ็ม)
from sympy.solvers.diophantine.diophantine import diop_DN

list(primerange(2, 4096))        # จำนวนเฉพาะใน [2,4096) — เปิดครึ่งหนึ่ง ไม่รวม 4096 -> 564 หมายเลข
isprime(n); nextprime(n); prevprime(n); prime(100); primepi(4096)   # 541; 564
randprime(a, b)                  # ไพรม์สุ่มใน [a,b)

factorint(n)                     # {p: k, ...} เช่น {1429:1, 1531:1}
factorint(n, limit=10**5)        # การแบ่งการทดลองเพื่อจำกัด; ส่วนที่ยังไม่มีปัจจัยอยู่
                                 # ระบุว่าเป็น "ปัจจัย" - ต้อง isprime() อีกครั้ง!

mod_inverse(e, phi)              # = pow(e,-1,phi); ValueError หากไม่สามารถย้อนกลับได้
igcdex(a, b)                     # เบซูต์ (x, y, g) โดยมี a*x + b*y = g — x ก่อน g
                                 # gmpy2.gcdext(a,b) คือ (g, x, y) — ลำดับย้อนกลับ!
crt([2, 3, 5], [1, 2, 3])        # -> (23, 30) — TUPLE (รูต, โมดูลัส); โมดูลคู่ NTLCN
sqrt_mod(a, p, all_roots=True)   # สแควร์รูท mod p ไพรม์ -> [r1, p-r1] (Tonelli-Shanks)
legendre_symbol(a, p); is_quad_residue(a, p)
n_order(g, p)                    # ระดับ g: n_order(10,17)=16 -> 1/17 ซ้ำ 16 หลัก
primitive_root(p); discrete_log(n, a, b)   # แก้ b^x ≡ a (mod n), กลุ่ม ≤ ~40 บิต

diop_DN(D, N)                    # สารละลายราก (x1,y1) ของ x²-Dy²=N; เช่น diop_DN(7,1)=(8,3)
                                 # ทดสอบ: (x1+y1√D)^k — เขียนลูปการคูณของคุณเองใน Z[√D]
diophantine(expr, syms=[x, y])   # รูปแบบสัญลักษณ์ พารามิเตอร์ต้องเป็น syms= (ใส่รายการ
                                 # ตำแหน่ง 2 = TypeError); เอาต์พุตตระกูลโซลูชัน = ใน t - สิ่งกีดขวาง
                                 # Pell ใช้ diop_DN + autogenous จริงๆ
```

หมายเหตุ:
สเกลความเร็ว - : sympy ช้ากว่า gmpy2 (ซิมปีสำหรับ CONCEPTS — ไพรม์/แฟคเตอร์/ออร์เดอร์/ไดโอแฟนไทน์; gmpy2 สำหรับการคูณขนาดยักษ์) สคริปต์สามารถผสมทั้งสองอย่างได้
- `discrete_log(n, a, b)` ได้รับลำดับ a/b ผิดและทำงานตลอดไป — ให้จด `b^x = a mod n` ไว้ข้างการโทรเสมอ
- sympy ส่งคืน `Integer` ของตัวเอง (ช้ากว่า int ในการคำนวณล้วนๆ) ปัดเดรัจฉานหนักๆ จากนั้น `int()` อีกครั้งก่อนแคป

## การโจมตีแบบเข้ารหัสลับ

คลังการโจมตีนับร้อย (RSA, lattice, DH, ECC...) การโจมตีแต่ละครั้ง = เป็นฟังก์ชัน Python พร้อม docstring บนเครื่อง Kali โดยปกติจะอยู่ที่ `/opt/tools/crypto-attacks`; ถ้าไม่ ให้โคลนจาก <https://github.com/jvdsn/crypto-attacks>
```bash
ls /opt/tools/crypto-attacks/attacks/rsa/        # wiener.py, common_modulus.py, ...
```
```python
import sys; sys.path.insert(0, "/opt/tools/crypto-attacks")
from attacks.rsa.wiener import attack
d = attack(n, e)
```
หมายเหตุ: ตรวจสอบชื่อโมดูล/ฟังก์ชัน/พารามิเตอร์ด้วย docstring สำหรับแต่ละไฟล์ก่อนใช้งาน

## RsaCtfTool (Windows/WSL)

RSA ออลอินวัน: เรียกใช้การโจมตีจากคีย์สาธารณะโดยอัตโนมัติ
```bash
python3 RsaCtfTool.py --publickey key.pub --uncipherfile flag.enc --attack all
python3 RsaCtfTool.py -n <N> -e 65537 --private
python3 RsaCtfTool.py --publickey key.pub --attack wiener
```
หมายเหตุ: `all` ทำงานช้า (หลายนาที); หากคุณสามารถเดาฮิวริสติกได้ ให้ระบุ

## PARI/GP

```bash
gp -q
```
```
factor(n)                        ~ ECM+MPQS, tốt tới ~60-70 bit thừa số
isprime(n); znorder(Mod(g,p))
znlog(Mod(h,p), Mod(g,p))        ~ DLP (p-1 smooth)
msqrt(a,p)                       ~ sqrt mod p (Tonelli-Shanks)
Mod(c,n)^d                       ~ pow
E=ellinit([a,b],p); ellmul(E,G,k); elllog(E,P,G)
```
ซับในเดียว: `gp -q <<<'print(factor(2^67-1))'`
หมายเหตุ: ECDLP จะทำได้เฉพาะเมื่อมีคำสั่งซื้อน้อย (ไม่กี่โหลบิต)

## OpenSSL

```bash
openssl rsa -in key.pem -text -noout          # ดูพารามิเตอร์ที่สำคัญ
openssl pkeyutl -decrypt -in ct.bin -inkey key.pem
openssl enc -aes-256-cbc -d -K <hexkey> -iv <hexiv> -in f.enc
openssl dgst -sha256 -verify pub.pem -signature sig.bin file
openssl x509 -in cert.pem -text -noout

# แยก n, e จากคีย์สาธารณะ
openssl rsa -pubin -in PublicKey.pem -text -noout      # คีย์สาธารณะ: (บิต) + โมดูลัสฐานสิบหก + เลขชี้กำลัง
openssl rsa -pubin -in PublicKey.pem -modulus -noout   # ฐานสิบหกต่อเนื่องกัน ไม่มี ':' (Modulus=00b6...)
openssl rsa -pubin -in PublicKey.pem -modulus -noout | cut -d= -f2 \
  | xargs -I{} python3 -c "print(int('{}',16))"        # n ทศนิยม โยนตรงไปที่ python/sage
python3 -c "from Crypto.PublicKey import RSA; k=RSA.import_key(open('PublicKey.pem','rb').read()); print('n =', k.n); print('e =', k.e)"   # กะทัดรัดที่สุด: n,e ทศนิยม
```
หมายเหตุ: `-K/-iv` (HOA) = คีย์ดิบ hex ไม่มี KDF; โดยปกติแล้ว `-k` จะเป็นรหัสผ่าน = (พร้อม KDF/salt) อินพุต `-pubin` = เป็นคีย์สาธารณะ (`BEGIN PUBLIC KEY`); ถ้า `BEGIN CERTIFICATE` แล้ว `openssl x509 -in cert.pem -noout -modulus` ข้อผิดพลาดในการแยกวิเคราะห์ PEM → ลองเพิ่ม `-inform DER` เคล็ดลับในการวัดขนาดคีย์จากความยาว base64: `modulus_bytes ≈ DER_bytes − 30` (เช่น ~2 base64 บรรทัด = ~62 ไบต์ DER = โมดูลัส 256 บิต; 162 ไบต์ DER = 1,024 บิต) → โมดูลัสมีขนาดเล็กผิดปกติ จากนั้นแยกตัวประกอบทันที

พบ Gotcha: PEM สาธารณะสามารถจงใจผิด 1 บิตใน n (คำใบ้เช่น "หายไป 1 บิต") - ข้อความเข้ารหัสที่เข้ารหัสด้วย n จริง = n PEM พร้อมบิตพลิก; ตำแหน่ง Brute 256 บิต เลือกผู้สมัครเป็นเซมิไพรม์โดยมี 2 ปัจจัยพอดี โมดูลัส RSA ที่แท้จริงจะเป็น ODD เสมอ → n เป็นเลขคู่ ลองใช้ `n | 1` ก่อน

รายละเอียดทั้งหมดของรายการคำสั่ง openssl ทั้ง 14 รายการ: `cheatsheet-openssl.md`

## hขยาย

การขยายความยาวแฮชเมื่อทราบ `hash(secret‖msg)` + ความยาวลับ
```python
import hlextend
h = hlextend.new('sha256')
data = h.extend(b'&admin=1', b'user=x', 16, known_hash_hex)   # ไบต์ที่ส่งไป
print(data, h.hexdigest())
```
หมายเหตุ: ความยาวความลับต้องถูกต้อง — ถ้าคุณไม่รู้ก็ brute 8..64

## padding-oracle-attacker

ทำให้ oracle เสริม CBC อัตโนมัติผ่าน HTTP
```bash
padding-oracle-attacker --help
padding-oracle-attacker -u http://t/dec -e <hexct> --block-size 16 --error "Padding"
```
หมายเหตุ: เครื่องมือนี้พิถีพิถันเกี่ยวกับเซิร์ฟเวอร์ การเขียนสคริปต์คำขอ 16 × 256 ของคุณเองนั้นรวดเร็วมากเช่นกัน (ดู `cheatsheet-symmetric.md` ส่วนที่ 3.5)

## jwt_tool

```bash
jwt_tool <token>              # การตรวจสอบอัตโนมัติ
jwt_tool <token> -T           # การงัดแงะแบบโต้ตอบ
jwt_tool <token> -X k -pk pub.pem   # โหมดการโจมตี (สับสน, ไม่มี, ...)
```

## hashid/hashcat/John

```bash
hashid '$6$abc...'                        # เดารูปแบบแฮช
hashcat -m 1800 -a 0 h.txt /usr/share/wordlists/rockyou.txt
john --wordlist=/usr/share/wordlists/rockyou.txt h.txt
john --show h.txt
```
`-m` ที่ใช้กันทั่วไป: `0` MD5, `100` SHA1, `1400` SHA256, `1000` NTLM, `1800` sha512crypt `$6$`, `3200` bcrypt
หมายเหตุ: ตรวจสอบ GPU (`nvidia-smi`) ก่อนที่จะคาดหวัง hashcat ที่รวดเร็ว bcrypt เกือบจะปิดการทำงานบน CPU

## zsteg

```bash
zsteg -a file.png                  # สแกนทุกช่อง/บิตสั่งซื้อ
zsteg -E b1,rgb,lsb,xy file.png    # แยก 1 โหมดอย่างแน่นอน
```

## ร็อคคุณ + SecLists

```
/usr/share/wordlists/rockyou.txt
/usr/share/seclists/Passwords/Common-Credentials/
```
Gotcha ไฟล์ wordlist ขนาดใหญ่: บรรทัดว่างตรงกลางไฟล์ทำให้สคริปต์ EOF ก่อนเวลาหากตรวจสอบเฉพาะ `if line`; อ่านไบนารี `latin-1` เพื่อหลีกเลี่ยงการชนกับไบต์แปลก ๆ

##  ชุดเครื่องมือคลาสสิก

โฟลเดอร์ `classical/` — stdlib ล้วนๆ ไม่จำเป็นต้องติดตั้งอะไรเลย ทดสอบการทำงานหลังจากการคัดลอกไปยังคอมพิวเตอร์เครื่องอื่น: `python _verify_all.py` → ควรส่งออก `24 passed` แทนที่ความต้องการโปรแกรมแก้ปัญหาเว็บ (dCode...) ด้วยเวอร์ชันออฟไลน์ + CyberChef ในเครื่อง

```bash
cd classical/

# เครื่องมือทุกตัวด้านล่างนี้ยอมรับอินพุตทั้ง 3 ประเภท: ข้อความในบรรทัด "..." | ไฟล์ | มาตรฐาน "-"
# (หาเรื่องไม่เหมือนกับชื่อไฟล์จริง = ตีความว่าเป็นข้อความอินไลน์ "-" = stdin)

# ขั้นตอนที่ 1 ทำงานเสมอ: วินิจฉัย IC/chi2 -> แนะนำตระกูลรหัส
python freq_ic.py ct.txt        # หรือ: python freq_ic.py "Khoor Zruog"
# IC ~0.066 -> การทดแทนโมโน / ROT -> rot_family.py -> substitution_hillclimb.py
# IC ~0.04 -> หลายตัวอักษร -> vigenere_keyless.py / xor_tool.py
# ไบนารี่ ผลคูณของ 5 -> baudot.py; จำนวนมากที่ไม่สามารถพิมพ์ได้ -> xor_tool.py

# ตระกูล ROT: brute ROT-N (26) + ROT47 (94 กะ) + Atbash + Affine (312 คีย์)
python rot_family.py "Khoor Zruog"
python rot_family.py ct.txt

# Vigenère NO key: ค้นหาความยาวคีย์ (IC) + คีย์โดยอัตโนมัติ (แบ่งแต่ละคอลัมน์)
python vigenere_keyless.py ct.txt
python vigenere_keyless.py --keylen 7 ct.txt      # กดความยาว
python vigenere_keyless.py --key LEMON ct.txt     # ถอดรหัสมีรหัส

# โมโนทดแทน: รูปสี่เหลี่ยมปีนเขา (ลองใช้จุดที่เหมาะสมที่สุดแล้ววิ่งอีกครั้ง)
python substitution_hillclimb.py ct.txt

# ตารางตัวอักษร Base64 CUSTOM จากข้อความธรรมดาที่รู้จัก
# เข้าร่วมทุกส่วนที่รู้จักเป็นคู่เดียวเพื่อครอบคลุมอักขระทั้ง 64 ตัว
python custom_b64_recover.py --known-plain "known..." --known-cipher "8kP3..." --target "Xy..."

# Baudot/ITA2 5 บิต — ทดสอบตัวเอง 4 โหมดการอ่าน (MSB/LSB x เริ่ม LTRS/FIGS)
python baudot.py decode bits.txt
python baudot.py decode5 file.txt        # ตัวแปร: แต่ละกลุ่ม 5 บิต = 1 ตัวอักษร (A=0)
python baudot.py encode "HELLO"

# XOR: 1 ไบต์ brute / คีย์ซ้ำ (รับ hex, base64, raw, ไฟล์)
python xor_tool.py single "1b37373331363f78..."
python xor_tool.py multi ct.bin
python xor_tool.py multi --keylen 11 ct.bin

# คี่: A1Z26 / Polybius / รหัสแทป / มอร์ส / เบคอน / รั้วราง
python misc_classical.py a1z26 "8 5 12 12 15"
python misc_classical.py polybius "23 15 31 31 34"
python misc_classical.py morse "... --- ... / .... . .-.. .-.. ---"
python misc_classical.py bacon "ABABA ABBAB BAABB AABAA"
python misc_classical.py railfence_brute "WECRLTEERDSOEEFEAOCAIVDEN"
```

หมายเหตุ:
หลักการ - : `caesar_shift(ct, k)` แปล BACKWARD k การถอดรหัส =; เข้ารหัสโดยใช้ `-k`
- `vigenere_keyless` ถือว่าข้อความธรรมดาภาษาอังกฤษ เลือก keylen = **คาบที่เล็กที่สุดที่มี IC สูง** (ผลคูณของคาบจริงก็มี IC สูงเช่นกัน — อย่าเลือกนานกว่านี้)
- `substitution_hillclimb` จำเป็นต้องมี `english_quadgrams.txt` (อยู่ในโฟลเดอร์อยู่แล้ว หากสูญหาย ให้ดาวน์โหลดใหม่ตาม README)
- yberChef LOCAL ครอบคลุม: ROT brute, Atbash, Affine, Vigenère พร้อมกุญแจ, XOR, รั้วราง, Bifid/Trifid, Morse, Bacon, **Enigma** (แยกส่วน: โรเตอร์/ตัวสะท้อนแสง/ปลั๊กบอร์ด), Base64/32/58/85 พร้อม **ตัวอักษรกำหนดเอง** แก้ไขอัตโนมัติโดยไม่ต้องใช้คีย์ → ชุดเครื่องมือด้านบน
-  pip ตัวเลือก: `pip install py-enigma pycipher xortool`

## CRC ของ PNG (เมื่อคุณต้องการแก้ไขส่วนหัว/ความกว้างของภาพ)

```python
import struct, zlib
width, height = 1500, 1125
data = (b'IHDR' + struct.pack(">I", width) + struct.pack(">I", height)
        + bytes.fromhex("08 06 00 00 01"))
crc = zlib.crc32(data) & 0xffffffff
print(f"CRC32 = {crc:08X}")
```

## STEGO / สื่อ

| เครื่องมือ | คำสั่ง | เมื่อ |
|------|------|---------|
| บินวอล์ค | `binwalk -Me file` | แยกไฟล์ฝังตัว, เฟิร์มแวร์ |
| ExifTool | `exiftool img.jpg` | ข้อมูลเมตา ความคิดเห็น |
| สตริง | `strings -n 6 file; strings -el file` | ASCII + UTF-16 |
| xxd | `xxd file \| head`; `xxd -r -p hex.txt > out.bin` | มุมมองฐานสิบหก / ฐานสิบหกย้อนกลับ |
| สตีไฮด์ | `steghide info -sf a.jpg`; `steghide extract -sf a.jpg -p pass` | ข้อความรหัสผ่าน JPEG/BMP |
| สเตกซีก | `stegseek a.jpg rockyou.txt -xf out` | ถอดรหัสข้อความรหัสผ่าน Steghide (เร็ว) |
| สเต๊กสโนว์ | `stegsnow -C -p pass f.txt` | stego ช่องว่างในข้อความ |
| สเต๊กโซลฟ์ | `java -jar StegSolve.jar` | เรียกดูระนาบ LSB แยกข้อมูล |
| pngตรวจสอบ | `pngcheck -v f.png` | PNG มีรูปแบบไม่ถูกต้อง / ชิ้นแปลก ๆ |
| ซีบาร์ | `zbarimg -q qr.png` | อ่าน QR |
| ImageMagick | `identify -verbose i.png`; `magick compare a.png b.png d.png` | เปรียบเทียบภาพช่องอัลฟ่า |
| FFmpeg | `ffmpeg -i f.mp4 -vn out.wav`; `ffmpeg -i f.mp4 fr/%05d.png` | แยกเสียง/เฟรม |
| ซ็อกซ์ | `sox f.wav -n spectrogram -o s.png` | spectrogram (ตั้งค่าสถานะเป็นสเปกตรัม) |
| เอสเอสทีวี | `sstv -d audio.wav -o img.png` | ถอดรหัส SSTV |
| multimon-ng | `multimon-ng -t wav audio.wav` | AFSK/POCSAG/DTMF |
| Sonic Visualiser / ความกล้า | กุย | การวิเคราะห์เสียงด้วยตนเอง |
| qpdf | `qpdf --decrypt locked.pdf out.pdf`; `qpdf --show-object=N f.pdf` | ปลดล็อค PDF ดูวัตถุ |
| มูทูล | `mutool clean -d in.pdf out.pdf` | แยกสตรีม PDF ที่ซ่อนอยู่ของ JS |
| peepdf-3 | `peepdf -i file.pdf` | การวิเคราะห์ PDF แบบโต้ตอบ |
| pdfid/pdf-parser | .pdfid/pdf-parser | .pdfid/pdf-parser `pdfid f.pdf`; `pdf-parser -o N f.pdf` | สแกน `/JS /OpenAction` วัตถุดัมพ์ |
| AperiSolve | รัน `/opt/tools/AperiSolve` ในเครื่อง (นักเทียบท่า) | stego แบบครบวงจร (ช้า ใช้ล่าสุด) |

## นิติวิทยาศาสตร์

| เครื่องมือ | คำสั่ง | เมื่อ |
|------|------|---------|
| ระเหย3 | `vol -f mem.raw windows.info` ; `windows.pslist`; `windows.cmdline`; `windows.netscan`; `windows.filescan`; `windows.dumpfiles --virtaddr 0x…` | การถ่ายโอนข้อมูลหน่วยความจำ Windows |
| ความผันผวน 2 | `vol.py -f mem.raw --profile=Win7SP1x64 pslist` | กองขยะเก่า |
| OpenSSH-เซสชัน-คีย์-การกู้คืน | ปลั๊กอิน vol3 (WSL) | กู้คืนคีย์เซสชัน SSH จากหน่วยความจำ |
| ชุดนักสืบ | `fls disk.raw`; `icat disk.raw inode > out` | เรียกดู FS แยกไฟล์โดย inode |
| สำคัญที่สุด | `foremost -i disk.img -o out/` | แกะสลักด้วยลายเซ็น |
| PhotoRec/TestDisk | `photorec disk.img` | แกะสลักแบบโต้ตอบ แก้ไขพาร์ติชัน |
| Bulk_extractor | `bulk_extractor -o out/ dump.raw` | สแกนอีเมล/url/ข้อมูลประจำตัวในดัมพ์ |
| ปลาโซ | `log2timeline.py t.plaso img`; `psort.py -w tl.txt t.plaso` | ไทม์ไลน์ทั้งระบบ |
| เลื่อยไฟฟ้า | `chainsaw hunt evtx/ -s sigma/ --mapping sigma_default.yml` | ล่า EVTX โดย sigma |
| ฮายาบูสะ | `hayabusa -d evtx/` | การวิเคราะห์ EVTX ที่รวดเร็ว |
| RegRipper | `rip.pl -r NTUSER.DAT -f all` | แยกกลุ่มรีจิสทรี |
| ALEAPP/iLEAPP/mac_apt/การเข้าใจถึงปัญหาหลังเหตุการณ์/FQLite | ดำเนินการโดย `-h` | แยกวิเคราะห์ Android/iOS/macOS/Chrome/SQLite |
| ewf-tools/libesedb/pff-tools | `ewfexport img.E01`; `esedbexport -t out ntds.dit`; `pffexport mail.pst` | E01 / ESE (NTDS) / PST |
| qemu-img | `qemu-img convert -O raw d.qcow2 d.raw` | เปลี่ยนรูปแบบดิสก์ก่อนแยกวิเคราะห์ |
| คนแคระ2json | `dwarf2json linux --elf vmlinux --systemmap map > json` | สัญลักษณ์สร้างตัวเอง เล่ม 3 |
| การชันสูตรศพ / เครื่องมือ EZ / HxD / เบราว์เซอร์ DB / DBeaver / Zui | กุย | เรียกดูหลักฐานภาพ |
| gitleaks | `gitleaks detect --source repo/` | สแกนความลับใน git repo |
| ยารา | `yara -r rule.yar dir/` | รูปแบบการจับคู่ |

## รายการตรวจสอบ 5 นาทีแรกของเซสชันการทดสอบ crypto

1. `sage --version` — หากเกิดข้อผิดพลาด อย่าลืมใช้ PARI/GP + การโจมตีแบบเข้ารหัสแทน
2. `uv venv && uv pip install pycryptodome gmpy2 sympy pwntools` (สภาพแวดล้อมที่สะอาด)
3. ตรวจสอบ `ls /opt/tools/crypto-attacks/attacks/` + `gp --version`
4. Factor N ตามสเกล: factordb-python → **Fermat self-write** (N สมดุล) → RsaCtfTool / PARI/GP / Sage
5. RsaCtfTool บน Windows/WSL เท่านั้น — เดาการวิเคราะห์พฤติกรรม RSA ได้อย่างถูกต้องและรันที่นั่น
