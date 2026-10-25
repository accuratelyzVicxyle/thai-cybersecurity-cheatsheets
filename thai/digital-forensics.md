# Digital Forensics Cheatsheet

> ทำงานบนสำเนา เก็บ hash และบันทึกทุกขั้นตอน ห้ามแก้ต้นฉบับถ้าเป็นหลักฐานจริง

## 1. Intake และ chain of custody

จดอย่างน้อย:

- ผู้ส่ง/ผู้รับหลักฐาน
- วันเวลาและ timezone
- แหล่งที่มาและวิธี acquisition
- ขนาดไฟล์/device
- SHA-256 ก่อนเริ่มวิเคราะห์
- เครื่องมือและ version

```bash
stat evidence.img
sha256sum evidence.img | tee evidence.img.sha256
date -u +'%Y-%m-%dT%H:%M:%SZ'
```

สร้าง working copy:

```bash
cp --reflink=auto --preserve=all evidence.img work.img
sha256sum evidence.img work.img
```

ถ้าเป็น block device ให้ใช้ write blocker เมื่อเป็นไปได้ และ acquire แบบ read-only:

```bash
sudo dd if=/dev/sdX of=evidence.img bs=4M conv=noerror,sync status=progress
```

## 2. File triage

```bash
file sample
stat sample
sha256sum sample
xxd -l 256 sample
strings -a -n 6 sample | less
strings -a -el sample | less      # UTF-16LE
```

ค้นหา embedded signature:

```bash
binwalk sample
binwalk -eM sample
```

ใช้ extraction บน working directory เพราะเครื่องมืออาจสร้างไฟล์จำนวนมาก

## 3. Magic bytes ที่พบบ่อย

| Format | Signature |
|---|---|
| PNG | `89 50 4e 47 0d 0a 1a 0a` |
| JPEG | `ff d8 ff` |
| PDF | `%PDF-` |
| ZIP/DOCX/XLSX/APK/JAR | `50 4b 03 04` |
| ELF | `7f 45 4c 46` |
| PE | `4d 5a` (`MZ`) |
| gzip | `1f 8b` |
| 7z | `37 7a bc af 27 1c` |

Extension ไม่ใช่หลักฐานของชนิดไฟล์ ให้ดู signature และ parser หลายตัว

## 4. Metadata

```bash
exiftool -G1 -a -s sample
pdfinfo document.pdf
identify -verbose image.png
ffprobe -hide_banner media.mp4
```

เวลาใน metadata อาจเป็น local time, UTC หรือไม่มี timezone ต้องบันทึก assumption

ลบ metadata ใช้เฉพาะสำเนา:

```bash
exiftool -all= -o sanitized.jpg original.jpg
```

## 5. Archive และ Office documents

List ก่อน extract:

```bash
7z l archive.zip
unzip -l archive.zip
tar -tvf archive.tar
```

Extract ใน sandbox:

```bash
mkdir extracted
7z x archive.zip -oextracted
```

Office Open XML เป็น ZIP:

```bash
unzip -l document.docx
unzip document.docx -d docx-unpacked
rg -n -i 'http|relationship|macro|external|hidden' docx-unpacked
```

Macro triage:

```bash
olevba suspicious.docm
oleid suspicious.docm
```

อย่าเปิดไฟล์ต้องสงสัยใน Office ปกติ ใช้ isolated VM และปิด network ถ้าไม่จำเป็น

## 6. Disk image

ดู partition:

```bash
mmls evidence.img
fdisk -l evidence.img
```

Mount read-only ด้วย offset จาก sector start:

```bash
offset=$((START_SECTOR * 512))
sudo mount -o ro,noload,loop,offset="$offset" evidence.img /mnt/evidence
```

The Sleuth Kit:

```bash
fsstat -o START_SECTOR evidence.img
fls -r -p -o START_SECTOR evidence.img > bodyfile-list.txt
icat -o START_SECTOR evidence.img INODE > recovered.bin
```

สร้าง timeline:

```bash
fls -r -m / -o START_SECTOR evidence.img > bodyfile
mactime -b bodyfile -d > timeline.csv
```

ระวัง MACB time:

- M: modified content
- A: accessed
- C: metadata/status changed
- B: birth/creation เมื่อ filesystem รองรับ

## 7. Deleted files และ carving

```bash
fls -rd -o START_SECTOR evidence.img
photorec evidence.img
foremost -i evidence.img -o carved
```

Carving ไม่มี filename/path เดิมและอาจได้ fragment/false positive ให้ยืนยันด้วย parser และ context

## 8. Memory forensics

เก็บ hash ก่อน:

```bash
sha256sum memory.raw
```

Volatility 3:

