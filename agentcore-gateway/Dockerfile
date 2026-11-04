FROM public.ecr.aws/lambda/python:3.12@sha256:4428def7584f7673df2341e011ef9a4e99e526754842aa2f3602bce7f89dc6c1

# Inject corporate CA certificate for SSL inspection proxies.
# Generate corporate-ca.pem with:
#   security find-certificate -a -p /Library/Keychains/System.keychain >> corporate-ca.pem
#   security find-certificate -a -p ~/Library/Keychains/login.keychain-db >> corporate-ca.pem
# Remove this block if building outside a corporate network.
COPY corporate-ca.pem /etc/pki/ca-trust/source/anchors/corporate-ca.pem
RUN update-ca-trust

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./

# SOLAR-2311: The Lambda managed runtime executes under its own non-root sandbox UID
# regardless of the USER directive, so omitting USER does not grant root privileges at
# runtime.  If this image is ever run outside Lambda (ECS, local dev, Kubernetes), add a
# non-root USER directive here and verify that the Lambda bootstrap paths remain writable.

CMD ["lambda_function.lambda_handler"]
