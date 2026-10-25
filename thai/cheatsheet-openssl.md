#  เอกสารสรุป OpenSSL (เต็ม)

> ทดสอบบน OpenSSL 3.6.3 (WSL) สภาพแวดล้อม WSL: `wsl -e bash -lc "..."`
> `openssl version -a` — ดูเวอร์ชัน + OPENSSLDIR (อยู่ที่ openssl.cnf, CA Bundle cert.pem)
>  คำสั่งใด ๆ ที่ลืมตัวเลือก: `openssl <cmd> -help` รายการคำสั่งย่อย: `openssl list` / `openssl help`
> 3.x: อัลกอริธึม "legacy" (DES, RC2, RC4, seed,ปักเป้า...) ถูกซ่อนอยู่ → เพิ่ม `-provider legacy -provider default` ต่อท้ายคำสั่ง

## 0. ไวยากรณ์ทั่วไป + รหัสผ่าน

- อินพุต/เอาต์พุต: `-in f` `-out f` (ไม่ใช่ `-in` = อ่าน stdin); รูปแบบ `-inform PEM|DER` `-outform PEM|DER` (PEM เริ่มต้น)
- `-noout` = ไม่พิมพ์อ็อบเจ็กต์ไปยัง stdout (ยังคงพิมพ์ `-text` หากมีอยู่)
- รหัสผ่าน: `-passin` (อ่านไฟล์/รหัสผ่านอินพุต), `-passout` (ตั้งค่าสำหรับเอาต์พุต), `-pass` (enc ใช้ทั้งสองอย่าง) แหล่งที่มาของรหัสผ่าน:
  ```bash
  -passin pass:matkhau        # โดยตรง (รั่วไหลเข้าสู่ประวัติศาสตร์ได้ง่าย)
  -passin env:MYVAR           # ตัวแปรสภาพแวดล้อม
  -passin file:f.txt          # บรรทัดแรกของไฟล์ (รวมถึง \n หากไม่ใช่แถบ!)
  -passin fd:0  /  -passin stdin   # มาตรฐาน (enc)
  ```
- หมายเหตุ `-passout pass:x` เมื่อสร้างคีย์: x คือรหัสผ่านสำหรับเข้ารหัสไฟล์คีย์

## 1. การระบุไฟล์ — ตารางส่วนหัว PEM

ไฟล์ PEM ข้อความ =: `-----BEGIN X-----` + base64 + `-----END X-----` ส่วนหัวกำหนดประเภทของวัตถุ:

| ส่วนหัว BEGIN | มันคืออะไร |
|---|---|
| `CERTIFICATE` | ใบรับรอง X.509 (DER ห่ออยู่ในฐาน 64) |
| `TRUSTED CERTIFICATE` | ใบรับรองพร้อมแฟล็กความน่าเชื่อถือ (openssl x509 -trustout) |
| `CERTIFICATE REQUEST` / `NEW CERTIFICATE REQUEST` | CSR PKCS#10 |
| `PRIVATE KEY` | PKCS#8 ไม่มีการเข้ารหัส |
| `ENCRYPTED PRIVATE KEY` | PKCS#8 พร้อมการเข้ารหัส (ASN.1 ไม่มี Proc-Type) |
| `RSA PRIVATE KEY` | PKCS#1 RSAPrivateKey (รูปแบบดั้งเดิม; ค่าเริ่มต้น 3.x genrsa ได้ถูกเปลี่ยนเป็น PKCS#8!) |
| `RSA PUBLIC KEY` | PKCS#1 RSAPublicKey |
| `PUBLIC KEY` | SPKI SubjectPublicKeyInfo (สามารถแทรกอะไรก็ได้โดย RSA/EC/DSA) |
| `EC PRIVATE KEY` | SEC1 ECPrivateKey (ecparam -genkey / openssl ec เอาต์พุตประเภทนี้) |
| `DSA PRIVATE KEY` / `DSA PARAMETERS` | DSA สไตล์ SEC1 |
| `EC PARAMETERS` | พารามิเตอร์เส้นโค้ง (ปกติเพียง 1 บรรทัด OID) |
| `DH PARAMETERS` / `X9.42 DH PARAMETERS` | พารามิเตอร์ Diffie-Hellman |
| `PKCS7` / `PKCS #7 SIGNED DATA` | PKCS#7 (.p7b): สตริงใบรับรอง, ไม่มีคีย์ |
| `X509 CRL` | รายการเพิกถอนใบรับรอง |
| `ENCRYPTED DATA` | CMS EnvelopedData รูปแบบ PEM (`cms -encrypt -a`) |
| `SSH2 PUBLIC KEY` | RFC 4716 (ssh-keygen -e) |
| `OPENSSH PRIVATE KEY` | รูปแบบใหม่ ssh-keygen (bcrypt KDF) — **openssl ไม่สามารถอ่านได้** |
| `SSH2 ENCRYPTED PRIVATE KEY` | รูปแบบ ssh.com |
| `SSL SESSION PARAMETERS` | แคชเซสชัน |

