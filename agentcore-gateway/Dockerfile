FROM public.ecr.aws/lambda/python:3.12

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
CMD ["lambda_function.lambda_handler"]
