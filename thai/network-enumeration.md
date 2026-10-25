# Network Enumeration Cheatsheet

> ใช้เฉพาะ network scope ที่ได้รับอนุญาต กำหนด rate และเวลาให้เหมาะกับระบบจริง

## 1. บันทึก scope

```text
CIDR / hosts:
Allowed protocols:
Excluded systems:
Maximum rate:
Testing window:
Contact / stop condition:
```

แปลง CIDR เป็นรายการ host สำหรับงาน lab:

```bash
nmap -sL -n 192.0.2.0/28
```

## 2. ข้อมูลเครื่องเรา

```bash
ip -br addr
ip route
ip neigh
resolvectl status 2>/dev/null
cat /etc/resolv.conf
ss -lntup
```

ตรวจเส้นทาง:

```bash
ping -c 3 TARGET
traceroute TARGET
tracepath TARGET
```

ICMP ถูก block ไม่ได้แปลว่า host down

## 3. Host discovery

บน LAN:

```bash
sudo arp-scan --localnet
sudo nmap -sn -PR 192.0.2.0/24
```

บน routed network:

```bash
sudo nmap -sn -PE -PS22,80,443 -PA80,443 192.0.2.0/24
```

ถ้ารู้ว่า host online แต่ discovery ถูก block:

```bash
nmap -Pn -n TARGET
```

## 4. Port scan แบบเป็นขั้น

เริ่มจาก TCP connect scan ที่ไม่ต้อง root:

```bash
nmap -sT -n -Pn --top-ports 1000 TARGET -oA scans/top1000
```

ถ้าได้รับอนุญาตให้ scan ทุก port:

```bash
nmap -sT -n -Pn -p- --min-rate 100 TARGET -oA scans/alltcp
```

ปรับ `--min-rate` ตามความเสถียรและข้อตกลง ไม่ใช้ rate สูงโดยอัตโนมัติ

ตรวจ service เฉพาะ port ที่เปิด:

```bash
nmap -sV -sC -n -Pn -p22,80,443 TARGET -oA scans/services
```

UDP ต้อง scan แยกและมักช้ากว่า:

```bash
sudo nmap -sU -n -Pn --top-ports 50 TARGET -oA scans/udp50
```

อ่าน state ให้ถูก:

| State | ความหมายโดยย่อ |
|---|---|
| open | มี service ตอบ |
| closed | host ตอบแต่ไม่มี service ฟัง |
| filtered | firewall/packet loss ทำให้สรุปไม่ได้ |
| open\|filtered | UDP ไม่มี response จึงแยกสองสถานะไม่ได้ |

## 5. Banner และ TLS

```bash
nc -nv TARGET PORT
curl -skI https://TARGET/
openssl s_client -connect TARGET:443 -servername example.test </dev/null
```

ดู certificate:

```bash
openssl s_client -connect TARGET:443 -servername example.test </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -serial -dates -ext subjectAltName
```

Banner อาจปลอม/ซ่อน version ให้ยืนยันจากหลายสัญญาณ

## 6. DNS

```bash
dig A example.test
dig AAAA example.test
dig MX example.test
dig TXT example.test
dig NS example.test
dig SOA example.test
dig +trace example.test
```

Reverse lookup:

```bash
dig -x 192.0.2.10
```

Zone transfer ทดสอบเฉพาะ authoritative server ใน scope:

```bash
dig AXFR example.test @ns1.example.test
```

## 7. HTTP / HTTPS

```bash
curl -skD- https://example.test/ -o /dev/null
curl -sk https://example.test/robots.txt
curl -sk https://example.test/.well-known/security.txt
```

ตรวจ virtual host เมื่อมีหลายชื่อบน IP เดียว:

```bash
curl -sk https://192.0.2.10/ -H 'Host: app.example.test'
```

บันทึก:

- title/status/redirect chain
- server/framework header
- certificate SAN
- cookie/security headers
- virtual hosts และ alternate ports

## 8. SMB

```bash
smbclient -L //TARGET -N
smbclient //TARGET/SHARE -N
nmap -n -Pn -p445 --script smb-protocols,smb2-security-mode TARGET
```

เมื่อมี credential:

```bash
smbclient -L //TARGET -U 'DOMAIN/user'
```