คีย์ PEM แบบดั้งเดิมพร้อมการเข้ารหัสมี 2 บรรทัดส่วนหัวใน base64:
```
-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: AES-256-CBC,<IV ฐานสิบหกที่ไม่มีเครื่องหมาย :>
```

ตารางนามสกุลไฟล์ (นามสกุลไม่ได้กำหนดเนื้อหา `file`/`head -1` เป็นมาตรฐาน):

| หาง | โดยปกติ |
|---|---|
| `.pem` | text base64, 1 ไฟล์สามารถมีวัตถุได้มากมาย (โดยปกติแล้ว openssl จะอ่านเฉพาะวัตถุ FIRST) |
| `.der` `.crt` `.cer` | Binary DER (Windows มักใช้ .cer สำหรับ DER) |
| `.key` | รหัสส่วนตัว (PEM หรือ DER) |
| `.csr` | คำขอ PKCS#10 |
| `.p12` `.pfx` | PKCS#12 (ใบรับรอง + คีย์ + เชน พร้อมรหัสผ่าน) |
| `.p7b` `.p7c` | PKCS#7 ใบรับรองเท่านั้น |
| `.crl` | ซีอาร์แอล |
| `.pub` | รหัสสาธารณะ (PEM/SPKI หรือ OpenSSH 1 บรรทัด) |
| `.jks` `.keystore` | ที่เก็บคีย์ Java — openssl ไม่อ่าน `keytool -list -keystore f.jks` (มายากล FE ED FE ED; MAGIC = JAVA-PKCS12) |
| `.pvk` | Windows PVK — openssl ไม่อ่านโดยตรง (เครื่องมือ pvk2pfx / openssl 1.0.2) |
| `.sst` | ร้านค้าใบรับรองอนุกรม MS (`certutil`) |

ความแตกต่างอย่างรวดเร็ว:
```bash
file f; head -c 32 f | xxd
# PEM : ASCII "-----เริ่มต้น"
# DER : 30 82 xx xx (ASN.1 SEQUENCE ความยาวแบบยาว) — ทุกคีย์/ใบรับรอง/p12 เริ่มต้นที่ 30
# p12 : 30 82 และ "ข้อมูลที่เข้ารหัส PKCS7" เมื่อ asn1parse; ลอง pkcs12 -info ทันที
# enc : "Salted__" = 53 61 6c 74 65 64 5f 5f จากนั้นเกลือ 8 ไบต์
```

## 2. asn1parse — สแกนไฟล์ key/cert/p7 ทั้งหมด (หมายเลขดีบัก 1)

```bash
openssl asn1parse -in f.pem                     # พีอีเอ็ม; เพิ่ม -inform der ถ้าเป็นไบนารี่
openssl asn1parse -in f -i                      # -i เยื้องเส้นตามความลึก
openssl asn1parse -in f -i -dump                # -dump พิมพ์ไบต์ดิบของแต่ละฟิลด์
openssl asn1parse -in f -i -strparse <offset>   # ขุดเข้าไปในวัตถุลูกที่ออฟเซ็ต (ออฟเซ็ตคอลัมน์ 1)
openssl asn1parse -in f -i -offset N -length M  # พื้นที่ดูพืชผล
```
อ่านเอาต์พุต: `offset:d=depth hl=header-len l=length cons|prim: TYPE :value`
- `INTEGER :0398...` หมายเลข = (อนุกรม/โมดูลัส...), `OCTET STRING [HEX DUMP]` = ดิบ, `OBJECT :sha256WithRSAEncryption` = OID
- PEM เสีย (ชื่อ "สูญหาย 1 บิต"): ถอดรหัส base64 ด้วย python จากนั้น `asn1parse -inform der` ค้นหาแท็กข้อผิดพลาด ("แท็กผิด")

## 3. คีย์ — สร้าง/ดู/แปลง

