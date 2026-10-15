FROM python:3.12-slim
WORKDIR /app
COPY requirements-mysql.txt .
RUN pip install --no-cache-dir -r requirements-mysql.txt
COPY . .
CMD ["python", "-m", "riskflow", "demo"]
