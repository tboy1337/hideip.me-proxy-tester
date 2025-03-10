# Proxy Tester

A GitHub project for checking and analyzing proxies from the [zloi-user/hideip.me](https://github.com/zloi-user/hideip.me) repository. The script retrieves the proxy list, verifies the working ones, and outputs relevant details such as protocol, anonymity level, and server information.

## Features

- **Multi-Protocol Support**: Checks HTTP, HTTPS, SOCKS4, SOCKS5, and CONNECT proxies.
- **Detailed Reports**: Outputs working proxies with additional details in a markdown report.
- **Anonymity Detection**: Identify proxy anonymity levels (transparent, anonymous, elite).
- **Server Detection**: Recognize proxy server software (Squid, Mikrotik, Tinyproxy, etc.).
- **Country Detection**: Identify the country of the proxy.

## Setup Instructions

### 1. Fork the Repository
Fork this repository to your own GitHub account.

### 2. Adjust Workflow Permissions
1. Go to **Settings** > **Actions** > **General**.
2. Scroll down to **Workflow permissions**.
3. Select **Read and write permissions**.
4. Click **Save**.

## Workflow Overview

- **Fetch Proxy Files**: Downloads the latest proxy files from the [zloi-user/hideip.me](https://github.com/zloi-user/hideip.me) repository.
- **Proxy Validation**: Verifies proxies for functionality and collects metadata.
- **Report Updates**: Commits and pushes the updated report (`proxy_check_results_*.md`) to your repository.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## License

This project is licensed under the [MIT License](LICENSE.txt).