```bash
# --- การเกิด ---
openssl genrsa -out k.pem 2048                       # 3.x: ปล่อย PKCS#8 (เริ่มต้นคีย์ส่วนตัว)
openssl genrsa -out k.pem -aes256 -passout pass:x 2048   # ด้วยการเข้ารหัส -3 = e=3, ค่าเริ่มต้น -f4 (65537)
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 \
        -pkeyopt rsa_keygen_pubexp:65537 -out k.pem       # สไตล์โมเดิร์น ออก PKCS#8 ด้วย
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out ec.pem
openssl ecparam -name prime256v1 -genkey -out ec.pem      # ออก SEC1 (เริ่มต้นคีย์ส่วนตัวของ EC)
openssl ecparam -list_curves | grep -i prime
openssl dhparam -out dh.pem 2048                     # ช้า; dhparam เก่ามักมีอยู่ในปัญหา
openssl prime -generate -bits 64 -safe               # การสร้างเลขเฉพาะ (ปลอดภัยคือ -ปลอดภัย)

# --- ดู (พิมพ์ n,e,d,p,q,dp,dq,qinv — คัดลอกไปที่ python โดยตรง) ---
openssl rsa -in k.pem -text -noout                   # คีย์ส่วนตัว: (2048 บิต 2 ไพรม์) โมดูลัส: xx:xx:xx...
openssl rsa -in k.pem -noout -modulus                # Modulus=D6DD... (CAPS, ไม่มี ':', อาจนำหน้า 00)
openssl rsa -in k.pem -check -noout                  # "คีย์ RSA โอเค"
openssl rsa -pubin -in pub.pem -text -noout          # รหัสสาธารณะ SPKI: รหัสสาธารณะ: (บิต) + โมดูลัส + เลขชี้กำลัง
openssl pkey -in k.pem -text -noout                  # โดยทั่วไป RSA/EC/DSA ใช้ได้ (แนะนำ 3.x)
openssl pkey -in k.pem -text_pub -noout              # ส่วนสาธารณะเท่านั้น
openssl ec -in ec.pem -text -noout                   # EC: ASN1 OID: prime256v1, ผับ, ส่วนตัว
openssl rsa -in k.pem -noout -text | grep -A2 prime1 # พี คิว

# --- แปลง (ตารางล่าง) ---
openssl rsa -in k.pem -pubout -out spki.pem          # ส่วนตัว → เริ่มต้นคีย์สาธารณะ (SPKI)
openssl rsa -in k.pem -RSAPublicKey_out -out p1.pub  # ส่วนตัว → เริ่มต้นคีย์สาธารณะ RSA (PKCS#1)
openssl rsa -pubin -in spki.pem -RSAPublicKey_out -out p1.pub   # SPKI → ผับ PKCS#1
openssl rsa -in p1.pub -RSAPublicKey_in -pubin -out spki.pem    # PKCS#1 ผับ → SPKI
openssl pkcs8 -topk8 -in k1.pem -nocrypt -out k8.pem # PKCS#1/SEC1 → PKCS#8 (-passout สำหรับการเข้ารหัส)
openssl rsa -in k8.pem -out k1.pem                   # PKCS#8 → PKCS#1 แบบเดิม
openssl pkey -in k.pem -aes256 -passout pass:x -out ken.pem     # ตั้งค่า/เปลี่ยนรหัสผ่าน
```

| จาก → ถึง | ส่วนหัวของปลายทาง | คำสั่ง |
|---|---|---|
| PKCS#1 ส่วนตัว → PKCS#8 | `PRIVATE KEY` | `pkcs8 -topk8 -nocrypt` (หรือคำสั่งใดๆ `rsa/pkey -out`) |
| PKCS#8 → PKCS#1 ส่วนตัว | `RSA PRIVATE KEY` | `openssl rsa -in k8.pem -out k1.pem` |
| priv → ผับ SPKI | `PUBLIC KEY` | `rsa -pubout` / `pkey -pubout` |
| SPKI ↔ PKCS#1 ผับ | `RSA PUBLIC KEY` | `-RSAPublicKey_out` / `-RSAPublicKey_in` |
| ผับ OpenSSH → PEM | `PUBLIC KEY` | `ssh-keygen -f id_rsa.pub -e -m PKCS8` |
| OpenSSH priv (OPENSSH) → PEM | `RSA PRIVATE KEY` | `ssh-keygen -p -m PEM -f id_rsa` (เปลี่ยนรูปแบบแทน) |

