# Linux Privilege Escalation Cheatsheet

> สำหรับ CTF/lab และระบบที่ได้รับอนุญาตเท่านั้น เริ่มจากการอ่าน configuration ก่อนรัน exploit เสมอ

## 1. เก็บ context ทันที

```bash
id
whoami
groups
hostname
uname -a
cat /etc/os-release
pwd
echo "$PATH"
env | sort
```

ข้อมูล session:

```bash
w
last -n 20
ps auxf
pstree -ap
```

## 2. Checklist หลัก

ตรวจตามลำดับที่ noise ต่ำก่อน:

1. `sudo -l`
2. group membership และ writable file
3. SUID/SGID
4. Linux capabilities
5. cron/systemd timer/service
6. credential/config/backup
7. socket/service ที่ฟังเฉพาะ localhost
8. container และ mount
9. kernel exploit เป็นทางท้าย ไม่ใช่ทางแรก

## 3. Sudo

```bash
sudo -l
sudo -V | head
cat /etc/sudoers 2>/dev/null
find /etc/sudoers.d -maxdepth 1 -type f -readable -print -exec sed -n '1,160p' {} \; 2>/dev/null
```

อ่าน rule ให้ครบ:

- run เป็น user ใด (`root`, user อื่น)
- ต้องใช้ password หรือ `NOPASSWD`
- command/path/argument ถูก fix หรือใช้ wildcard
- environment ถูก preserve เช่น `LD_PRELOAD`, `PYTHONPATH`
- binary สามารถเปิด editor, shell, plugin, pager หรือโหลด config ได้หรือไม่

