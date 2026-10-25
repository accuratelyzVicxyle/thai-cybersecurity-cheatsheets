# Web Security Testing Cheatsheet

> ทดสอบเฉพาะ application, lab หรือ scope ที่ได้รับอนุญาต หลีกเลี่ยงการยิงคำขอจำนวนมากจนกระทบบริการ

## 1. เริ่มจาก scope และ baseline

จดข้อมูลก่อนทดสอบ:

- domain/subdomain/IP ที่อยู่ใน scope
- account และ role ที่ได้รับ
- endpoint ที่ห้ามทดสอบ
- rate limit และช่วงเวลาที่อนุญาต
- วิธีติดต่อเมื่อเกิดผลกระทบ

เก็บ baseline request:

```bash
curl -skD headers.txt -o body.html https://example.test/
curl -skI https://example.test/
curl -sk --http2 -v https://example.test/ -o /dev/null
```

ดู DNS และ certificate:

```bash
dig +short A example.test
dig +short AAAA example.test
dig +short CNAME example.test
openssl s_client -connect example.test:443 -servername example.test </dev/null
```

## 2. ทำแผนที่ application

สำรวจโดยไม่ brute force ก่อน:

- link, form, JavaScript bundle
- `robots.txt`, `sitemap.xml`, `.well-known/`
- API schema เช่น OpenAPI/Swagger/GraphQL
- cookie, local storage, session storage
- request ที่ browser ส่งตอน login/logout/password reset

```bash
curl -sk https://example.test/robots.txt
curl -sk https://example.test/sitemap.xml
curl -sk https://example.test/.well-known/security.txt
```

ค้นหา path ใน JavaScript:

```bash
rg -o 'https?://[^"'"' ]+|/[A-Za-z0-9_./?=&-]+' app.js | sort -u
```

Fuzz เฉพาะเมื่อได้รับอนุญาต:

```bash
ffuf -u https://example.test/FUZZ \
  -w /path/to/wordlist.txt \
  -mc all -fc 404 -rate 20
```

## 3. HTTP ที่ต้องอ่านให้เป็น

| ส่วน | คำถาม |
|---|---|
| Method | server แยก `GET/POST/PUT/PATCH/DELETE` ถูกหรือไม่ |
| Path | normalize `//`, `..`, encoded path อย่างไร |
| Query/body | validation อยู่ฝั่ง server หรือแค่ client |
| Header | proxy เชื่อ `Host`, `X-Forwarded-*` หรือไม่ |
| Cookie | มี `Secure`, `HttpOnly`, `SameSite` หรือไม่ |
| Status | error ต่างกันจนใช้ enumerate user/object ได้หรือไม่ |
| Cache | response ส่วนตัวถูก cache หรือไม่ |

ส่ง JSON:

```bash
curl -sk https://example.test/api/items \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer TOKEN' \
  --data '{"name":"test"}'
```

## 4. Authentication และ session

ตรวจ:

- username enumeration จากข้อความ/status/time
- rate limit และ lockout
- session เปลี่ยนหลัง login หรือ privilege change หรือไม่
- logout invalidate session จริงหรือไม่
- password reset token ผูกกับ user, expire และใช้ครั้งเดียวหรือไม่
- MFA bypass ผ่าน endpoint เก่าหรือ recovery flow หรือไม่
- cookie scope กว้างเกินไปหรือไม่

JWT triage:

```bash
TOKEN='HEADER.PAYLOAD.SIGNATURE' python3 - <<'PY'
import base64, json, os
token = os.environ["TOKEN"]
for part in token.split('.')[:2]:
    part += '=' * (-len(part) % 4)
    print(json.dumps(json.loads(base64.urlsafe_b64decode(part)), indent=2))
PY
```

อย่าสรุปว่า JWT ปลอดภัยเพียงเพราะ signature ถูกต้อง ต้องตรวจ `alg`, key selection, `iss`, `aud`, `exp`, `nbf` และ authorization หลัง decode ด้วย

## 5. Authorization / IDOR

สร้าง matrix ของ role กับ action:

| Endpoint | anonymous | user A | user B | admin |
|---|---:|---:|---:|---:|
| `GET /api/profile/{id}` | ✗ | own | other? | ✓ |
| `PATCH /api/order/{id}` | ✗ | own | other? | ✓ |

ทดสอบทั้ง:

- เปลี่ยน object ID
- เปลี่ยน HTTP method
- เรียก API โดยไม่ผ่าน UI
- nested object เช่น `/org/1/user/2`
- bulk endpoint และ export/download
- field ที่ client ซ่อนไว้ เช่น `role`, `owner_id`, `is_admin`

## 6. Injection quick checks

ใช้ marker ที่มองเห็นง่ายและไม่ทำลายข้อมูล:

