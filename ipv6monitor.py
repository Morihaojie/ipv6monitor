import os
import re
import requests
import socket
import subprocess
import time
import email
import smtplib
import logging
from email.header import Header
from email.mime.text import MIMEText
from html import unescape
from email.header import decode_header
import poplib

class IPv6_monitor():
    def __init__(self):
        LOG_FORMAT = "%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s"
        DATE_FORMAT = "%Y/%m/%d %H:%M:%S"
        logfilename = time.strftime("%Y-%m-%d %H-%M-%S",time.localtime())        
        logging.basicConfig(filename=logfilename+'.log', level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
        self.email_account = 'xxxx@xx.com'
        self.password = 'xxxxxxxxxx'
        self.pop3_server = 'pop.xx.com'
        self.smtp_server = 'smtp.xx.com'
        try:
            with open(os.path.join(os.path.abspath('./'),'ipv6cache.txt'),'r') as a:
                ipv6_addresses = a.readlines()
        except:            
            file = open(os.path.join(os.path.abspath('./'),'ipv6cache.txt','w'))
            file.close()

    def get_ipv6_address(self):
        ipv6_addresses = []
        addresses_info = socket.getaddrinfo(socket.gethostname(),None)
        for item in addresses_info:
            if ':' in item[4][0]:
                ipv6_addresses.append(item[4][0])
        ipv6_address = None
        for ip in ipv6_addresses:
            if ip.split(':')[0].find('240e') >= 0 or ip.split(':')[0].find('2400') >= 0 or ip.split(':')[0].find('2408') >= 0 or ip.split(':')[0].find('2001') >= 0:
                        ipv6_address = ip
                        break
        return ipv6_address

    def obtain_ipv6_address_from_email(self):
        # 连接到POP3服务器:
        server = poplib.POP3_SSL(self.pop3_server)
        # 可以打开或关闭调试信息:
        server.set_debuglevel(0)
        # 身份认证:
        server.user(self.email_account)
        server.pass_(self.password)

        resp, mails, octets = server.list()
        # 可以查看返回的列表类似[b'1 82923', b'2 2184', ...]
        email_titles=[]        

        for i in range(len(mails)):  
            message = b'\n'.join(server.retr(i+1)[1])
            mail = email.message_from_bytes(message)
            subject = mail.get("Subject")
            try:
                dh = decode_header(subject)
                if dh[0][1] == None:
                    email_titles.append(dh[0][0])
                else:
                    result = dh[0][0].decode(dh[0][1])
                    email_titles.append(result)
            except:
                email_titles.append(str(decode_header(subject)[0][0]))
                continue

        newest_index = len(email_titles)
        for j in range(len(email_titles)):
            if email_titles[j].find('获得的ipv6地址') >= 0 :
                newest_index = j + 1
        newest_message = b'\n'.join(server.retr(newest_index)[1])
        newest_mail = email.message_from_bytes(newest_message)
        server.quit()
        ipv6_pattern='(([a-f0-9]{1,4}:){0,7}[a-f0-9]{1,4})'
        m = re.search(ipv6_pattern, str(self.get_file(newest_mail)))
        try:
            if m is not None and len(m.group()) > 10:
                return m.group()
            else:
                ipv6_pattern='([a-f0-9:]*::[a-f0-9:]*)'
                m = re.search(ipv6_pattern, str(self.get_file(newest_mail)))
                return m.group()
        except:
            try:
                result = re.findall(r"(([a-f0-9]{1,4}:){7}[a-f0-9]{1,4})", str(self.get_file(newest_mail)), re.I)[0][0]
                return result
            except:
                print('出现错误')

    def get_file(self, msg):
        data_char=''
        for part in msg.walk():
            part_charset=part.get_content_charset()
            part_type=part.get_content_type()
            if part_type=="text/plain" or part_type=='text/html':
                data=part.get_payload(decode=True)
                try:
                    data=data.decode(part_charset,errors="replace")
                except:
                    data=data.decode('gb2312',errors="replace")
                data=self.html_to_plain_text(data)
                data_char=data_char+'\n'+data
        return data_char+'\n'

    def html_to_plain_text(self, html):
        text = re.sub('<head.*?>.*?</head>', ' ', html, flags=re.M | re.S | re.I)
        text = re.sub(r'<a\s.*?>', ' HYPERLINK ', text, flags=re.M | re.S | re.I)
        text = re.sub('<.*?>', ' ', text, flags=re.M | re.S)
        text = re.sub(r'(\s*\n)+', '\n', text, flags=re.M | re.S)
        return unescape(text)

    def send_ipv6_address_to_email(self,ipv6_address):
        msg = MIMEText(socket.gethostname()+'的IPV6地址为：'+ipv6_address, 'plain', 'utf-8')    
        server = smtplib.SMTP(self.smtp_server, 25) # SMTP协议默认端口是25        
        server.login(self.email_account, self.password)   # 登录SMTP服务器
        msg['From'] = self.email_account+' <'+self.email_account+'>'
        msg['Subject'] = Header(u'获得的ipv6地址', 'utf8').encode()
        msg['To'] = u'<'+self.email_account+'>'
        server.sendmail(self.email_account, [self.email_account], msg.as_string())    # 发邮件
        logging.info('IPV6地址:'+ipv6_address+'已发送')
        server.quit()

    def read_ipv6_address(self):        
        path = os.path.join(os.path.abspath('./'),'ipv6cache.txt')
        with open(path,'r') as a:
            ipv6_addresses = a.readlines()
        if ipv6_addresses[-1][-1] == '\n':
            ipv6_address = ipv6_addresses[-1][0:-1]
        elif ipv6_addresses[-1][-1] != '\n':
            ipv6_address = ipv6_addresses[-1]
        return ipv6_address

    def read_ipv6_address_from_host(self):        
        path = r'C:\Windows\System32\drivers\etc\hosts'
        ipv6_addresses = []
        with open(path,'r', encoding="utf-8") as a:
            hosts_strs = a.readlines()
            for hosts_str in hosts_strs:
                if hosts_str.find('www.xxxx.com') >= 0 :
                    ipv6_addresses.append(hosts_str)
        return ipv6_addresses[-1].split()[0]

    def write_ipv6_address(self,ipv6_address):
        path = os.path.join(os.path.abspath('./'),'ipv6cache.txt')
        with open(path,'r') as a:
            ipv6_addresses = a.readlines()
        if ipv6_addresses[-1] == ipv6_address or ipv6_addresses[-1] == ipv6_address+'\n':
            pass
        else:
            with open('ipv6cache.txt', 'a', encoding="utf-8") as file_object:
                if ipv6_addresses[-1][-1] != '\n':
                    file_object.write('\n'+ipv6_address)
                    logging.info('IPV6地址:'+ipv6_address+'已缓存')
                elif ipv6_addresses[-1][-1] == '\n':
                    file_object.write(ipv6_address+'\n')
                    logging.info('IPV6地址:'+ipv6_address+'已缓存')

    def synchronize_ipv6_address(self):
        if self.current_ipv6_address != self.stored_ipv6_address or self.current_ipv6_address.find(self.stored_ipv6_address) < 0:                
            self.write_ipv6_address(self.current_ipv6_address)
            self.stored_ipv6_address = self.read_ipv6_address()
            logging.info('已同步当前与缓存中存储的地址')
        if self.current_ipv6_address != self.email_ipv6_address or self.current_ipv6_address.find(self.email_ipv6_address) < 0:
            self.send_ipv6_address_to_email(self.current_ipv6_address)
            self.email_ipv6_address = self.obtain_ipv6_address_from_email()
            logging.info('已同步当前与邮件中存储的地址')

    def change_ipv6_address(self,ipv6_address):
        subprocess.Popen('echo '+ipv6_address+' www.xxxx.com >> %systemroot%\system32\drivers\etc\hosts',shell=True)

    def get_ipv6_address_from_web(self):
        try:
            ipv6_address = requests.get('https://v6.ident.me').text
        except:
            ipv6_address = None
        return ipv6_address

    def disconnect_WLAN(self):
        subprocess.Popen('netsh wlan disconnect')

    def disable_WLAN(self,interface):
        subprocess.Popen('netsh interface set interface "'+interface+'" disabled')

    def enable_WLAN(self,interface):
        subprocess.Popen('netsh interface set interface "'+interface+'" enabled')   

    def connect_WLAN(self,wlan_name):
        logging.info('正在联网')
        subprocess.Popen('netsh wlan connect name='+wlan_name)

    def show_WLAN_interface(self):
        interface = subprocess.Popen('netsh wlan show interface').readlines()
        return interface[3][interface[3].find(':')+2:-1]

    def ip_monitor(self,wlan_name):
        # 初始化
        self.check_flag = 1
        logging.info('初始化开始')        
        self.current_ipv6_address = self.get_ipv6_address()
        self.stored_ipv6_address = self.read_ipv6_address()
        self.email_ipv6_address = self.obtain_ipv6_address_from_email()      
        if self.current_ipv6_address is not None:
            self.synchronize_ipv6_address('monitor')
        elif self.current_ipv6_address is None:
            while True:
                if self.current_ipv6_address is None:
                    time.sleep(0.2)
                    self.connect_WLAN(wlan_name)
                    time.sleep(5)
                    self.current_ipv6_address = self.get_ipv6_address()
                elif self.current_ipv6_address is not None:
                    self.synchronize_ipv6_address('monitor')
                    break
        logging.info('初始化完成')
        logging.info('开始监控')
        while True:
            self.current_ipv6_address = self.get_ipv6_address()
            # 检查联网
            if self.current_ipv6_address is None:
                while True:
                    if self.current_ipv6_address is None:                        
                        time.sleep(0.2)
                        self.connect_WLAN(wlan_name)
                        time.sleep(5)
                        self.current_ipv6_address = self.get_ipv6_address()
                    elif self.current_ipv6_address is not None:
                        logging.info('联网成功')
                        break
            # 检查ip变化                        
            if self.current_ipv6_address is not None:
                self.synchronize_ipv6_address('monitor')                
            if self.check_flag == 1:
                self.check_flag = 0
                try:
                    self.get_ipv6_address_from_web()
                except:
                    self.disconnect_WLAN()
                    time.sleep(0.3)
                    self.connect_WLAN(wlan_name)
                time.sleep(60)
            elif self.check_flag == 0:
                time.sleep(60)
                self.check_flag = 1       

if __name__ == "__main__":
    IPv6_monitor().ip_monitor('wifi_name')