หมายเหตุ:
- 3.x: `genrsa` มีค่าเริ่มต้นเป็น **PKCS#8** (`BEGIN PRIVATE KEY`) — 1.1.1 และต่ำกว่าเอาต์พุต `BEGIN RSA PRIVATE KEY` openssl ทั้งสองสามารถอ่านได้โดย `rsa` และ `pkey` อย่าตัดสินจากส่วนหัว
- `rsa` อ่านทั้ง PKCS#8 และ PKCS#1; คั่นด้วยส่วนหัวเมื่อต้องถอดรหัสด้วยตนเองใน python (PKCS#8 มี SEQUENCE เวอร์ชัน 0 เพิ่มเติม + AlgorithmIdentifier ที่ด้านนอก)
- Input RSA ขนาดเล็ก/ตำราเรียน (m < n) pkeyutl ไม่สามารถใช้งานได้ (รายการที่ 8) — การถอดรหัสแบบแมนนวล: base64 → ASN.1 → n,e

## 4. x509 — ใบรับรอง

```bash
openssl x509 -in c.pem -text -noout                  # ดูทั้งหมด: อนุกรม, ผู้ออก, หัวเรื่อง, ความถูกต้อง, SAN, OID sig
openssl x509 -in c.pem -noout -subject -issuer -serial -dates -fingerprint -sha256
openssl x509 -in c.pem -noout -ext subjectAltName    # 1.1.0+: ระบุส่วนขยาย (ชื่อ x509_extensions)
openssl x509 -in c.pem -noout -purpose               # สามารถตรวจสอบการใช้งานได้หรือไม่?
openssl x509 -in c.pem -pubkey -noout > pub.pem      # แยกรหัสสาธารณะออกจากใบรับรอง (ทั่วไปมาก)
openssl x509 -in c.pem -noout -modulus               # Modulus=... (RSA เท่านั้น) — ปุ่มเปรียบเทียบ
openssl x509 -in c.pem -outform der -out c.der       # PEM → DER
openssl x509 -inform der -in c.cer -outform pem      # เดอร์ → พีอีเอ็ม
openssl x509 -in c.pem -checkend 86400               # กำลังจะหมดเขตใน 24 ชม. เหรอ?
openssl x509 -in c.pem -noout -subject -nameopt RFC2253   # รูปแบบวิชามาตรฐาน
openssl verify -CAfile ca.pem -untrusted intermediate.pem leaf.pem   # ตรวจสอบสตริง
# รับใบรับรองจากเซิร์ฟเวอร์ที่ทำงานอยู่:
openssl s_client -connect host:443 -showcerts </dev/null 2>/dev/null > full.txt
awk '/BEGIN CERT/,/END CERT/' full.txt > chain.pem   # แยกโซ่ทั้งหมด (วัตถุแรกใบไม้ =)
```
- Match cert ↔ key (ใบรับรองเป็นของคีย์นี้หรือไม่): เปรียบเทียบ `-modulus` ของ `x509` กับ `rsa` - หรือกะทัดรัดกว่า:
  ```bash
  openssl x509 -in c.pem -pubkey -noout | openssl md5
  openssl pkey -in k.pem -pubout | openssl md5        # แฮชที่เท่ากันสองรายการ = ตรงกัน
  ```
- แยกสตริงใบรับรองในไฟล์ PEM ที่มีหลายใบรับรอง: `openssl crl2pkcs7 -nocrl -certfile chain.pem | openssl pkcs7 -print_certs -out certs.pem`
- CTF ทั่วไป: n ของหัวข้อโมดูลัส = ในใบรับรอง (ทำงานร่วมกับใบรับรองสาธารณะ); แยก `pubkey` จากนั้นกด n,e ลงใน python หรือโมดูลัสตรวจพบคีย์/ใบรับรองที่ไม่ตรงกัน

## 5. ความต้องการ — CSR (PKCS#10)

```bash
# สร้างคีย์ + CSR หนึ่งครั้ง (-nodes = DO NOT encrypt key — "No DES"):
openssl req -new -newkey rsa:2048 -nodes -keyout k.pem -out r.csr -subj "/C=VN/O=x/CN=y"
openssl req -new -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout k.pem -out r.csr -subj "/CN=y"
# ใบรับรองที่ลงนามด้วยตนเอง (CTF หรือต้องการใบรับรองท้องถิ่น):
openssl req -x509 -newkey rsa:2048 -nodes -keyout k.pem -out c.pem -days 365 \
        -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
openssl req -in r.csr -noout -text                   # ดู CSR (หัวเรื่อง + pubkey)
openssl req -in r.csr -noout -verify                 # ตรวจสอบลายเซ็น CSR
openssl req -in r.csr -pubkey -noout                 # แยก pubkey ออกจาก CSR
```

