import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import socket

class ProxyChecker:
    def __init__(self, proxies, options, ip):
        self.ip = ip
        self.proxies = proxies
        self.options = options
        self.results = []

    def check_proxy(self, proxy, protocol):
        if protocol == 'connect':
            return self.check_connect_proxy(proxy)

        try:
            host, port, country = proxy.split(':')
            agent_options = self.get_agent(host, port, protocol)

            if protocol in ['socks5', 'socks4']:
                preferred_protocol = f"{protocol}h" if protocol == 'socks5' else f"{protocol}a"
                try:
                    print(f"Checking {protocol} proxy: {proxy} with preferred agent: {agent_options['preferred']}")  # Debugging
                    response = requests.get('http://localhost', proxies=agent_options['preferred'], timeout=self.options['timeout'])
                    if response.status_code == 200:
                        ip = self.get_ip(response.text)
                        anon = self.get_anon(response.text)
                        server = self.get_server(response.text)
                        return {"protocol": preferred_protocol, "proxy": f"{host}:{port}", "status": "working", "ip": ip, "anon": anon, "server": server, "country": country}
                except requests.RequestException as e:
                    print(f"Preferred protocol for {proxy} failed with error: {e}")

                try:
                    print(f"Checking {protocol} proxy: {proxy} with fallback agent: {agent_options['fallback']}")
                    response = requests.get('http://localhost', proxies=agent_options['fallback'], timeout=self.options['timeout'])
                    if response.status_code == 200:
                        ip = self.get_ip(response.text)
                        anon = self.get_anon(response.text)
                        server = self.get_server(response.text)
                        return {"protocol": protocol, "proxy": f"{host}:{port}", "status": "working", "ip": ip, "anon": anon, "server": server, "country": country}
                except requests.RequestException as e:
                    print(f"Fallback protocol for {proxy} failed with error: {e}")

            else:
                agent = agent_options
                print(f"Checking {protocol} proxy: {proxy} with agent: {agent}")
                verify_ssl = False if protocol == 'https' else True
                response = requests.get('http://localhost', proxies=agent, timeout=self.options['timeout'], verify=verify_ssl)
                if response.status_code == 200:
                    ip = self.get_ip(response.text)
                    anon = self.get_anon(response.text)
                    server = self.get_server(response.text)
                    return {"protocol": protocol, "proxy": f"{host}:{port}", "status": "working", "ip": ip, "anon": anon, "server": server, "country": country}

        except requests.RequestException as e:
            print(f"Proxy {proxy} failed with error: {e}")
        return None

    def check_connect_proxy(self, proxy):
        try:
            host, port, country = proxy.split(':')
            print(f"Checking CONNECT proxy: {proxy}")

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.options['timeout'])
            sock.connect((host, int(port)))

            connect_request = f"CONNECT localhost:80 HTTP/1.1\r\nHost: localhost:80\r\n\r\n"
            sock.sendall(connect_request.encode())

            response = sock.recv(4096).decode()
            if "200 Connection established" in response:
                return {"protocol": "connect", "proxy": f"{host}:{port}", "status": "working", "country": country}
            else:
                print(f"CONNECT proxy {proxy} failed with response: {response}")
                return None

        except Exception as e:
            print(f"CONNECT proxy {proxy} failed with error: {e}")
            return None
        finally:
            sock.close()

    def run_checks(self):
        with ThreadPoolExecutor(max_workers=self.options['threads']) as executor:
            futures = []
            for protocol, proxies in self.proxies.items():
                for proxy in proxies:
                    futures.append(executor.submit(self.check_proxy, proxy, protocol))
            self.results = [future.result() for future in futures]

    def save_results(self):
        grouped_results = {
            'http': [],
            'https': [],
            'socks4': [],
            'socks5': [],
            'connect': []
        }

        for result in self.results:
            if result is not None:
                protocol = result['protocol']
                if protocol.startswith('socks4'):
                    grouped_results['socks4'].append(result)
                elif protocol.startswith('socks5'):
                    grouped_results['socks5'].append(result)
                else:
                    grouped_results[protocol].append(result)

        for protocol, results in grouped_results.items():
            if results:
                with open(f'proxy_check_results_{protocol}.md', 'w', encoding='utf-8') as f:
                    for result in results:
                        f.write(f"Protocol: {result['protocol']}\n")
                        f.write(f"Proxy: {result['proxy']}\n")
                        f.write(f"Status: {result['status']}\n")
                        f.write(f"IP: {result.get('ip', 'N/A')}\n")
                        f.write(f"Anon: {result.get('anon', 'N/A')}\n")
                        f.write(f"Server: {result.get('server', 'N/A')}\n")
                        f.write(f"Country: {result['country']}\n\n")

    def get_ip(self, body):
        trimmed = body.strip()
        if re.match(r'\d+\.\d+\.\d+\.\d+', trimmed):
            return trimmed
        find_ip = re.search(r'REMOTE_ADDR = (.*)', trimmed)
        if find_ip and re.match(r'\d+\.\d+\.\d+\.\d+', find_ip.group(1)):
            return find_ip.group(1)
        return None

    def get_anon(self, body):
        if self.ip in body:
            return "transparent"
        if re.search(r'HTTP_VIA|PROXY_REMOTE_ADDR', body):
            return "anonymous"
        return "elite"

    def get_server(self, body):
        if re.search(r'squid', body, re.IGNORECASE):
            return "squid"
        if re.search(r'mikrotik', body, re.IGNORECASE):
            return "mikrotik"
        if re.search(r'tinyproxy', body, re.IGNORECASE):
            return "tinyproxy"
        if re.search(r'litespeed', body, re.IGNORECASE):
            return "litespeed"
        if re.search(r'varnish', body, re.IGNORECASE):
            return "varnish"
        if re.search(r'haproxy', body, re.IGNORECASE):
            return "haproxy"
        return None

    def get_agent(self, host, port, protocol):
        if protocol == 'socks5':
            return {
                'preferred': {
                    'http': f"socks5h://{host}:{port}",
                    'https': f"socks5h://{host}:{port}"
                },
                'fallback': {
                    'http': f"socks5://{host}:{port}",
                    'https': f"socks5://{host}:{port}"
                }
            }
        elif protocol == 'socks4':
            return {
                'preferred': {
                    'http': f"socks4a://{host}:{port}",
                    'https': f"socks4a://{host}:{port}"
                },
                'fallback': {
                    'http': f"socks4://{host}:{port}",
                    'https': f"socks4://{host}:{port}"
                }
            }
        else:
            return {protocol: f"http://{host}:{port}"}

def read_proxies(file_path):
    try:
        return Path(file_path).read_text(encoding='utf-8').splitlines()
    except UnicodeDecodeError:
        return Path(file_path).read_text(encoding='latin-1').splitlines()

if __name__ == "__main__":
    proxies = {
        'http': read_proxies('http.txt'),
        'https': read_proxies('https.txt'),
        'socks4': read_proxies('socks4.txt'),
        'socks5': read_proxies('socks5.txt'),
        'connect': read_proxies('connect.txt')
    }
    options = {
        "timeout": 30,
        "threads": 100
    }
    checker = ProxyChecker(proxies, options, "127.0.0.1")
    checker.run_checks()
    checker.save_results()
