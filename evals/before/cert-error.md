## What's happening

When curl connects over HTTPS, the server presents a certificate, and curl checks that it was signed by a Certificate Authority (CA) it trusts. It does this by following the chain: server cert → intermediate CA(s) → root CA, and the root has to be in curl's trusted CA bundle.

"Unable to get local issuer certificate" means curl couldn't complete that chain. Common causes for an internal API:

1. **The cert is signed by an internal/private CA** that isn't in curl's trust store. This is the most likely one.
2. **The server isn't sending the intermediate certificate**, so curl can't link the server cert to a trusted root.
3. **A TLS-inspecting proxy** (corporate firewall) is re-signing traffic with its own CA.
4. **Curl is using an outdated or wrong CA bundle.**

## Diagnose

```bash
openssl s_client -connect api.internal.example.com:443 -showcerts
```

Look at the chain it prints and at the `Verify return code` at the end. Check:
- Who issued the cert (the `issuer` line)?
- Is there only one cert in the chain (missing intermediates), or a full chain?

## Fixes

**If it's a private CA** (most common): get the CA's root certificate (PEM format) and tell curl to trust it:

```bash
curl --cacert /path/to/internal-ca.pem https://api.internal.example.com/
```

Or set it for all curl calls in your shell:

```bash
export CURL_CA_BUNDLE=/path/to/internal-ca.pem
```

For a system-wide fix, install the CA into the OS trust store:
- Debian/Ubuntu: copy to `/usr/local/share/ca-certificates/internal-ca.crt`, then `sudo update-ca-certificates`
- RHEL/Fedora: copy to `/etc/pki/ca-trust/source/anchors/`, then `sudo update-ca-trust`
- macOS: `sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain internal-ca.pem`

**If the server is missing the intermediate**: fix it on the server by configuring it to serve the full chain (e.g. in nginx, use `fullchain.pem` rather than just the leaf cert for `ssl_certificate`). This is the right fix, since other clients will hit the same problem.

## What not to do

`curl -k` / `--insecure` will make the error go away, but it disables certificate verification entirely, so you lose protection against man-in-the-middle attacks. It's OK for a quick one-off test, but don't leave it in scripts.

Also note that apps and runtimes (Python `requests`, Node, Java) often use their own trust stores, so you may need to configure the CA separately for them (`REQUESTS_CA_BUNDLE`, `NODE_EXTRA_CA_CERTS`, the Java keystore, etc.).