## 6. pkcs12/pkcs7/crl

```bash
openssl pkcs12 -in f.p12 -nodes -passin pass:x -out all.pem   # ดัมพ์ไปที่ PEM: คีย์ + ใบรับรอง + เชน
openssl pkcs12 -in f.p12 -passin pass:x -nocerts -nodes -out key.pem   # ที่สำคัญเท่านั้น
openssl pkcs12 -in f.p12 -passin pass:x -nokeys -clcerts -out cert.pem # ใบรับรองผู้ใช้เท่านั้น (-cacerts = CA)
openssl pkcs12 -info -in f.p12 -passin pass:x                  # ดูโครงสร้าง (MAC, PBES2, อัลกอริธึม)
openssl pkcs12 -legacy -in old.p12 -nodes -passin pass:x ...   # p12 สร้างโดย openssl ≤1.1.1 (RC2/3DES)
openssl pkcs12 -export -in c.pem -inkey k.pem -out f.p12 -name alias -certfile chain.pem -passout pass:x
openssl pkcs7 -in p7.pem -print_certs -out certs.pem           # .p7b → ใบรับรองแยก
openssl pkcs7 -in p7.pem -text -noout                          # ดู PKCS#7
openssl crl -in crl.pem -text -noout                           # ดูซีอาร์แอล
openssl crl -inform der -in f.crl -out crl.pem                 # เดอร์ → พีอีเอ็ม
```
- 3.x เปลี่ยนค่าเริ่มต้น pkcs12: PBES2/PBKDF2/AES-256-CBC + MAC sha256 ไฟล์ p12 เก่าเปิดขึ้นโดยมีข้อผิดพลาด 3.x แต่มีข้อผิดพลาด "ไม่รองรับ" → เพิ่ม `-legacy`; ในทางตรงกันข้าม p12 ที่สร้างด้วย 3.x และเปิดด้วยเครื่องมือเก่าอาจล้มเหลว
รหัสผ่านที่ไม่รู้จัก - p12: ลองรหัสผ่านที่ว่างเปล่า `-passin pass:`; หรือ `pkcs12 -info -nokeys -nocerts` บางครั้งต้องการเพียง MAC pass เท่านั้น

## 7. enc - การเข้ารหัสแบบสมมาตร

```bash
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 10000 -in f -out f.enc -pass pass:x
openssl enc -aes-256-cbc -d -in f.enc -out f -pass pass:x          # -d ถอดรหัส =
openssl enc -aes-256-cbc -d -K <HEX key> -iv <HEX iv> -in f.enc -out f   # คีย์ดิบไม่มี KDF
openssl enc -aes-128-ecb -K <HEX> -in ...                          # ECB ไม่ต้องการ -iv
echo -n data | openssl enc -aes-256-cbc -K ... -iv ... -a          # -= ฐาน 64 เข้า/ออก
openssl list -cipher-algorithms                                    # รายการ (3.x; 1.x: openssl enc -ciphers)
```
- `-K`/`-iv` (HOA) = raw hex: คีย์ AES-256 = อักขระฐานสิบหก 64 ตัว, iv = อักขระฐานสิบหก 32 ตัว `-k` (ปกติ) รหัสผ่าน = เปิดใช้งาน KDF + Salt (ไวยากรณ์ที่เลิกใช้แล้ว ยังคงใช้งานได้)
- โครงสร้างไฟล์เอาต์พุตที่มีเกลือ: `"Salted__"` (8 ไบต์ ASCII) + เกลือ (8 ไบต์) + ไซเฟอร์เท็กซ์ หากไม่มีไฟล์ธรรมดา = ขนาด 16 ไบต์เหล่านี้ (เข้ารหัสด้วย -K/-iv หรือ -nosalt หรือเครื่องมืออื่นๆ) — **อย่าใช้ `enc -d` เพื่อถอดรหัส** ต้องเป็นไฟล์ดิบ
- **"ถอดรหัสไม่ถูกต้อง" → แก้ไขคีย์/โหมดผิด KDF.** คำสั่งให้ลองใช้เมื่อใช้ไฟล์ด้วยรหัสผ่าน `Salted__` + โดยไม่ระบุเวอร์ชัน:
  1. `enc -d ... -pass pass:x` (EVP_BytesToKey, SHA-256 — ค่าเริ่มต้น openssl ≥ 1.1.0)
  2. add `-md md5` (ไฟล์ที่สร้างโดย openssl < 1.1.0 — ทั่วไปมากใน CTF)
  3.  เพิ่ม `-pbkdf2` (+ `-iter N` หากกล่าวถึง)
  4. `-nosalt` ไม่มี `Salted__`