อ้าง behavior ของ binary จาก manual และ [GTFOBins](https://gtfobins.github.io/) แต่ยืนยันกับ version จริง

## 4. SUID / SGID

```bash
find / -xdev -type f -perm -4000 -ls 2>/dev/null
find / -xdev -type f -perm -2000 -ls 2>/dev/null
```

สำหรับไฟล์แปลก:

```bash
file /path/to/bin
stat /path/to/bin
strings -a /path/to/bin | less
ldd /path/to/bin
readelf -dW /path/to/bin
```

ตรวจ logic:

- เรียก program อื่นด้วย relative path หรือไม่
- ใช้ `system()`/shell หรือไม่
- เชื่อ environment variable หรือ config ที่เราเขียนได้หรือไม่
- เปิดไฟล์ก่อน/หลังเปลี่ยน UID อย่างไร
- drop privilege ครบทุก UID (`ruid/euid/suid`) หรือไม่
- มี race ระหว่าง check กับ use หรือไม่

## 5. Linux capabilities

```bash
getcap -r / 2>/dev/null
capsh --print 2>/dev/null
grep -E 'Cap(Inh|Prm|Eff|Bnd|Amb)' /proc/self/status
```

Capability ที่ควรสนใจ:

| Capability | ความเสี่ยงที่ต้องตรวจ |
|---|---|
| `cap_setuid` | process เปลี่ยน UID ได้ |
| `cap_dac_override` | ข้าม file permission checks หลายชนิด |
| `cap_sys_admin` | scope กว้างมาก; mount/namespace และอื่น ๆ |
| `cap_sys_ptrace` | inspect/inject process ที่อนุญาต |
| `cap_net_raw` | raw packet/socket |
| `cap_chown` | เปลี่ยน owner ของไฟล์ |

Capability อาจถูกจำกัดด้วย bounding set, namespace, seccomp และ LSM จึงต้องทดสอบจริง

## 6. Writable paths และ PATH hijacking

```bash
find / -xdev -type d -writable -print 2>/dev/null
find / -xdev -type f -writable -print 2>/dev/null
namei -l /path/to/interesting/file
```

ตรวจ PATH ทีละ directory:

```bash
printf '%s\n' "$PATH" | tr ':' '\n' | while read -r d; do ls -ld "$d"; done
```

PATH hijack เกิดได้เมื่อ privileged process เรียกชื่อ command โดยไม่ใช้ absolute path และค้นเจอไฟล์ของ attacker ก่อน

## 7. Cron และ systemd

Cron:

```bash
cat /etc/crontab
ls -la /etc/cron.d /etc/cron.daily /var/spool/cron 2>/dev/null
systemctl list-timers --all
```

Systemd:

```bash
systemctl list-units --type=service --state=running
systemctl list-unit-files --type=service
systemctl cat suspicious.service
systemctl show suspicious.service -p User -p Group -p ExecStart -p EnvironmentFiles
```

ตรวจ permission ของ:

- unit file
- `ExecStart` binary/script
- working directory
- environment/config file
- logrotate rule
- file ที่ service อ่าน/เขียนด้วย privilege สูง

## 8. Process, socket และ service ภายใน

```bash
ps auxww
ss -lntup
ss -lxap
lsof -nP -i 2>/dev/null
ls -l /proc/*/exe 2>/dev/null | head
```

หา service ที่ bind แค่ loopback แล้วตรวจ version/config:

```bash
curl -i http://127.0.0.1:PORT/
```

ตรวจ Unix socket permission โดยเฉพาะ Docker, containerd, database และ custom daemon

```bash
find /run /var/run -type s -ls 2>/dev/null
ls -l /var/run/docker.sock 2>/dev/null
```

สมาชิก group `docker` หรือการเขียน Docker socket มักเทียบเท่า root บน host

## 9. Credentials และ secrets

เริ่มจาก path ที่เกี่ยวข้องกับ application ไม่ใช่ค้นทั้ง disk แบบไร้ขอบเขต:

```bash
find /opt /srv /var/www -maxdepth 4 -type f \
  \( -name '*.env' -o -name '*.conf' -o -name '*.ini' -o -name '*.yml' -o -name '*.bak' \) \
  -readable -print 2>/dev/null

rg -n -i 'pass(word)?|secret|token|api[_-]?key|private[_-]?key' \
  /opt /srv /var/www 2>/dev/null
```

ตรวจ:

- shell history
- deployment scripts
- backup/archive
- SSH keys และ agent
- database config
- cloud/container credential
- reused password ระหว่าง service account

อย่าแสดง secret ใน report/chat มากกว่าที่จำเป็น ให้ redact แต่เก็บหลักฐานที่ยืนยันได้

## 10. NFS และ mount

```bash
mount
findmnt
cat /etc/fstab
df -hT
```

NFS:

```bash
cat /etc/exports 2>/dev/null
showmount -e SERVER
```

ตรวจ `no_root_squash`, writable export, mount option เช่น `nosuid/nodev/noexec` และ owner mapping

## 11. Container triage

```bash
cat /proc/1/cgroup
cat /proc/self/mountinfo | head
test -f /.dockerenv && echo docker
grep -E 'docker|kubepods|containerd' /proc/1/cgroup
```

ตรวจ:

- privileged container
- host filesystem mount
- Docker/container runtime socket
- excessive capabilities
- host PID/network namespace
- service-account token และ RBAC ใน Kubernetes

การออกจาก container ต้องถือเป็นคนละ trust boundary และต้องอยู่ใน scope

## 12. Kernel และ version

```bash
uname -a
cat /proc/version
sysctl kernel.unprivileged_userns_clone 2>/dev/null
sysctl kernel.kptr_restrict 2>/dev/null
dmesg 2>/dev/null | tail
```

อย่าเลือก exploit จาก string version อย่างเดียว:

- distro อาจ backport patch โดยไม่เปลี่ยน major version
- ตรวจ package release และ changelog
- ยืนยัน config, architecture และ mitigation
- ทดลองใน snapshot/lab ก่อน
- kernel exploit อาจ crash เครื่องหรือทำข้อมูลเสียหาย

## 13. Script enumeration

เครื่องมือเช่น LinPEAS ช่วยลดเวลา แต่ output ไม่ใช่ข้อพิสูจน์:

- อ่าน script ก่อนรัน
- ตรวจ hash/source
- รู้ว่า script เขียนไฟล์หรือยิง network หรือไม่
- ยืนยัน finding ด้วย command แบบ manual
- ลบ artifact เมื่อจบตามกติกา engagement

## 14. Evidence checklist

- [ ] current user/group/host/kernel ถูกบันทึก
- [ ] `sudo -l`, SUID, SGID, capabilities ถูกตรวจ
- [ ] writable path ถูก trace ถึง privileged consumer
- [ ] cron/timer/service permission ถูกตรวจครบ chain
- [ ] secret ถูก redact
- [ ] escalation path ทำซ้ำได้และระบุ precondition
- [ ] cleanup และ impact ถูกบันทึก

## อ้างอิง

- [Linux capabilities manual](https://man7.org/linux/man-pages/man7/capabilities.7.html)
- [sudo manual](https://www.sudo.ws/docs/man/)
- [systemd manual](https://www.freedesktop.org/software/systemd/man/)
- [GTFOBins](https://gtfobins.github.io/)
