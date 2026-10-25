# ชุด Cheatsheet Cybersecurity ภาษาไทย

เอกสารอ้างอิงแบบลงมือทำสำหรับ CTF, lab และงาน security testing ที่ได้รับอนุญาต ประกอบด้วยฉบับแปลจากชุด Crypto เดิมและ cheatsheet ภาษาไทยที่เขียนเพิ่มสำหรับสายอื่น

## Offensive Security และ Incident Response

1. [Pwn / Binary Exploitation](pwn-binary-exploitation.md)
2. [Web Security Testing](web-security-testing.md)
3. [Linux Privilege Escalation](linux-privilege-escalation.md)
4. [Network Enumeration](network-enumeration.md)
5. [Digital Forensics](digital-forensics.md)

## Cryptography

1. [แผนผังจำแนกโจทย์ RSA](<RSA - Sơ đồ nhận diện dạng bài.md>)
2. [แผนผังจำแนกโจทย์ Symmetric Cipher](<Symmetric Cipher - Sơ đồ nhận diện dạng bài.md>)
3. [RSA และการเข้ารหัสแบบอสมมาตร](cheatsheet-asymmetric.md)
4. [Symmetric Cipher](cheatsheet-symmetric.md)
5. [OpenSSL](cheatsheet-openssl.md)
6. [Casebook: encoding, classical, forensics, stego และ RE](cheatsheet-casebook.md)
7. [กล่องเครื่องมือ Crypto](tools.md)
8. [Crypto cheatsheet ฉบับพื้นฐาน](<Cheatsheet Crypto.md>)
9. [ไลบรารีที่ใช้กับ CryptoHack](<Cryptohack Libs cần dùng.md>)

## วิธีใช้ชุดนี้

- เริ่มจาก workflow และ checklist ของแต่ละไฟล์ แล้วค่อยเลือกคำสั่งตามหลักฐานจริง
- คำสั่ง, API, สมการ, filename และชื่อเทคนิคคงรูปเดิมเพื่อให้ค้นและคัดลอกได้
- อย่า hardcode version หรือ offset จาก cheatsheet ให้ยืนยันกับ target/environment ทุกครั้ง
- เก็บ command, raw output, hash, timestamp และ assumption เพื่อให้ทำซ้ำได้
- ทดสอบเฉพาะระบบที่คุณเป็นเจ้าของหรือได้รับอนุญาตอย่างชัดเจน

แผนผัง Mermaid จะแสดงอัตโนมัติบน GitHub และ Markdown viewer ที่รองรับ Mermaid
