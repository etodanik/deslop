curl can't build a chain of trust from your API's certificate to a root CA it trusts. On an internal API, the usual reason is that the certificate was signed by your company's private CA, which isn't in curl's CA bundle. Less often, the server isn't sending its intermediate certificate, a TLS-inspecting corporate proxy is re-signing the traffic, or curl's CA bundle is out of date.

To see which it is, run:

```bash
openssl s_client -connect api.internal.example.com:443 -showcerts
```

Check the `issuer` line, whether more than one certificate comes back, and the `Verify return code` at the end.

If it's a private CA, get that CA's root certificate in PEM format and point curl at it:

```bash
curl --cacert /path/to/internal-ca.pem https://api.internal.example.com/
```

You can also run `export CURL_CA_BUNDLE=/path/to/internal-ca.pem` to apply it to every curl call in your shell. To fix it for the whole machine, add the CA to the OS trust store:

- Debian/Ubuntu: copy it to `/usr/local/share/ca-certificates/internal-ca.crt`, then run `sudo update-ca-certificates`.
- RHEL/Fedora: copy it to `/etc/pki/ca-trust/source/anchors/`, then run `sudo update-ca-trust`.
- macOS: `sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain internal-ca.pem`

If the server is missing its intermediate certificate, fix the server so it sends the full chain. In nginx, for example, set `ssl_certificate` to `fullchain.pem`, not the leaf certificate. That's the better fix, because every other client is hitting the same error.

`curl -k` will make the message go away, but it turns off certificate checking, which leaves you open to man-in-the-middle attacks. It's fine for a one-off test. Don't leave it in a script. Also, many runtimes keep their own trust stores, so Python `requests`, Node and Java may each need the CA configured separately (`REQUESTS_CA_BUNDLE`, `NODE_EXTRA_CA_CERTS`, the Java keystore).