- Padding เริ่มต้น PKCS#7; `-nopad` ถ้ามันบอกว่ามีช่องว่างภายใน
- `-a` นับ base64: เมื่อถอดรหัส `-a` จะรับเฉพาะอินพุต base64 เท่านั้น

## 8. dgst — แฮช / HMAC / ลายเซ็นดิจิทัล

```bash
openssl dgst -sha256 f                       # พิมพ์ "SHA2-256(f)= ฐานสิบหก…” ; -md5/-sha1/-sha512/-sha3-256...
openssl dgst -sha256 -binary f | xxd         # -binary raw แทน -hex (ฐานสิบหกเริ่มต้น)
openssl dgst -sha256 -hmac "key" f           # สตริงคีย์ HMAC; เลขฐานสิบหก HMAC: ใช้ `openssl mac`
openssl mac -digest SHA256 -macopt hexkey:0011.. HMAC -in f   # 3.x
openssl dgst -sha256 -sign k.pem -out sig.bin f        # เครื่องหมาย RSA/EC (แฮช + DigestInfo จากนั้น RSA)
openssl dgst -sha256 -verify pub.pem -signature sig.bin f   # → "ยืนยันแล้วตกลง" / "ยืนยันล้มเหลว"
openssl dgst -sha256 -prverify k.pem -signature sig.bin f   # ตรวจสอบด้วยรหัสส่วนตัว
```
-  อื่น ๆ `pkeyutl -sign`: dgst แฮชตัวเอง + wrap DigestInfo; `pkeyutl -sign` (การเติม pkcs1 เริ่มต้น) ลงนามข้อมูลดิบ — ด้วย RSA คุณต้องเตรียม DigestInfo ด้วยตัวเอง และ `-raw`/`none` เป็นหนังสือเรียน m^d mod n
- Verify หนังสือเรียน RSA (หัวข้อสำหรับ sig ขนาดเล็ก): ถอดรหัส sig = sig^e mod n กับ python จากนั้นเปรียบเทียบช่องว่างภายใน openssl `pkeyutl -verify` ต้องการ DigestInfo ที่ถูกต้อง ดังนั้นจึงมักจะได้รับ "ความล้มเหลวในการตรวจสอบลายเซ็น" แม้ว่า sig จะถูกต้อง - ถอดรหัสด้วยตนเองเมื่อมีข้อสงสัย

## 9. pkeyutl / rsautl - การดำเนินการ RSA/EC

```bash
openssl pkeyutl -encrypt -inkey spki.pem -pubin -in m.bin -out c.bin    # ค่าเริ่มต้น PKCS#1 v1.5
openssl pkeyutl -decrypt -inkey k.pem -in c.bin -out m.bin
openssl pkeyutl -encrypt -inkey pub.pem -pubin -pkeyopt rsa_padding_mode:oaep \
        -pkeyopt rsa_oaep_md:sha256 -pkeyopt rsa_mgf1_md:sha256 -in m.bin
openssl pkeyutl -sign -inkey k.pem -in f -out sig -pkeyopt rsa_padding_mode:pss \
        -pkeyopt rsa_pss_saltlen:-1                                     # ปล
openssl pkeyutl -verify -inkey pub.pem -pubin -sigfile sig -in f
openssl pkeyutl -derive -inkey k.pem -peerkey pub.pem -out shared.bin   # ECDH/DH: แบ่งปันความลับ
```
โหมด - Padding: `pkcs1` (การเข้ารหัส/ถอดรหัสเริ่มต้น + เครื่องหมาย), `oaep` (เข้ารหัส/ถอดรหัสเท่านั้น), `pss` (ลงชื่อเข้าใช้เท่านั้น), หนังสือเรียน `none` (=)
- **Big gotcha: หนังสือเรียน RSA ที่มี m เล็กไม่สามารถทำได้ด้วย pkeyutl `-raw`/`rsa_padding_mode:none`** — เข้ารหัสอินพุตที่เล็กกว่าโมดูลัส → `RSA_padding_add_none:data too small for key size`; ถอดรหัสผลลัพธ์ด้วยศูนย์นำหน้าและ "ข้อมูลเล็กเกินไป" หัวข้อหนังสือเรียน RSA (n,e,c) → **ใช้ python `pow(c,d,n)`** openssl เพื่อแยกพารามิเตอร์เท่านั้น
- `openssl rsautl` = นามแฝง pkeyutl เก่า (เลิกใช้แล้ว แต่ยังคงใช้งานได้) รวมถึง `-raw` แบบคลาสสิก
- E เอาต์พุตการเข้ารหัสจะยาวเท่ากับโมดูลัสเสมอ (มีช่องว่างเพียงพอ); หากไฟล์ไซเฟอร์เท็กซ์มีความยาว 128/256 ไบต์พอดี = RSA 1024/2048 บิต CT สั้นกว่า = โดยไม่มีช่องว่างภายในตำราเรียน =
- Decrypt PKCS#1 v1.5: ข้อความธรรมดาเริ่มต้น `00 02 <nonzero random> 00 <msg>` - ตัดหลังจากไบต์แรก 0x00 (เห็น gotcha: ข้อความไบนารี่ที่มีการตัด 0x00 ด้วยตรรกะการเติม ไม่ใช่ rstrip)