ตรวจ share permission แยก read/write และอย่า upload ไฟล์ทดสอบโดยไม่จำเป็น

## 9. SNMP

SNMP ใช้ UDP 161 เป็นหลัก:

```bash
snmpwalk -v2c -c COMMUNITY TARGET 1.3.6.1.2.1
snmpget  -v2c -c COMMUNITY TARGET 1.3.6.1.2.1.1.1.0
```

OID ที่มีประโยชน์:

| OID | ข้อมูล |
|---|---|
| `1.3.6.1.2.1.1` | system |
| `1.3.6.1.2.1.2` | interfaces |
| `1.3.6.1.2.1.4` | IP/network |
| `1.3.6.1.2.1.25` | host resources |

หลีกเลี่ยง brute force community string บน production ถ้าไม่ได้ตกลง rate ไว้

## 10. LDAP

```bash
ldapsearch -x -H ldap://TARGET -s base -b '' namingContexts
ldapsearch -x -H ldap://TARGET -b 'dc=example,dc=test' '(objectClass=*)' dn
```

เมื่อใช้ StartTLS:

```bash
ldapsearch -x -ZZ -H ldap://TARGET -b 'dc=example,dc=test' '(objectClass=*)' dn
```

ตรวจ anonymous bind, naming context, TLS และ access control โดยไม่ dump attribute ที่มี secret เกินจำเป็น

## 11. SMTP

```bash
nc -nv TARGET 25
```

บทสนทนาพื้นฐาน:

```text
EHLO audit.example
HELP
STARTTLS
QUIT
```

ตรวจ:

- banner และ supported extensions
- STARTTLS/certificate
- relay policy ด้วย mailbox ที่ได้รับอนุญาต
- user enumeration เฉพาะเมื่อ scope อนุญาต
- SPF, DKIM, DMARC ของ domain

```bash
dig TXT example.test
dig TXT _dmarc.example.test
```

## 12. Database quick identification

| Service | Port ทั่วไป | Client |
|---|---:|---|
| PostgreSQL | 5432 | `psql` |
| MySQL/MariaDB | 3306 | `mysql` |
| MSSQL | 1433 | `sqlcmd` |
| Redis | 6379 | `redis-cli` |
| MongoDB | 27017 | `mongosh` |

ตัวอย่างใช้ credential ที่ได้รับ:

```bash
psql 'host=TARGET port=5432 user=USER dbname=DB sslmode=require'
mysql -h TARGET -P 3306 -u USER -p
redis-cli -h TARGET -p 6379 --tls
```

อย่าใส่ password ใน command line เพราะอาจโผล่ใน shell history/process list

## 13. Packet capture

```bash
sudo tcpdump -ni any host TARGET
sudo tcpdump -ni eth0 -w capture.pcap 'host TARGET and (tcp or udp)'
tshark -r capture.pcap -q -z conv,tcp
```

Display filters ใน Wireshark:

```text
ip.addr == 192.0.2.10
tcp.port == 443
dns
http.request
tls.handshake.type == 1
tcp.analysis.retransmission
```

PCAP อาจมี credential/session/personal data ต้องเก็บและแชร์อย่างปลอดภัย

## 14. จัดผล scan

```bash
mkdir -p scans
nmap ... -oA scans/target-date
```

สำหรับทุก service จด:

| Host | Port/proto | Service | Version/evidence | TLS | Next check |
|---|---|---|---|---|---|

แยกสิ่งที่เครื่องมือ "เดา" ออกจากสิ่งที่ยืนยันจาก protocol response

## 15. Final checklist

- [ ] scope/rate/stop condition ชัดเจน
- [ ] host discovery ใช้หลาย signal
- [ ] TCP และ UDP ถูกแยก
- [ ] service scan ทำเฉพาะ port ที่เปิด
- [ ] DNS/TLS/virtual host ถูกตรวจ
- [ ] credential ไม่อยู่ใน command history/report
- [ ] raw output เก็บพร้อม timestamp และ command

## อ้างอิง

- [Nmap Reference Guide](https://nmap.org/book/man.html)
- [Wireshark User's Guide](https://www.wireshark.org/docs/wsug_html_chunked/)
- [OpenSSL documentation](https://docs.openssl.org/)
- [BIND 9 Administrator Reference Manual](https://bind9.readthedocs.io/)