```bash
python3 vol.py -f memory.raw windows.info
python3 vol.py -f memory.raw windows.pslist
python3 vol.py -f memory.raw windows.pstree
python3 vol.py -f memory.raw windows.netscan
python3 vol.py -f memory.raw windows.cmdline
python3 vol.py -f memory.raw windows.filescan
```

Linux plugin และ symbol ต้องตรง kernel:

```bash
python3 vol.py -f memory.raw linux.pslist
python3 vol.py -f memory.raw linux.pstree
```

แนวคิด correlation:

- process tree + command line
- parent/child ที่ผิดปกติ
- network connection + owning PID
- loaded module/DLL
- injected/executable memory
- open files/handles
- timestamp เทียบ log/disk/PCAP

## 9. PCAP triage

```bash
capinfos capture.pcap
tshark -r capture.pcap -q -z io,phs
tshark -r capture.pcap -q -z conv,tcp
tshark -r capture.pcap -q -z endpoints,ip
```

ค้นหา DNS และ HTTP:

```bash
tshark -r capture.pcap -Y dns -T fields \
  -e frame.time_epoch -e ip.src -e dns.qry.name | sort -u

tshark -r capture.pcap -Y http.request -T fields \
  -e frame.number -e ip.src -e http.request.method -e http.host -e http.request.uri
```

Export object:

```bash
mkdir http-objects
tshark -r capture.pcap --export-objects http,http-objects
```

Wireshark filters:

```text
dns.qry.name contains "example"
http.request
tls.handshake.extensions_server_name
tcp.stream eq 7
tcp.analysis.retransmission
frame contains "flag"
```

Encrypted TLS payload อ่านไม่ได้หากไม่มี session key; metadata เช่น SNI, certificate, IP, timing ยังใช้ได้

## 10. Logs และ timeline

Linux:

```bash
journalctl --utc --since '2026-01-01 00:00:00'
last -F
lastb -F 2>/dev/null
rg -n 'sudo|session opened|Accepted|Failed password' /var/log 2>/dev/null
```

Windows artifacts ที่พบบ่อย:

- Event Logs (`.evtx`)
- Registry hives
- Prefetch
- Amcache/Shimcache
- SRUM
- LNK/Jump Lists
- browser history/downloads
- PowerShell history/logging

Normalize ทุก timestamp เป็น timezone เดียว แต่เก็บค่าต้นฉบับด้วย

## 11. Image / steganography triage

```bash
file image.png
exiftool image.png
pngcheck -v image.png
zsteg -a image.png
strings -a image.png | less
binwalk image.png
```

JPEG:

```bash
steghide info image.jpg
```

ตรวจด้วยสายตา:

- dimension/สี/alpha channel
- appended data หลัง end marker
- palette หรือ LSB pattern
- QR/barcode
- contrast/levels/channel แยก

อย่าเริ่ม brute force password ก่อนตรวจ metadata, hint และ wordlist context

## 12. YARA starter

```yara
rule Suspicious_Marker
{
    meta:
        author = "analyst"
        purpose = "triage"
    strings:
        $a = "vxmp-test-marker" ascii wide nocase
        $mz = { 4D 5A }
    condition:
        $mz at 0 and $a
}
```

```bash
yara -r rules.yar samples/
```

Rule ที่ดีต้องทดสอบทั้ง malicious และ clean corpus และลด string ที่กว้างเกินไป

## 13. Report structure

1. Executive summary
2. Scope และ evidence inventory
3. Method/tool versions
4. Timeline (พร้อม timezone)
5. Findings และ supporting artifacts
6. Hash/path ของ extracted files
7. Limitations และ alternative explanations
8. Indicators of compromise
9. Recommendations

แยก **fact**, **interpretation** และ **hypothesis** ให้ชัด

## 14. Final checklist

- [ ] original evidence ไม่ถูกแก้
- [ ] hash ตรงก่อน/หลัง acquisition
- [ ] ทุกเวลา normalize และระบุ timezone
- [ ] artifact สำคัญย้อนกลับไปหา source ได้
- [ ] tool output ถูกยืนยันด้วยหลักฐานอื่นเมื่อทำได้
- [ ] secret/personal data ถูก redact ก่อนแชร์
- [ ] conclusion ไม่เกินสิ่งที่หลักฐานพิสูจน์

## อ้างอิง

- [The Sleuth Kit documentation](https://www.sleuthkit.org/sleuthkit/docs/)
- [Volatility 3 documentation](https://volatility3.readthedocs.io/)
- [Wireshark User's Guide](https://www.wireshark.org/docs/wsug_html_chunked/)
- [ExifTool documentation](https://exiftool.org/)
- [YARA documentation](https://yara.readthedocs.io/)