## 10. passwd/rand/prime/odd

```bash
openssl passwd -6 -salt saithay matkhau      # $6$saithay$... crypt(3) SHA-512 (ลินุกซ์เงา)
openssl passwd -1 matkhau                    # $1$ MD5 ฝังศพใต้ถุนโบสถ์; -5 SHA-256; -apr1 อาปาเช่ MD5
openssl passwd -salt xyz -6 -verify hash ... # เปรียบเทียบรหัสผ่านกับแฮชที่มีอยู่ (คัดลอกเกลือจากแฮช)
openssl rand -hex 32                         # 32 ไบต์ → 64 ตัวอักษรฐานสิบหก; -ฐาน64 32
openssl prime 104729                         # อินพุตคือ DECIMAL → "19919 (104729) เป็นจำนวนเฉพาะ" (hex)(dec)
openssl prime -hex 1F                        # -hex: อินพุตและเอาต์พุตมีทั้งเลขฐานสิบหก
openssl prime -checks 20 104729              # เพิ่มจำนวนรอบมิลเลอร์-ราบิน
```
-  หมายเหตุเฉพาะ: NO `-hex` จากนั้นป้อนทศนิยม เอาต์พุตจะอยู่ในรูปแบบ `<hex> (<số vừa nhập>)` เสมอ ป้อนสตริงเลขฐานสิบหกประเภท `1C` โดยไม่มี -hex → **silent, exit 0, no error** (3.6.3) — การคิดว่าเป็นจำนวนเฉพาะ เป็นไปได้ก็ผิด
เกณฑ์มาตรฐาน - `openssl speed rsa2048`; `openssl storeutl certs.pem` แสดงรายการออบเจ็กต์ทั้งหมดในไฟล์ PEM (x509 อ่านเฉพาะอันแรกเท่านั้น)

## 11. s_client / s_server — TLS

```bash
openssl s_client -connect host:443 -servername host          # SNI;Enter จากนั้นพิมพ์ HTTP ด้วยตนเอง
openssl s_client -connect host:443 -brief                    # เอาต์พุตขนาดกะทัดรัด: เวอร์ชัน, การเข้ารหัส, ใบรับรอง DN
openssl s_client -connect host:443 -showcerts                # พิมพ์ใบรับรองทั้งหมดที่ส่งโดยเซิร์ฟเวอร์ (รับลูกโซ่)
openssl s_client -connect host:25 -starttls smtp             # smtp/pop3/imap/ftp/http(post)/xmpp/mysql/postgres...
openssl s_client -connect host:443 -tls1_2 -cipher ECDHE-RSA-AES128-GCM-SHA256   # กดเวอร์ชัน/รหัส
openssl s_client -connect host:443 -crlf -quiet              # -crlf เปลี่ยน LF → CRLF (HTTP / SMTP ด้วยตนเอง), -quiet + -ign_eof เก็บเซสชัน
openssl s_client -connect host:443 -CAfile ca.pem            # ตรวจสอบผ่าน CA ที่กำหนด -verify_return_error
openssl s_server -accept 4433 -cert c.pem -key k.pem -www    # การทดสอบเซิร์ฟเวอร์ (หน้า GET / คืนสถานะ)
```
- CTF: บริการ HTTPS/STARTTLS → s_client เป็นเทอร์มินัลแบบโต้ตอบ รวม `| openssl x509 -text -noout` เพื่ออ่านใบรับรองทันที ใบรับรองในรูปแบบ DER เปลือย (พอร์ตที่กำหนดเองส่งคืน 0x30 0x82) → `openssl x509 -inform der -text -noout -in <(nc host port)`