```text
vxmp-test-7f31
' " ` ) ] }
```

### SQL injection

สัญญาณ: quote ทำให้ error/response/time เปลี่ยนอย่างสม่ำเสมอ

- แยก input ตาม context: string, number, identifier, ORDER BY
- เปรียบเทียบ true/false request ที่ต่างกันจุดเดียว
- หลีกเลี่ยง query ที่แก้ไข/ลบข้อมูล
- ยืนยันด้วยข้อมูลขั้นต่ำใน lab

### Command injection

ตรวจว่า input ถูกส่งเข้า shell หรือโปรแกรมด้วย argument ที่ปลอดภัยหรือไม่ ใช้ harmless command ใน lab และยืนยันจาก marker ที่คาดเดาได้

### SSTI

เริ่มจาก expression คณิตศาสตร์ที่ไม่ทำ side effect แล้วระบุ template engine ก่อนทำขั้นต่อไป

```text
{{7*7}}
${7*7}
<%= 7*7 %>
```

### XSS

ระบุ context ก่อนเสมอ: HTML text, attribute, URL, JavaScript string หรือ DOM sink

```html
<b>vxmp-test-7f31</b>
```

เริ่มด้วย markup ที่ไม่รัน script เพื่อดู encoding จากนั้นค่อยใช้ PoC ที่ปลอดภัยใน lab

## 7. Path traversal และ file handling

ตรวจ:

- path ถูก canonicalize ก่อนตรวจ allowlist หรือไม่
- encoded separator/dot ถูก decode กี่รอบ
- archive extraction ป้องกัน Zip Slip หรือไม่
- filename จาก upload/download ถูกเชื่อโดยตรงหรือไม่
- symlink ทำให้หลุด directory หรือไม่

สำหรับ upload ให้ดูครบ:

- extension, MIME, magic bytes
- server เปลี่ยนชื่อไฟล์หรือไม่
- เก็บนอก web root หรือไม่
- image/document ถูก re-encode หรือไม่
- download บังคับ `Content-Disposition` หรือไม่

## 8. SSRF

หา feature ที่ server ไป fetch URL เช่น webhook, avatar import, PDF preview และ URL unfurl

ตรวจ controls:

- allowlist scheme/host/port
- redirect ถูกตรวจซ้ำหรือไม่
- DNS rebinding/IPv6/alternate IP notation
- private/link-local/loopback ถูก block หลัง resolve หรือไม่
- response body/error/time เปิดเผยข้อมูลมากแค่ไหน

ใช้ callback server ที่คุณควบคุมและไม่ยิง metadata/internal address นอก lab

## 9. CSRF และ CORS

CSRF:

- action เปลี่ยน state ใช้ token ที่คาดเดาไม่ได้หรือไม่
- token ผูกกับ session/action หรือไม่
- `SameSite` เหมาะสมหรือไม่
- server ยอมรับ state change ผ่าน `GET` หรือไม่

CORS:

```bash
curl -skI https://example.test/api/me \
  -H 'Origin: https://attacker.invalid'
```

ระวัง origin reflection, `null`, wildcard ร่วมกับ credential และ validation แบบ suffix ที่หลอกได้

## 10. Security headers

```bash
curl -skI https://example.test/
```

ตรวจอย่างน้อย:

- `Content-Security-Policy`
- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy`
- `Permissions-Policy`
- frame protection ผ่าน CSP `frame-ancestors`
- cache policy ของข้อมูลส่วนตัว

Header ที่มีอยู่แต่ policy อ่อน/ผิดก็ยังไม่ช่วย ต้องอ่านค่าจริง

## 11. Evidence ที่ดี

แต่ละ finding ควรมี:

1. title และ severity พร้อมเหตุผล
2. affected endpoint/version
3. precondition และ role
4. request/response ขั้นต่ำที่ reproduce ได้
5. impact ที่พิสูจน์แล้ว ไม่ขยายเกินหลักฐาน
6. remediation ที่แก้ root cause
7. retest result

เก็บ raw request โดยลบ token/password ก่อนแชร์:

```bash
curl -sk --trace-ascii trace.txt https://example.test/
```

## 12. Final checklist

- [ ] endpoint และ role สำคัญถูก map
- [ ] authorization ทดสอบแบบ horizontal และ vertical
- [ ] session lifecycle ครบ login → change privilege → logout
- [ ] input ถูกตรวจตาม context
- [ ] upload/download/export ถูกทดสอบ
- [ ] error, cache, CORS และ security headers ถูกตรวจ
- [ ] PoC ไม่ทำลายข้อมูลและอยู่ใน scope

## อ้างอิง

- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)
- [curl documentation](https://curl.se/docs/)
