# Crypto Cheatsheet ภาษาไทย

รวมไลบรารีเมื่อฝึก CryptoHack: `Cryptohack Libs cần dùng.md`

# บทที่ 1

## จำนวนเฉพาะ, การแยกตัวประกอบเฉพาะ, ฟิลด์จำกัด

โดยปกติ: ใน mod m นั้น a จะมีค่าผกผันใน Z/mZ ก็ต่อเมื่อ gcd(a,m)=1

อย่างไรก็ตาม ถ้า m เป็นจำนวนเฉพาะ เราก็จะได้ว่าสมาชิกที่ไม่ใช่ศูนย์ทุกตัวใน Z/mZ จะมีค่าผกผัน

เมื่อทำโจทย์เกี่ยวกับจำนวนเฉพาะ ให้ตรวจดูว่าเป็นเศษซากกำลังสองหรือมีคุณสมบัติพิเศษใดๆ หรือไม่

#  เลขคณิตแบบโมดูลาร์

GCD แบบขยาย:

```python
def egcd(a, b):
    x,y, u,v = 0,1, 1,0
    while a != 0:
        q, r = b//a, b%a
        m, n = x-u*q, y-v*q
        b,a, x,y, u,v = a,r, u,v, m,n
    gcd = b
    return gcd, x, y

print(egcd(26513, 32321))
```

# โมดูลาร์ผกผัน

ปราชญ์

```python
a = 3
m = 11

kq = inverse_mod(a, m)
print(kq)  # ผลลัพธ์: 4 (เพราะ 3 * 4 = 12 ≡ 1 mod 11)
```

หรือ:

```python
a = 3
m = 11

# ใช้ Zmod
kq1 = Zmod(m)(a)^-1

# หรือใช้ฟังก์ชัน mod()
kq2 = mod(a, m)^-1
```

# กำลังสองส่วนเกิน

```python
p = 29
ints = [14,6,11]

for x in ints:
    if Mod(x, p).is_square():
        print(x)
        print(Mod(x, p).sqrt(), p - Mod(x, p).sqrt())
        
# คุณยังสามารถใช้สัญลักษณ์ Legendre (สัญลักษณ์ Kronecker)
# ส่งคืนค่า 1 (ใช่), -1 (ไม่ใช่) หรือ 0 (x หารด้วย p ลงตัว)
leg = kronecker(x, p) 
print(f"Ký hiệu Legendre: {leg}")
```

เรซิดิวกำลังสอง * เรซิดิวกำลังสอง = เรซิดิวกำลังสอง

สารตกค้างกำลังสอง * กำลังสองไม่มีสารตกค้าง = กำลังสองไม่มีสารตกค้าง

สมการกำลังสองไม่มีสารตกค้าง * สมการกำลังสองไม่มีสารตกค้าง = สมการกำลังสองไม่มีสารตกค้าง

# Oวัตถุ Mod()

```python
a = Mod(6, 29) # เอาท์พุต: obj
b = Mod(31, 29)
print(1 / a) # ถ้าไม่เช่นนั้น จะส่งคืน ZeroDivisionError: ไม่มีค่าผกผันของ Mod(x, p)
print(b) # ส่งคืน 2
```

# CRT

```python
# รายการยอดคงเหลือ (a_i)
rem = [2, 3, 2]

# รายการโมดูโล (m_i)
mod = [3, 5, 7]

# คำนวณราก x บวกที่น้อยที่สุด
x = crt(rem, mod) # ค้นหา Sage Integer -> แถบตรวจสอบ int(x)

print(f"Nghiệm của hệ là: {x}")
```

# กุญแจสาธารณะ

```python
import hashlib
```

```bash
pip install git+https://github.com/elliptic-shiho/primefac-fork@master
```

รูตที่ # N

```python
ct = <int>
print(long_to_bytes(ct.nth_root(3)))
```

# รากดั้งเดิม