## 12. cms / smime — S/MIME

```bash
openssl cms -encrypt -in msg.txt -recip cert.pem -aes256 -to a@b -from c@d -subject hi -out msg.cms
openssl cms -decrypt -in msg.cms -recip cert.pem -inkey k.pem -out msg.txt
openssl cms -sign -in msg.txt -signer cert.pem -inkey k.pem -out msg.sig
openssl cms -verify -in msg.sig -CAfile ca.pem -out msg.txt
openssl cms -encrypt -in msg.txt -recip cert.pem -aes256 -outform DER -out msg.der   # ไบนารี่
# smime = cms เวอร์ชันเก่า ไวยากรณ์เกือบจะเหมือนกัน CMS ในรูปแบบ PEM: cms -encrypt ... -outform PEM
```

## 13. ตารางข้อผิดพลาดทั่วไป

| ผิดพลาด | สาเหตุ + การรักษา |
|---|---|
| `no start line` / `Could not find private key` | อ่าน DER ด้วย PEM parser → เพิ่ม `-inform der`; หรือส่วนหัว PEM ผิด/ไม่อยู่ในบรรทัด หรือไฟล์เป็น p12 (`pkcs12 -in`) |
| `unable to load Private Key` | รหัสผ่านไม่ถูกต้อง (ไม่มี `-passin pass:`) หรือคีย์ผสมระหว่าง PKCS#8/RSA/EC |
| `bad decrypt` (enc) | คีย์/iv/โหมดผิด หรือ KDF ผิด → รายการที่ 7 (ลอง `-md md5`, `-pbkdf2`, `-nosalt`) |
| `wrong tag` (asn1parse) | ไบนารีเสียหาย/เสียหาย 1 บิต — ค้นหาออฟเซ็ตที่ผิดพลาด, brute flip |
| `data too small for key size` (ไม่มี pkeyutl) | หนังสือเรียน RSA m ขนาดเล็ก → แก้ด้วย python อย่าใช้ openssl |
| `unsupported` (3.x) | อัลกอริธึมดั้งเดิม → เพิ่ม `-provider legacy -provider default` |
| `unable to get local issuer certificate` | ตรวจสอบห่วงโซ่ที่ขาด → `-CAfile` / `-untrusted` |
| `Error reading password from BIO` | แหล่งรหัสผ่านหายไป หรือ `-passin file:f` มี `\n` ต่อท้าย → ใช้ `pass:` |
| `header too long` /เอาต์พุตขยะ | ถอดรหัสในรูปแบบที่ไม่ถูกต้อง (ไฟล์ `-d` ไม่ใช่เอาต์พุต enc) |
| p12 ไม่สามารถเปิด | รหัสผ่านผิด; หรือหายไป `-legacy` (p12 RC2/3DES เก่า) |

## 14. รายการตรวจสอบ 2 นาทีเมื่อพบไฟล์ crypto ในปัญหา

1. `file f && head -c 32 f | xxd` → ข้อความ PEM หรือไม่ เดอร์ `30 82`? `Salted__`? p12 (30 82 + ลอง `pkcs12 -info -passin pass:`)?
ปุ่ม 2. PEM → `openssl pkey -in f -text -noout` (n,e,d,p,q → หลาม); ใบรับรอง PEM → `openssl x509 -text -noout` รับ `-pubkey` เปรียบเทียบ `-modulus` ด้วยคีย์ (แสดงหรือซ่อนที่ไม่ตรงกัน)
3. Key บิตเล็กผิดปกติ (512–1024) → แยกตัวประกอบทันที (factordb/Fermat) ก่อนที่จะคิดอย่างลึกซึ้ง
4. File มี `Salted__` → `enc -d` ตาม 4 ขั้นตอน KDF ส่วนที่ 7
5. `.sig` RSA: ลอง `dgst -verify`; ล้มเหลว → ถอดรหัสตำราเรียนด้วย python (sig^e mod n, soi padding `00 01 FF..FF 00`)
6.  ไฟล์แปลก/ขยะ base64: `openssl asn1parse -inform der -i -dump` ซอย; PEM เสียหาย 1 บิต → หลามถอดรหัส + เดรัจฉานพลิกรอบข้อผิดพลาดชดเชย
7. Server HTTPS/STARTTLS → `s_client -connect -showcerts`, ห่วงโซ่การจับภาพ, แยกใบรับรองเพื่อรับ n