ระดับของโมดูโล n คือ d นาที โดยที่ $a^d \equiv 1$ mod n

รากดั้งเดิม g คือตัวเลขที่สามารถแทนค่าสนามจำกัด p (p: ไพรม์) ในรูปแบบ: $g^1,g^2,...,g^{p-1}$

ดังนั้นระดับของ g จะต้องเป็น p - 1

สูตรคำนวณดีกรีของ g ตาม p - 1:

$$
ord(g)=\frac{p-1}{gcd(k,p-1)}
$$

```python
# ประกาศจำนวนเฉพาะ p
p = 17

# 1. ค้นหารากดั้งเดิมตัวแรก
g = primitive_root(p)

# 2. สร้างรายการรากดั้งเดิมทั้งหมด
# โดยการคำนวณ g^k mod p สำหรับ k coprimes ด้วย p-1
all_roots = [power_mod(g, k, p) for k in range(1, p) if gcd(k, p - 1) == 1]
```

# DLP

$$
เป้าหมาย base^x =
$$

```python
discrete_log(target, base) # บีเอสจีเอส

Alice_pub = E(public_x, public_y) # โปห์ลิก / BSGS

# ฟังก์ชัน .log() ของ SageMath จะใช้ Pohlig-Hellman/BSGS โดยอัตโนมัติ
n = Alice_pub.log(G) # G: เครื่องกำเนิดไฟฟ้า
```

# เอลลิปติก

```python
p = 97 # ประกาศจำนวนเฉพาะ
F = GF(p) # เริ่มต้นฟิลด์จำกัด F_97
    
# เส้นโค้ง y^2 = x^3 + 2x + 3 บนโมดูโล 97
E_finite = EllipticCurve(F, [2, 3])
    
# นับจำนวนคะแนนทั้งหมด (Order) บนเส้นโค้งตามทฤษฎีบทของ Hasse
print("จำนวนจุดบนเส้นโค้ง:", E_finite.cardinality())
    
# สร้างจุดสุ่ม
G = E_finite.random_point()
print("จุดสุ่ม G:", G)
    
# การคูณสเกลาร์ - แกนหลักของ ECC
k = 15
print("15 * G =", k * G)
# ชี้ไปที่ ECC
P = E_finite(100, 100)
```

ประกาศแต่ละ G.x เพื่อค้นหาจุด y:

```python
G.lift_x(<x>)

```

# มอนต์โกเมอรี่

```python
# เส้นโค้งมอนโกเมอรี: By^2 = x^3 + Ax^2 + x
p = 2 ** 255 - 19
A, B = 486662, 1
# [1, a2, a3, a4, a6] สอดคล้องกับ y^2 + a1xy + a3y = x^3 + a2x^2 + a4x + a6 ถ้า B = 1
E = EllipticCurve(GF(p), [0, A, 0, 1, 0])
G = E.lift_x(9)
k = bin(0x1337c0decafe)[2:] # คลาส 'sage.rings.integer.Integer'>

def add(P, Q):
    x1, y1 = P.xy()
    x2, y2 = Q.xy()
    alpha = (y2 - y1) / (x2 - x1)
    x3 = alpha ** 2 - A - x1 - x2
    y3 = alpha * (x1 - x3) - y1
    return E(x3, y3)
def doubling(P):
    x1, y1 = P.xy()
    alpha = (3 * x1 ** 2 + 2 * A * x1 + 1) / (2 * y1)
    x3 = alpha ** 2 - A - 2 * x1
    y3 = alpha * (x1 - x3) - y1
    return E(x3, y3)

def algo(P, k): # คิว = kP
    R0, R1 = P, doubling(P)
    for i in k[1:]:
        if i == '0':
            R0, R1 = doubling(R0), add(R0, R1)
        else: R0, R1 = add(R0, R1), doubling(R1)
    return R0

print(algo(G, k).xy())

```
